#!/usr/bin/env python3
"""Independent tests for direct pair-scatter matrices and coordinate formulas."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest import mock

import numpy as np

import pair_scatter_direct_matrix as direct

ROWS = 2
WIDTH = 3
TERMINAL = (0, 2)
PAIRS = (((0, 0), (1, 1)),)
THETA = np.float64(0.37)
PHI = np.float64(-0.61)
TOLERANCE = np.float64(1e-12)


def bounded_vector(rows: int = ROWS, width: int = WIDTH) -> np.ndarray:
    size = direct.dimension(rows, width)
    real = np.arange(1, size + 1, dtype=np.float64)
    imaginary = np.arange(size, 0, -1, dtype=np.float64)
    return np.ascontiguousarray((real + np.complex128(1j) * imaginary) /
                                np.float64(4 * size), dtype=np.complex128)


def bounded_batch() -> np.ndarray:
    vector = bounded_vector()
    return np.ascontiguousarray(np.stack((vector, vector * np.float64(-0.25)), axis=1),
                                dtype=np.complex128)


class BasisAndMatrixTests(unittest.TestCase):
    def test_basis_mapping_is_a_bijection(self) -> None:
        seen = set()
        for row in range(ROWS):
            for column in range(WIDTH):
                for direction in range(direct.DIRECTION_COUNT):
                    index = direct.basis_index(row, column, direction, ROWS, WIDTH)
                    seen.add(index)
                    self.assertEqual(direct.basis_coordinate(index, ROWS, WIDTH),
                                     (row, column, direction))
        self.assertEqual(seen, set(range(direct.dimension(ROWS, WIDTH))))


    def test_oracle_has_exact_terminal_signs(self) -> None:
        matrix = direct.oracle_matrix(ROWS, WIDTH, TERMINAL)
        diagonal = np.diag(matrix)
        for index in range(matrix.shape[0]):
            coordinate = direct.basis_coordinate(index, ROWS, WIDTH)
            expected = -1.0 if coordinate[:2] == TERMINAL else 1.0
            self.assertEqual(diagonal[index], np.complex128(expected))
        self.assertEqual(np.count_nonzero(matrix - np.diag(diagonal)), 0)

    def test_pair_block_signs_and_pi_over_two_phases(self) -> None:
        theta = np.float64(np.pi / 2.0)
        phi = np.float64(np.pi / 2.0)
        matrix = direct.pair_matrix(1, 2, (((0, 0), (0, 1)),), theta, phi)
        for direction in range(direct.DIRECTION_COUNT):
            left = direct.basis_index(0, 0, direction, 1, 2)
            right = direct.basis_index(0, 1, direction, 1, 2)
            self.assertAlmostEqual(matrix[left, left].real, 0.0, places=15)
            self.assertAlmostEqual(matrix[right, right].real, 0.0, places=15)
            self.assertAlmostEqual(matrix[left, right].real, 0.0, places=15)
            self.assertAlmostEqual(matrix[left, right].imag, 1.0, places=15)
            self.assertAlmostEqual(matrix[right, left].real, 0.0, places=15)
            self.assertAlmostEqual(matrix[right, left].imag, 1.0, places=15)

    def test_grover_entries_are_local_minus_half_and_plus_half(self) -> None:
        matrix = direct.grover_coin_matrix(1, 2)
        for output in range(matrix.shape[0]):
            out_row, out_column, out_direction = direct.basis_coordinate(output, 1, 2)
            for source in range(matrix.shape[1]):
                in_row, in_column, in_direction = direct.basis_coordinate(source, 1, 2)
                if (out_row, out_column) != (in_row, in_column):
                    expected = 0.0
                elif out_direction == in_direction:
                    expected = -0.5
                else:
                    expected = 0.5
                self.assertEqual(matrix[output, source], np.complex128(expected))

    def test_shift_wraps_and_reverses_direction(self) -> None:
        matrix = direct.shift_matrix(2, 3)
        cases = ((0, 0, 0, 1, 0, 2), (0, 2, 1, 0, 0, 3),
                 (1, 1, 2, 0, 1, 0), (1, 0, 3, 1, 2, 1))
        for row, column, direction, target_row, target_column, reverse in cases:
            source = direct.basis_index(row, column, direction, 2, 3)
            target = direct.basis_index(target_row, target_column, reverse, 2, 3)
            self.assertEqual(matrix[target, source], np.complex128(1.0))
            self.assertEqual(np.count_nonzero(matrix[:, source]), 1)

    def test_candidate_order_and_noncommutation(self) -> None:
        paired_terminal = (0, 0)
        oracle = direct.oracle_matrix(ROWS, WIDTH, paired_terminal)
        pair = direct.pair_matrix(ROWS, WIDTH, PAIRS, THETA, PHI)
        coin = direct.grover_coin_matrix(ROWS, WIDTH)
        shift = direct.shift_matrix(ROWS, WIDTH)
        candidate = direct.candidate_step_matrix(ROWS, WIDTH, paired_terminal,
                                                 PAIRS, THETA, PHI)
        np.testing.assert_allclose(candidate, shift @ coin @ pair @ oracle,
                                   rtol=0.0, atol=2e-16)
        swapped = shift @ coin @ oracle @ pair
        self.assertGreater(np.max(np.abs(candidate - swapped)), 1e-3)


    def test_theta_zero_is_exact_baseline(self) -> None:
        candidate = direct.candidate_step_matrix(
            ROWS, WIDTH, TERMINAL, PAIRS, np.float64(0.0), PHI)
        baseline = direct.baseline_step_matrix(ROWS, WIDTH, TERMINAL)
        np.testing.assert_array_equal(candidate, baseline)

    def test_matrices_are_canonical_and_unitary(self) -> None:
        matrices = (
            direct.oracle_matrix(ROWS, WIDTH, TERMINAL),
            direct.pair_matrix(ROWS, WIDTH, PAIRS, THETA, PHI),
            direct.grover_coin_matrix(ROWS, WIDTH),
            direct.shift_matrix(ROWS, WIDTH),
            direct.candidate_step_matrix(ROWS, WIDTH, TERMINAL, PAIRS, THETA, PHI),
            direct.baseline_step_matrix(ROWS, WIDTH, TERMINAL),
        )
        for matrix in matrices:
            with self.subTest(shape=matrix.shape):
                self.assertEqual(matrix.dtype, np.dtype(np.complex128))
                self.assertTrue(matrix.flags.c_contiguous)
                error = direct.maximum_unitarity_error(matrix)
                self.assertIs(type(error), np.float64)
                self.assertLessEqual(error, np.float64(1e-12))


class FormulaApplicationTests(unittest.TestCase):
    def test_each_formula_matches_its_complete_matrix_and_preserves_layout(self) -> None:
        vectors = (bounded_vector(), bounded_batch())
        cases = (
            (lambda value: direct.apply_oracle_formula(value, ROWS, WIDTH, TERMINAL),
             direct.oracle_matrix(ROWS, WIDTH, TERMINAL)),
            (lambda value: direct.apply_pair_formula(value, ROWS, WIDTH, PAIRS,
                                                     THETA, PHI),
             direct.pair_matrix(ROWS, WIDTH, PAIRS, THETA, PHI)),
            (lambda value: direct.apply_grover_formula(value, ROWS, WIDTH),
             direct.grover_coin_matrix(ROWS, WIDTH)),
            (lambda value: direct.apply_shift_formula(value, ROWS, WIDTH),
             direct.shift_matrix(ROWS, WIDTH)),
        )
        for vector in vectors:
            for apply, matrix in cases:
                with self.subTest(shape=vector.shape, apply=apply):
                    result = apply(vector)
                    np.testing.assert_allclose(result, matrix @ vector,
                                               rtol=0.0, atol=3e-16)
                    self.assertEqual(result.shape, vector.shape)
                    self.assertEqual(result.dtype, np.dtype(np.complex128))
                    self.assertTrue(result.flags.c_contiguous)

    def test_candidate_formula_matches_matrix_for_one_and_seven_steps(self) -> None:
        matrix = direct.candidate_step_matrix(ROWS, WIDTH, TERMINAL, PAIRS,
                                              THETA, PHI)
        for initial in (bounded_vector(), bounded_batch()):
            formula = initial
            complete = initial
            for step in range(1, 8):
                formula = direct.apply_candidate_formula(
                    formula, ROWS, WIDTH, TERMINAL, PAIRS, THETA, PHI)
                complete = matrix @ complete
                if step in (1, 7):
                    np.testing.assert_allclose(formula, complete,
                                               rtol=0.0, atol=2e-15)

    def test_baseline_formula_matches_matrix_for_one_and_seven_steps(self) -> None:
        matrix = direct.baseline_step_matrix(ROWS, WIDTH, TERMINAL)
        formula = bounded_vector()
        complete = formula
        for step in range(1, 8):
            formula = direct.apply_baseline_formula(formula, ROWS, WIDTH, TERMINAL)
            complete = matrix @ complete
            if step in (1, 7):
                np.testing.assert_allclose(formula, complete, rtol=0.0, atol=2e-15)


class ValidationAndOverflowTests(unittest.TestCase):
    def test_theta_and_phi_require_exact_finite_float64(self) -> None:
        bad_values = (0.1, np.float32(0.1), 1, np.float64(np.nan),
                      np.float64(np.inf), np.float64(-np.inf))
        for bad in bad_values:
            with self.subTest(theta=bad):
                expected = TypeError if type(bad) is not np.float64 else ValueError
                with self.assertRaises(expected):
                    direct.pair_matrix(ROWS, WIDTH, PAIRS, bad, PHI)
            with self.subTest(phi=bad):
                expected = TypeError if type(bad) is not np.float64 else ValueError
                with self.assertRaises(expected):
                    direct.apply_pair_formula(bounded_vector(), ROWS, WIDTH,
                                              PAIRS, THETA, bad)

    def test_vector_type_shape_layout_and_finiteness_failures(self) -> None:
        size = direct.dimension(ROWS, WIDTH)
        bad_type = np.zeros(size, dtype=np.complex64)
        with self.assertRaises(TypeError):
            direct.apply_shift_formula(bad_type, ROWS, WIDTH)
        with self.assertRaises(ValueError):
            direct.apply_shift_formula(np.zeros((size - 1,), dtype=np.complex128),
                                       ROWS, WIDTH)
        with self.assertRaises(ValueError):
            direct.apply_shift_formula(np.zeros((size, 1, 1), dtype=np.complex128),
                                       ROWS, WIDTH)
        noncontiguous = np.zeros((size, 2), dtype=np.complex128)[:, 0]
        self.assertFalse(noncontiguous.flags.c_contiguous)
        with self.assertRaises(ValueError):
            direct.apply_shift_formula(noncontiguous, ROWS, WIDTH)
        nonfinite = bounded_vector()
        nonfinite[0] = np.complex128(complex(np.nan, 0.0))
        with self.assertRaises(ValueError):
            direct.apply_shift_formula(nonfinite, ROWS, WIDTH)

    def test_matrix_validation_and_unitarity_overflow(self) -> None:
        with self.assertRaises(TypeError):
            direct.maximum_unitarity_error(np.eye(2, dtype=np.complex64))
        fortran = np.asfortranarray(np.eye(3, dtype=np.complex128))
        self.assertFalse(fortran.flags.c_contiguous)
        with self.assertRaises(ValueError):
            direct.maximum_unitarity_error(fortran)
        nonfinite = np.eye(2, dtype=np.complex128)
        nonfinite[0, 0] = np.inf
        with self.assertRaises(ValueError):
            direct.maximum_unitarity_error(nonfinite)
        huge = np.eye(2, dtype=np.complex128) * np.float64(np.finfo(np.float64).max)
        with self.assertRaises(FloatingPointError):
            direct.maximum_unitarity_error(huge)

    def test_formula_and_composition_overflow_are_rejected(self) -> None:
        size = direct.dimension(1, 1)
        huge_vector = np.full(size, np.finfo(np.float64).max,
                              dtype=np.complex128)
        with self.assertRaises(FloatingPointError):
            direct.apply_grover_formula(huge_vector, 1, 1)
        huge_matrix = np.full((direct.dimension(ROWS, WIDTH),) * 2,
                              np.finfo(np.float64).max, dtype=np.complex128)
        with mock.patch.object(direct, "shift_matrix", return_value=huge_matrix):
            with self.assertRaises(FloatingPointError):
                direct.candidate_step_matrix(ROWS, WIDTH, TERMINAL, PAIRS,
                                             THETA, PHI)
            with self.assertRaises(FloatingPointError):
                direct.baseline_step_matrix(ROWS, WIDTH, TERMINAL)


class ProbabilityTests(unittest.TestCase):
    def test_probability_is_explicit_float64_and_not_clipped(self) -> None:
        vector = np.zeros(direct.dimension(1, 1), dtype=np.complex128)
        vector[0] = np.complex128(np.sqrt(np.float64(1.0) + np.float64(5e-13)))
        probability = direct.matrix_terminal_probability(
            vector, 1, 1, (0, 0), TOLERANCE)
        self.assertIs(type(probability), np.float64)
        self.assertGreater(probability, np.float64(1.0))

    def test_probability_rejects_bad_tolerance_overflow_and_bounds(self) -> None:
        vector = np.zeros(direct.dimension(1, 1), dtype=np.complex128)
        for tolerance, expected in ((1e-12, TypeError),
                                    (np.float32(1e-12), TypeError),
                                    (np.float64(np.nan), ValueError),
                                    (np.float64(-1.0), ValueError)):
            with self.subTest(tolerance=tolerance), self.assertRaises(expected):
                direct.matrix_terminal_probability(vector, 1, 1, (0, 0), tolerance)
        vector[0] = np.complex128(np.finfo(np.float64).max)
        with self.assertRaises(FloatingPointError):
            direct.matrix_terminal_probability(vector, 1, 1, (0, 0), TOLERANCE)
        vector[0] = np.complex128(np.sqrt(np.float64(1.01)))
        with self.assertRaises(ValueError):
            direct.matrix_terminal_probability(vector, 1, 1, (0, 0), TOLERANCE)


class IndependenceGuardTests(unittest.TestCase):
    def test_module_imports_only_standard_helpers_and_numpy(self) -> None:
        path = Path(direct.__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        self.assertEqual(set(imported), {"__future__", "collections.abc", "numpy"})
        forbidden = ("production", "aggregation", "selection", "manifest", "verifier")
        for name in imported:
            self.assertFalse(any(fragment in name.lower() for fragment in forbidden), name)

    def test_application_apis_have_no_matrix_multiplication(self) -> None:
        path = Path(direct.__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names = {"apply_oracle_formula", "apply_pair_formula", "apply_grover_formula",
                 "apply_shift_formula", "apply_candidate_formula", "apply_baseline_formula"}
        functions = {node.name: node for node in tree.body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and node.name in names}
        self.assertEqual(set(functions), names)
        for name, function in functions.items():
            with self.subTest(function=name):
                self.assertFalse(any(isinstance(node, ast.MatMult)
                                     for node in ast.walk(function)))
                called_attributes = {node.func.attr for node in ast.walk(function)
                                     if isinstance(node, ast.Call)
                                     and isinstance(node.func, ast.Attribute)}
                self.assertTrue({"matmul", "dot"}.isdisjoint(called_attributes))


if __name__ == "__main__":
    unittest.main(verbosity=2)
