#!/usr/bin/env python3
"""Focused tests for Area One lane-A production kernels."""

from __future__ import annotations

import unittest

import numpy as np

import pair_scatter_kernels as kernels


class KernelTestCase(unittest.TestCase):
    def assert_canonical(self, state: np.ndarray) -> None:
        self.assertEqual(state.dtype, np.dtype(np.complex128))
        self.assertTrue(state.flags.c_contiguous)
        self.assertEqual(state.strides, kernels._canonical_strides(state.shape))
        self.assertTrue(np.isfinite(state).all())
        kernels.validate_state(state)

    @staticmethod
    def fixed_state(shape: tuple[int, ...]) -> np.ndarray:
        state = np.zeros(shape, dtype=np.complex128)
        if len(shape) == 3:
            state[0, 0, 0] = np.complex128(complex(1.0, 0.5))
            state[0, 1, 2] = np.complex128(complex(-0.25, 0.75))
            state[1, 0, 1] = np.complex128(complex(0.5, -0.5))
        else:
            state[0, 0, 0, 0] = np.complex128(complex(1.0, 0.5))
            state[0, 1, 2, 1] = np.complex128(complex(-0.25, 0.75))
            state[1, 0, 1, 2] = np.complex128(complex(0.5, -0.5))
            state[1, 1, 3, 3] = np.complex128(complex(-0.5, -0.25))
        norm = np.sqrt(np.sum(state.real * state.real + state.imag * state.imag, dtype=np.float64))
        state /= norm
        return state


