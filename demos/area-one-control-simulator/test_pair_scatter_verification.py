from __future__ import annotations

import ast
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import unittest
from unittest import mock

import numpy as np

import pair_scatter_direct_matrix as direct
import pair_scatter_verification as verification

ROOT = Path(__file__).resolve().parent
GOLDENS = {
    "control-009": {
        6: (4, 3, 1, 2, 5), 7: (4, 1, 5, 3, 6, 2),
        8: (4, 6, 7, 3, 1, 5, 2), 9: (6, 4, 7, 2, 1, 8, 3, 5),
    },
    "control-099": {
        6: (5, 3, 1, 4, 2), 7: (5, 1, 6, 2, 4, 3),
        8: (6, 3, 1, 5, 4, 7, 2), 9: (3, 5, 2, 8, 1, 6, 4, 7),
    },
}


class IndependenceTests(unittest.TestCase):
    def test_independent_modules_have_only_permitted_imports(self) -> None:
        banned = (
            "pair_scatter_kernels", "manifest", "generator", "aggregation",
            "selection", "publication", "runtime", "shards",
        )
        for filename in ("pair_scatter_verification.py", "pair_scatter_direct_matrix.py"):
            tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
            self.assertFalse(
                [name for name in imports if any(word in name for word in banned)],
                (filename, imports),
            )
        comparison = ast.parse(
            (ROOT / "pair_scatter_production_comparison.py").read_text(encoding="utf-8")
        )
        production_imports = [
            alias.name for node in ast.walk(comparison) if isinstance(node, ast.Import)
            for alias in node.names if alias.name == "pair_scatter_kernels"
        ]
        self.assertEqual(production_imports, ["pair_scatter_kernels"])


class ControlAndCaseTests(unittest.TestCase):
    def test_random_control_goldens_and_checked_manifest(self) -> None:
        checked = json.loads((ROOT / "control-family-manifest.json").read_text(encoding="utf-8"))
        manifest = {
            family["family_id"]: {
                member["R"]: tuple(member["destination_rows"])
                for member in family["members"]
            }
            for family in checked["families"]
        }
        for family in verification.FAMILIES[1:]:
            for rows in verification.ROWS_TO_VERIFY:
                with self.subTest(manifest_family=family, rows=rows):
                    self.assertEqual(
                        verification.destination_permutation(rows, family),
                        manifest[family][rows],
                    )
        for family, by_row in GOLDENS.items():
            for rows, expected in by_row.items():
                with self.subTest(family=family, rows=rows):
                    self.assertEqual(verification.destination_permutation(rows, family), expected)
                    self.assertEqual(manifest[family][rows], expected)
                    self.assertEqual(
                        verification._canonical_permutation(expected),
                        json.dumps(list(expected), separators=(",", ":")),
                    )

    def test_exact_case_parameter_family_and_terminal_accounting(self) -> None:
        cases = verification.verification_cases()
        self.assertEqual(len(cases), 7000)
        self.assertEqual(Counter(case.rows for case in cases), verification.EXPECTED_CASES_PER_ROW)
        grouped: dict[tuple[int, str], list[verification.VerificationCase]] = defaultdict(list)
        for case in cases:
            grouped[(case.rows, case.family)].append(case)
            self.assertEqual(case.width, 3)
            self.assertIs(type(case.theta), np.float64)
            self.assertIs(type(case.phi), np.float64)
        for rows in verification.ROWS_TO_VERIFY:
            expected_terminals = verification.terminals(rows)
            self.assertEqual(len(expected_terminals), 2 * rows - 1)
            self.assertEqual(len(set(expected_terminals)), len(expected_terminals))
            for family in verification.FAMILIES:
                selected = grouped[(rows, family)]
                self.assertEqual(len(selected), 25 * (2 * rows - 1))
                self.assertEqual(set(case.parameter for case in selected), set(verification.PARAMETER_INDICES))
                for parameter in verification.PARAMETER_INDICES:
                    self.assertEqual(
                        tuple(case.terminal for case in selected if case.parameter == parameter),
                        expected_terminals,
                    )

    def test_candidate_and_control_pair_invariants(self) -> None:
        for rows in verification.ROWS_TO_VERIFY:
            genuine = verification.genuine_pairs(rows)
            self.assertEqual(verification.family_pairs(rows, "candidate"), genuine)
            for family in verification.FAMILIES:
                pairs = verification.family_pairs(rows, family)
                positions = [position for pair in pairs for position in pair]
                self.assertEqual(len(pairs), rows - 1)
                self.assertEqual(len(positions), len(set(positions)))
                self.assertTrue(all(left[1] == 2 and right[1] == 0 for left, right in pairs))


class FrozenVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vectors = verification.generate_mt19937_vectors()

    def test_count_order_layout_norm_and_stable_values(self) -> None:
        self.assertEqual(tuple(self.vectors), (72, 84, 96, 108))
        for dimension, vectors in self.vectors.items():
            self.assertEqual(len(vectors), 32)
            for vector in vectors:
                self.assertEqual(vector.shape, (dimension,))
                self.assertEqual(vector.dtype, np.dtype(np.complex128))
                self.assertTrue(vector.flags.c_contiguous)
                norm = np.sum(
                    vector.real * vector.real + vector.imag * vector.imag,
                    dtype=np.float64,
                )
                self.assertLessEqual(abs(float(norm) - 1.0), 5e-16)
        self.assertEqual(
            self.vectors[72][0][0],
            np.complex128(-0.11903864395089701 + 0.07269834081212032j),
        )
        self.assertEqual(
            self.vectors[72][0][1],
            np.complex128(0.006661986709833929 - 0.01781611513769006j),
        )
        self.assertEqual(
            self.vectors[72][31][-1],
            np.complex128(-0.04108963942991409 + 0.008965918793261115j),
        )

    def test_vectors_are_reused_by_dimension_in_case_matrices(self) -> None:
        first = verification.vectors_for_rows(6, self.vectors)
        second = verification.vectors_for_rows(6, self.vectors)
        np.testing.assert_array_equal(first[:, 72:], second[:, 72:])
        for index, vector in enumerate(self.vectors[72]):
            np.testing.assert_array_equal(first[:, 72 + index], vector)

    def test_malformed_dimension_order_is_rejected(self) -> None:
        for dimensions in ((84, 72), (72, 72), (0,), (True,)):
            with self.subTest(dimensions=dimensions):
                with self.assertRaises(ValueError):
                    verification.generate_mt19937_vectors(dimensions)


class IndependentExecutionTests(unittest.TestCase):
    def test_one_case_smoke_is_finite_incomplete_and_non_approving(self) -> None:
        result = verification.run_bounded_verification(max_cases=1)
        self.assertEqual(result.cases_checked, 1)
        self.assertEqual(result.vectors_checked, 104)
        self.assertFalse(result.full_coverage)
        self.assertFalse(result.implementation_evidence_complete)
        for name, value in result.__dict__.items():
            if name.startswith("maximum_"):
                self.assertTrue(np.isfinite(value), name)
                self.assertLessEqual(value, 1e-12, name)

    def test_malformed_limits_are_rejected(self) -> None:
        for value in (0, -1, True, 1.5, 7001):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    verification.run_bounded_verification(value)  # type: ignore[arg-type]

    def test_deliberate_formula_mismatch_fails_closed(self) -> None:
        original = direct.apply_candidate_formula

        def mismatched(*args: object, **kwargs: object) -> np.ndarray:
            result = original(*args, **kwargs)
            changed = result.copy(order="C")
            changed *= np.complex128(-1.0)
            return changed

        with mock.patch.object(direct, "apply_candidate_formula", side_effect=mismatched):
            with self.assertRaisesRegex(AssertionError, "amplitude"):
                verification.run_bounded_verification(max_cases=1)

    @unittest.skipUnless(os.environ.get("AREA_ONE_RUN_T4_FULL") == "1", "full T4 run disabled")
    def test_full_independent_verification(self) -> None:
        result = verification.run_bounded_verification()
        self.assertEqual((result.cases_checked, result.vectors_checked), (7000, 869000))
        self.assertTrue(result.full_coverage)
        self.assertTrue(result.implementation_evidence_complete)


if __name__ == "__main__":
    unittest.main()
