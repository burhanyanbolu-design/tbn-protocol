from __future__ import annotations

import ast
import os
from pathlib import Path
import unittest
from unittest import mock

import numpy as np

import pair_scatter_production_comparison as comparison
import pair_scatter_verification as independent

ROOT = Path(__file__).resolve().parent


class ProductionComparisonTests(unittest.TestCase):
    def test_only_integration_harness_imports_production_kernels(self) -> None:
        importing_files = []
        for filename in (
            "pair_scatter_direct_matrix.py",
            "pair_scatter_verification.py",
            "pair_scatter_production_comparison.py",
        ):
            tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
            names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    names.append(node.module or "")
            if "pair_scatter_kernels" in names:
                importing_files.append(filename)
        self.assertEqual(importing_files, ["pair_scatter_production_comparison.py"])

    def test_one_case_smoke_uses_four_column_groups_and_never_approves(self) -> None:
        original = comparison.production.candidate_step
        shapes = []

        def recording(*args: object, **kwargs: object) -> np.ndarray:
            state = args[0]
            self.assertIsInstance(state, np.ndarray)
            shapes.append(state.shape)
            return original(*args, **kwargs)

        with mock.patch.object(comparison.production, "candidate_step", side_effect=recording):
            result = comparison.run_production_comparison(max_cases=1)
        self.assertEqual(result.cases_checked, 1)
        self.assertEqual(result.vectors_checked, 104)
        self.assertEqual(len(shapes), 26 * 7)
        self.assertEqual(set(shapes), {(6, 3, 4, 4)})
        self.assertFalse(result.full_coverage)
        self.assertFalse(result.implementation_evidence_complete)
        for name, value in result.__dict__.items():
            if name.startswith("maximum_"):
                self.assertTrue(np.isfinite(value), name)
                self.assertLessEqual(value, 1e-12, name)

    def test_malformed_limits_are_rejected(self) -> None:
        for value in (0, -1, False, "1", 7001):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    comparison.run_production_comparison(value)  # type: ignore[arg-type]

    def test_deliberate_production_mismatch_fails_closed(self) -> None:
        original = comparison.production.candidate_step

        def mismatched(*args: object, **kwargs: object) -> np.ndarray:
            result = original(*args, **kwargs)
            changed = result.copy(order="C")
            changed *= np.complex128(-1.0)
            return changed

        with mock.patch.object(comparison.production, "candidate_step", side_effect=mismatched):
            with self.assertRaisesRegex(AssertionError, "production/formula|theta-zero"):
                comparison.run_production_comparison(max_cases=1)

    def test_exact_full_count_formula(self) -> None:
        cases = independent.verification_cases()
        expected = sum(
            independent.EXPECTED_CASES_PER_ROW[rows]
            * (direct_dimension + 32)
            for rows, direct_dimension in ((6, 72), (7, 84), (8, 96), (9, 108))
        )
        self.assertEqual(len(cases), 7000)
        self.assertEqual(expected, 869000)
        self.assertEqual(independent.EXPECTED_VECTORS, expected)

    @unittest.skipUnless(os.environ.get("AREA_ONE_RUN_T4_FULL") == "1", "full T4 run disabled")
    def test_full_production_comparison(self) -> None:
        result = comparison.run_production_comparison()
        self.assertEqual((result.cases_checked, result.vectors_checked), (7000, 869000))
        self.assertTrue(result.full_coverage)
        self.assertTrue(result.implementation_evidence_complete)


if __name__ == "__main__":
    unittest.main()