class ScalarValidationTests(unittest.TestCase):
    """No evolution: exact scalar dtype and finiteness contract only."""

    def test_float64_is_exact_and_never_coerced(self) -> None:
        value = np.float64(0.25)
        self.assertIs(kernels.require_float64_scalar(value, "value"), value)
        for bad in (0.25, np.float32(0.25), 1, np.int64(1)):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                kernels.require_float64_scalar(bad, "value")
        for bad in (np.float64(np.nan), np.float64(np.inf), np.float64(-np.inf)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                kernels.require_float64_scalar(bad, "value")

    def test_complex128_is_exact_and_checks_both_components(self) -> None:
        value = np.complex128(complex(1.0, -2.0))
        self.assertIs(kernels.require_complex128_scalar(value, "value"), value)
        for bad in (complex(1.0, -2.0), np.complex64(complex(1.0, -2.0))):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                kernels.require_complex128_scalar(bad, "value")
        for bad in (
            np.complex128(complex(np.nan, 0.0)),
            np.complex128(complex(0.0, np.nan)),
            np.complex128(complex(np.inf, 0.0)),
            np.complex128(complex(0.0, -np.inf)),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                kernels.require_complex128_scalar(bad, "value")


class StrictStateValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = np.zeros((3, 3, 4), dtype=np.complex128)
        self.state[0, 0, 0] = np.complex128(1.0)

    def test_accepts_only_protocol_shapes(self) -> None:
        self.assertEqual(kernels.validate_state(self.state), (3, 3))
        columns = np.zeros((3, 3, 4, 4), dtype=np.complex128)
        self.assertEqual(kernels.validate_state(columns), (3, 3))
        for shape in ((3, 3), (3, 3, 3), (3, 3, 4, 3), (0, 3, 4)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                kernels.validate_state(np.zeros(shape, dtype=np.complex128))

    def test_rejects_wrong_dtype_layout_and_nonfinite_values(self) -> None:
        with self.assertRaises(TypeError):
            kernels.validate_state(self.state.astype(np.complex64))
        with self.assertRaises(ValueError):
            kernels.validate_state(np.asfortranarray(self.state))
        for value in (complex(np.nan, 0.0), complex(np.inf, 0.0)):
            nonfinite = self.state.copy()
            nonfinite[0, 0, 0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                kernels.validate_state(nonfinite)

    def test_rejects_bad_pairs_and_scalars(self) -> None:
        with self.assertRaises(ValueError):
            kernels.pair_scatter(
                self.state,
                (((0, 0), (1, 0)), ((1, 0), (2, 0))),
                np.float64(0.1),
                np.float64(0.2),
            )
        with self.assertRaises(ValueError):
            kernels.pair_scatter(
                self.state,
                (((0, 0), (4, 0)),),
                np.float64(0.1),
                np.float64(0.2),
            )
        with self.assertRaises(TypeError):
            kernels.pair_scatter(self.state, (), float("nan"), np.float64(0.2))


class PrimitiveOperatorTests(KernelTestCase):
    def test_terminal_oracle_is_phase_only_norm_preserving_and_canonical(self) -> None:
        state = np.zeros((2, 2, 4), dtype=np.complex128)
        state[0, 0, :] = np.array((1.0 + 2.0j, -3.0 + 4.0j, 0.5j, -0.25), dtype=np.complex128)
        state[1, 1, 3] = np.complex128(2.0 - 1.0j)
        original = state.copy()
        expected = state.copy()
        expected[0, 0, :] *= np.complex128(-1.0)

        result = kernels.terminal_phase_oracle(state, (0, 0))

        np.testing.assert_array_equal(result, expected)
        np.testing.assert_array_equal(state, original)
        self.assertEqual(kernels.state_norm(result), kernels.state_norm(state))
        self.assertFalse(np.shares_memory(result, state))
        self.assert_canonical(result)

    def test_pair_block_has_required_signs_and_phases_at_pi_over_two(self) -> None:
        state = np.zeros((1, 2, 4), dtype=np.complex128)
        state[0, 0, 0] = np.complex128(1.0)
        state[0, 1, 1] = np.complex128(1.0)
        theta = np.float64(np.pi / 2.0)
        phi = np.float64(np.pi / 2.0)

        result = kernels.pair_scatter(state, (((0, 0), (0, 1)),), theta, phi)

        ideal = np.zeros_like(state)
        ideal[0, 0, 1] = np.complex128(1.0j)  # -conj(i) has the required positive sign.
        ideal[0, 1, 0] = np.complex128(1.0j)  # i times the left amplitude.
        np.testing.assert_allclose(result, ideal, rtol=0.0, atol=8.0e-16)
        self.assertGreater(result[0, 0, 1].imag, 0.0)
        self.assertGreater(result[0, 1, 0].imag, 0.0)
        np.testing.assert_array_equal(state[0, 0, :], np.array((1.0, 0.0, 0.0, 0.0), dtype=np.complex128))
        self.assert_canonical(result)

    def test_grover_coin_is_two_mean_minus_each_direction(self) -> None:
        state = np.zeros((1, 1, 4), dtype=np.complex128)
        state[0, 0, :] = np.array((1.0 + 1.0j, 2.0 - 1.0j, 3.0 + 2.0j, 4.0 - 2.0j), dtype=np.complex128)
        original = state.copy()

        result = kernels.grover_coin(state)

        expected = np.array((4.0 - 1.0j, 3.0 + 1.0j, 2.0 - 2.0j, 1.0 + 2.0j), dtype=np.complex128)
        np.testing.assert_array_equal(result[0, 0, :], expected)
        np.testing.assert_array_equal(state, original)
        self.assert_canonical(result)

    def test_periodic_flip_flop_shift_wraps_and_reverses_direction(self) -> None:
        state = np.zeros((2, 3, 4), dtype=np.complex128)
        state[0, 0, 0] = np.complex128(1.0)
        state[1, 2, 1] = np.complex128(2.0)
        state[1, 1, 2] = np.complex128(3.0)
        state[0, 0, 3] = np.complex128(4.0)
        expected = np.zeros_like(state)
        expected[1, 0, 2] = np.complex128(1.0)
        expected[1, 0, 3] = np.complex128(2.0)
        expected[0, 1, 0] = np.complex128(3.0)
        expected[0, 2, 1] = np.complex128(4.0)

        result = kernels.periodic_flip_flop_shift(state)

        np.testing.assert_array_equal(result, expected)
        self.assert_canonical(result)


class StepAndLayoutTests(KernelTestCase):
    def test_candidate_uses_immutable_oracle_pair_coin_shift_order(self) -> None:
        state = self.fixed_state((2, 2, 4))
        original = state.copy()
        terminal = (0, 0)
        pairs = (((0, 0), (1, 1)),)
        theta = np.float64(np.pi / 3.0)
        phi = np.float64(np.pi / 5.0)
        expected = kernels.periodic_flip_flop_shift(
            kernels.grover_coin(
                kernels.pair_scatter(
                    kernels.terminal_phase_oracle(state, terminal), pairs, theta, phi
                )
            )
        )
        wrong_order = kernels.periodic_flip_flop_shift(
            kernels.grover_coin(
                kernels.terminal_phase_oracle(
                    kernels.pair_scatter(state, pairs, theta, phi), terminal
                )
            )
        )

        result = kernels.candidate_step(state, terminal, iter(pairs), theta, phi)

        np.testing.assert_array_equal(result, expected)
        self.assertFalse(np.allclose(result, wrong_order, rtol=0.0, atol=1.0e-15))
        np.testing.assert_array_equal(state, original)
        self.assertFalse(np.shares_memory(result, state))
        self.assert_canonical(result)

    def test_theta_zero_candidate_exactly_agrees_with_explicit_baseline(self) -> None:
        for shape in ((2, 2, 4), (2, 2, 4, 4)):
            with self.subTest(shape=shape):
                state = self.fixed_state(shape)
                original = state.copy()
                baseline = kernels.baseline_step(state, (0, 0))
                candidate = kernels.candidate_step(
                    state,
                    (0, 0),
                    (((0, 0), (1, 1)),),
                    np.float64(0.0),
                    np.float64(np.pi / 7.0),
                )
                np.testing.assert_array_equal(candidate, baseline)
                np.testing.assert_array_equal(state, original)
                self.assert_canonical(baseline)
                self.assert_canonical(candidate)

    def test_every_operator_returns_finite_canonical_direct_and_four_column_layouts(self) -> None:
        theta = np.float64(0.375)
        phi = np.float64(-0.625)
        pairs = (((0, 0), (1, 1)),)
        for shape in ((2, 2, 4), (2, 2, 4, 4)):
            with self.subTest(shape=shape):
                state = self.fixed_state(shape)
                original = state.copy()
                outputs = (
                    kernels.terminal_phase_oracle(state, (0, 1)),
                    kernels.pair_scatter(state, pairs, theta, phi),
                    kernels.grover_coin(state),
                    kernels.periodic_flip_flop_shift(state),
                    kernels.baseline_step(state, (0, 1)),
                    kernels.candidate_step(state, (0, 1), pairs, theta, phi),
                )
                for output in outputs:
                    self.assert_canonical(output)
                    self.assertFalse(np.shares_memory(output, state))
                    self.assertAlmostEqual(kernels.state_norm(output), kernels.state_norm(state), delta=2.0e-15)
                np.testing.assert_array_equal(state, original)


class NormAndProbabilityTests(KernelTestCase):
    def test_state_norm_and_final_terminal_probability_use_all_trailing_axes(self) -> None:
        for shape in ((2, 2, 4), (2, 2, 4, 4)):
            with self.subTest(shape=shape):
                state = np.zeros(shape, dtype=np.complex128)
                if len(shape) == 3:
                    state[0, 0, 0] = np.complex128(0.5)
                    state[0, 0, 1] = np.complex128(0.5j)
                    state[1, 1, 2] = np.complex128(np.sqrt(np.float64(0.5)))
                else:
                    state[0, 0, 0, 0] = np.complex128(0.5)
                    state[0, 0, 1, 3] = np.complex128(0.5j)
                    state[1, 1, 2, 2] = np.complex128(np.sqrt(np.float64(0.5)))
                self.assertAlmostEqual(kernels.state_norm(state), 1.0, delta=2.0e-16)
                self.assertEqual(kernels.final_terminal_probability(state, (0, 0)), np.float64(0.5))
                self.assertEqual(kernels.final_terminal_probability(state, (0, 1)), np.float64(0.0))

    def test_terminal_probability_accepts_only_the_documented_upper_tolerance(self) -> None:
        tolerance = np.float64(1.0e-12)
        state = np.zeros((1, 1, 4), dtype=np.complex128)
        state[0, 0, 0] = np.complex128(
            np.sqrt(np.float64(1.0) + np.float64(5.0e-13))
        )
        probability = kernels.final_terminal_probability(state, (0, 0), tolerance)
        self.assertGreater(probability, np.float64(1.0))
        self.assertLessEqual(probability, np.float64(1.0) + tolerance)


class NumericalFailureTests(unittest.TestCase):
    def test_pair_and_coin_reject_overflowing_intermediates(self) -> None:
        huge = np.float64(np.finfo(np.float64).max)
        pair_state = np.zeros((1, 2, 4), dtype=np.complex128)
        pair_state[0, 0, 0] = np.complex128(huge)
        pair_state[0, 1, 0] = np.complex128(-huge)
        with self.assertRaises(FloatingPointError):
            kernels.pair_scatter(
                pair_state,
                (((0, 0), (0, 1)),),
                np.float64(np.pi / 4.0),
                np.float64(0.0),
            )

        coin_state = np.full((1, 1, 4), np.complex128(huge), dtype=np.complex128)
        with self.assertRaises(FloatingPointError):
            kernels.grover_coin(coin_state)

    def test_nonfinite_intermediate_and_overflowing_reductions_are_rejected(self) -> None:
        nonfinite = np.array((complex(np.nan, 0.0),), dtype=np.complex128)
        with self.assertRaises(FloatingPointError):
            kernels._finite_complex_intermediate(nonfinite, "test intermediate")

        huge_state = np.zeros((1, 1, 4), dtype=np.complex128)
        huge_state[0, 0, 0] = np.complex128(np.finfo(np.float64).max)
        with self.assertRaises(FloatingPointError):
            kernels.state_norm(huge_state)
        with self.assertRaises(FloatingPointError):
            kernels.final_terminal_probability(huge_state, (0, 0))

    def test_terminal_probability_outside_tolerance_is_rejected(self) -> None:
        state = np.zeros((1, 1, 4), dtype=np.complex128)
        state[0, 0, 0] = np.complex128(1.000001)
        with self.assertRaises(ValueError):
            kernels.final_terminal_probability(state, (0, 0), np.float64(1.0e-12))
        with self.assertRaises(ValueError):
            kernels.final_terminal_probability(state, (0, 0), np.float64(-1.0e-12))


if __name__ == "__main__":
    unittest.main()
