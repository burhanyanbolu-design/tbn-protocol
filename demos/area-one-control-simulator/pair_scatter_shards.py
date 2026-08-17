#!/usr/bin/env python3
"""Deterministic ordinal sharding for Area One pair-scatter rows."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

SHARD_ROWS = 100_000
WORKER_COUNT = 4


@dataclass(frozen=True)
class Shard:
    shard_id: int
    owner: int
    ordinals: tuple[int, ...]
    data: bytes
    sha256: str
    row_count: int
    byte_size: int


@dataclass(frozen=True)
class Artifact:
    data: bytes
    sha256: str
    row_count: int
    byte_size: int


def _require_int(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def shard_id_for_ordinal(ordinal: int, *, shard_rows: int = SHARD_ROWS) -> int:
    """Pure assignment helper; tests may inject a smaller shard size."""
    ordinal = _require_int(ordinal, "ordinal")
    shard_rows = _require_int(shard_rows, "shard_rows", minimum=1)
    return ordinal // shard_rows


def owner_for_shard(shard_id: int) -> int:
    """Return ownership under the immutable four-worker topology."""
    return _require_int(shard_id, "shard_id") % WORKER_COUNT


def encode_canonical_row(row: Mapping[str, object]) -> bytes:
    """Encode sorted-key compact UTF-8 JSON followed by exactly one LF."""
    if not isinstance(row, Mapping):
        raise TypeError("row must be a mapping")
    try:
        text = json.dumps(
            row,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("row is not canonical-JSON encodable") from exc
    return text.encode("utf-8", errors="strict") + b"\n"


def _make_shard(shard_id: int, ordinals: list[int], chunks: list[bytes]) -> Shard:
    data = b"".join(chunks)
    return Shard(
        shard_id=shard_id,
        owner=owner_for_shard(shard_id),
        ordinals=tuple(ordinals),
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
        row_count=len(ordinals),
        byte_size=len(data),
    )


def build_shards(
    records: Iterable[tuple[int, Mapping[str, object]]],
    *,
    shard_rows: int,
) -> tuple[Shard, ...]:
    """Pure helper requiring one global ordinal sequence beginning at zero."""
    shard_rows = _require_int(shard_rows, "shard_rows", minimum=1)
    result: list[Shard] = []
    current_id: int | None = None
    ordinals: list[int] = []
    chunks: list[bytes] = []
    expected = 0
    for record in records:
        if not isinstance(record, tuple) or len(record) != 2:
            raise TypeError("each record must be an (ordinal, row) tuple")
        ordinal = _require_int(record[0], "ordinal")
        if ordinal != expected:
            raise ValueError(f"expected ordinal {expected}, received {ordinal}")
        expected += 1
        shard_id = shard_id_for_ordinal(ordinal, shard_rows=shard_rows)
        if current_id is None:
            current_id = shard_id
        elif shard_id != current_id:
            result.append(_make_shard(current_id, ordinals, chunks))
            current_id, ordinals, chunks = shard_id, [], []
        ordinals.append(ordinal)
        chunks.append(encode_canonical_row(record[1]))
    if current_id is not None:
        result.append(_make_shard(current_id, ordinals, chunks))
    return tuple(result)


def build_production_shards(
    records: Iterable[tuple[int, Mapping[str, object]]],
) -> tuple[Shard, ...]:
    """Production entry point with immutable 100,000-row shards."""
    return build_shards(records, shard_rows=SHARD_ROWS)


def _validate_shard(shard: Shard, *, shard_rows: int) -> None:
    if not isinstance(shard, Shard):
        raise TypeError("all shards must be Shard instances")
    shard_id = _require_int(shard.shard_id, "shard_id")
    if shard.owner != owner_for_shard(shard_id):
        raise ValueError(f"shard {shard_id} has incorrect worker owner")
    if not shard.ordinals:
        raise ValueError(f"shard {shard_id} is empty")
    expected_first = shard_id * shard_rows
    expected = tuple(range(expected_first, expected_first + len(shard.ordinals)))
    if shard.ordinals != expected:
        raise ValueError(f"shard {shard_id} ordinals are not strictly sequential")
    if shard.row_count != len(shard.ordinals):
        raise ValueError(f"shard {shard_id} row count metadata mismatch")
    if shard.byte_size != len(shard.data):
        raise ValueError(f"shard {shard_id} byte size metadata mismatch")
    if hashlib.sha256(shard.data).hexdigest() != shard.sha256:
        raise ValueError(f"shard {shard_id} SHA-256 metadata mismatch")
    if not shard.data.endswith(b"\n"):
        raise ValueError(f"shard {shard_id} lacks final LF")
    if shard.data.count(b"\n") != shard.row_count:
        raise ValueError(f"shard {shard_id} encoded row count mismatch")


def merge_shards(shards: Sequence[Shard], *, shard_rows: int) -> Artifact:
    """Validate then merge by shard ID, independent of supplied shard order."""
    shard_rows = _require_int(shard_rows, "shard_rows", minimum=1)
    materialized = tuple(shards)
    if not materialized:
        return Artifact(b"", hashlib.sha256(b"").hexdigest(), 0, 0)
    ids = [item.shard_id for item in materialized if isinstance(item, Shard)]
    if len(ids) != len(materialized):
        raise TypeError("all shards must be Shard instances")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate shard ID")
    ordered = tuple(sorted(materialized, key=lambda item: item.shard_id))
    expected_ids = list(range(len(ordered)))
    if [item.shard_id for item in ordered] != expected_ids:
        raise ValueError("missing shard ID")
    for index, shard in enumerate(ordered):
        _validate_shard(shard, shard_rows=shard_rows)
        if index < len(ordered) - 1 and shard.row_count != shard_rows:
            raise ValueError("every non-final shard must be exactly full")
        if index == len(ordered) - 1 and not 1 <= shard.row_count <= shard_rows:
            raise ValueError("final shard must contain at most shard_rows rows")
    data = b"".join(shard.data for shard in ordered)
    row_count = sum(shard.row_count for shard in ordered)
    return Artifact(data, hashlib.sha256(data).hexdigest(), row_count, len(data))


def merge_production_shards(shards: Sequence[Shard]) -> Artifact:
    """Production merge entry point with immutable shard sizing."""
    return merge_shards(shards, shard_rows=SHARD_ROWS)


def deterministic_gzip(data: bytes, *, row_count: int) -> Artifact:
    """Compress with level 9, mtime zero, and no embedded filename."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    row_count = _require_int(row_count, "row_count")
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=output, compresslevel=9, mtime=0
    ) as handle:
        handle.write(data)
    compressed = output.getvalue()
    return Artifact(
        compressed, hashlib.sha256(compressed).hexdigest(), row_count, len(compressed)
    )
