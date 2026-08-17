#!/usr/bin/env python3
"""Focused tests for deterministic Area One ordinal shards."""

from __future__ import annotations

import dataclasses
import gzip
import hashlib
import unittest

import pair_scatter_shards as shards


def records(count: int):
    return tuple((ordinal, {"value": ordinal, "kind": "synthetic"}) for ordinal in range(count))


class ShardTests(unittest.TestCase):
    def test_boundary_assignment_and_owner(self) -> None:
        self.assertEqual(shards.shard_id_for_ordinal(0, shard_rows=3), 0)
        self.assertEqual(shards.shard_id_for_ordinal(2, shard_rows=3), 0)
        self.assertEqual(shards.shard_id_for_ordinal(3, shard_rows=3), 1)
        self.assertEqual(shards.owner_for_shard(5), 1)


    def test_final_partial_and_metadata(self) -> None:
        built = shards.build_shards(records(8), shard_rows=3)
        self.assertEqual([item.row_count for item in built], [3, 3, 2])
        self.assertEqual([item.owner for item in built], [0, 1, 2])
        for item in built:
            self.assertEqual(item.sha256, hashlib.sha256(item.data).hexdigest())
            self.assertEqual(item.byte_size, len(item.data))

    def test_canonical_utf8_sorted_compact_lf(self) -> None:
        self.assertEqual(shards.encode_canonical_row({"z": "é", "a": 1}), b'{"a":1,"z":"\xc3\xa9"}\n')

    def test_merge_is_independent_of_supplied_shard_order(self) -> None:
        built = shards.build_shards(records(8), shard_rows=3)
        merged = shards.merge_shards((built[2], built[0], built[1]), shard_rows=3)
        self.assertEqual(merged.data, b"".join(item.data for item in built))
        self.assertEqual(merged.row_count, 8)
        self.assertEqual(merged.byte_size, len(merged.data))

    def test_rejects_missing_duplicate_and_out_of_order(self) -> None:
        built = shards.build_shards(records(8), shard_rows=3)
        with self.assertRaisesRegex(ValueError, "missing"):
            shards.merge_shards((built[0], built[2]), shard_rows=3)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            shards.merge_shards((built[0], built[1], built[1], built[2]), shard_rows=3)
        corrupt = dataclasses.replace(built[1], ordinals=(3, 5, 4))
        with self.assertRaisesRegex(ValueError, "sequential"):
            shards.merge_shards((built[0], corrupt, built[2]), shard_rows=3)

    def test_rejects_nonfinal_partial_and_bad_metadata(self) -> None:
        built = shards.build_shards(records(8), shard_rows=3)
        partial = shards.build_shards(records(2), shard_rows=3)[0]
        with self.assertRaisesRegex(ValueError, "non-final"):
            shards.merge_shards((partial, built[1], built[2]), shard_rows=3)
        corrupt = dataclasses.replace(built[0], sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            shards.merge_shards((corrupt, built[1], built[2]), shard_rows=3)

    def test_build_rejects_missing_duplicate_and_out_of_order_ordinals(self) -> None:
        for values in (
            ((0, {}), (2, {})),
            ((0, {}), (0, {})),
            ((1, {}),),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                shards.build_shards(values, shard_rows=3)

    def test_production_constants_and_entry_points_are_fixed(self) -> None:
        self.assertEqual(shards.SHARD_ROWS, 100_000)
        self.assertEqual(shards.WORKER_COUNT, 4)
        built = shards.build_production_shards(records(2))
        self.assertEqual(len(built), 1)
        self.assertEqual(built[0].row_count, 2)


    def test_gzip_is_byte_identical_and_has_blank_header_fields(self) -> None:
        merged = shards.merge_shards(shards.build_shards(records(8), shard_rows=3), shard_rows=3)
        first = shards.deterministic_gzip(merged.data, row_count=merged.row_count)
        second = shards.deterministic_gzip(merged.data, row_count=merged.row_count)
        self.assertEqual(first, second)
        self.assertEqual(first.data[3] & 0x08, 0)  # FNAME flag is absent.
        self.assertEqual(first.data[4:8], b"\x00\x00\x00\x00")
        self.assertEqual(gzip.decompress(first.data), merged.data)
        self.assertEqual(first.sha256, hashlib.sha256(first.data).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
