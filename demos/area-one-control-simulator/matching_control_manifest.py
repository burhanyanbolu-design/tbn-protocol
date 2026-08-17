#!/usr/bin/env python3
"""Generate and strictly validate immutable Area One control families."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

ROW_COUNTS = (6, 7, 8, 9)
FAMILY_COUNT = 100
RANDOM_FAMILY_COUNT = 91
SCHEMA_VERSION = "area-one-control-family-manifest/1.0"
GENERATOR_VERSION = "area-one-control-random-v1"
DEFAULT_PATH = Path(__file__).with_name("control-family-manifest.json")


class ManifestValidationError(ValueError):
    """Raised when a control-family manifest violates the T1 contract."""


def canonical_permutation(permutation: Sequence[int]) -> str:
    """Encode a permutation as the compact JSON array used for SHA ranking."""
    return json.dumps(list(permutation), ensure_ascii=False, separators=(",", ":"))


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """Serialize a manifest as canonical compact UTF-8 JSON plus one LF."""
    return (_canonical_json(manifest) + "\n").encode("utf-8")


def manifest_sha256(manifest: dict[str, Any]) -> str:
    """Hash canonical content excluding ``manifest_hash``, without a domain."""
    body = dict(manifest)
    body.pop("manifest_hash", None)
    digest = hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _left_rotation(values: Sequence[int], offset: int) -> tuple[int, ...]:
    split = offset % len(values)
    return tuple(values[split:]) + tuple(values[:split])


def _symmetry_permutations(row_count: int) -> set[tuple[int, ...]]:
    forward = tuple(range(1, row_count))
    reflected = tuple(reversed(forward))
    return {
        *(_left_rotation(forward, offset) for offset in range(row_count - 1)),
        *(_left_rotation(reflected, offset) for offset in range(row_count - 1)),
    }


def _ranked_random_permutations(
    row_count: int,
    permutations: Iterable[Sequence[int]],
) -> list[tuple[int, ...]]:
    excluded = _symmetry_permutations(row_count)
    ranked: list[tuple[str, str, tuple[int, ...]]] = []
    for candidate in permutations:
        permutation = tuple(candidate)
        if permutation in excluded:
            continue
        canonical = canonical_permutation(permutation)
        payload = f"{GENERATOR_VERSION}|{row_count}|{canonical}".encode("utf-8")
        ranked.append((hashlib.sha256(payload).hexdigest(), canonical, permutation))
    ranked.sort(key=lambda item: (item[0], item[1]))
    if len(ranked) < RANDOM_FAMILY_COUNT:
        raise ManifestValidationError(
            f"R={row_count} has {len(ranked)} eligible random controls; "
            f"at least {RANDOM_FAMILY_COUNT} are required"
        )
    return [item[2] for item in ranked[:RANDOM_FAMILY_COUNT]]


def _member(row_count: int, permutation: Sequence[int]) -> dict[str, Any]:
    destinations = tuple(permutation)
    displacements = [
        destination - (source + 1)
        for source, destination in enumerate(destinations)
    ]
    return {
        "R": row_count,
        "destination_rows": list(destinations),
        "displacements": displacements,
        "retained_genuine_edges": sum(value == 0 for value in displacements),
        "cardinality": len(destinations),
        "disjoint": (
            len(destinations) == row_count - 1
            and set(destinations) == set(range(1, row_count))
        ),
    }


def _generate_manifest_body(
    permutation_factory: Callable[[Sequence[int]], Iterable[Sequence[int]]],
) -> dict[str, Any]:
    random_by_row = {
        row_count: _ranked_random_permutations(
            row_count, permutation_factory(tuple(range(1, row_count)))
        )
        for row_count in ROW_COUNTS
    }
    families: list[dict[str, Any]] = []
    for ordinal in range(FAMILY_COUNT):
        members: list[dict[str, Any]] = []
        for row_count in ROW_COUNTS:
            destinations = tuple(range(1, row_count))
            if ordinal < 4:
                permutation = _left_rotation(destinations, ordinal + 1)
            elif ordinal < 9:
                permutation = _left_rotation(tuple(reversed(destinations)), ordinal - 4)
            else:
                permutation = random_by_row[row_count][ordinal - 9]
            members.append(_member(row_count, permutation))
        families.append({
            "family_id": f"control-{ordinal:03d}",
            "kind": "structured" if ordinal < 9 else "random",
            "structured_subkind": (
                "cyclic" if ordinal < 4
                else "reflected" if ordinal < 9
                else None
            ),
            "members": members,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "families": families,
    }


def _generated_manifest() -> dict[str, Any]:
    manifest = _generate_manifest_body(itertools.permutations)
    manifest["manifest_hash"] = manifest_sha256(manifest)
    return manifest


def generate_manifest() -> dict[str, Any]:
    """Generate and validate the production manifest."""
    manifest = _generated_manifest()
    validate_manifest(manifest)
    return manifest


def independently_regenerate_manifest() -> dict[str, Any]:
    """Regenerate through the standalone implementation module."""
    from independent_control_manifest import generate_manifest as independent_generate

    return independent_generate()


def independently_regenerate_manifest_bytes() -> bytes:
    """Regenerate canonical bytes through the standalone implementation module."""
    from independent_control_manifest import generate_manifest_bytes

    return generate_manifest_bytes()


def _require_exact_keys(
    value: dict[str, Any], expected: set[str], location: str
) -> None:
    actual = set(value)
    if actual != expected:
        raise ManifestValidationError(
            f"{location} fields differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def validate_manifest(manifest: dict[str, Any], *, verify_exact: bool = True) -> None:
    """Validate schema shape, self-hash, families, metadata, and bindings."""
    if not isinstance(manifest, dict):
        raise ManifestValidationError("manifest must be an object")
    _require_exact_keys(
        manifest,
        {"schema_version", "generator_version", "families", "manifest_hash"},
        "manifest",
    )
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestValidationError("schema_version is not frozen")
    if manifest["generator_version"] != GENERATOR_VERSION:
        raise ManifestValidationError("generator_version is not frozen")
    expected_hash = manifest_sha256(manifest)
    if manifest["manifest_hash"] != expected_hash:
        raise ManifestValidationError("manifest_hash does not match canonical content")

    families = manifest["families"]
    if not isinstance(families, list) or len(families) != FAMILY_COUNT:
        raise ManifestValidationError("manifest must contain exactly 100 families")
    seen_permutations = {row_count: set() for row_count in ROW_COUNTS}
    for ordinal, family in enumerate(families):
        location = f"families[{ordinal}]"
        if not isinstance(family, dict):
            raise ManifestValidationError(f"{location} must be an object")
        _require_exact_keys(
            family, {"family_id", "kind", "structured_subkind", "members"}, location
        )
        expected_id = f"control-{ordinal:03d}"
        if family["family_id"] != expected_id:
            raise ManifestValidationError(f"{location} has noncanonical family_id")
        expected_kind = "structured" if ordinal < 9 else "random"
        expected_subkind = (
            "cyclic" if ordinal < 4 else "reflected" if ordinal < 9 else None
        )
        if family["kind"] != expected_kind or family["structured_subkind"] != expected_subkind:
            raise ManifestValidationError(f"{expected_id} kind/subkind changed")

        members = family["members"]
        if not isinstance(members, list) or len(members) != len(ROW_COUNTS):
            raise ManifestValidationError(f"{expected_id} must have exactly four members")
        if [member.get("R") if isinstance(member, dict) else None for member in members] != list(ROW_COUNTS):
            raise ManifestValidationError(f"{expected_id} members must be ordered R=6,7,8,9")
        for member, row_count in zip(members, ROW_COUNTS):
            member_location = f"{expected_id}.members[R={row_count}]"
            _require_exact_keys(member, {
                "R", "destination_rows", "displacements", "retained_genuine_edges",
                "cardinality", "disjoint",
            }, member_location)
            destinations = member["destination_rows"]
            if (
                not isinstance(destinations, list)
                or any(type(value) is not int for value in destinations)
                or len(destinations) != row_count - 1
                or set(destinations) != set(range(1, row_count))
            ):
                raise ManifestValidationError(f"{member_location} is not a bijection")
            permutation = tuple(destinations)
            candidate = tuple(range(1, row_count))
            if permutation == candidate:
                raise ManifestValidationError(f"{member_location} includes the candidate")
            if permutation in seen_permutations[row_count]:
                raise ManifestValidationError(f"R={row_count} has duplicate permutations")
            seen_permutations[row_count].add(permutation)
            if member != _member(row_count, permutation):
                raise ManifestValidationError(f"{member_location} metadata is inconsistent")

            symmetries = _symmetry_permutations(row_count)
            if ordinal < 4:
                expected = _left_rotation(candidate, ordinal + 1)
                if permutation != expected:
                    raise ManifestValidationError(f"{member_location} cyclic binding changed")
            elif ordinal < 9:
                expected = _left_rotation(tuple(reversed(candidate)), ordinal - 4)
                if permutation != expected:
                    raise ManifestValidationError(f"{member_location} reflected binding changed")
            elif permutation in symmetries:
                raise ManifestValidationError(
                    f"{member_location} random family uses a cyclic/reflected permutation"
                )

    if verify_exact and canonical_manifest_bytes(manifest) != canonical_manifest_bytes(_generated_manifest()):
        raise ManifestValidationError("manifest does not match frozen SHA-ranked families")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ManifestValidationError(f"non-finite JSON constant: {value}")


def load_manifest(path: Path | str, *, require_canonical: bool = True) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    try:
        manifest = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"invalid manifest JSON: {exc}") from exc
    validate_manifest(manifest)
    if require_canonical and raw != canonical_manifest_bytes(manifest):
        raise ManifestValidationError(
            "manifest bytes are not canonical compact UTF-8 JSON plus LF"
        )
    return manifest


def write_manifest(path: Path | str, manifest: dict[str, Any]) -> str:
    validate_manifest(manifest)
    Path(path).write_bytes(canonical_manifest_bytes(manifest))
    return manifest["manifest_hash"]


def verify_independent_regeneration(manifest: dict[str, Any]) -> None:
    validate_manifest(manifest)
    if canonical_manifest_bytes(manifest) != independently_regenerate_manifest_bytes():
        raise ManifestValidationError("independent regeneration is not byte-identical")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--verify", type=Path, help="verify an existing manifest instead")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.verify is not None:
            manifest = load_manifest(args.verify)
            path = args.verify
        else:
            manifest = generate_manifest()
            write_manifest(args.output, manifest)
            path = args.output
        verify_independent_regeneration(manifest)
    except (OSError, ManifestValidationError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(f"manifest_path={path}")
    print(f"manifest_hash={manifest['manifest_hash']}")
    print(f"families={len(manifest['families'])}")
    print("independent_regeneration=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
