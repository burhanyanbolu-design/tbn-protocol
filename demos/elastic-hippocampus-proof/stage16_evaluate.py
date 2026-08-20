#!/usr/bin/env python3
"""Build a blind two-file Stage Sixteen pool or consume it exactly once."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from stage16_prepare import QUERIES
from stage16_retrieval import canonical_hash, verify_prepared_corpus

TOP_K = 5
POOL_TFIDF_K = 15
POOL_LSA_K = 15
LSA_COMPONENTS = 64
LSA_RANDOM_STATE = 20260813
CANDIDATE_DOMAIN = "stage16-candidate|"
SEALED_PROVENANCE = "sealed_stage16_flat_global_top30"
METHOD_NAMES = (
    "flat_scan", "area_five_scan_ranked_cells",
    "area_five_indexed_ranked_cells",
)
FROZEN_FILES = {
    "stage16_acquire.py", "stage16_prepare.py", "stage16_retrieval.py",
    "stage16_predict.py", "stage16_labels.py", "stage16_evaluate.py",
    "benchmark.py", "document_benchmark.py",
}
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"
PREREGISTRATION = DATA_DIR / "elastic-hippocampus-stage-sixteen-preregistration-2026-08-13.md"
CORPUS_DIR = (SCRIPT_DIR / "stage16-corpus").resolve()
PREDICTIONS_PATH = (CORPUS_DIR / "sealed-predictions.json").resolve()
POOL_PATH = (CORPUS_DIR / "adjudication-pool.json").resolve()
REVIEW_PATH = (CORPUS_DIR / "adjudication-review.json").resolve()
PROPOSAL_PATH = (CORPUS_DIR / "blind-label-proposal.json").resolve()
LABELS_PATH = (CORPUS_DIR / "relevance-labels.json").resolve()
LOCK_PATH = (CORPUS_DIR / "stage-sixteen-score.lock").resolve()
RESULT_PATH = (DATA_DIR / "elastic-hippocampus-stage-sixteen-held-out-2026-08-13.json").resolve()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes(); value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value, raw


def write_new_bytes(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    return sha256_bytes(raw)


def write_lock_exclusive(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    return sha256_bytes(raw)


def verify_predictions(path: Path, loaded: dict[str, Any]) -> tuple[dict[str, Any], str]:
    value, raw = load_json(path); digest = sha256_bytes(raw); query_hash = canonical_hash([q["query"] for q in QUERIES])
    if value.get("schema_version") != 1 or value.get("stage") != 16 or value.get("state") != "sealed" or value.get("label_free") is not True or value.get("gold_available_to_retrieval") is not False:
        raise ValueError("predictions are not sealed label-free Stage Sixteen")
    if value.get("corpus_merkle_root") != loaded["corpus_merkle_root"] or value.get("query_strings_sha256") != query_hash:
        raise ValueError("prediction corpus/query binding mismatch")
    if value.get("input_hashes", {}).get("corpus_files") != loaded["file_hashes"]:
        raise ValueError("prediction prepared-file hash binding mismatch")
    scripts = value.get("input_hashes", {}).get("scripts")
    if not isinstance(scripts, dict) or set(scripts) != FROZEN_FILES:
        raise ValueError("prediction script binding set mismatch")
    prereg = PREREGISTRATION.read_text(encoding="utf-8")
    script_dir = Path(__file__).resolve().parent
    for name, expected in scripts.items():
        match = re.search(rf"`demos/elastic-hippocampus-proof/{re.escape(name)}`: `([0-9a-f]{{64}})`", prereg)
        if match is None:
            raise ValueError(f"preregistration lacks frozen hash for {name}")
        if expected != match.group(1):
            raise ValueError(f"prediction/preregistration script hash mismatch: {name}")
        if sha256_bytes((script_dir / name).read_bytes()) != expected:
            raise ValueError(f"prediction script hash mismatch: {name}")
    rows = value.get("queries")
    if not isinstance(rows, list) or [row.get("query_id") for row in rows] != [q["query_id"] for q in QUERIES]:
        raise ValueError("prediction query set/order mismatch")
    all_ids = {chunk["chunk_id"] for chunk in loaded["chunks"]}
    for row, spec in zip(rows, QUERIES):
        if row.get("query") != spec["query"] or row.get("expected_control") != (spec["kind"] == "control"):
            raise ValueError(f"prediction frozen query mismatch: {spec['query_id']}")
        methods = row.get("methods")
        if not isinstance(methods, dict) or set(methods) != set(METHOD_NAMES): raise ValueError("prediction method set mismatch")
        for method in methods.values():
            candidates = method.get("candidate_chunk_ids"); ranked = method.get("ranked_chunk_ids")
            if not isinstance(candidates, list) or not isinstance(ranked, list) or len(candidates) > 30 or len(ranked) > 5:
                raise ValueError("invalid sealed candidate/ranking size")
            if len(candidates) != len(set(candidates)) or len(ranked) != len(set(ranked)) or not set(ranked) <= set(candidates) or not set(candidates) <= all_ids:
                raise ValueError("invalid or unknown sealed prediction IDs")
    validations = value.get("validations", {})
    if validations.get("failures") != {"integrity": 0, "provenance": 0, "determinism": 0} or validations.get("area_five_scan_index_parity_failures") != []:
        raise ValueError("sealed prediction validations did not pass")
    return value, digest


def ranked_indices(scores: Iterable[float], chunks: tuple[dict[str, Any], ...]) -> list[int]:
    values = [float(score) if math.isfinite(float(score)) else 0.0 for score in scores]
    return sorted(range(len(chunks)), key=lambda index: (-values[index], chunks[index]["chunk_id"]))


def independent_pool_rankings(chunks: tuple[dict[str, Any], ...], query_text: str, state: dict[str, Any]) -> tuple[list[int], list[int]]:
    vectorizer: TfidfVectorizer = state["vectorizer"]; matrix = state["matrix"]; svd: TruncatedSVD = state["svd"]; document_lsa = state["document_lsa"]
    query_vector = vectorizer.transform([query_text]); tfidf_scores = (matrix @ query_vector.T).toarray().ravel()
    query_lsa = svd.transform(query_vector)[0]; denominator = np.linalg.norm(document_lsa, axis=1) * np.linalg.norm(query_lsa)
    lsa_scores = np.divide(document_lsa @ query_lsa, denominator, out=np.zeros(len(chunks)), where=denominator != 0)
    return ranked_indices(tfidf_scores, chunks)[:POOL_TFIDF_K], ranked_indices(lsa_scores, chunks)[:POOL_LSA_K]


def opaque_key(query_id: str, chunk_id: str) -> str:
    return "c-" + hashlib.sha256((CANDIDATE_DOMAIN + query_id + "|" + chunk_id).encode()).hexdigest()


def order_key(query_id: str, chunk_id: str) -> str:
    return hashlib.sha256((query_id + "|" + chunk_id).encode()).hexdigest()


def build_pool(corpus_dir: Path, predictions_path: Path, pool_output: Path, review_output: Path) -> tuple[str, str]:
    if os.path.lexists(pool_output) or os.path.lexists(review_output):
        raise FileExistsError("refusing to overwrite adjudication pool or review file")
    loaded = verify_prepared_corpus(corpus_dir); predictions, prediction_hash = verify_predictions(predictions_path, loaded)
    chunks = loaded["chunks"]; by_id = {chunk["chunk_id"]: chunk for chunk in chunks}; by_index = {chunk["chunk_id"]: index for index, chunk in enumerate(chunks)}
    vectorizer_config = {"analyzer": "word", "lowercase": True, "norm": "l2", "smooth_idf": True, "sublinear_tf": False, "token_pattern": r"(?u)\b\w\w+\b", "use_idf": True}
    vectorizer = TfidfVectorizer(**vectorizer_config); matrix = vectorizer.fit_transform([chunk["text"] for chunk in chunks])
    if min(matrix.shape) <= LSA_COMPONENTS: raise ValueError("independent LSA-64 dimensions unavailable")
    svd = TruncatedSVD(n_components=LSA_COMPONENTS, algorithm="randomized", n_iter=5, random_state=LSA_RANDOM_STATE); document_lsa = svd.fit_transform(matrix)
    independent_state = {"vectorizer": vectorizer, "matrix": matrix, "svd": svd, "document_lsa": document_lsa}
    private_queries: list[dict[str, Any]] = []; review_queries: list[dict[str, Any]] = []
    for spec, prediction in zip(QUERIES, predictions["queries"]):
        flat = prediction["methods"]["flat_scan"]["candidate_chunk_ids"][:30]
        tfidf_rows, lsa_rows = independent_pool_rankings(chunks, spec["query"], independent_state)
        provenance: dict[str, set[str]] = {}
        def add(chunk_id: str, method: str) -> None:
            provenance.setdefault(chunk_id, set()).add(method)
        for chunk_id in flat: add(chunk_id, SEALED_PROVENANCE)
        for index in tfidf_rows: add(chunks[index]["chunk_id"], "independent_all_corpus_tfidf_top15")
        for index in lsa_rows: add(chunks[index]["chunk_id"], "independent_all_corpus_lsa64_top15")
        initial = tuple(provenance)
        for chunk_id in initial:
            chunk = by_id[chunk_id]
            for relation, adjacent in (("previous", chunk.get("previous_chunk_id")), ("next", chunk.get("next_chunk_id"))):
                if adjacent is not None: add(adjacent, f"within_artifact_{relation}_adjacent")
        ordered_ids = sorted(provenance, key=lambda chunk_id: (order_key(spec["query_id"], chunk_id), chunk_id))
        private_candidates: list[dict[str, Any]] = []; review_candidates: list[dict[str, Any]] = []
        for chunk_id in ordered_ids:
            chunk = by_id[chunk_id]; key = opaque_key(spec["query_id"], chunk_id)
            private_candidates.append({"candidate_key": key, "chunk_id": chunk_id, "artifact_id": chunk["artifact_id"], "text_sha256": chunk["text_sha256"], "method_provenance": sorted(provenance[chunk_id]), "corpus_index": by_index[chunk_id]})
            review_candidates.append({"candidate_key": key, "heading": chunk["heading"], "text": chunk["text"], "source_title": chunk["source"]["title"]})
        private_queries.append({"query_id": spec["query_id"], "query": spec["query"], "candidates": private_candidates})
        review_queries.append({"query_id": spec["query_id"], "query": spec["query"], "candidates": review_candidates})
    query_hash = canonical_hash([q["query"] for q in QUERIES])
    common = {"schema_version": 1, "stage": 16, "corpus_merkle_root": loaded["corpus_merkle_root"], "query_strings_sha256": query_hash, "sealed_predictions_sha256": prediction_hash}
    review = {**common, "state": "blind_review", "privacy": "No rank, score, method, chunk_id, artifact_id, or evaluator mapping is exposed.", "queries": review_queries}
    review_raw = json_bytes(review); review_hash = sha256_bytes(review_raw)
    proposal_schema = {"schema_version": 1, "stage": 16, "state": "blind_machine_proposal", "label_provenance": "machine-pooled", "independent_human_judgment": False, "labels": {"q01": ["opaque candidate_key"], "q02": [], "...": "exactly q01..q20; every positive nonempty; every control empty"}}
    pool = {**common, "state": "private_machine_pool", "review_sha256": review_hash, "candidate_generation": {"sealed_prediction": {"method": "flat/global", "top_k": 30, "provenance": SEALED_PROVENANCE}, "independent_tfidf": {"scope": "all corpus", "top_k": 15, "vectorizer": vectorizer_config}, "independent_lsa": {"scope": "all corpus", "top_k": 15, "components": 64, "algorithm": "randomized", "n_iter": 5, "random_state": LSA_RANDOM_STATE, "similarity": "cosine"}, "adjacency": "one-hop previous and next within artifact for every pre-adjacency union member", "order": "SHA-256(query_id + '|' + chunk_id), ascending"}, "queries": private_queries, "expected_proposal_schema": proposal_schema}
    pool_raw = json_bytes(pool)
    # Paired exclusive creation is deliberately review-first. If pool creation
    # fails for any reason, the partial canonical review remains preserved and
    # the attempt aborts; this function never deletes, repairs, or retries it.
    review_digest = write_new_bytes(review_output, review_raw)
    pool_digest = write_new_bytes(pool_output, pool_raw)
    print(f"adjudication-review {review_output} sha256={review_digest} queries=20")
    print(f"adjudication-pool {pool_output} sha256={pool_digest} queries=20")
    return pool_digest, review_digest


def quality(candidate_ids: list[str], ranked_ids: list[str], relevant: set[str]) -> dict[str, float]:
    if not relevant:
        return {"candidate_recall": 0.0, "recall_at_5": 0.0, "ndcg_at_5": 0.0, "mrr": 0.0, "hit_at_5": 0.0, "nonempty_retrieval": float(bool(ranked_ids))}
    candidate_hits = len(relevant & set(candidate_ids)); ranked = ranked_ids[:TOP_K]; hits = len(relevant & set(ranked))
    dcg = sum(1.0 / math.log2(position + 1) for position, item in enumerate(ranked, 1) if item in relevant)
    ideal = sum(1.0 / math.log2(position + 1) for position in range(1, min(TOP_K, len(relevant)) + 1))
    reciprocal = next((1.0 / position for position, item in enumerate(ranked_ids, 1) if item in relevant), 0.0)
    return {"candidate_recall": candidate_hits / len(relevant), "recall_at_5": hits / len(relevant), "ndcg_at_5": dcg / ideal, "mrr": reciprocal, "hit_at_5": float(hits > 0), "nonempty_retrieval": 0.0}


def rounded(value: float) -> float:
    return round(float(value), 6)


def mean(values: Iterable[float]) -> float:
    items = list(values); return statistics.fmean(items) if items else 0.0


def evaluate_method(name: str, prediction_rows: list[dict[str, Any]], labels: dict[str, list[str]], positive_ids: set[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []; validations: list[int] = []; routing: list[int] = []
    for row in prediction_rows:
        method = row["methods"][name]; gold = set(labels[row["query_id"]]); metrics = quality(method["candidate_chunk_ids"], method["ranked_chunk_ids"], gold)
        validations.append(method["evidence_validations"]); routing.append(method["routing_work"])
        rows.append({"query_id": row["query_id"], "candidate_chunk_ids": method["candidate_chunk_ids"], "ranked_chunk_ids": method["ranked_chunk_ids"], "selected_artifact": method["selected_artifact"], "stop_reason": method["stop_reason"], "evidence_validations": method["evidence_validations"], "routing_work": method["routing_work"], "evaluation": {"gold_chunk_ids": sorted(gold), **{key: rounded(value) for key, value in metrics.items()}}})
    positives = [row for row in rows if row["query_id"] in positive_ids]; controls = [row for row in rows if row["query_id"] not in positive_ids]
    metrics = {"candidate_recall": rounded(mean(row["evaluation"]["candidate_recall"] for row in positives)), "recall_at_5": rounded(mean(row["evaluation"]["recall_at_5"] for row in positives)), "ndcg_at_5": rounded(mean(row["evaluation"]["ndcg_at_5"] for row in positives)), "mrr": rounded(mean(row["evaluation"]["mrr"] for row in positives)), "positive_hits_at_5": int(sum(row["evaluation"]["hit_at_5"] for row in positives)), "control_nonempty_retrievals": int(sum(row["evaluation"]["nonempty_retrieval"] for row in controls)), "evidence_validations_median": rounded(statistics.median(validations)), "routing_work_median": rounded(statistics.median(routing))}
    return {"label": name, "metrics": metrics, "queries": rows}


def add_gate(checks: list[dict[str, Any]], name: str, passed: bool, observed: Any, threshold: Any) -> None:
    checks.append({"name": name, "passed": bool(passed), "observed": observed, "threshold": threshold})


def evaluate_gates(loaded: dict[str, Any], methods: dict[str, dict[str, Any]], labels: dict[str, list[str]], failures: dict[str, int], parity: list[str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []; positives = [q for q in QUERIES if q["kind"] == "positive"]; controls = [q for q in QUERIES if q["kind"] == "control"]
    area = methods["area_five_indexed_ranked_cells"]["metrics"]; flat = methods["flat_scan"]["metrics"]
    add_gate(checks, "exact artifact count", len(loaded["artifact_ids"]) == 6, len(loaded["artifact_ids"]), 6)
    add_gate(checks, "chunk count is within 400..2000 inclusive", 400 <= len(loaded["chunks"]) <= 2000, len(loaded["chunks"]), "400..2000 inclusive")
    add_gate(checks, "exact query count", len(labels) == 20, len(labels), 20)
    add_gate(checks, "exact positive/control split", len(positives) == 16 and len(controls) == 4, {"positive": len(positives), "controls": len(controls)}, {"positive": 16, "controls": 4})
    add_gate(checks, "all labels resolve in the bound candidate pool", all(labels[q["query_id"]] for q in positives) and all(not labels[q["query_id"]] for q in controls), {"positive_labels": sum(bool(labels[q["query_id"]]) for q in positives), "empty_controls": sum(not labels[q["query_id"]] for q in controls)}, True)
    add_gate(checks, "zero integrity/provenance/determinism failures", sum(failures.values()) == 0, failures, 0)
    add_gate(checks, "exact Area Five scan/index logical parity", not parity, parity, 0)
    add_gate(checks, "Area Five positive Hit@5 >= 13/16", area["positive_hits_at_5"] >= 13, area["positive_hits_at_5"], ">= 13")
    add_gate(checks, "Area Five Recall@5 >= 0.60", area["recall_at_5"] >= 0.60, area["recall_at_5"], ">= 0.60")
    add_gate(checks, "Area Five nDCG@5 >= 0.60", area["ndcg_at_5"] >= 0.60, area["ndcg_at_5"], ">= 0.60")
    add_gate(checks, "Area Five MRR >= 0.60", area["mrr"] >= 0.60, area["mrr"], ">= 0.60")
    recall_deficit = rounded(flat["recall_at_5"] - area["recall_at_5"]); ndcg_deficit = rounded(flat["ndcg_at_5"] - area["ndcg_at_5"])
    add_gate(checks, "Area Five recall deficit from flat <= 0.10", recall_deficit <= 0.10 + 1e-12, recall_deficit, "<= 0.10")
    add_gate(checks, "Area Five nDCG deficit from flat <= 0.10", ndcg_deficit <= 0.10 + 1e-12, ndcg_deficit, "<= 0.10")
    area_rows = {row["query_id"]: row for row in methods["area_five_indexed_ranked_cells"]["queries"]}
    artifact_hits = {artifact: any(area_rows[q["query_id"]]["evaluation"]["hit_at_5"] > 0 for q in positives if q["artifact_id"] == artifact) for artifact in loaded["artifact_ids"]}
    add_gate(checks, "every positive artifact group has a hit", len(artifact_hits) == 6 and all(artifact_hits.values()), artifact_hits, "6/6")
    control_nonempty = {name: result["metrics"]["control_nonempty_retrievals"] for name, result in methods.items()}
    add_gate(checks, "all methods have zero nonempty retrieval on controls", all(value == 0 for value in control_nonempty.values()), control_nonempty, 0)
    scan_work = methods["area_five_scan_ranked_cells"]["metrics"]["routing_work_median"]; indexed_work = area["routing_work_median"]
    add_gate(checks, "indexed median routing work < scan and <= 25% of scan", indexed_work < scan_work and indexed_work <= 0.25 * scan_work, {"indexed": indexed_work, "scan": scan_work, "fraction": rounded(indexed_work / max(1.0, scan_work))}, "indexed < scan and <= 0.25 * scan")
    add_gate(checks, "Area Five indexed median evidence validations <= 30", area["evidence_validations_median"] <= 30, area["evidence_validations_median"], "<= 30")
    if len(checks) != 17: raise AssertionError("exactly 17 gates are required")
    return checks


def verify_pool_review_labels(pool_path: Path, review_path: Path, proposal_path: Path, labels_path: Path, predictions_hash: str, loaded: dict[str, Any]) -> tuple[dict[str, Any], str, str, str, dict[str, list[str]], str]:
    pool, pool_raw = load_json(pool_path); review, review_raw = load_json(review_path); proposal, proposal_raw = load_json(proposal_path); labels_doc, labels_raw = load_json(labels_path)
    pool_hash = sha256_bytes(pool_raw); review_hash = sha256_bytes(review_raw); proposal_hash = sha256_bytes(proposal_raw); labels_hash = sha256_bytes(labels_raw); query_hash = canonical_hash([q["query"] for q in QUERIES])
    common = {"corpus_merkle_root": loaded["corpus_merkle_root"], "query_strings_sha256": query_hash, "sealed_predictions_sha256": predictions_hash}
    if pool.get("schema_version") != 1 or pool.get("stage") != 16 or pool.get("state") != "private_machine_pool" or any(pool.get(key) != value for key, value in common.items()) or pool.get("review_sha256") != review_hash:
        raise ValueError("private pool hash/binding mismatch")
    if review.get("schema_version") != 1 or review.get("stage") != 16 or review.get("state") != "blind_review" or any(review.get(key) != value for key, value in common.items()):
        raise ValueError("review hash/binding mismatch")
    pool_rows = pool.get("queries"); review_rows = review.get("queries")
    expected_ids = [q["query_id"] for q in QUERIES]
    if not isinstance(pool_rows, list) or not isinstance(review_rows, list) or [row.get("query_id") for row in pool_rows] != expected_ids or [row.get("query_id") for row in review_rows] != expected_ids:
        raise ValueError("pool/review query set mismatch")
    key_domains: dict[str, set[str]] = {}
    for spec, private, public in zip(QUERIES, pool_rows, review_rows):
        if private.get("query") != spec["query"] or public.get("query") != spec["query"]: raise ValueError("pool/review query text mismatch")
        private_candidates = private.get("candidates"); public_candidates = public.get("candidates")
        if not isinstance(private_candidates, list) or not isinstance(public_candidates, list): raise ValueError("invalid pool/review candidates")
        private_keys = [item.get("candidate_key") for item in private_candidates]; public_keys = [item.get("candidate_key") for item in public_candidates]
        if private_keys != public_keys or len(private_keys) != len(set(private_keys)): raise ValueError("pool/review opaque key mismatch")
        expected_order = sorted(private_candidates, key=lambda item: (order_key(spec["query_id"], item["chunk_id"]), item["chunk_id"]))
        if private_candidates != expected_order: raise ValueError("private pool random order binding mismatch")
        for item in private_candidates:
            if item.get("candidate_key") != opaque_key(spec["query_id"], item.get("chunk_id", "")): raise ValueError("invalid opaque candidate key")
        for item in public_candidates:
            if set(item) != {"candidate_key", "heading", "text", "source_title"}: raise ValueError("review leaks private rank/score/method/chunk identity")
        key_domains[spec["query_id"]] = set(private_keys)
    required = {"schema_version": 1, "stage": 16, "state": "frozen", "label_provenance": "machine-pooled", "independent_human_judgment": False, "corpus_merkle_root": loaded["corpus_merkle_root"], "corpus_file_hashes": loaded["file_hashes"], "query_strings_sha256": query_hash, "pool_sha256": pool_hash, "review_sha256": review_hash, "predictions_sha256": predictions_hash, "proposal_sha256": proposal_hash, "evaluator_join_policy": "exactly one join from opaque candidate keys to private chunk IDs after score-lock creation"}
    if any(labels_doc.get(key) != value for key, value in required.items()): raise ValueError("labels are not frozen and bound to proposal, pool, review, predictions, corpus, and queries")
    proposal_required = {"schema_version": 1, "stage": 16, "state": "blind_machine_proposal", "label_provenance": "machine-pooled", "independent_human_judgment": False}
    if set(proposal) != {*proposal_required, "labels"} or any(proposal.get(key) != value for key, value in proposal_required.items()): raise ValueError("canonical proposal schema or provenance mismatch")
    labels = labels_doc.get("labels")
    if labels != proposal.get("labels"): raise ValueError("final labels differ from the hash-bound canonical proposal")
    if not isinstance(labels, dict) or set(labels) != set(expected_ids): raise ValueError("labels must contain exactly q01..q20")
    for spec in QUERIES:
        values = labels[spec["query_id"]]
        if not isinstance(values, list) or len(values) != len(set(values)) or any(not isinstance(value, str) for value in values): raise ValueError("each label must be a unique opaque-key list")
        if not set(values) <= key_domains[spec["query_id"]]: raise ValueError(f"unknown candidate key in labels: {spec['query_id']}")
        if (spec["kind"] == "positive") != bool(values): raise ValueError(f"positive/control label mismatch: {spec['query_id']}")
    return pool, pool_hash, review_hash, proposal_hash, labels, labels_hash


def join_labels_once(pool: dict[str, Any], labels: dict[str, list[str]]) -> dict[str, list[str]]:
    """The sole evaluator join from opaque reviewer keys to private chunk IDs."""
    joined: dict[str, list[str]] = {}
    for row in pool["queries"]:
        mapping = {item["candidate_key"]: item["chunk_id"] for item in row["candidates"]}
        joined[row["query_id"]] = [mapping[key] for key in labels[row["query_id"]]]
    return joined


def score_once(corpus_dir: Path, predictions_path: Path, pool_path: Path, review_path: Path, proposal_path: Path, labels_path: Path, output: Path, lock_path: Path) -> dict[str, Any]:
    if os.path.lexists(output): raise FileExistsError(f"refusing to overwrite Stage Sixteen result: {output}")
    if os.path.lexists(lock_path): raise FileExistsError("Stage Sixteen score lock already exists; a second evaluator join is forbidden")
    loaded = verify_prepared_corpus(corpus_dir); predictions, prediction_hash = verify_predictions(predictions_path, loaded)
    pool, pool_hash, review_hash, proposal_hash, opaque_labels, labels_hash = verify_pool_review_labels(pool_path, review_path, proposal_path, labels_path, prediction_hash, loaded)
    lock = {"schema_version": 1, "stage": 16, "state": "score_consumed", "policy": "one score only; never delete or bypass this lock", "sealed_predictions_sha256": prediction_hash, "pool_sha256": pool_hash, "review_sha256": review_hash, "proposal_sha256": proposal_hash, "labels_sha256": labels_hash, "corpus_merkle_root": loaded["corpus_merkle_root"], "intended_output": str(output.resolve())}
    lock_hash = write_lock_exclusive(lock_path, json_bytes(lock))  # O_EXCL before the sole evaluator join
    labels = join_labels_once(pool, opaque_labels)
    all_ids = {chunk["chunk_id"] for chunk in loaded["chunks"]}
    if any(not set(values) <= all_ids for values in labels.values()): raise ValueError("joined labels reference unknown chunks")
    failures = dict(predictions["validations"]["failures"]); parity: list[str] = []
    for row in predictions["queries"]:
        scan = row["methods"]["area_five_scan_ranked_cells"]; indexed = row["methods"]["area_five_indexed_ranked_cells"]
        fields = ("selected_artifact", "candidate_chunk_ids", "ranked_chunk_ids", "routing_trace_chunk_ids", "score_trace", "stop_reason", "evidence_validations", "integrity_failures")
        if any(scan[field] != indexed[field] for field in fields): parity.append(row["query_id"])
    positive_ids = {q["query_id"] for q in QUERIES if q["kind"] == "positive"}
    methods = {name: evaluate_method(name, predictions["queries"], labels, positive_ids) for name in METHOD_NAMES}
    checks = evaluate_gates(loaded, methods, labels, failures, parity); passed = all(check["passed"] for check in checks)
    result = {"schema_version": 1, "stage": 16, "benchmark": "area_five_stage_sixteen_untouched_confirmation", "scope_statement": "One untouched score using blind machine-pooled labels. No superiority, neural understanding, human-level memory, novelty, or general-intelligence claim.", "verdict": "STAGE_SIXTEEN_HELD_OUT_PASS" if passed else "HELD_OUT_FAIL", "one_score_lock": {"path": str(lock_path.resolve()), "sha256": lock_hash}, "evaluator_join_count": 1, "configuration": {"artifacts": 6, "queries": 20, "positive_queries": 16, "controls": 4, "candidate_budget": 30, "top_k": 5, "gates": "all exact 17 Stage Sixteen gates"}, "input_hashes": {"sealed_predictions": prediction_hash, "private_pool": pool_hash, "blind_review": review_hash, "blind_label_proposal": proposal_hash, "frozen_labels": labels_hash, "corpus_files": loaded["file_hashes"]}, "failure_totals": failures, "scan_index_parity_failures": parity, "gate_checks": checks, "methods": methods}
    digest = write_new_bytes(output, json_bytes(result))
    print(f"Verdict: {result['verdict']}"); print(f"Gates: {sum(g['passed'] for g in checks)}/17 passed"); print(f"result={output} sha256={digest} lock={lock_hash}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--build-pool", action="store_true")
    modes.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    try:
        if args.build_pool:
            build_pool(CORPUS_DIR, PREDICTIONS_PATH, POOL_PATH, REVIEW_PATH)
        else:
            score_once(
                CORPUS_DIR, PREDICTIONS_PATH, POOL_PATH, REVIEW_PATH,
                PROPOSAL_PATH, LABELS_PATH, RESULT_PATH, LOCK_PATH,
            )
    except FileExistsError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
