#!/usr/bin/env python3
"""Canonical R=6-only projection of the frozen Area One control manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import independent_control_manifest
from matching_control_manifest import (
    DEFAULT_PATH as FULL_MANIFEST_PATH,
    ManifestValidationError,
    load_manifest,
    verify_independent_regeneration,
)

SCHEMA_VERSION = "area-one-control-family-development-r6/1.0"
SOURCE_MANIFEST_HASH = (
    "sha256:7f7dfc6f7773b59f7b13d8a9ddcb3bc35ad800eef5faec25cb20bf0f42164b9e"
)
ROW_COUNT = 6
FAMILY_COUNT = 100
DEFAULT_PATH = Path(__file__).with_name(
    "control-family-manifest-development-r6.json"
)


class DevelopmentManifestError(ValueError):
    """Raised when the development projection violates its closed contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def canonical_projection_bytes(projection: dict[str, Any]) -> bytes:
    return (_canonical_json(projection) + "\n").encode("utf-8")

def projection_sha256(projection: dict[str, Any]) -> str:
    body = dict(projection)
    body.pop("projection_hash", None)
    digest = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _project_family(family: dict[str, Any]) -> dict[str, Any]:
    members = family["members"]
    member = next((item for item in members if item["R"] == ROW_COUNT), None)
    if member is None:
        raise DevelopmentManifestError(
            f"{family.get('family_id', '<unknown>')} has no R=6 member"
        )
    return {
        "family_id": family["family_id"],
        "kind": family["kind"],
        "structured_subkind": family["structured_subkind"],
        "member": {
            "R": member["R"],
            "destination_rows": list(member["destination_rows"]),
            "displacements": list(member["displacements"]),
            "retained_genuine_edges": member["retained_genuine_edges"],
            "cardinality": member["cardinality"],
            "disjoint": member["disjoint"],
        },
    }


def project_manifest(full_manifest: dict[str, Any]) -> dict[str, Any]:
    """Extract only the frozen R=6 member after full-manifest validation."""
    if full_manifest.get("manifest_hash") != SOURCE_MANIFEST_HASH:
        raise DevelopmentManifestError("full manifest hash is not the frozen T1 hash")
    projection = {
        "schema_version": SCHEMA_VERSION,
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
        "R": ROW_COUNT,
        "families": [_project_family(family) for family in full_manifest["families"]],
    }
    projection["projection_hash"] = projection_sha256(projection)
    validate_projection(projection, verify_exact=False)
    return projection


def independently_generate_projection() -> dict[str, Any]:
    """Regenerate from the standalone T1 implementation, not production helpers."""
    full = independent_control_manifest.generate_manifest()
    if full.get("manifest_hash") != SOURCE_MANIFEST_HASH:
        raise DevelopmentManifestError("independent T1 hash is not frozen")
    families: list[dict[str, Any]] = []
    for ordinal, source in enumerate(full["families"]):
        r6 = source["members"][0]
        if r6.get("R") != ROW_COUNT:
            raise DevelopmentManifestError("independent members are not R-major")
        families.append({
            "family_id": f"control-{ordinal:03d}",
            "kind": source["kind"],
            "structured_subkind": source["structured_subkind"],
            "member": {
                "R": ROW_COUNT,
                "destination_rows": list(r6["destination_rows"]),
                "displacements": list(r6["displacements"]),
                "retained_genuine_edges": r6["retained_genuine_edges"],
                "cardinality": r6["cardinality"],
                "disjoint": r6["disjoint"],
            },
        })
    result = {
        "schema_version": SCHEMA_VERSION,
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
        "R": ROW_COUNT,
        "families": families,
    }
    result["projection_hash"] = projection_sha256(result)
    return result

