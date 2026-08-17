#!/usr/bin/env python3
"""Focused T1 tests for immutable Area One control-family manifests."""

import copy
import hashlib
import io
import itertools
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import independent_control_manifest
import matching_control_manifest as manifest_module
import publication_verifier
from matching_control_manifest import (
    DEFAULT_PATH,
    ManifestValidationError,
    canonical_manifest_bytes,
    canonical_permutation,
    generate_manifest,
    independently_regenerate_manifest,
    load_manifest,
    manifest_sha256,
    validate_manifest,
    verify_independent_regeneration,
    write_manifest,
)


class MatchingControlManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generate_manifest()
        cls.canonical = canonical_manifest_bytes(cls.manifest)

    def test_normative_schema_and_publication_semantics(self) -> None:
        schemas = publication_verifier.load_schemas()
        schema_id = "area-one-control-family-manifest/1.0"
        publication_verifier.validate_schema(
            self.manifest, schemas[schema_id], "family manifest"
        )
        publication_verifier._verify_manifest(self.manifest)
        self.assertEqual(
            set(self.manifest),
            {"schema_version", "generator_version", "families", "manifest_hash"},
        )

    def test_exact_identity_kind_and_ordered_cross_row_contract(self) -> None:
        families = self.manifest["families"]
        self.assertEqual(len(families), 100)
        self.assertEqual(
            [family["family_id"] for family in families],
            [f"control-{ordinal:03d}" for ordinal in range(100)],
        )
        self.assertEqual(
            [(family["kind"], family["structured_subkind"]) for family in families[:9]],
            [("structured", "cyclic")] * 4
            + [("structured", "reflected")] * 5,
        )
        self.assertTrue(all(
            (family["kind"], family["structured_subkind"]) == ("random", None)
            for family in families[9:]
        ))
        for family in families:
            self.assertEqual([member["R"] for member in family["members"]], [6, 7, 8, 9])

    def test_structured_permutations_and_destination_relative_metadata(self) -> None:
        families = self.manifest["families"]
        self.assertEqual(families[0]["members"][0]["destination_rows"], [2, 3, 4, 5, 1])
        self.assertEqual(families[3]["members"][0]["destination_rows"], [5, 1, 2, 3, 4])
        self.assertEqual(families[4]["members"][0]["destination_rows"], [5, 4, 3, 2, 1])
        cyclic = families[0]["members"][0]
        self.assertEqual(cyclic["displacements"], [1, 1, 1, 1, -4])
        self.assertEqual(cyclic["retained_genuine_edges"], 0)
        self.assertEqual(cyclic["cardinality"], 5)
        self.assertIs(cyclic["disjoint"], True)
        reflected = families[4]["members"][0]
        self.assertEqual(reflected["displacements"], [4, 2, 0, -2, -4])
        self.assertEqual(reflected["retained_genuine_edges"], 1)

    def test_random_rank_and_all_symmetry_exclusions(self) -> None:
        selected = tuple(self.manifest["families"][9]["members"][0]["destination_rows"])
        excluded = manifest_module._symmetry_permutations(6)
        ranked = []
        for permutation in itertools.permutations(range(1, 6)):
            if permutation in excluded:
                continue
            canonical = canonical_permutation(permutation)
            digest = hashlib.sha256(
                f"area-one-control-random-v1|6|{canonical}".encode("utf-8")
            ).hexdigest()
            ranked.append((digest, canonical, permutation))
        ranked.sort(key=lambda item: (item[0], item[1]))
        self.assertEqual(selected, ranked[0][2])
        for family in self.manifest["families"][9:]:
            for member in family["members"]:
                self.assertNotIn(
                    tuple(member["destination_rows"]),
                    manifest_module._symmetry_permutations(member["R"]),
                )

    def test_internal_hash_is_unprefixed_canonical_body_sha256(self) -> None:
        body = dict(self.manifest)
        body.pop("manifest_hash")
        encoded = json.dumps(
            body, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        expected = "sha256:" + hashlib.sha256(encoded).hexdigest()
        self.assertEqual(self.manifest["manifest_hash"], expected)
        self.assertEqual(manifest_sha256(self.manifest), expected)
        self.assertNotEqual(expected, "sha256:" + hashlib.sha256(encoded + b"\n").hexdigest())

    def test_independent_module_is_exact_and_does_not_call_production_helpers(self) -> None:
        with (
            mock.patch.object(manifest_module, "_ranked_random_permutations", side_effect=AssertionError),
            mock.patch.object(manifest_module, "_generate_manifest_body", side_effect=AssertionError),
            mock.patch.object(manifest_module, "_member", side_effect=AssertionError),
        ):
            independent_bytes = independent_control_manifest.generate_manifest_bytes()
        self.assertEqual(self.canonical, independent_bytes)
        self.assertEqual(self.manifest, independently_regenerate_manifest())
        verify_independent_regeneration(self.manifest)

    def test_checked_artifact_is_exactly_generated(self) -> None:
        self.assertEqual(DEFAULT_PATH.read_bytes(), self.canonical)
        self.assertEqual(load_manifest(DEFAULT_PATH), self.manifest)

    def test_canonical_file_write_load_and_cli_verification(self) -> None:
        self.assertTrue(self.canonical.endswith(b"\n"))
        self.assertFalse(self.canonical.endswith(b"\n\n"))
        self.assertNotIn(b"\r", self.canonical)
        self.assertNotIn(b": ", self.canonical)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            digest = write_manifest(path, self.manifest)
            self.assertEqual(path.read_bytes(), self.canonical)
            self.assertEqual(load_manifest(path), self.manifest)
            output = io.StringIO()
            with redirect_stdout(output):
                status = manifest_module.main(["--verify", str(path)])
            self.assertEqual(status, 0)
            self.assertIn(f"manifest_hash={digest}", output.getvalue())
            self.assertIn("independent_regeneration=PASS", output.getvalue())

    def test_noncanonical_and_duplicate_key_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            for bad in (
                self.canonical[:-1],
                self.canonical.replace(b"\n", b"\r\n"),
                json.dumps(self.manifest, indent=2).encode("utf-8") + b"\n",
            ):
                path.write_bytes(bad)
                with self.assertRaises(ManifestValidationError):
                    load_manifest(path)
            path.write_bytes(b'{"schema_version":"a","schema_version":"b"}\n')
            with self.assertRaises(ManifestValidationError):
                load_manifest(path)

    def _assert_mutation_rejected(self, mutate) -> None:
        changed = copy.deepcopy(self.manifest)
        mutate(changed)
        changed["manifest_hash"] = manifest_sha256(changed)
        with self.assertRaises(ManifestValidationError):
            validate_manifest(changed)

    def test_strict_shape_identity_bijection_candidate_and_order_rejections(self) -> None:
        self._assert_mutation_rejected(
            lambda value: value.update({"unknown": True})
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][0].update({"family_id": "control-001"})
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][0]["members"][0].update(
                {"destination_rows": [1, 2, 3, 4, 5]}
            )
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][0]["members"][0].update(
                {"destination_rows": [2, 2, 4, 5, 1]}
            )
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][9].update({"kind": "structured"})
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][0]["members"].reverse()
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][0]["members"].pop()
        )

    def test_strict_metadata_duplicate_symmetry_rank_and_hash_rejections(self) -> None:
        self._assert_mutation_rejected(
            lambda value: value["families"][0]["members"][0].update({"cardinality": 4})
        )
        self._assert_mutation_rejected(
            lambda value: value["families"][1]["members"][0].update(
                value["families"][0]["members"][0]
            )
        )

        def put_symmetry_in_random(value) -> None:
            value["families"][9]["members"][0] = manifest_module._member(
                6, manifest_module._left_rotation(tuple(range(1, 6)), 1)
            )

        self._assert_mutation_rejected(put_symmetry_in_random)

        def swap_random_ranks(value) -> None:
            first = value["families"][9]["members"][0]
            second = value["families"][10]["members"][0]
            value["families"][9]["members"][0], value["families"][10]["members"][0] = (
                second,
                first,
            )

        self._assert_mutation_rejected(swap_random_ranks)
        changed = copy.deepcopy(self.manifest)
        changed["manifest_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ManifestValidationError, "manifest_hash"):
            validate_manifest(changed)

    def test_insufficient_random_space_is_rejected(self) -> None:
        with self.assertRaisesRegex(ManifestValidationError, "eligible random controls"):
            manifest_module._ranked_random_permutations(6, [(1, 2, 3, 4, 5)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
