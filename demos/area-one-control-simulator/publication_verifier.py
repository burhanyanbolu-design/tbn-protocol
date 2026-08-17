#!/usr/bin/env python3
"""Independent, standard-library verifier for Area One publications."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import sqlite3
import stat
import struct
import sys
import tempfile
import zlib
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

SCHEMA_DIR = Path(__file__).with_name("publication_schemas")
SCHEMA_FILES = {
    "area-one-pair-lock/1.0": "area-one-pair-lock-1.0.schema.json",
    "area-one-control-family-manifest/1.0": "area-one-control-family-manifest-1.0.schema.json",
    "area-one-pair-row/1.0": "area-one-pair-row-1.0.schema.json",
    "area-one-pair-shard/1.0": "area-one-pair-shard-1.0.schema.json",
    "area-one-pair-summary/1.0": "area-one-pair-summary-1.0.schema.json",
    "area-one-pair-results-complete/1.0": "area-one-pair-results-complete-1.0.schema.json",
    "area-one-pair-results-failure/1.0": "area-one-pair-results-failure-1.0.schema.json",
}
COINS = ("uniform", "up", "right", "down", "left", "phase-balanced")
CONTROL_IDS = tuple(f"control-{i:03d}" for i in range(100))
STRUCTURED_IDS = CONTROL_IDS[:9]
THETA_PI = ("0.0625", "0.125", "0.1875", "0.25", "0.375", "0.5")
PHI_PI = ("0", "0.5", "1", "1.5")
GZIP_HEADER = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff"
MARKER_NAME = "attempt-consumed.json"
STAGING_NAME = "atomic-publication-staging"
FAILURE_MESSAGE = "Publication attempt was consumed but did not complete."
MAX_DOCUMENT_BYTES = 64 * 1024 * 1024
MAX_DEPENDENCY_LOCK_BYTES = 1024 * 1024
MAX_NUMPY_CONFIGURATION_CHARS = 1024 * 1024
MAX_COMPRESSED_BYTES = 256 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_TOTAL_DECOMPRESSED_BYTES = 64 * 1024 * 1024 * 1024
MAX_TOTAL_COMPRESSED_BYTES = 10 * 1024 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_COMPRESSION_RATIO = 200
MAX_SHARDS = 1000
MAX_ROWS = 20_000_000
BATCH_ROWS = 4096
_HASH_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ATTEMPT_RE = re.compile(r"[0-9a-f]{32}\Z")
DEPENDENCY_LOCK_FILE = Path(__file__).with_name("requirements-research.lock")
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
}
EXPECTED_PACKAGES = (
    {
        "name": "numpy", "version": "2.4.2",
        "filename": "numpy-2.4.2-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl",
        "sha256": "sha256:d0d9b7c93578baafcbc5f0b83eaf17b79d345c6f36917ba0c67f45226911d499",
    },
    {
        "name": "threadpoolctl", "version": "3.6.0",
        "filename": "threadpoolctl-3.6.0-py3-none-any.whl",
        "sha256": "sha256:43a0b8fd5a2928500110039e43a5eed8480b918967083ea48dc3ab9f13c4a7fb",
    },
)


class PublicationError(ValueError):
    """A publication is malformed, unsafe, or inconsistent."""


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    rows: int
    completion_hash: str | None
    verdict_passed: bool | None
    errors: tuple[str, ...]


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise PublicationError("value is not canonical-JSON encodable") from exc


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def document_hash(value: dict[str, Any], field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return _sha256(canonical_json(body).encode("utf-8"))


def scalar_string(value: float) -> str:
    if not isinstance(value, float) or not math.isfinite(value):
        raise PublicationError("non-finite reconstructed scalar")
    if value == 0.0:
        return "0"
    return format(value, ".17g")


def parse_scalar(value: Any, label: str) -> float:
    if not isinstance(value, str) or not value:
        raise PublicationError(f"{label} must be a scalar string")
    if value == "-0":
        raise PublicationError(f"{label} uses negative zero")
    try:
        parsed = float(value)
    except (ValueError, OverflowError) as exc:
        raise PublicationError(f"{label} is not binary64") from exc
    if not math.isfinite(parsed):
        raise PublicationError(f"{label} is not finite")
    expected = "0" if parsed == 0.0 else format(parsed, ".17g")
    if value != expected:
        raise PublicationError(f"{label} is not canonical finite .17g")
    return parsed


def _fsub(left: float, right: float, label: str) -> float:
    result = float(left - right)
    if not math.isfinite(result):
        raise PublicationError(f"non-finite {label}")
    return result


def _fadd(left: float, right: float, label: str) -> float:
    result = float(left + right)
    if not math.isfinite(result):
        raise PublicationError(f"non-finite {label}")
    return result


def frozen_quantile(items: Iterable[tuple[float, str]], numerator: int,
                    denominator: int) -> float:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise PublicationError("invalid quantile fraction")
    if numerator < 0 or numerator > denominator:
        raise PublicationError("quantile is outside [0,1]")
    sample = list(items)
    if not sample:
        raise PublicationError("empty quantile sample")
    keys = [key for _, key in sample]
    if any(not isinstance(key, str) or not key for key in keys) or len(keys) != len(set(keys)):
        raise PublicationError("quantile keys must be unique nonempty strings")
    if any(not isinstance(value, float) or not math.isfinite(value) for value, _ in sample):
        raise PublicationError("quantile sample contains a non-finite binary64")
    sample.sort(key=lambda item: (item[0], item[1]))
    lo, remainder = divmod((len(sample) - 1) * numerator, denominator)
    hi = min(lo + 1, len(sample) - 1)
    x_lo, x_hi = sample[lo][0], sample[hi][0]
    weight = float(float(remainder) / float(denominator))
    difference = float(x_hi - x_lo)
    weighted = float(weight * difference)
    result = float(x_lo + weighted)
    if not all(math.isfinite(x) for x in (weight, difference, weighted, result)):
        raise PublicationError("non-finite quantile intermediate")
    return result


def _median(items: Iterable[tuple[float, str]]) -> float:
    return frozen_quantile(items, 1, 2)


def _q10(items: Iterable[tuple[float, str]]) -> float:
    return frozen_quantile(items, 1, 10)


def _q90(items: Iterable[tuple[float, str]]) -> float:
    return frozen_quantile(items, 9, 10)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PublicationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PublicationError(f"non-standard JSON constant: {value}")


def strict_json(data: bytes, label: str) -> Any:
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(text, object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PublicationError(f"{label} is not strict UTF-8 JSON: {exc}") from exc


def _stat_is_link(info: os.stat_result) -> bool:
    if stat.S_ISLNK(info.st_mode):
        return True
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse and getattr(info, "st_file_attributes", 0) & reparse)


def _is_link(path: Path) -> bool:
    return _stat_is_link(path.lstat())


def _open_regular_fd(path: Path, limit: int) -> int:
    try:
        initial = path.lstat()
    except OSError as exc:
        raise PublicationError(f"cannot stat {path.name}: {exc}") from exc
    if _stat_is_link(initial) or not stat.S_ISREG(initial.st_mode):
        raise PublicationError(f"{path.name} is not a regular non-symlink file")
    if initial.st_size > limit:
        raise PublicationError(f"{path.name} exceeds size limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PublicationError(f"cannot open {path.name}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if (_stat_is_link(opened) or not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != initial.st_dev or opened.st_ino != initial.st_ino
                or stat.S_IFMT(opened.st_mode) != stat.S_IFMT(initial.st_mode)):
            raise PublicationError(f"{path.name} changed during no-follow open")
        if opened.st_size > limit:
            raise PublicationError(f"{path.name} exceeds size limit")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _safe_root(root: os.PathLike[str] | str) -> Path:
    path = Path(root).absolute()
    if not path.exists() or not path.is_dir():
        raise PublicationError("publication root must be an existing directory")
    cursor = path
    while True:
        if _is_link(cursor):
            raise PublicationError("publication root has a symlink/reparse component")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return path


def _safe_child(root: Path, supplied: os.PathLike[str] | str, label: str) -> Path:
    candidate = Path(supplied)
    candidate = candidate.absolute() if candidate.is_absolute() else root / candidate
    if candidate.parent != root or candidate.name in ("", ".", ".."):
        raise PublicationError(f"{label} must be a direct child of the publication root")
    return candidate


def _regular_file(path: Path, limit: int) -> bytes:
    descriptor = _open_regular_fd(path, limit)
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            try:
                chunk = os.read(descriptor, min(65536, limit - total + 1))
            except OSError as exc:
                raise PublicationError(f"cannot read {path.name}: {exc}") from exc
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise PublicationError(f"{path.name} exceeds size limit")
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def load_canonical_object(path: Path) -> tuple[dict[str, Any], bytes]:
    data = _regular_file(path, MAX_DOCUMENT_BYTES)
    value = strict_json(data, path.name)
    if not isinstance(value, dict):
        raise PublicationError(f"{path.name} root must be an object")
    if data != (canonical_json(value) + "\n").encode("utf-8"):
        raise PublicationError(f"{path.name} is not canonical compact JSON with final LF")
    return value, data


def _schema_type(value: Any, expected: str) -> bool:
    if expected == "object": return isinstance(value, dict)
    if expected == "array": return isinstance(value, list)
    if expected == "string": return isinstance(value, str)
    if expected == "integer": return type(value) is int
    if expected == "number": return type(value) in (int, float) and math.isfinite(value)
    if expected == "boolean": return type(value) is bool
    if expected == "null": return value is None
    return False


def _resolve_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise PublicationError(f"unsupported schema reference: {reference}")
    current: Any = root
    for part in reference[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(current, dict):
        raise PublicationError("schema reference is not an object")
    return current


def validate_schema(value: Any, schema: dict[str, Any] | bool, label: str,
                    root: dict[str, Any] | None = None) -> None:
    if schema is False:
        raise PublicationError(f"{label} is not permitted")
    if schema is True:
        return
    root = schema if root is None else root
    if "$ref" in schema:
        validate_schema(value, _resolve_ref(root, schema["$ref"]), label, root)
        return
    if "const" in schema and value != schema["const"]:
        raise PublicationError(f"{label} has wrong constant")
    if "enum" in schema and value not in schema["enum"]:
        raise PublicationError(f"{label} is outside its enum")
    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_schema_type(value, choice) for choice in choices):
            raise PublicationError(f"{label} has wrong type")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [field for field in schema.get("required", []) if field not in value]
        if missing:
            raise PublicationError(f"{label} missing fields: {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise PublicationError(f"{label} has unknown fields: {', '.join(unknown)}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{label}.{key}", root)
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise PublicationError(f"{label} has invalid item count")
        if schema.get("uniqueItems") and len({canonical_json(x) for x in value}) != len(value):
            raise PublicationError(f"{label} items are not unique")
        prefix_items = schema.get("prefixItems", [])
        for index, item in enumerate(value):
            if index < len(prefix_items):
                validate_schema(item, prefix_items[index], f"{label}[{index}]", root)
            elif "items" in schema:
                validate_schema(item, schema["items"], f"{label}[{index}]", root)
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
            raise PublicationError(f"{label} has invalid length")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise PublicationError(f"{label} has invalid format")
    elif type(value) in (int, float):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            raise PublicationError(f"{label} is outside its range")


def load_schemas() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for schema_id, filename in SCHEMA_FILES.items():
        value = strict_json(_regular_file(SCHEMA_DIR / filename, MAX_DOCUMENT_BYTES), filename)
        if not isinstance(value, dict) or value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise PublicationError(f"schema {filename} is invalid")
        if value.get("$id") != schema_id or value.get("additionalProperties") is not False:
            raise PublicationError(f"schema {filename} has wrong ID or is not closed")
        result[schema_id] = value
    return result


def _verify_document(value: dict[str, Any], schema_id: str,
                     schemas: dict[str, dict[str, Any]], label: str) -> None:
    validate_schema(value, schemas[schema_id], label)


def _verify_hash(value: dict[str, Any], field: str, label: str) -> None:
    if value.get(field) != document_hash(value, field):
        raise PublicationError(f"{label} {field} does not match canonical content")


def _horizons(s: int, rows: int) -> tuple[int, int, int]:
    root = math.sqrt(rows * (s + 1))
    return math.ceil(root), math.ceil(2.0 * root), math.ceil(4.0 * root)


def _verify_source_files(lock: dict[str, Any]) -> None:
    source_files = lock["source_files"]
    paths = [item["path"] for item in source_files]
    for path in paths:
        segments = path.split("/")
        if (not path or path.startswith("/") or "\\" in path or ":" in path
                or any(segment in ("", ".", "..") for segment in segments)
                or any(ord(character) < 32 for character in path)):
            raise PublicationError(f"unsafe source path: {path!r}")
    if len(paths) != len(set(paths)):
        raise PublicationError("source file paths are duplicated")
    if paths != sorted(paths):
        raise PublicationError("source files are not in canonical path order")
    expected_hash = _sha256(canonical_json(source_files).encode("utf-8"))
    if lock["source_tree_hash"] != expected_hash:
        raise PublicationError("source_tree_hash does not match canonical source files")


def _thread_pool_key(pool: dict[str, Any]) -> tuple[Any, ...]:
    return (pool["internal_api"], pool["user_api"], pool["prefix"],
            pool["filepath"], pool["version"])


def _verify_runtime_evidence(runtime: dict[str, Any]) -> None:
    if _HASH_RE.fullmatch(runtime["image_digest"]) is None:
        raise PublicationError("runtime image digest is not canonical")
    if runtime["python_implementation"] != "CPython" or runtime["python_version"] != "3.13.7":
        raise PublicationError("runtime must use exactly CPython 3.13.7")
    python_build = runtime["python_build"]
    if (not isinstance(python_build, list) or len(python_build) != 2
            or any(not isinstance(item, str) or not item for item in python_build)):
        raise PublicationError("runtime python_build must contain exactly two nonempty strings")
    if (runtime["numpy_version"] != "2.4.2"
            or runtime["threadpoolctl_version"] != "3.6.0"
            or runtime["platform"] != "linux-x86_64"):
        raise PublicationError("runtime dependency versions or platform are not frozen")
    configuration = runtime["numpy_configuration"]
    if (not isinstance(configuration, str) or not configuration
            or len(configuration) > MAX_NUMPY_CONFIGURATION_CHARS):
        raise PublicationError("runtime NumPy configuration is empty or exceeds its bound")
    if not isinstance(runtime["cpu_model"], str) or not runtime["cpu_model"]:
        raise PublicationError("runtime CPU model must be nonempty")
    flags = runtime["cpu_flags"]
    if (not flags or any(not isinstance(flag, str) or not flag or flag != flag.lower()
                         for flag in flags)
            or len(flags) != len(set(flags)) or flags != sorted(flags)):
        raise PublicationError("runtime CPU flags must be nonempty, lowercase, sorted, and unique")
    if runtime["thread_environment"] != THREAD_ENVIRONMENT:
        raise PublicationError("runtime thread environment is not frozen to one thread")
    pools = runtime["thread_pools"]
    if not pools or pools != sorted(pools, key=_thread_pool_key):
        raise PublicationError("runtime thread pools are empty or not canonically sorted")
    if any(pool["num_threads"] != 1 for pool in pools):
        raise PublicationError("runtime thread pool does not use exactly one thread")
    if runtime["packages"] != list(EXPECTED_PACKAGES):
        raise PublicationError("runtime packages do not match the two frozen wheel records")
    dependency_bytes = _regular_file(DEPENDENCY_LOCK_FILE, MAX_DEPENDENCY_LOCK_BYTES)
    if runtime["dependency_lock_hash"] != _sha256(dependency_bytes):
        raise PublicationError("runtime dependency_lock_hash does not match requirements-research.lock")


def _verify_lock(lock: dict[str, Any]) -> dict[str, tuple[int, int]]:
    _verify_hash(lock, "lock_hash", "lock")
    _verify_source_files(lock)
    _verify_runtime_evidence(lock["runtime"])
    epsilon = scalar_string(float(1e-12))
    expected_thresholds = {
        "overall_median": scalar_string(float(0.05)), "grid_median": "0",
        "overall_positive": "7/10", "grid_positive": "3/5",
        "grid_q10": scalar_string(float(-0.02)), "control_q90": "0",
        "control_rank": 10, "control_advantage": scalar_string(float(0.02)),
        "strongest_grid_wins": 7,
    }
    if lock["epsilon"] != epsilon or lock["thresholds"] != expected_thresholds:
        raise PublicationError("lock thresholds differ from the frozen protocol")
    if tuple(lock["coins"]) != COINS or lock["worker_count"] != 4 or lock["shard_rows"] != 100000:
        raise PublicationError("lock topology is not frozen")
    if lock["horizons"] != {"short": "ceil(sqrt(N))", "primary": "ceil(2*sqrt(N))", "long": "ceil(4*sqrt(N))"}:
        raise PublicationError("lock horizon formulas are not frozen")
    grids = [(item["s"], item["R"]) for item in lock["grids"]]
    expected_grids = ([(s, r) for s in (5, 6, 7) for r in (7, 8, 9)]
                      if lock["dataset_kind"] == "holdout" else [(2, 6), (3, 6), (4, 6)])
    if grids != expected_grids:
        raise PublicationError("lock does not contain the exact canonical grids")
    parameters = lock["selected_parameters"]
    if tuple(item["family_id"] for item in parameters) != ("candidate",) + CONTROL_IDS:
        raise PublicationError("selected parameters are not candidate then control-000..099")
    return {item["family_id"]: (item["theta_index"], item["phi_index"]) for item in parameters}


def _left_rotate(values: list[int], offset: int) -> list[int]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def _ranked_random(rows: int) -> list[tuple[int, ...]]:
    forward = tuple(range(1, rows))
    reflected = tuple(reversed(forward))
    excluded = {tuple(_left_rotate(list(forward), i)) for i in range(rows - 1)}
    excluded |= {tuple(_left_rotate(list(reflected), i)) for i in range(rows - 1)}
    ranked: list[tuple[str, str, tuple[int, ...]]] = []
    for permutation in itertools.permutations(forward):
        if permutation in excluded:
            continue
        canonical = json.dumps(list(permutation), ensure_ascii=False, separators=(",", ":"))
        payload = f"area-one-control-random-v1|{rows}|{canonical}".encode("utf-8")
        ranked.append((hashlib.sha256(payload).hexdigest(), canonical, permutation))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in ranked[:91]]


def _verify_manifest(manifest: dict[str, Any]) -> None:
    _verify_hash(manifest, "manifest_hash", "family manifest")
    if manifest["generator_version"] != "area-one-control-random-v1":
        raise PublicationError("family manifest generator is not frozen")
    families = manifest["families"]
    if tuple(item["family_id"] for item in families) != CONTROL_IDS:
        raise PublicationError("family records are not control-000..099 in order")
    random_by_rows = {rows: _ranked_random(rows) for rows in (6, 7, 8, 9)}
    seen: dict[int, set[tuple[int, ...]]] = {rows: set() for rows in (6, 7, 8, 9)}
    for ordinal, family in enumerate(families):
        kind = "structured" if ordinal < 9 else "random"
        subkind = "cyclic" if ordinal < 4 else "reflected" if ordinal < 9 else None
        if family["kind"] != kind or family["structured_subkind"] != subkind:
            raise PublicationError(f"{family['family_id']} kind/subkind is inconsistent")
        if [member["R"] for member in family["members"]] != [6, 7, 8, 9]:
            raise PublicationError(f"{family['family_id']} members are not in R order")
        for member in family["members"]:
            rows = member["R"]
            destinations = member["destination_rows"]
            permutation = tuple(destinations)
            displacement = [destination - (source + 1) for source, destination in enumerate(destinations)]
            expected_member = {
                "R": rows, "destination_rows": destinations, "displacements": displacement,
                "retained_genuine_edges": sum(x == 0 for x in displacement),
                "cardinality": rows - 1, "disjoint": True,
            }
            if member != expected_member or sorted(destinations) != list(range(1, rows)):
                raise PublicationError(f"{family['family_id']} R={rows} metadata is inconsistent")
            if permutation in seen[rows]:
                raise PublicationError(f"duplicate family permutation for R={rows}")
            seen[rows].add(permutation)
            if ordinal < 4:
                expected = tuple(_left_rotate(list(range(1, rows)), ordinal + 1))
            elif ordinal < 9:
                expected = tuple(_left_rotate(list(reversed(range(1, rows))), ordinal - 4))
            else:
                expected = random_by_rows[rows][ordinal - 9]
            if permutation != expected:
                raise PublicationError(f"{family['family_id']} R={rows} permutation is wrong")


def micro_case_key(row: dict[str, Any]) -> str:
    return canonical_json([row["s"], row["R"], row["start_row"], row["start_column"],
                           row["terminal_row"], row["terminal_column"], row["coin"], row["horizon"]])


def row_key(row: dict[str, Any]) -> str:
    return canonical_json([row["s"], row["R"], row["start_row"], row["start_column"],
                           row["terminal_row"], row["terminal_column"], row["coin"], row["horizon"],
                           row["method_kind"], row["family_id"], row["theta_index"], row["phi_index"]])


def _method_specs(horizon: int, primary: int,
                  parameters: dict[str, tuple[int, int]]) -> Iterable[tuple[str, str, int, int]]:
    yield "baseline", "baseline", -1, -1
    theta, phi = parameters["candidate"]
    yield "candidate", "candidate", theta, phi
    if horizon == primary:
        for family_id in CONTROL_IDS:
            theta, phi = parameters[family_id]
            yield "control", family_id, theta, phi


def expected_rows(lock: dict[str, Any], parameters: dict[str, tuple[int, int]]) -> Iterator[tuple[Any, ...]]:
    for grid in lock["grids"]:
        s, rows = grid["s"], grid["R"]
        width = s + 1
        short, primary, long = _horizons(s, rows)
        for start_row in range(rows):
            for start_column in range(width):
                for terminal_row in range(rows):
                    for terminal_column in range(width):
                        if (start_row, start_column) == (terminal_row, terminal_column):
                            continue
                        for coin in COINS:
                            for horizon in (short, primary, long):
                                for method, family, theta, phi in _method_specs(horizon, primary, parameters):
                                    yield (s, rows, start_row, start_column, terminal_row,
                                           terminal_column, coin, horizon, method, family, theta, phi)


def _row_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row["s"], row["R"], row["start_row"], row["start_column"],
            row["terminal_row"], row["terminal_column"], row["coin"], row["horizon"],
            row["method_kind"], row["family_id"], row["theta_index"], row["phi_index"])


def _verify_row(row: dict[str, Any], lock: dict[str, Any],
                parameters: dict[str, tuple[int, int]], ordinal: int) -> tuple[float, bool]:
    if row["ordinal"] != ordinal or row["shard_id"] != ordinal // lock["shard_rows"]:
        raise PublicationError(f"row {ordinal} has wrong ordinal or shard_id")
    if row["micro_case_key"] != micro_case_key(row) or row["row_key"] != row_key(row):
        raise PublicationError(f"row {ordinal} has a noncanonical key")
    if (row["start_row"], row["start_column"]) == (row["terminal_row"], row["terminal_column"]):
        raise PublicationError(f"row {ordinal} start equals terminal")
    if not (0 <= row["start_row"] < row["R"] and 0 <= row["terminal_row"] < row["R"]):
        raise PublicationError(f"row {ordinal} row coordinate is outside grid")
    if not (0 <= row["start_column"] <= row["s"] and 0 <= row["terminal_column"] <= row["s"]):
        raise PublicationError(f"row {ordinal} column coordinate is outside grid")
    if (row["lock_hash"], row["family_manifest_hash"], row["holdout_hash"]) != (
            lock["lock_hash"], lock["family_manifest_hash"], lock["holdout_hash"]):
        raise PublicationError(f"row {ordinal} hash binding is wrong")
    method, family = row["method_kind"], row["family_id"]
    if method == "baseline":
        if (family, row["theta_index"], row["phi_index"], row["theta_pi"], row["phi_pi"]) != ("baseline", -1, -1, "0", "0"):
            raise PublicationError(f"row {ordinal} baseline parameter binding is wrong")
    else:
        if family not in parameters or parameters[family] != (row["theta_index"], row["phi_index"]):
            raise PublicationError(f"row {ordinal} family parameter binding is wrong")
        if (method == "candidate") != (family == "candidate"):
            raise PublicationError(f"row {ordinal} candidate binding is wrong")
        if method == "control" and family not in CONTROL_IDS:
            raise PublicationError(f"row {ordinal} control binding is wrong")
        if row["theta_pi"] != THETA_PI[row["theta_index"]] or row["phi_pi"] != PHI_PI[row["phi_index"]]:
            raise PublicationError(f"row {ordinal} parameter ratio is wrong")
    short, primary, long = _horizons(row["s"], row["R"])
    if row["horizon"] not in (short, primary, long) or (method == "control" and row["horizon"] != primary):
        raise PublicationError(f"row {ordinal} method/horizon binding is wrong")
    horizon = row["horizon"]
    pairs = 0 if method == "baseline" else 4 * (row["R"] - 1) * horizon
    expected_operations = {
        "oracle_calls": horizon, "coin_applications": horizon, "shifts": horizon,
        "pair_rotations": pairs, "final_measurements": 1,
        "hilbert_dimension": row["R"] * (row["s"] + 1) * 4,
    }
    if row["operations"] != expected_operations:
        raise PublicationError(f"row {ordinal} operation counts are inconsistent")
    probability = parse_scalar(row["probability"], f"row {ordinal}.probability")
    norm = parse_scalar(row["max_norm_drift"], f"row {ordinal}.max_norm_drift")
    bound = parse_scalar(row["max_probability_bound_error"], f"row {ordinal}.max_probability_bound_error")
    epsilon = parse_scalar(lock["epsilon"], "lock.epsilon")
    if probability < -epsilon or probability > _fadd(1.0, epsilon, "probability bound"):
        raise PublicationError(f"row {ordinal} probability is outside physical bounds")
    if norm < 0.0 or bound < 0.0 or norm > epsilon or bound > epsilon:
        raise PublicationError(f"row {ordinal} numerical invariant failed")
    return probability, True


class Reconstructor:
    """Bounded independent summary reconstruction over primary-horizon lifts."""
    def __init__(self, database: Path, lock: dict[str, Any]) -> None:
        self.lock = lock
        self.connection = sqlite3.connect(database)
        self.connection.execute("PRAGMA journal_mode=OFF")
        self.connection.execute("PRAGMA synchronous=OFF")
        self.connection.execute("PRAGMA temp_store=FILE")
        self.connection.execute("CREATE TABLE lifts(s INTEGER,R INTEGER,family TEXT,k TEXT,value REAL)")
        self.pending: list[tuple[int, int, str, str, float]] = []
        self.group: tuple[Any, ...] | None = None
        self.probabilities: dict[str, float] = {}
        self.operations = {name: 0 for name in ("records", "oracle_calls", "coin_applications", "shifts", "pair_rotations", "final_measurements")}
        self.invariants = True
        self.closed = False

    def __enter__(self) -> "Reconstructor":
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        if not self.closed:
            self.connection.close()
            self.closed = True

    def _flush(self) -> None:
        if self.pending:
            self.connection.executemany("INSERT INTO lifts VALUES(?,?,?,?,?)", self.pending)
            self.pending.clear()

    def add(self, row: dict[str, Any], probability: float, invariant_ok: bool) -> None:
        group = (row["s"], row["R"], row["start_row"], row["start_column"],
                 row["terminal_row"], row["terminal_column"], row["coin"], row["horizon"])
        if self.group is not None and group != self.group:
            self._finish_group()
        self.group = group
        if row["family_id"] in self.probabilities:
            raise PublicationError(f"duplicate family in micro-case {row['micro_case_key']}")
        self.probabilities[row["family_id"]] = probability
        self.invariants = self.invariants and invariant_ok
        self.operations["records"] += 1
        for name in self.operations:
            if name != "records":
                self.operations[name] += row["operations"][name]

    def _finish_group(self) -> None:
        assert self.group is not None
        s, rows, sr, sc, tr, tc, coin, horizon = self.group
        primary = _horizons(s, rows)[1]
        expected = {"baseline", "candidate"} | (set(CONTROL_IDS) if horizon == primary else set())
        if set(self.probabilities) != expected:
            missing = sorted(expected - set(self.probabilities))
            extra = sorted(set(self.probabilities) - expected)
            raise PublicationError(f"micro-case group membership mismatch; missing={missing}, extra={extra}")
        if horizon == primary:
            baseline = self.probabilities["baseline"]
            key = canonical_json([s, rows, sr, sc, tr, tc, coin, horizon])
            for family in ("candidate",) + CONTROL_IDS:
                lift = _fsub(self.probabilities[family], baseline, "lift")
                self.pending.append((s, rows, family, key, lift))
            if len(self.pending) >= BATCH_ROWS:
                self._flush()
        self.group = None
        self.probabilities.clear()

    def _sample(self, s: int, rows: int, family: str) -> list[tuple[float, str]]:
        cursor = self.connection.execute(
            "SELECT value,k FROM lifts WHERE s=? AND R=? AND family=? ORDER BY value,k",
            (s, rows, family))
        result = [(float(value), key) for value, key in cursor]
        if not result:
            raise PublicationError(f"missing lift sample for {family} grid {(s, rows)}")
        return result

    def finish(self) -> dict[str, Any]:
        if self.group is not None:
            self._finish_group()
        self._flush()
        self.connection.commit()
        self.connection.execute("CREATE INDEX lifts_lookup ON lifts(s,R,family,value,k)")
        epsilon = parse_scalar(self.lock["epsilon"], "lock.epsilon")
        thresholds = self.lock["thresholds"]
        grids_internal: list[dict[str, Any]] = []
        family_grid: dict[str, list[tuple[float, str]]] = {f: [] for f in ("candidate",) + CONTROL_IDS}
        for grid in self.lock["grids"]:
            s, rows = grid["s"], grid["R"]
            grid_key = canonical_json([s, rows])
            candidate_sample = self._sample(s, rows, "candidate")
            candidate_median = _median(candidate_sample)
            candidate_q10 = _q10(candidate_sample)
            positive = sum(value > epsilon for value, _ in candidate_sample)
            control_medians: dict[str, float] = {}
            family_grid["candidate"].append((candidate_median, grid_key))
            for family in CONTROL_IDS:
                value = _median(self._sample(s, rows, family))
                control_medians[family] = value
                family_grid[family].append((value, grid_key))
            central = _median((value, family) for family, value in control_medians.items())
            grids_internal.append({
                "s": s, "R": rows, "total_count": len(candidate_sample), "positive_count": positive,
                "candidate_median": candidate_median, "candidate_q10": candidate_q10,
                "central": central, "advantage": _fsub(candidate_median, central, "grid advantage"),
                "controls": control_medians,
            })
        scores = {family: _median(values) for family, values in family_grid.items()}
        candidate_score = scores["candidate"]
        control_q90 = _q90((scores[family], family) for family in CONTROL_IDS)
        rank_boundary = _fsub(candidate_score, epsilon, "candidate rank boundary")
        rank = 1 + sum(scores[family] >= rank_boundary for family in CONTROL_IDS)
        strongest = min(STRUCTURED_IDS, key=lambda family: (-scores[family], family))
        grid_output: list[dict[str, Any]] = []
        wins = 0
        for item in grids_internal:
            strongest_value = item["controls"][strongest]
            beat = item["candidate_median"] > _fadd(strongest_value, epsilon, "strongest boundary")
            wins += beat
            grid_output.append({
                "s": item["s"], "R": item["R"], "total_count": item["total_count"],
                "positive_count": item["positive_count"],
                "candidate_median_lift": scalar_string(item["candidate_median"]),
                "candidate_q10_lift": scalar_string(item["candidate_q10"]),
                "central_control_median_lift": scalar_string(item["central"]),
                "candidate_advantage": scalar_string(item["advantage"]),
                "strongest_control_median_lift": scalar_string(strongest_value),
                "candidate_beats_strongest": beat,
            })
        median_advantage = _median((item["advantage"], canonical_json([item["s"], item["R"]])) for item in grids_internal)
        fractions = [Fraction(item["positive_count"], item["total_count"]) for item in grids_internal]
        overall_fraction = sum(fractions, Fraction(0, 1)) / len(fractions)
        checks = {
            "overall_median": candidate_score > _fadd(parse_scalar(thresholds["overall_median"], "threshold"), epsilon, "overall median boundary"),
            "every_grid_median": all(item["candidate_median"] > epsilon for item in grids_internal),
            "overall_positive": overall_fraction > Fraction(7, 10),
            "every_grid_positive": all(value > Fraction(3, 5) for value in fractions),
            "every_grid_q10": all(item["candidate_q10"] > _fadd(parse_scalar(thresholds["grid_q10"], "threshold"), epsilon, "q10 boundary") for item in grids_internal),
            "operation_consistency": True,
            "control_quantile": candidate_score > _fadd(control_q90, epsilon, "control q90 boundary"),
            "control_rank": rank <= thresholds["control_rank"],
            "control_advantage": median_advantage > _fadd(parse_scalar(thresholds["control_advantage"], "threshold"), epsilon, "control advantage boundary"),
            "strongest_grid_wins": wins >= thresholds["strongest_grid_wins"],
            "invariants": self.invariants,
        }
        failure_order = (
            ("overall_median", "overall-median"), ("every_grid_median", "grid-median"),
            ("overall_positive", "overall-positive"), ("every_grid_positive", "grid-positive"),
            ("every_grid_q10", "grid-q10"), ("operation_consistency", "operation-consistency"),
            ("invariants", "invariants"), ("control_quantile", "control-quantile"),
            ("control_rank", "control-rank"), ("control_advantage", "control-advantage"),
            ("strongest_grid_wins", "strongest-grid-wins"),
        )
        failure_reasons = [reason for check, reason in failure_order if not checks[check]]
        grover_names = ("overall_median", "every_grid_median", "overall_positive", "every_grid_positive",
                        "every_grid_q10", "operation_consistency", "invariants")
        control_names = ("control_quantile", "control_rank", "control_advantage", "strongest_grid_wins",
                         "operation_consistency", "invariants")
        grover_pass = all(checks[name] for name in grover_names)
        control_pass = all(checks[name] for name in control_names)
        passed = grover_pass and control_pass
        outcome = "outcome-0" if not grover_pass else "outcome-1" if not control_pass else "outcome-2"
        return {
            "schema_version": "area-one-pair-summary/1.0", "dataset_kind": self.lock["dataset_kind"],
            "lock_hash": self.lock["lock_hash"], "family_manifest_hash": self.lock["family_manifest_hash"],
            "holdout_hash": self.lock["holdout_hash"], "grids": grid_output,
            "method_scores": [{"family_id": family, "median_grid_lift": scalar_string(scores[family])}
                              for family in ("candidate",) + CONTROL_IDS],
            "candidate_score": scalar_string(candidate_score),
            "control_quantile_90": scalar_string(control_q90), "candidate_rank": rank,
            "strongest_control_id": strongest, "median_candidate_advantage": scalar_string(median_advantage),
            "strongest_grid_wins": wins, "checks": checks, "operations": self.operations,
            "verdict": {"grover_pass": grover_pass, "control_pass": control_pass,
                        "passed": passed, "outcome": outcome},
            "failure_reasons": failure_reasons,
        }


def _consume_lines(chunks: Iterable[bytes], callback: Callable[[bytes], None]) -> tuple[int, int, str, int]:
    buffer = bytearray()
    count = total = 0
    crc = 0
    digest = hashlib.sha256()
    for chunk in chunks:
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_DECOMPRESSED_BYTES:
            raise PublicationError("gzip member exceeds decompressed byte limit")
        digest.update(chunk)
        crc = zlib.crc32(chunk, crc)
        buffer.extend(chunk)
        while True:
            newline = buffer.find(b"\n")
            if newline < 0:
                if len(buffer) > MAX_LINE_BYTES:
                    raise PublicationError("JSONL line exceeds byte limit")
                break
            line = bytes(buffer[:newline])
            del buffer[:newline + 1]
            if not line or len(line) > MAX_LINE_BYTES or b"\r" in line:
                raise PublicationError("JSONL has empty, oversized, or CRLF line")
            callback(line)
            count += 1
    if buffer:
        raise PublicationError("JSONL lacks final LF")
    return count, total, "sha256:" + digest.hexdigest(), crc & 0xffffffff


def _gzip_chunks(path: Path, compressed_digest: hashlib._Hash) -> tuple[Iterable[bytes], Callable[[], tuple[int, bytes]]]:
    # The iterable owns the descriptor until exhaustion or explicit close.
    state: dict[str, Any] = {"size": 0, "trailer": b""}
    def iterator() -> Iterator[bytes]:
        descriptor = _open_regular_fd(path, MAX_COMPRESSED_BYTES)
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
        def read_chunk(amount: int) -> bytes:
            try:
                chunk = os.read(descriptor, amount)
            except OSError as exc:
                raise PublicationError(f"cannot read {path.name}: {exc}") from exc
            if chunk:
                state["size"] += len(chunk)
                if state["size"] > MAX_COMPRESSED_BYTES:
                    raise PublicationError(f"{path.name} exceeds compressed limit")
                compressed_digest.update(chunk)
            return chunk
        try:
            header = read_chunk(10)
            if header != GZIP_HEADER:
                raise PublicationError("gzip header is not the exact deterministic header")
            trailing = bytearray()
            while not decompressor.eof:
                chunk = read_chunk(16384)
                if not chunk:
                    raise PublicationError("truncated gzip member")
                data = chunk
                while data and not decompressor.eof:
                    output = decompressor.decompress(data, 65536)
                    data = decompressor.unconsumed_tail
                    if output:
                        yield output
                if decompressor.eof:
                    trailing.extend(decompressor.unused_data)
                    break
            while True:
                chunk = read_chunk(16384)
                if not chunk:
                    break
                remaining = max(0, 8 - len(trailing))
                trailing.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    state["extra"] = True
            if len(trailing) != 8 or state.get("extra"):
                raise PublicationError("gzip has concatenated member or trailing bytes")
            state["trailer"] = bytes(trailing)
        finally:
            os.close(descriptor)
    return iterator(), lambda: (state["size"], state["trailer"])


def _verify_gzip(path: Path, callback: Callable[[bytes], None]) -> dict[str, Any]:
    compressed_digest = hashlib.sha256()
    chunks, state = _gzip_chunks(path, compressed_digest)
    try:
        try:
            count, size, decompressed_hash, crc = _consume_lines(chunks, callback)
        except zlib.error as exc:
            raise PublicationError(f"invalid raw-deflate gzip payload: {exc}") from exc
        compressed_size, trailer = state()
        expected_crc, expected_size = struct.unpack("<II", trailer)
        if crc != expected_crc or size & 0xffffffff != expected_size:
            raise PublicationError("gzip CRC32 or ISIZE mismatch")
        if size > compressed_size * MAX_COMPRESSION_RATIO:
            raise PublicationError("gzip compression ratio exceeds limit")
        return {"count": count, "decompressed_bytes": size, "decompressed_hash": decompressed_hash,
                "compressed_bytes": compressed_size,
                "compressed_hash": "sha256:" + compressed_digest.hexdigest()}
    finally:
        close = getattr(chunks, "close", None)
        if close is not None:
            close()


def _load_marker(root: Path) -> dict[str, Any]:
    marker, _ = load_canonical_object(root / MARKER_NAME)
    expected_keys = {"schema_version", "dataset_kind", "lock_hash", "holdout_hash", "attempt_id"}
    if set(marker) != expected_keys or marker.get("schema_version") != "area-one-attempt-consumed/1.0":
        raise PublicationError("attempt-consumed marker has wrong shape")
    if marker.get("dataset_kind") not in ("holdout", "development-fixture"):
        raise PublicationError("attempt-consumed marker has invalid dataset kind")
    if (not isinstance(marker.get("lock_hash"), str) or _HASH_RE.fullmatch(marker["lock_hash"]) is None
            or not isinstance(marker.get("holdout_hash"), str)
            or _HASH_RE.fullmatch(marker["holdout_hash"]) is None):
        raise PublicationError("attempt-consumed marker has invalid hash binding")
    if not isinstance(marker.get("attempt_id"), str) or _ATTEMPT_RE.fullmatch(marker["attempt_id"]) is None:
        raise PublicationError("attempt-consumed marker has invalid attempt ID")
    return marker


def _verify_marker(root: Path, lock: dict[str, Any]) -> dict[str, Any]:
    marker = _load_marker(root)
    if marker.get("dataset_kind") != lock["dataset_kind"] or marker.get("lock_hash") != lock["lock_hash"] or marker.get("holdout_hash") != lock["holdout_hash"]:
        raise PublicationError("attempt-consumed marker does not match publication")
    return marker


def _verify_staging(root: Path) -> None:
    staging = root / STAGING_NAME
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    if _is_link(staging) or not stat.S_ISDIR(info.st_mode):
        raise PublicationError("atomic-publication-staging is not a safe directory")
    if any(staging.iterdir()):
        raise PublicationError("atomic-publication-staging is nonempty")


def _find_failure(root: Path, schemas: dict[str, dict[str, Any]]) -> tuple[Path, dict[str, Any]] | None:
    for entry in sorted(root.iterdir(), key=lambda path: path.name):
        if entry.suffix != ".json" or entry.name == MARKER_NAME:
            continue
        try:
            value, _ = load_canonical_object(entry)
        except PublicationError:
            try:
                raw = _regular_file(entry, MAX_DOCUMENT_BYTES)
            except PublicationError:
                continue
            if b"area-one-pair-results-failure/1.0" in raw:
                raise PublicationError("malformed failure document coexists with completion")
            continue
        if value.get("schema_version") == "area-one-pair-results-failure/1.0":
            _verify_document(value, "area-one-pair-results-failure/1.0", schemas, "failure")
            return entry, value
    return None


def _verify_failure_semantics(failure: dict[str, Any], marker: dict[str, Any]) -> None:
    expected = {
        "schema_version": "area-one-pair-results-failure/1.0",
        "dataset_kind": marker["dataset_kind"], "lock_hash": marker["lock_hash"],
        "holdout_hash": marker["holdout_hash"], "attempt_id": marker["attempt_id"],
        "stage": "completion-publication", "reason_code": "interrupted", "message": FAILURE_MESSAGE,
    }
    if failure != expected:
        raise PublicationError("failure document does not have fixed non-outcome semantics")
    forbidden = ("outcome", "probability", "verdict", "score", "rank", "median", "quantile", "lift")
    text = canonical_json(failure).lower()
    if any(word in text for word in forbidden):
        raise PublicationError("failure document contains outcome-bearing text")


def verify_failure_document(root: os.PathLike[str] | str,
                            failure_path: os.PathLike[str] | str) -> VerificationResult:
    try:
        root_path = _safe_root(root)
        path = _safe_child(root_path, failure_path, "failure path")
        schemas = load_schemas()
        failure, _ = load_canonical_object(path)
        _verify_document(failure, "area-one-pair-results-failure/1.0", schemas, "failure")
        marker = _load_marker(root_path)
        _verify_failure_semantics(failure, marker)
        _verify_staging(root_path)
        for entry in root_path.iterdir():
            if entry == path:
                continue
            if entry.suffix == ".json":
                try:
                    value, _ = load_canonical_object(entry)
                except PublicationError:
                    continue
                if value.get("schema_version") == "area-one-pair-results-complete/1.0":
                    raise PublicationError("completion and failure documents coexist")
        return VerificationResult(True, 0, None, None, ())
    except (PublicationError, OSError, sqlite3.Error) as exc:
        return VerificationResult(False, 0, None, None, (str(exc),))


def _verify_publication(root: Path, completion_path: Path, require_marker: bool) -> VerificationResult:
    schemas = load_schemas()
    _verify_staging(root)
    completion, _ = load_canonical_object(completion_path)
    _verify_document(completion, "area-one-pair-results-complete/1.0", schemas, "completion")
    _verify_hash(completion, "completion_hash", "completion")
    failure = _find_failure(root, schemas)
    if failure is not None:
        raise PublicationError("completion and failure documents coexist")
    lock_path = _safe_child(root, completion["lock_file"], "lock file")
    manifest_path = _safe_child(root, completion["family_manifest_file"], "family manifest file")
    summary_path = _safe_child(root, completion["summary_file"], "summary file")
    lock, _ = load_canonical_object(lock_path)
    manifest, _ = load_canonical_object(manifest_path)
    summary, summary_bytes = load_canonical_object(summary_path)
    _verify_document(lock, "area-one-pair-lock/1.0", schemas, "lock")
    _verify_document(manifest, "area-one-control-family-manifest/1.0", schemas, "family manifest")
    _verify_document(summary, "area-one-pair-summary/1.0", schemas, "summary")
    parameters = _verify_lock(lock)
    _verify_manifest(manifest)
    if lock["family_manifest_hash"] != manifest["manifest_hash"]:
        raise PublicationError("lock family-manifest binding is wrong")
    bindings = (completion["dataset_kind"], completion["lock_hash"], completion["family_manifest_hash"], completion["holdout_hash"])
    expected_bindings = (lock["dataset_kind"], lock["lock_hash"], lock["family_manifest_hash"], lock["holdout_hash"])
    if bindings != expected_bindings:
        raise PublicationError("completion lock/manifest/holdout bindings are wrong")
    if (summary["dataset_kind"], summary["lock_hash"], summary["family_manifest_hash"], summary["holdout_hash"]) != expected_bindings:
        raise PublicationError("summary lock/manifest/holdout bindings are wrong")
    if completion["summary_hash"] != _sha256(summary_bytes):
        raise PublicationError("completion summary hash is wrong")
    if require_marker:
        _verify_marker(root, lock)
    shards = completion["shards"]
    if not 1 <= len(shards) <= MAX_SHARDS or [item["shard_id"] for item in shards] != list(range(len(shards))):
        raise PublicationError("shard IDs are not contiguous from zero")
    expected_iterator = iter(expected_rows(lock, parameters))
    global_digest = hashlib.sha256()
    total_rows = total_bytes = total_compressed = 0
    with tempfile.TemporaryDirectory(prefix="area-one-publication-verifier-") as directory:
        with Reconstructor(Path(directory) / "lifts.sqlite3", lock) as reconstructor:
            ordinal = 0
            for index, item in enumerate(shards):
                shard_id = item["shard_id"]
                metadata_name = f"shard-{shard_id:06d}.json"
                gzip_name = f"rows-{shard_id:06d}.jsonl.gz"
                if item["metadata_file"] != metadata_name or item["gzip_file"] != gzip_name:
                    raise PublicationError(f"shard {shard_id} filenames are not ID-derived")
                metadata, _ = load_canonical_object(_safe_child(root, metadata_name, "shard metadata"))
                _verify_document(metadata, "area-one-pair-shard/1.0", schemas, f"shard {shard_id}")
                if metadata["shard_id"] != shard_id or metadata["gzip_file"] != gzip_name:
                    raise PublicationError(f"shard {shard_id} metadata identity is wrong")
                first_key: str | None = None
                last_key: str | None = None
                def accept(line: bytes) -> None:
                    nonlocal ordinal, first_key, last_key
                    global_digest.update(line + b"\n")
                    value = strict_json(line, f"row {ordinal}")
                    if not isinstance(value, dict) or line != canonical_json(value).encode("utf-8"):
                        raise PublicationError(f"row {ordinal} is not canonical compact JSON")
                    _verify_document(value, "area-one-pair-row/1.0", schemas, f"row {ordinal}")
                    try:
                        expected = next(expected_iterator)
                    except StopIteration as exc:
                        raise PublicationError(f"extra row at ordinal {ordinal}") from exc
                    if _row_tuple(value) != expected:
                        raise PublicationError(f"row {ordinal} is out of canonical order or has wrong expected tuple")
                    probability, invariant = _verify_row(value, lock, parameters, ordinal)
                    reconstructor.add(value, probability, invariant)
                    first_key = value["row_key"] if first_key is None else first_key
                    last_key = value["row_key"]
                    ordinal += 1
                gzip_result = _verify_gzip(_safe_child(root, gzip_name, "gzip shard"), accept)
                count = gzip_result["count"]
                total_rows += count
                total_bytes += gzip_result["decompressed_bytes"]
                total_compressed += gzip_result["compressed_bytes"]
                if (total_rows > MAX_ROWS or total_bytes > MAX_TOTAL_DECOMPRESSED_BYTES
                        or total_compressed > MAX_TOTAL_COMPRESSED_BYTES):
                    raise PublicationError("publication exceeds global streaming limits")
                expected_count = lock["shard_rows"] if index < len(shards) - 1 else count
                if index < len(shards) - 1 and count != lock["shard_rows"]:
                    raise PublicationError("nonfinal shard is not full")
                if not 1 <= count <= lock["shard_rows"]:
                    raise PublicationError("final shard count is invalid")
                expected_metadata = {
                    "schema_version": "area-one-pair-shard/1.0", "shard_id": shard_id,
                    "gzip_file": gzip_name, "first_ordinal": shard_id * lock["shard_rows"],
                    "expected_count": expected_count, "actual_count": count,
                    "decompressed_bytes": gzip_result["decompressed_bytes"],
                    "decompressed_hash": gzip_result["decompressed_hash"],
                    "compressed_bytes": gzip_result["compressed_bytes"],
                    "compressed_hash": gzip_result["compressed_hash"],
                    "first_row_key": first_key, "last_row_key": last_key,
                    "lock_hash": lock["lock_hash"],
                }
                if metadata != expected_metadata:
                    raise PublicationError(f"shard {shard_id} metadata does not match streamed content")
                completion_projection = {key: metadata[key] for key in (
                    "shard_id", "expected_count", "actual_count", "decompressed_hash", "compressed_hash")}
                completion_projection.update({"metadata_file": metadata_name, "gzip_file": gzip_name})
                if item != completion_projection:
                    raise PublicationError(f"completion shard {shard_id} binding is wrong")
            try:
                next(expected_iterator)
            except StopIteration:
                pass
            else:
                raise PublicationError("publication is missing expected rows")
            reconstructed = reconstructor.finish()
    if completion["global_expected_count"] != total_rows or completion["global_actual_count"] != total_rows:
        raise PublicationError("completion global row counts are wrong")
    if completion["canonical_jsonl_hash"] != "sha256:" + global_digest.hexdigest():
        raise PublicationError("completion canonical decompressed hash is wrong")
    reconstructed_bytes = (canonical_json(reconstructed) + "\n").encode("utf-8")
    if summary_bytes != reconstructed_bytes:
        raise PublicationError("summary is not byte-for-byte independent reconstruction")
    return VerificationResult(True, total_rows, completion["completion_hash"],
                              reconstructed["verdict"]["passed"], ())


def verify_publication(root: os.PathLike[str] | str,
                       completion_path: os.PathLike[str] | str) -> VerificationResult:
    """Verify a final publication; caller must explicitly supply its completion path."""
    try:
        root_path = _safe_root(root)
        path = _safe_child(root_path, completion_path, "completion path")
        return _verify_publication(root_path, path, True)
    except (PublicationError, OSError, sqlite3.Error, zlib.error) as exc:
        return VerificationResult(False, 0, None, None, (str(exc),))


def verify_staged_publication(root: os.PathLike[str] | str,
                              completion_path: os.PathLike[str] | str) -> VerificationResult:
    """Verify staged artifacts before the final attempt marker is colocated."""
    try:
        root_path = _safe_root(root)
        path = _safe_child(root_path, completion_path, "completion path")
        return _verify_publication(root_path, path, False)
    except (PublicationError, OSError, sqlite3.Error, zlib.error) as exc:
        return VerificationResult(False, 0, None, None, (str(exc),))


def completion_verification_callback(completion_path: Path) -> bool:
    """T5 callback adapter for staged and final completion verification."""
    path = Path(completion_path)
    if path.parent.name == STAGING_NAME:
        return verify_staged_publication(path.parent, path.name).valid
    return verify_publication(path.parent, path.name).valid


def staged_verification_callback(staging: Path, plan: Any) -> bool:
    """Two-argument atomic-publication staged callback adapter."""
    name = getattr(plan, "completion_name", None)
    return isinstance(name, str) and verify_staged_publication(staging, name).valid


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="dedicated publication root")
    parser.add_argument("completion_path", help="caller-supplied completion path")
    args = parser.parse_args(argv)
    result = verify_publication(args.root, args.completion_path)
    if result.valid:
        print(canonical_json({"valid": True, "rows": result.rows,
                              "completion_hash": result.completion_hash,
                              "verdict_passed": result.verdict_passed}))
        return 0
    print(canonical_json({"valid": False, "errors": list(result.errors)}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
