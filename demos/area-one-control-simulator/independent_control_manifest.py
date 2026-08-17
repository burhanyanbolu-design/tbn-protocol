#!/usr/bin/env python3
"""Standalone regeneration of the immutable Area One control-family manifest.

This module deliberately does not import the production manifest generator. It
independently implements permutation enumeration, ranking, assembly, metadata,
canonical serialization, and the internal manifest hash.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Sequence
from typing import Any

_ROWS = (6, 7, 8, 9)
_SCHEMA_VERSION = "area-one-control-family-manifest/1.0"
_GENERATOR_VERSION = "area-one-control-random-v1"
_RANDOM_COUNT = 91


def _compact_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _permutation_text(values: Sequence[int]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def _permutations(values: tuple[int, ...]) -> Iterator[tuple[int, ...]]:
    if not values:
        yield ()
        return
    for position in range(len(values)):
        chosen = values[position]
        remaining = values[:position] + values[position + 1 :]
        for tail in _permutations(remaining):
            yield (chosen,) + tail


def _rotate(values: tuple[int, ...], amount: int) -> tuple[int, ...]:
    split = amount % len(values)
    return values[split:] + values[:split]


def _forbidden_symmetries(rows: int) -> set[tuple[int, ...]]:
    forward = tuple(range(1, rows))
    backward = forward[::-1]
    return {
        *(_rotate(forward, offset) for offset in range(rows - 1)),
        *(_rotate(backward, offset) for offset in range(rows - 1)),
    }


def _random_choices(rows: int) -> list[tuple[int, ...]]:
    forbidden = _forbidden_symmetries(rows)
    ordered: list[tuple[str, str, tuple[int, ...]]] = []
    for values in _permutations(tuple(range(1, rows))):
        if values in forbidden:
            continue
        encoded = _permutation_text(values)
        rank_input = f"{_GENERATOR_VERSION}|{rows}|{encoded}".encode("utf-8")
        ordered.append((hashlib.sha256(rank_input).hexdigest(), encoded, values))
    ordered.sort(key=lambda record: (record[0], record[1]))
    if len(ordered) < _RANDOM_COUNT:
        raise ValueError(f"R={rows} has only {len(ordered)} eligible random controls")
    return [record[2] for record in ordered[:_RANDOM_COUNT]]


def _member(rows: int, destinations: tuple[int, ...]) -> dict[str, Any]:
    displacement = [
        destination - (source + 1)
        for source, destination in enumerate(destinations)
    ]
    return {
        "R": rows,
        "destination_rows": list(destinations),
        "displacements": displacement,
        "retained_genuine_edges": sum(value == 0 for value in displacement),
        "cardinality": len(destinations),
        "disjoint": (
            len(destinations) == rows - 1
            and set(destinations) == set(range(1, rows))
        ),
    }


def _body() -> dict[str, Any]:
    random_by_rows = {rows: _random_choices(rows) for rows in _ROWS}
    families: list[dict[str, Any]] = []
    for ordinal in range(100):
        members: list[dict[str, Any]] = []
        for rows in _ROWS:
            forward = tuple(range(1, rows))
            if ordinal < 4:
                destinations = _rotate(forward, ordinal + 1)
            elif ordinal < 9:
                destinations = _rotate(forward[::-1], ordinal - 4)
            else:
                destinations = random_by_rows[rows][ordinal - 9]
            members.append(_member(rows, destinations))
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
        "schema_version": _SCHEMA_VERSION,
        "generator_version": _GENERATOR_VERSION,
        "families": families,
    }


def generate_manifest() -> dict[str, Any]:
    """Return a fully assembled and internally hashed manifest."""
    manifest = _body()
    digest = hashlib.sha256(_compact_json(manifest).encode("utf-8")).hexdigest()
    manifest["manifest_hash"] = f"sha256:{digest}"
    return manifest


def generate_manifest_bytes() -> bytes:
    """Return canonical sorted compact UTF-8 JSON with exactly one final LF."""
    return (_compact_json(generate_manifest()) + "\n").encode("utf-8")
