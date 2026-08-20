#!/usr/bin/env python3
"""Create the one-time label-free sealed Stage Sixteen prediction artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import benchmark as core
import document_benchmark as documents
from stage16_acquire import (
    ALLOWED_HOSTS, ARTIFACTS, MAX_BYTES, MAX_TOTAL_BYTES, TIMEOUT_SECONDS,
    validate_rights_url, validate_source_url,
)
from stage16_prepare import MAX_TOKENS, OVERLAP_TOKENS, QUERIES, RESOURCE_LIMITS
from stage16_retrieval import (
    CANDIDATE_BUDGET, KNOWN_TERM_COVERAGE_THRESHOLD, TOP_K,
    StageSixteenAreaFive, StageSixteenFlat, StageSixteenScorer, build_records,
    canonical_hash, normalize_query_case_aware, verify_prepared_corpus,
)

SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-sixteen-preregistration-2026-08-13.md"
SCRIPT_NAMES = (
    "stage16_acquire.py", "stage16_prepare.py", "stage16_retrieval.py",
    "stage16_predict.py", "stage16_labels.py", "stage16_evaluate.py",
    "benchmark.py", "document_benchmark.py",
)
EXPECTED_ARTIFACT_IDS = (
    "rfc791", "rfc2131", "rfc5849", "rfc6376", "rfc7230", "rfc3261",
)
PRIOR_BINDINGS = (
    ("stage12_result", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-twelve-held-out-2026-08-13.json", "ddbe8ecbd70e6d7c5035a2c81dd1a8a3bd5ef760f6e0c9aa27fd1445a4607796"),
    ("stage12_score_lock", SCRIPT_DIR / "stage12-corpus" / "stage-twelve-score.lock", "28129496ce6c0e196545c64f1879fdb4417fe60e5e8709ada2793c69f278a803"),
    ("stage13_result", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-thirteen-development-result-2026-08-13.json", "62803a7961f7236de2f25af816d0a081dc81d217bdac8aafe32b4b0ed7434ab7"),
    ("stage13_report", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-thirteen-development-report-2026-08-13.md", "5b103698439be30b687961bfe15d4c03eb977ff22c6055974466297041c62514"),
    ("stage14_preregistration", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-fourteen-preregistration-2026-08-13.md", "8c0dfc720a2be44abcff96a8e611df16440cb9cebf5ffbe1930e776c54a9e0af"),
    ("stage14_incident_report", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-fourteen-protocol-incident-2026-08-13.md", "372119db23c2da56c707750378ccac723a79827ee7063fa592a88aea31c25970"),
    ("stage14_sealed_predictions", SCRIPT_DIR / "stage14-corpus" / "sealed-predictions.json", "2e46afcfffdee241e86f589be415bffffefab4b064f8359af2b6ae93959f1ac8"),
    ("stage14_invalid_labels", SCRIPT_DIR / "stage14-corpus" / "relevance-labels.json", "a0048dad3d2d87db9852340bdfb900264c78c516b33c4f68dda3ad7af9a7074e"),
    ("stage15_preregistration", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-fifteen-preregistration-2026-08-13.md", "2ec990bebb68a3da273433f8324e2ab3dba5121205c46a774719a9b6b03f52c7"),
    ("stage15_report", SCRIPT_DIR.parent.parent / "data" / "elastic-hippocampus-stage-fifteen-report-2026-08-13.md", "a093cb4f7315e256397406c4d4a1d074fa3b33c0db1dcb8625f794d44c4ba7e5"),
)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_prior_bindings() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, path, expected in PRIOR_BINDINGS:
        digest = sha256_file(path)
        if digest != expected:
            raise ValueError(f"immutable prior-stage hash drift: {name}")
        observed[name] = digest
    return observed

def write_new_json(path: Path, value: Any) -> str:
    encoded = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    return hashlib.sha256(encoded).hexdigest()

def verify_frozen_bindings(loaded: dict[str, Any]) -> dict[str, str]:
    if tuple(item["artifact_id"] for item in ARTIFACTS) != EXPECTED_ARTIFACT_IDS:
        raise ValueError("frozen acquisition artifact order drift")
    if ALLOWED_HOSTS != frozenset({"www.rfc-editor.org"}):
        raise ValueError("frozen source host allowlist drift")
    if (MAX_BYTES, MAX_TOTAL_BYTES, TIMEOUT_SECONDS, MAX_TOKENS, OVERLAP_TOKENS) != (5 * 1024 * 1024, 30 * 1024 * 1024, 30, 320, 40):
        raise ValueError("frozen transport or chunk constants drift")
    acquisition = loaded["acquisition"]
    if acquisition.get("transport") != {
        "allowed_hosts": sorted(ALLOWED_HOSTS), "https_only": True,
        "max_bytes_per_artifact": MAX_BYTES, "max_total_bytes": MAX_TOTAL_BYTES,
        "timeout_seconds": TIMEOUT_SECONDS, "user_agent": "Stage16ConfirmationAcquirer/1.0",
        "sequential": True, "content_types": {"txt": "text/plain", "html": "text/html"},
    }:
        raise ValueError("acquisition transport does not match the frozen specification")
    acquired = acquisition.get("artifacts")
    if not isinstance(acquired, list) or [item.get("artifact_id") for item in acquired] != list(EXPECTED_ARTIFACT_IDS):
        raise ValueError("frozen acquisition must contain exactly six artifacts in frozen order")
    by_id = {item["artifact_id"]: item for item in acquired}
    for specification in ARTIFACTS:
        artifact = by_id.get(specification["artifact_id"])
        if artifact is None or any(artifact.get(field) != specification[field] for field in ("title", "publisher", "version", "url", "raw_file", "rights_url")):
            raise ValueError(f"frozen source metadata drift: {specification['artifact_id']}")
        validate_source_url(artifact["url"]); validate_source_url(artifact["retrieved_url"]); validate_rights_url(artifact["rights_url"])
        expected_media_type = "text/plain" if artifact["raw_file"].endswith(".txt") else "text/html"
        if artifact.get("media_type") != expected_media_type or artifact.get("byte_size", MAX_BYTES + 1) > MAX_BYTES:
            raise ValueError(f"frozen source media/size drift: {specification['artifact_id']}")
    config = loaded["chunks_document"].get("config", {})
    chunking = config.get("chunking", {})
    if config.get("offline") is not True or config.get("network_step") is not False or config.get("preparation_candidates") is not False:
        raise ValueError("prepared offline/candidate policy drift")
    if chunking.get("max_tokens") != MAX_TOKENS or chunking.get("overlap_tokens") != OVERLAP_TOKENS or loaded["chunks_document"].get("artifact_count") != 6:
        raise ValueError("prepared chunk/artifact constants drift")
    preflight = config.get("resource_preflight", {})
    if preflight.get("status") != "PASS" or preflight.get("limits") != RESOURCE_LIMITS:
        raise ValueError("prepared Stage Sixteen resource ceilings drift")
    runtime = loaded["runtime_document"]
    if runtime.get("network_step") is not False or runtime.get("candidate_generation") is not False or runtime.get("resource_preflight") != preflight:
        raise ValueError("prepared runtime/offline binding drift")
    if config.get("queries") != list(QUERIES) or config.get("query_strings_sha256") != canonical_hash([item["query"] for item in QUERIES]):
        raise ValueError("prepared query set is not the exact frozen Stage Sixteen set")
    if len(QUERIES) != 20 or sum(q["kind"] == "positive" for q in QUERIES) != 16 or sum(q["kind"] == "control" for q in QUERIES) != 4:
        raise ValueError("frozen query split drift")
    expected_assignments = (
        "rfc791", "rfc791", "rfc791", "rfc2131", "rfc2131", "rfc2131",
        "rfc5849", "rfc5849", "rfc5849", "rfc6376", "rfc6376", "rfc6376",
        "rfc7230", "rfc7230", "rfc3261", "rfc3261", "", "", "", "",
    )
    if tuple(q["artifact_id"] for q in QUERIES) != expected_assignments:
        raise ValueError("frozen 3/3/3/3/2/2 artifact distribution drift")
    prereg = PREREGISTRATION.read_text(encoding="utf-8")
    script_hashes: dict[str, str] = {}
    for name in SCRIPT_NAMES:
        match = re.search(rf"`demos/elastic-hippocampus-proof/{re.escape(name)}`: `([0-9a-f]{{64}})`", prereg)
        if match is None: raise ValueError(f"preregistration lacks frozen hash for {name}")
        observed = sha256_file(SCRIPT_DIR / name)
        if observed != match.group(1): raise ValueError(f"frozen script hash mismatch: {name}")
        script_hashes[name] = observed
    return script_hashes


def execute_once(method: core.Method, query: core.SearchQuery, vocabulary: frozenset[str]) -> tuple[core.Retrieval, core.QueryResult]:
    coverage = sum(term in vocabulary for term in query.tokens) / len(query.tokens)
    if coverage < KNOWN_TERM_COVERAGE_THRESHOLD:
        retrieval = core.Retrieval((), 0, 0, (), len(query.tokens), "insufficient_known_subject")
    else:
        retrieval = method.retrieve(query)
    ranked = method.ranker.rank(retrieval.candidate_ids, query)
    return retrieval, core.QueryResult(ranked, retrieval.evidence_validations, retrieval.integrity_failures, retrieval.trace, retrieval.routing_work, retrieval.stop_reason)


def predict(corpus_dir: Path) -> dict[str, Any]:
    loaded = verify_prepared_corpus(corpus_dir)
    script_hashes = verify_frozen_bindings(loaded)
    prior_hashes = verify_prior_bindings()
    chunks = loaded["chunks"]; artifact_ids = loaded["artifact_ids"]
    records = build_records(chunks, artifact_ids)
    core.CANDIDATE_BUDGET = CANDIDATE_BUDGET; core.TOP_K = TOP_K
    documents.CANDIDATE_BUDGET = CANDIDATE_BUDGET; documents.TOP_K = TOP_K
    scorer = StageSixteenScorer(chunks, artifact_ids)
    methods: tuple[tuple[str, core.Method], ...] = (
        ("flat_scan", StageSixteenFlat(records, scorer)),
        ("area_five_scan_ranked_cells", StageSixteenAreaFive(records, scorer, "scan")),
        ("area_five_indexed_ranked_cells", StageSixteenAreaFive(records, scorer, "indexed")),
    )
    frequency: Counter[str] = Counter()
    for record in records: frequency.update(set(core.tokenize(record.value)))
    vocabulary = frozenset(term for record in records for term in record.tokens)
    rows: list[dict[str, Any]] = []; integrity = sum(not record.valid() for record in records); provenance = sum(not record.source for record in records); determinism = 0
    for spec in QUERIES:
        tokens = normalize_query_case_aware(spec["query"], frequency)
        if not tokens: raise ValueError(f"query normalization removed every term for {spec['query_id']}")
        query = core.SearchQuery(spec["query_id"], "stage_sixteen", spec["query"], tokens, None)
        method_rows: dict[str, Any] = {}
        for name, method in methods:
            first_retrieval, first = execute_once(method, query, vocabulary)
            second_retrieval, second = execute_once(method, query, vocabulary)
            if first_retrieval != second_retrieval or first != second: determinism += 1
            integrity += first.integrity_failures
            returned = set(first_retrieval.candidate_ids) | set(first.ranked_ids)
            for record_id in returned:
                if not 0 <= record_id < len(records) or records[record_id].record_id != record_id or not records[record_id].valid(): integrity += 1
                elif not records[record_id].source: provenance += 1
            scope = "global" if name == "flat_scan" else "artifact"
            selected, _, scores = scorer.score(query, scope)
            method_rows[name] = {
                "selected_artifact": selected,
                "candidate_chunk_ids": [chunks[i]["chunk_id"] for i in first_retrieval.candidate_ids],
                "ranked_chunk_ids": [chunks[i]["chunk_id"] for i in first.ranked_ids],
                "routing_trace_chunk_ids": [chunks[i]["chunk_id"] for i in first.trace],
                "score_trace": [{"chunk_id": chunks[i]["chunk_id"], "score": round(float(scores[i]), 15)} for i in first_retrieval.candidate_ids],
                "stop_reason": first.stop_reason,
                "evidence_validations": first.evidence_validations,
                "routing_work": first.routing_work,
                "integrity_failures": first.integrity_failures,
            }
        rows.append({
            "query_id": spec["query_id"], "query": spec["query"],
            "expected_control": spec["kind"] == "control",
            "normalized_tokens": list(tokens), "absent_terms": sorted(set(tokens) - vocabulary),
            "methods": method_rows,
        })
    parity = []
    for row in rows:
        scan = row["methods"]["area_five_scan_ranked_cells"]; indexed = row["methods"]["area_five_indexed_ranked_cells"]
        if any(scan[field] != indexed[field] for field in ("selected_artifact", "candidate_chunk_ids", "ranked_chunk_ids", "routing_trace_chunk_ids", "score_trace", "stop_reason", "evidence_validations", "integrity_failures")):
            parity.append(row["query_id"])
    failures = {"integrity": integrity, "provenance": provenance, "determinism": determinism}
    if sum(failures.values()) or parity:
        raise ValueError(f"prediction validation failed: failures={failures}, parity={parity}")
    return {
        "schema_version": 1, "stage": 16, "state": "sealed", "label_free": True,
        "gold_available_to_retrieval": False,
        "corpus_merkle_root": loaded["corpus_merkle_root"],
        "query_strings_sha256": canonical_hash([q["query"] for q in QUERIES]),
        "configuration": {"candidate_budget": CANDIDATE_BUDGET, "top_k": TOP_K, "controls": "known normalized term coverage below 0.75 causes abstention", "scorer": scorer.metadata()},
        "input_hashes": {"corpus_files": loaded["file_hashes"], "scripts": script_hashes, "prior_stages": prior_hashes},
        "validations": {"failures": failures, "area_five_scan_index_parity_failures": parity, "raw_provenance_verified": True, "merkle_verified": True, "deterministic_double_run": True},
        "queries": rows,
    }


def main() -> int:
    corpus_dir = (SCRIPT_DIR / "stage16-corpus").resolve()
    output = (corpus_dir / "sealed-predictions.json").resolve()
    if os.path.lexists(output):
        raise FileExistsError(f"refusing to overwrite sealed predictions: {output}")
    result = predict(corpus_dir); digest = write_new_json(output, result)
    print(f"sealed predictions={output} sha256={digest} queries=20 labels=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