def _require_exact_keys(
    value: object, expected: set[str], location: str
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DevelopmentManifestError(f"{location} must be an object")
    actual = set(value)
    if actual != expected:
        raise DevelopmentManifestError(
            f"{location} fields differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )
    return value


def validate_projection(
    projection: dict[str, Any], *, verify_exact: bool = True
) -> None:
    root = _require_exact_keys(projection, {
        "schema_version", "source_manifest_hash", "projection_hash", "R",
        "families",
    }, "projection")
    if root["schema_version"] != SCHEMA_VERSION:
        raise DevelopmentManifestError("schema_version is not frozen")
    if root["source_manifest_hash"] != SOURCE_MANIFEST_HASH:
        raise DevelopmentManifestError("source_manifest_hash is not frozen")
    if root["R"] != ROW_COUNT or type(root["R"]) is not int:
        raise DevelopmentManifestError("projection must contain only exact integer R=6")
    if root["projection_hash"] != projection_sha256(root):
        raise DevelopmentManifestError("projection_hash mismatch")
    families = root["families"]
    if not isinstance(families, list) or len(families) != FAMILY_COUNT:
        raise DevelopmentManifestError("projection must contain exactly 100 families")
    seen: set[tuple[int, ...]] = set()
    for ordinal, raw_family in enumerate(families):
        family = _require_exact_keys(raw_family, {
            "family_id", "kind", "structured_subkind", "member",
        }, f"families[{ordinal}]")
        family_id = f"control-{ordinal:03d}"
        if family["family_id"] != family_id:
            raise DevelopmentManifestError("family order or identity changed")
        expected_kind = "structured" if ordinal < 9 else "random"
        expected_subkind = (
            "cyclic" if ordinal < 4
            else "reflected" if ordinal < 9
            else None
        )
        if (family["kind"], family["structured_subkind"]) != (
            expected_kind, expected_subkind
        ):
            raise DevelopmentManifestError(f"{family_id} kind/subkind changed")
        member = _require_exact_keys(family["member"], {
            "R", "destination_rows", "displacements", "retained_genuine_edges",
            "cardinality", "disjoint",
        }, f"{family_id}.member")
        if member["R"] != ROW_COUNT or type(member["R"]) is not int:
            raise DevelopmentManifestError("non-development row count in projection")
        destinations = member["destination_rows"]
        if (
            not isinstance(destinations, list)
            or any(type(value) is not int for value in destinations)
            or len(destinations) != 5
            or set(destinations) != set(range(1, 6))
        ):
            raise DevelopmentManifestError(f"{family_id} member is not an R=6 bijection")
        permutation = tuple(destinations)
        if permutation == tuple(range(1, 6)) or permutation in seen:
            raise DevelopmentManifestError("candidate or duplicate permutation in projection")
        seen.add(permutation)
        displacement = [value - (index + 1) for index, value in enumerate(destinations)]
        expected_member = {
            "R": 6,
            "destination_rows": destinations,
            "displacements": displacement,
            "retained_genuine_edges": sum(value == 0 for value in displacement),
            "cardinality": 5,
            "disjoint": True,
        }
        if member != expected_member:
            raise DevelopmentManifestError(f"{family_id} member metadata changed")
    if verify_exact:
        independent = independently_generate_projection()
        if canonical_projection_bytes(root) != canonical_projection_bytes(independent):
            raise DevelopmentManifestError("independent R=6 projection mismatch")

def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DevelopmentManifestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise DevelopmentManifestError(f"non-finite JSON constant: {value}")


def load_projection(path: Path | str = DEFAULT_PATH) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    try:
        projection = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DevelopmentManifestError(f"invalid projection JSON: {exc}") from exc
    validate_projection(projection)
    if raw != canonical_projection_bytes(projection):
        raise DevelopmentManifestError("projection bytes are not canonical JSON plus LF")
    return projection


def generate_from_file(
    full_manifest_path: Path | str = FULL_MANIFEST_PATH,
) -> dict[str, Any]:
    full = load_manifest(full_manifest_path)
    verify_independent_regeneration(full)
    return project_manifest(full)


def write_projection(path: Path | str, projection: dict[str, Any]) -> str:
    validate_projection(projection)
    Path(path).write_bytes(canonical_projection_bytes(projection))
    return projection["projection_hash"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=FULL_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verify is not None:
            projection = load_projection(args.verify)
            path = args.verify
        else:
            projection = generate_from_file(args.source)
            write_projection(args.output, projection)
            path = args.output
    except (OSError, ManifestValidationError, DevelopmentManifestError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(f"development_manifest_path={path}")
    print(f"source_manifest_hash={projection['source_manifest_hash']}")
    print(f"projection_hash={projection['projection_hash']}")
    print(f"families={len(projection['families'])}")
    print("row_counts=6")
    print("independent_projection=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
