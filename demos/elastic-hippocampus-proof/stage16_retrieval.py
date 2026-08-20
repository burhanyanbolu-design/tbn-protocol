#!/usr/bin/env python3
"""Frozen label-free Stage Sixteen retrieval, verification, records, and parity test."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import benchmark as core  # noqa: E402
import document_benchmark as documents  # noqa: E402

RRF_K = 60
HEADING_RRF_WEIGHT = 0.5
LSA_COMPONENTS = 64
LSA_RANDOM_STATE = 20260813
CANDIDATE_BUDGET = 30
TOP_K = 5
KNOWN_TERM_COVERAGE_THRESHOLD = 0.75
SYMBOL_RRF_WEIGHT = 1.0
SYMBOL_ALIASES = {"caret": "^", "tilde": "~"}
DOCUMENT_FREQUENCY_CAP = 50
TOKEN_RE = re.compile(r"[a-z0-9]+")
SURFACE_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
QUERY_STOPWORDS = frozenset(
    "a an and are as at be before by can did do does for from had has have how in "
    "including into is it may must not of on or rather should than that the this through "
    "to use using was were what when which who why with would".split()
)

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def canonical_hash(value: Any) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode())

def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes(); value = json.loads(raw)
    if not isinstance(value, dict): raise ValueError(f"{path.name} must contain an object")
    return value, raw


def verified_merkle_root(chunks: Sequence[dict[str, Any]]) -> str:
    level: list[bytes] = []
    for index, chunk in enumerate(chunks):
        value = dict(chunk); expected = value.pop("merkle_leaf_sha256", None); observed = canonical_hash(value)
        if expected != observed: raise ValueError(f"Merkle leaf mismatch at {index}")
        level.append(bytes.fromhex(observed))
    if not level: raise ValueError("empty Merkle tree")
    while len(level) > 1:
        if len(level) % 2: level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


def verify_prepared_corpus(corpus_dir: Path) -> dict[str, Any]:
    completion, completion_raw = load_json(corpus_dir / "preparation-complete.json")
    if completion.get("schema_version") != 1 or completion.get("stage") != 16 or completion.get("state") != "complete":
        raise ValueError("preparation marker is not complete Stage Sixteen")
    outputs = completion.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != {"chunks.json", "runtime-inventory.json"}:
        raise ValueError("unexpected preparation output set")
    documents: dict[str, dict[str, Any]] = {}; hashes = {"preparation-complete.json": sha256_bytes(completion_raw)}
    for name in sorted(outputs):
        document, raw = load_json(corpus_dir / name); digest = sha256_bytes(raw)
        if digest != outputs[name]: raise ValueError(f"SHA-256 mismatch: {name}")
        documents[name] = document; hashes[name] = digest
    acquisition, acquisition_raw = load_json(corpus_dir / "acquisition-manifest.json")
    acquisition_hash = sha256_bytes(acquisition_raw); hashes["acquisition-manifest.json"] = acquisition_hash
    if acquisition.get("schema_version") != 1 or acquisition.get("stage") != 16 or acquisition.get("state") != "complete":
        raise ValueError("acquisition is incomplete")
    if completion.get("acquisition_manifest_sha256") != acquisition_hash:
        raise ValueError("completion/acquisition binding mismatch")
    chunks_doc = documents["chunks.json"]; chunks = chunks_doc.get("chunks")
    if not isinstance(chunks, list) or chunks_doc.get("chunk_count") != len(chunks): raise ValueError("invalid chunk array")
    if chunks_doc.get("acquisition_manifest_sha256") != acquisition_hash: raise ValueError("chunks/acquisition binding mismatch")
    if not 400 <= len(chunks) <= 2000: raise ValueError("chunk count outside frozen gate")
    root = verified_merkle_root(chunks)
    if root != completion.get("corpus_merkle_root") or root != chunks_doc.get("corpus_merkle_root"):
        raise ValueError("Merkle root binding mismatch")
    artifacts = acquisition.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 6: raise ValueError("exactly six artifacts required")
    by_id = {item.get("artifact_id"): item for item in artifacts}
    if len(by_id) != 6: raise ValueError("artifact IDs must be unique")
    expected_raw = {item.get("raw_file") for item in artifacts}
    actual_raw = {path.name for path in (corpus_dir / "raw").iterdir() if path.is_file() and not path.name.startswith(".")}
    if actual_raw != expected_raw: raise ValueError("raw directory membership mismatch")
    for artifact in artifacts:
        name = artifact.get("raw_file")
        if not isinstance(name, str) or Path(name).name != name: raise ValueError("unsafe raw filename")
        raw_file = (corpus_dir / "raw" / name).read_bytes()
        if len(raw_file) != artifact.get("byte_size") or sha256_bytes(raw_file) != artifact.get("sha256"):
            raise ValueError(f"raw source hash/size mismatch: {artifact.get('artifact_id')}")
    ids: list[str] = []
    for index, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_id"); text = chunk.get("text")
        if not isinstance(chunk_id, str) or not isinstance(text, str) or sha256_bytes(text.encode()) != chunk.get("text_sha256") or not chunk_id.endswith("|" + chunk["text_sha256"]):
            raise ValueError(f"chunk integrity mismatch at {index}")
        ids.append(chunk_id); artifact = by_id.get(chunk.get("artifact_id")); source = chunk.get("source")
        if artifact is None or not isinstance(source, dict): raise ValueError("missing chunk provenance")
        for field in ("title", "publisher", "version", "url", "retrieved_url", "media_type", "byte_size", "sha256", "retrieval_utc", "rights_url", "raw_file"):
            if source.get(field) != artifact.get(field): raise ValueError(f"source provenance mismatch at {index}: {field}")
        previous = chunks[index - 1]["chunk_id"] if index and chunks[index - 1]["artifact_id"] == chunk["artifact_id"] else None
        following = chunks[index + 1]["chunk_id"] if index + 1 < len(chunks) and chunks[index + 1]["artifact_id"] == chunk["artifact_id"] else None
        if chunk.get("previous_chunk_id") != previous or chunk.get("next_chunk_id") != following:
            raise ValueError("neighbor binding mismatch")
    if len(ids) != len(set(ids)): raise ValueError("duplicate chunk IDs")
    return {
        "chunks_document": chunks_doc, "runtime_document": documents["runtime-inventory.json"],
        "acquisition": acquisition, "chunks": tuple(chunks),
        "artifact_ids": tuple(dict.fromkeys(chunk["artifact_id"] for chunk in chunks)),
        "file_hashes": hashes, "corpus_merkle_root": root,
    }


def normalize_query_case_aware(text: str, document_frequency: Counter[str]) -> tuple[str, ...]:
    """Preserve exact lowercase lookup but never morph an unknown uppercase acronym."""
    surfaces = SURFACE_TOKEN_RE.findall(text)
    if [surface.lower() for surface in surfaces] != TOKEN_RE.findall(text.lower()):
        raise ValueError("case-aware token segmentation drift")
    normalized: list[str] = []
    for surface in surfaces:
        original = surface.lower()
        if original in QUERY_STOPWORDS:
            continue
        term = original
        uppercase_acronym = surface.isalpha() and len(surface) > 1 and surface.isupper()
        if document_frequency.get(term, 0) == 0 and not uppercase_acronym:
            candidates: list[str] = []
            if term.endswith("s") and len(term) > 3:
                candidates.append(term[:-1])
            if term.endswith("ed") and len(term) > 4:
                candidates.extend((term[:-1], term[:-2]))
            term = next(
                (candidate for candidate in candidates if document_frequency.get(candidate, 0) > 0),
                term,
            )
        if document_frequency.get(term, 0) <= DOCUMENT_FREQUENCY_CAP:
            normalized.append(term)
    return tuple(normalized)


def build_records(chunks: Sequence[dict[str, Any]], artifact_ids: Sequence[str]) -> tuple[core.Record, ...]:
    artifact_index = {artifact: index for index, artifact in enumerate(artifact_ids)}
    id_by_chunk = {chunk["chunk_id"]: index for index, chunk in enumerate(chunks)}
    offsets: defaultdict[str, int] = defaultdict(int); records: list[core.Record] = []
    for record_id, chunk in enumerate(chunks):
        topic = artifact_index[chunk["artifact_id"]]
        links = tuple(id_by_chunk[item] for item in (chunk.get("previous_chunk_id"), chunk.get("next_chunk_id")) if item is not None)
        container = topic * 1000 + offsets[chunk["artifact_id"]] // 8; offsets[chunk["artifact_id"]] += 1
        source = json.dumps({"artifact_id": chunk["artifact_id"], **chunk["source"]}, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        tokens = core.tokenize(chunk["heading"] + " " + chunk["text"])
        value = {"record_id": record_id, "cell_id": record_id, "container_id": container, "topic_id": topic, "claim_key": chunk["heading"], "value": chunk["text"], "source": source, "links": list(links), "tokens": list(tokens)}
        payload = core.canonical(value)
        records.append(core.Record(record_id, record_id, container, topic, chunk["heading"], chunk["text"], source, links, tokens, payload, sha256_bytes(payload)))
    frozen = tuple(records)
    if any(record.record_id != i or not record.valid() or not record.source for i, record in enumerate(frozen)):
        raise AssertionError("record integrity failure")
    return frozen

def technical_normalize(text: str) -> str:
    value = text.lower().replace("^", " caret_symbol ").replace("~", " tilde_symbol ")
    for word in SYMBOL_ALIASES:
        value = re.sub(rf"\b{word}\b", f"{word} {word}_symbol", value)
    return value


class StageSixteenScorer:
    """Frozen Stage Sixteen body-max router and local RRF scorer."""
    def __init__(self, chunks: Sequence[dict[str, Any]], artifact_ids: Sequence[str]) -> None:
        started = time.perf_counter_ns(); self.chunks = tuple(chunks); supplied = tuple(artifact_ids)
        if not self.chunks or len(supplied) != len(set(supplied)) or {chunk["artifact_id"] for chunk in self.chunks} != set(supplied):
            raise ValueError("chunks/artifact IDs mismatch")
        self.artifacts = tuple(sorted(supplied))
        self.artifact_rows = {artifact: np.array([i for i, chunk in enumerate(self.chunks) if chunk["artifact_id"] == artifact], dtype=np.int64) for artifact in self.artifacts}
        self.body_vectorizer = TfidfVectorizer(lowercase=True, sublinear_tf=True)
        self.body_matrix = self.body_vectorizer.fit_transform([chunk["text"] for chunk in self.chunks])
        self.svd = TruncatedSVD(n_components=LSA_COMPONENTS, algorithm="randomized", n_iter=5, random_state=LSA_RANDOM_STATE)
        self.body_lsa = self.svd.fit_transform(self.body_matrix); self.body_lsa_norms = np.linalg.norm(self.body_lsa, axis=1)
        self.heading_vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)
        self.heading_matrix = self.heading_vectorizer.fit_transform([chunk["heading"] for chunk in self.chunks])
        self.symbol_vectorizer = TfidfVectorizer(preprocessor=technical_normalize, sublinear_tf=True)
        self.symbol_matrix = self.symbol_vectorizer.fit_transform(f"{chunk['heading']} {chunk['text']}" for chunk in self.chunks)
        self._cache: dict[tuple[str, str], tuple[str | None, tuple[int, ...], dict[int, float]]] = {}
        self.build_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    @staticmethod
    def _rank_map(scores: Sequence[float], rows: Iterable[int]) -> dict[int, int]:
        ordered = sorted(rows, key=lambda index: (-float(scores[index]), int(index)))
        return {int(record_id): rank for rank, record_id in enumerate(ordered, 1)}
    def _select_artifact(self, query_text: str) -> str:
        """Route by maximum all-corpus body TF-IDF chunk score per artifact."""
        vector = self.body_vectorizer.transform([query_text])
        chunk_scores = (self.body_matrix @ vector.T).toarray().ravel()
        artifact_scores = {
            artifact: max(float(chunk_scores[int(row)]) for row in self.artifact_rows[artifact])
            for artifact in self.artifacts
        }
        return min(self.artifacts, key=lambda artifact: (-artifact_scores[artifact], artifact))
    def score(self, query: Any, scope: str) -> tuple[str | None, tuple[int, ...], dict[int, float]]:
        if scope not in {"global", "artifact"}: raise ValueError(f"unsupported Stage Sixteen score scope: {scope}")
        key = (query.text, scope); cached = self._cache.get(key)
        if cached is not None: return cached
        selected = self._select_artifact(query.text) if scope == "artifact" else None
        rows = self.artifact_rows[selected] if selected is not None else np.arange(len(self.chunks), dtype=np.int64)
        body_query = self.body_vectorizer.transform([query.text]); body = np.zeros(len(self.chunks), dtype=float)
        body[rows] = (self.body_matrix[rows] @ body_query.T).toarray().ravel()
        query_lsa = self.svd.transform(body_query)[0]; denominator = self.body_lsa_norms[rows] * float(np.linalg.norm(query_lsa)); lsa = np.zeros(len(self.chunks), dtype=float)
        lsa[rows] = np.divide(self.body_lsa[rows] @ query_lsa, denominator, out=np.zeros(len(rows), dtype=float), where=denominator != 0)
        heading_query = self.heading_vectorizer.transform([query.text]); heading = np.zeros(len(self.chunks), dtype=float)
        heading[rows] = (self.heading_matrix[rows] @ heading_query.T).toarray().ravel()
        body_ranks = self._rank_map(body, rows); lsa_ranks = self._rank_map(lsa, rows); heading_ranks = self._rank_map(heading, rows)
        fused = {int(record_id): 1.0 / (RRF_K + body_ranks[int(record_id)]) + 1.0 / (RRF_K + lsa_ranks[int(record_id)]) + HEADING_RRF_WEIGHT / (RRF_K + heading_ranks[int(record_id)]) for record_id in rows}
        signal = any(re.search(rf"(?:\b{word}\b|{re.escape(symbol)})", query.text.lower()) for word, symbol in SYMBOL_ALIASES.items())
        if signal:
            symbol_query = self.symbol_vectorizer.transform([query.text]); symbol = np.zeros(len(self.chunks), dtype=float)
            symbol[rows] = (self.symbol_matrix[rows] @ symbol_query.T).toarray().ravel(); symbol_ranks = self._rank_map(symbol, rows)
            for record_id in rows:
                item = int(record_id); fused[item] += SYMBOL_RRF_WEIGHT / (RRF_K + symbol_ranks[item])
        ordered = tuple(sorted(fused, key=lambda record_id: (-fused[record_id], record_id)))
        result = (selected, ordered, fused); self._cache[key] = result; return result
    def metadata(self) -> dict[str, Any]:
        return {"strategy": "body_max artifact routing then local body/LSA/heading RRF with conditional technical-symbol channel", "artifact_routing": {"name": "body_max", "query_similarity": "body TF-IDF over all chunks", "artifact_aggregation": "maximum chunk score", "tie_break": "ascending artifact_id", "ablation_variants": False}, "body_tfidf_shape": list(self.body_matrix.shape), "heading_tfidf_shape": list(self.heading_matrix.shape), "symbol_tfidf_shape": list(self.symbol_matrix.shape), "lsa_components": LSA_COMPONENTS, "lsa_random_state": LSA_RANDOM_STATE, "lsa_algorithm": "randomized", "lsa_n_iter": 5, "rrf_k": RRF_K, "heading_rrf_weight": HEADING_RRF_WEIGHT, "symbol_rrf_weight": SYMBOL_RRF_WEIGHT, "symbol_aliases": dict(SYMBOL_ALIASES), "candidate_budget": CANDIDATE_BUDGET, "top_k": TOP_K, "known_term_coverage_threshold": KNOWN_TERM_COVERAGE_THRESHOLD, "tie_break": "ascending record_id", "body_vocabulary_sha256": canonical_hash(sorted(self.body_vectorizer.vocabulary_)), "heading_vocabulary_sha256": canonical_hash(sorted(self.heading_vectorizer.vocabulary_)), "symbol_vocabulary_sha256": canonical_hash(sorted(self.symbol_vectorizer.vocabulary_)), "gold_available_to_retrieval": False}


class StageSixteenRanker:
    def __init__(self, scorer: StageSixteenScorer, scope: str) -> None:
        self.scorer = scorer; self.scope = scope
    def rank(self, candidate_ids: Iterable[int], query: core.SearchQuery) -> tuple[int, ...]:
        _, _, scores = self.scorer.score(query, self.scope)
        return tuple(sorted(set(candidate_ids), key=lambda record_id: (-scores[record_id], record_id))[:TOP_K])


class StageSixteenFlat(core.Method):
    """Production-method wrapper around the frozen global Stage Sixteen scorer."""
    name = "stage_sixteen_full_corpus_rrf"
    def __init__(self, records: tuple[core.Record, ...], scorer: StageSixteenScorer) -> None:
        self.scorer = scorer; super().__init__(records, StageSixteenRanker(scorer, "global"))
    def serializable_index(self) -> Any:
        return {"scope": "all verified records", **self.scorer.metadata()}
    def retrieve(self, query: core.SearchQuery) -> core.Retrieval:
        _, ordered, _ = self.scorer.score(query, "global"); candidates = ordered[:CANDIDATE_BUDGET]
        valid, validations, failures = self.validate_candidates(candidates)
        return core.Retrieval(valid, validations, failures, candidates, len(self.records), "candidate_budget_reached" if len(ordered) >= CANDIDATE_BUDGET else "routing_exhausted")


class StageSixteenAreaFive(documents.DocumentAreaFiveIndex):
    """DocumentAreaFiveIndex production wrapper around artifact-scoped scoring."""
    name = "stage_sixteen_area_five_artifact_rrf"
    def __init__(self, records: tuple[core.Record, ...], scorer: StageSixteenScorer, router: str) -> None:
        self.scorer = scorer; super().__init__(records, StageSixteenRanker(scorer, "artifact"), router=router)
    def serializable_index(self) -> Any:
        result = super().serializable_index(); result["stage_sixteen"] = self.scorer.metadata(); return result
    def retrieve(self, query: core.SearchQuery) -> core.Retrieval:
        selected, ordered, _ = self.scorer.score(query, "artifact")
        if selected is None: raise AssertionError("artifact-scoped retrieval did not select an artifact")
        rows = self.scorer.artifact_rows[selected]
        selected_containers = tuple(sorted({self.records[int(record_id)].container_id for record_id in rows}))
        summary_failures = sum(self.container_by_id.get(container_id) is None or self.container_by_id[container_id].summary_id != container_id or not self.container_by_id[container_id].valid() for container_id in selected_containers)
        if summary_failures: return core.Retrieval((), 0, summary_failures, (), 0, "integrity_failure")
        candidates = ordered[:CANDIDATE_BUDGET]; valid, validations, failures = self.validate_candidates(candidates)
        routing_work = len(self.records) + len(self.containers) + len(self.scorer.artifacts) if self.router == "scan" else len(rows) + len(selected_containers) + len(self.scorer.artifacts)
        return core.Retrieval(valid, validations, failures, candidates, routing_work, "candidate_budget_reached" if len(ordered) >= CANDIDATE_BUDGET else "routing_exhausted")


def self_test() -> None:
    # Read-only pre-freeze checks use the immutable Stage Twelve corpus; no Stage Sixteen corpus is created.
    import stage12_retrieval as stage12
    from stage12_prepare import QUERIES as STAGE12_QUERIES

    corpus_dir = SCRIPT_DIR / "stage12-corpus"
    loaded = stage12.verify_prepared_corpus(corpus_dir)
    records = stage12.build_records(loaded["chunks"], loaded["artifact_ids"])
    frequency: Counter[str] = Counter()
    for record in records:
        frequency.update(set(core.tokenize(record.value)))
    reference = stage12.StageTwelveScorer(loaded["chunks"], loaded["artifact_ids"])
    candidate = StageSixteenScorer(loaded["chunks"], loaded["artifact_ids"])
    checked = 0
    for spec in STAGE12_QUERIES:
        tokens = stage12.normalize_query_case_aware(spec["query"], frequency)
        query = core.SearchQuery(spec["query_id"], "stage_sixteen_self_test", spec["query"], tokens, None)
        left = reference.score(query, "global")
        right = candidate.score(query, "global")
        if left != right:
            raise AssertionError(f"preserved global scorer parity failed for {query.query_id}")
        checked += 1
        vector = candidate.body_vectorizer.transform([query.text])
        chunk_scores = (candidate.body_matrix @ vector.T).toarray().ravel()
        artifact_scores = {
            artifact: max(float(chunk_scores[int(row)]) for row in candidate.artifact_rows[artifact])
            for artifact in candidate.artifacts
        }
        expected = min(candidate.artifacts, key=lambda artifact: (-artifact_scores[artifact], artifact))
        first = candidate.score(query, "artifact")
        second = candidate.score(query, "artifact")
        if first != second or first[0] != expected:
            raise AssertionError(f"body-max routing/determinism failed for {query.query_id}")
        checked += 1
    if normalize_query_case_aware("FITS", Counter({"fit": 1})) != ("fits",):
        raise AssertionError("unknown uppercase acronym must bypass plural fallback")
    if normalize_query_case_aware("DNS", Counter({"dns": 1})) != ("dns",):
        raise AssertionError("known uppercase acronym must retain exact lowercase match")
    if normalize_query_case_aware("records", Counter({"record": 1})) != ("record",):
        raise AssertionError("ordinary plural fallback drift")
    if normalize_query_case_aware("walked", Counter({"walk": 1})) != ("walk",):
        raise AssertionError("ordinary past-tense fallback drift")
    metadata = candidate.metadata()
    if metadata.get("artifact_routing", {}).get("name") != "body_max" or metadata["artifact_routing"].get("ablation_variants") is not False:
        raise AssertionError("body-max metadata drift")
    print(f"self-test PASS preserved_global_and_body_max_checks={checked} normalization_vectors=4 metadata=body_max")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    if not args.self_test: parser.error("no production CLI action; use --self-test")
    self_test(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
