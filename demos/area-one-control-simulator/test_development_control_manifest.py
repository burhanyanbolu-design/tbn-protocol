#!/usr/bin/env python3
"""Focused T9 tests for the R=6-only control projection."""

from __future__ import annotations

import copy
import hashlib
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import development_control_manifest as development
import matching_control_manifest


class DevelopmentControlManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.projection = development.generate_from_file()
        cls.encoded = development.canonical_projection_bytes(cls.projection)

    def test_exact_r6_only_family_order_and_binding(self) -> None:
        self.assertEqual(self.projection["R"], 6)
        self.assertEqual(
            self.projection["source_manifest_hash"],
            development.SOURCE_MANIFEST_HASH,
        )
        families = self.projection["families"]
        self.assertEqual(len(families), 100)
        self.assertEqual(
            [family["family_id"] for family in families],
            [f"control-{index:03d}" for index in range(100)],
        )
        self.assertEqual({family["member"]["R"] for family in families}, {6})
        text = self.encoded.decode("utf-8")
        for forbidden in ('"R":7', '"R":8', '"R":9'):
            self.assertNotIn(forbidden, text)

    def test_projection_matches_every_full_manifest_r6_member(self) -> None:
        full = matching_control_manifest.load_manifest(
            matching_control_manifest.DEFAULT_PATH
        )
        for projected, source in zip(
            self.projection["families"], full["families"]
        ):
            self.assertEqual(projected["family_id"], source["family_id"])
            self.assertEqual(projected["member"], source["members"][0])

    def test_independent_generation_does_not_call_production_projection(self) -> None:
        with mock.patch.object(
            development, "_project_family", side_effect=AssertionError
        ):
            independent = development.independently_generate_projection()
        self.assertEqual(
            self.encoded, development.canonical_projection_bytes(independent)
        )

    def test_checked_artifact_is_canonical_and_exact(self) -> None:
        self.assertEqual(development.DEFAULT_PATH.read_bytes(), self.encoded)
        self.assertEqual(
            development.load_projection(development.DEFAULT_PATH), self.projection
        )
        self.assertTrue(self.encoded.endswith(b"\n"))
        self.assertFalse(self.encoded.endswith(b"\n\n"))
        self.assertNotIn(b"\r", self.encoded)
        self.assertNotIn(b": ", self.encoded)

    def test_projection_hash_is_canonical_body_hash(self) -> None:
        body = dict(self.projection)
        body.pop("projection_hash")
        expected = "sha256:" + hashlib.sha256(
            development._canonical_json(body).encode("utf-8")
        ).hexdigest()
        self.assertEqual(self.projection["projection_hash"], expected)

    def test_cli_write_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "r6.json"
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    development.main(["--output", str(path)]), 0
                )
            self.assertEqual(path.read_bytes(), self.encoded)
            self.assertIn("row_counts=6", output.getvalue())
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    development.main(["--verify", str(path)]), 0
                )
            self.assertIn("independent_projection=PASS", output.getvalue())

    def test_mutations_and_noncanonical_bytes_fail_closed(self) -> None:
        mutations = (
            lambda value: value.update({"R": 7}),
            lambda value: value["families"][0]["member"].update({"R": 7}),
            lambda value: value["families"][0].update(
                {"family_id": "control-001"}
            ),
            lambda value: value["families"][0]["member"].update(
                {"destination_rows": [1, 2, 3, 4, 5]}
            ),
            lambda value: value.update({"heldout": True}),
        )
        for mutate in mutations:
            changed = copy.deepcopy(self.projection)
            mutate(changed)
            changed["projection_hash"] = development.projection_sha256(changed)
            with self.subTest(mutate=mutate), self.assertRaises(
                development.DevelopmentManifestError
            ):
                development.validate_projection(changed)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "r6.json"
            path.write_bytes(self.encoded[:-1])
            with self.assertRaises(development.DevelopmentManifestError):
                development.load_projection(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
