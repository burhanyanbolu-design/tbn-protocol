#!/usr/bin/env python3
"""Validate the canonical blind proposal and exclusively freeze Stage Sixteen labels."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
CORPUS_DIR = (SCRIPT_DIR / "stage16-corpus").resolve()
PROPOSAL_PATH = (CORPUS_DIR / "blind-label-proposal.json").resolve()
REVIEW_PATH = (CORPUS_DIR / "adjudication-review.json").resolve()
POOL_PATH = (CORPUS_DIR / "adjudication-pool.json").resolve()
PREDICTIONS_PATH = (CORPUS_DIR / "sealed-predictions.json").resolve()
LABELS_PATH = (CORPUS_DIR / "relevance-labels.json").resolve()
QUERY_IDS = tuple(f"q{i:02d}" for i in range(1, 21))
POSITIVE_IDS = frozenset(QUERY_IDS[:16])
CONTROL_IDS = frozenset(QUERY_IDS[16:])
PROPOSAL_FIELDS = frozenset({
    "schema_version", "stage", "state", "label_provenance",
    "independent_human_judgment", "labels",
})
JOIN_POLICY = "exactly one join from opaque candidate keys to private chunk IDs after score-lock creation"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_object_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return value, raw


def require_common(document: dict[str, Any], state: str) -> None:
    if document.get("schema_version") != 1 or document.get("stage") != 16 or document.get("state") != state:
        raise ValueError(f"invalid canonical {state} document")


def validate_inputs() -> tuple[dict[str, list[str]], dict[str, Any]]:
    # Proposal bytes are never modified, repaired, deleted, or rewritten, including on failure.
    proposal, proposal_raw = load_object_bytes(PROPOSAL_PATH)
    review, review_raw = load_object_bytes(REVIEW_PATH)
    pool, pool_raw = load_object_bytes(POOL_PATH)
    predictions, predictions_raw = load_object_bytes(PREDICTIONS_PATH)
    if set(proposal) != PROPOSAL_FIELDS:
        raise ValueError("blind label proposal has unknown or missing fields")
    required = {
        "schema_version": 1, "stage": 16, "state": "blind_machine_proposal",
        "label_provenance": "machine-pooled", "independent_human_judgment": False,
    }
    if any(proposal.get(key) != value for key, value in required.items()):
        raise ValueError("blind label proposal metadata is invalid")
    require_common(review, "blind_review")
    require_common(pool, "private_machine_pool")
    require_common(predictions, "sealed")
    predictions_hash = sha256_bytes(predictions_raw)
    review_hash = sha256_bytes(review_raw)
    pool_hash = sha256_bytes(pool_raw)
    corpus_root = predictions.get("corpus_merkle_root")
    query_hash = predictions.get("query_strings_sha256")
    corpus_hashes = predictions.get("input_hashes", {}).get("corpus_files")
    if not isinstance(corpus_root, str) or not isinstance(query_hash, str) or not isinstance(corpus_hashes, dict):
        raise ValueError("sealed prediction corpus/query bindings are incomplete")
    common = {
        "corpus_merkle_root": corpus_root,
        "query_strings_sha256": query_hash,
        "sealed_predictions_sha256": predictions_hash,
    }
    if any(review.get(key) != value or pool.get(key) != value for key, value in common.items()):
        raise ValueError("pool/review/prediction binding mismatch")
    if pool.get("review_sha256") != review_hash:
        raise ValueError("private pool is not bound to the canonical blind review")
    review_rows = review.get("queries")
    pool_rows = pool.get("queries")
    prediction_rows = predictions.get("queries")
    if not all(isinstance(rows, list) for rows in (review_rows, pool_rows, prediction_rows)):
        raise ValueError("canonical query arrays are invalid")
    if any([row.get("query_id") for row in rows] != list(QUERY_IDS) for rows in (review_rows, pool_rows, prediction_rows)):
        raise ValueError("canonical query order mismatch")
    domains: dict[str, set[str]] = {}
    for public, private in zip(review_rows, pool_rows):
        query_id = public["query_id"]
        public_candidates = public.get("candidates")
        private_candidates = private.get("candidates")
        if not isinstance(public_candidates, list) or not isinstance(private_candidates, list):
            raise ValueError("canonical candidate arrays are invalid")
        public_keys = [item.get("candidate_key") for item in public_candidates if isinstance(item, dict)]
        private_keys = [item.get("candidate_key") for item in private_candidates if isinstance(item, dict)]
        if len(public_keys) != len(public_candidates) or public_keys != private_keys or len(public_keys) != len(set(public_keys)) or any(not isinstance(key, str) for key in public_keys):
            raise ValueError("canonical opaque candidate domains do not match")
        domains[query_id] = set(public_keys)
    labels = proposal.get("labels")
    if not isinstance(labels, dict) or set(labels) != set(QUERY_IDS):
        raise ValueError("proposal labels must contain exactly q01..q20")
    validated: dict[str, list[str]] = {}
    for query_id in QUERY_IDS:
        values = labels[query_id]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values) or len(values) != len(set(values)):
            raise ValueError("each proposal label must be a unique opaque-key list")
        if not set(values) <= domains[query_id]:
            raise ValueError("proposal contains an unknown or cross-query opaque key")
        if query_id in POSITIVE_IDS and not values:
            raise ValueError("every positive proposal label set must be nonempty")
        if query_id in CONTROL_IDS and values:
            raise ValueError("every control proposal label set must be empty")
        validated[query_id] = list(values)
    bindings = {
        "corpus_merkle_root": corpus_root,
        "corpus_file_hashes": corpus_hashes,
        "query_strings_sha256": query_hash,
        "pool_sha256": pool_hash,
        "review_sha256": review_hash,
        "predictions_sha256": predictions_hash,
        "proposal_sha256": sha256_bytes(proposal_raw),
    }
    return validated, bindings


def freeze_labels() -> str:
    if os.path.lexists(LABELS_PATH):
        raise FileExistsError("canonical Stage Sixteen labels already exist; overwrite is forbidden")
    labels, bindings = validate_inputs()
    document = {
        "schema_version": 1,
        "stage": 16,
        "state": "frozen",
        "label_provenance": "machine-pooled",
        "independent_human_judgment": False,
        **bindings,
        "evaluator_join_policy": JOIN_POLICY,
        "labels": labels,
    }
    raw = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    descriptor = os.open(LABELS_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return sha256_bytes(raw)


def main() -> int:
    digest = freeze_labels()
    print(f"frozen labels={LABELS_PATH} sha256={digest} proposal_preserved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
