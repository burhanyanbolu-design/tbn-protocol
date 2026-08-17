#!/usr/bin/env python3
"""Focused boundary and tie tests for frozen Area One numerical semantics."""

from fractions import Fraction
import unittest

import numpy as np

from research_numerics import (
    CONTROL_FAMILY_IDS,
    DEVELOPMENT_GRID_ORDER,
    DEVELOPMENT_Q10_THRESHOLD,
    EPSILON,
    PARAMETER_INDEX_PAIRS,
    STRUCTURED_CONTROL_FAMILY_IDS,
    NumericalValidationError,
    ParameterScore,
    candidate_rank,
    canonical_float64,
    classify_lift,
    control_score_quantile_90,
    count_lifts,
    exact_fraction,
    exceeds_by_epsilon,
    exceeds_epsilon_adjusted,
    frozen_median,
    frozen_quantile,
    frozen_quantile_10,
    overall_positive_fraction,
    parse_canonical_float64,
    positive_fraction_conditions,
    require_complex128,
    require_complex128_array,
    require_float64,
    require_float64_array,
    select_parameter,
    strongest_structured_control,
)

F = np.float64


def q10_by_development_grid(value: np.float64) -> dict[tuple[int, int], np.float64]:
    return {grid: value for grid in DEVELOPMENT_GRID_ORDER}


def complete_parameter_scores(
    overrides: dict[tuple[int, int], tuple[np.float64, np.float64]] | None = None,
) -> list[ParameterScore]:
    overrides = {} if overrides is None else overrides
    return [
        ParameterScore(
            q10_by_development_grid(overrides.get(indices, (F(-0.03), F(0.0)))[0]),
            overrides.get(indices, (F(-0.03), F(0.0)))[1],
            indices[0],
            indices[1],
        )
        for indices in sorted(PARAMETER_INDEX_PAIRS)
    ]


def complete_control_scores(value: np.float64 = F(-1.0)) -> dict[str, np.float64]:
    return {family_id: value for family_id in CONTROL_FAMILY_IDS}


class ResearchNumericsTests(unittest.TestCase):
    def test_exact_scalar_and_array_dtypes_and_finiteness(self) -> None:
        self.assertEqual(require_float64(F(1.0)), F(1.0))
        self.assertEqual(require_complex128(np.complex128(1 + 2j)), np.complex128(1 + 2j))
        require_float64_array(np.array([1.0], dtype=np.float64))
        require_complex128_array(np.array([1 + 2j], dtype=np.complex128))
        for bad in (1.0, np.float32(1.0), F(np.nan), F(np.inf), F(-np.inf)):
            with self.assertRaises(NumericalValidationError):
                require_float64(bad)
        with self.assertRaises(NumericalValidationError):
            require_complex128(np.complex128(complex(np.inf, 0.0)))
        with self.assertRaises(NumericalValidationError):
            require_float64_array(np.array([1.0], dtype=np.float32))
        with self.assertRaises(NumericalValidationError):
            require_complex128_array(np.array([complex(0.0, np.nan)], dtype=np.complex128))

    def test_epsilon_classification_at_equality_and_adjacent_ulps(self) -> None:
        positive_adjacent = np.nextafter(EPSILON, F(np.inf))
        below_positive = np.nextafter(EPSILON, F(-np.inf))
        negative_boundary = F(-EPSILON)
        negative_adjacent = np.nextafter(negative_boundary, F(-np.inf))
        above_negative = np.nextafter(negative_boundary, F(np.inf))
        self.assertEqual(classify_lift(positive_adjacent), "positive")
        self.assertEqual(classify_lift(EPSILON), "zero")
        self.assertEqual(classify_lift(below_positive), "zero")
        self.assertEqual(classify_lift(negative_adjacent), "negative")
        self.assertEqual(classify_lift(negative_boundary), "zero")
        self.assertEqual(classify_lift(above_negative), "zero")

    def test_positive_counts_are_exact_integer_fractions(self) -> None:
        deltas = [np.nextafter(EPSILON, F(np.inf)), EPSILON, F(0), F(-2e-12)]
        self.assertEqual(count_lifts(deltas), (1, 4))
        self.assertEqual(exact_fraction(7, 10), Fraction(7, 10))
        with self.assertRaises(NumericalValidationError):
            exact_fraction(1.0, 2)
        with self.assertRaises(NumericalValidationError):
            exact_fraction(3, 2)

    def test_grid_balance_decisions_do_not_use_floating_fractions(self) -> None:
        grids = tuple(f"g{index}" for index in range(9))
        equality = {grid: (7, 10) for grid in grids}
        self.assertEqual(overall_positive_fraction(equality, grids), Fraction(7, 10))
        self.assertFalse(positive_fraction_conditions(equality, grids))
        passing = {grid: (8, 10) for grid in grids}
        self.assertTrue(positive_fraction_conditions(passing, grids))
        one_grid_equal = dict(passing)
        one_grid_equal["g8"] = (3, 5)
        self.assertFalse(positive_fraction_conditions(one_grid_equal, grids))
        with self.assertRaises(NumericalValidationError):
            overall_positive_fraction(passing, grids[:-1])

    def test_frozen_quantiles_use_declared_interpolation_order(self) -> None:
        values = [F(3.0), F(0.0), F(2.0), F(1.0)]
        keys = ["d", "a", "c", "b"]
        self.assertEqual(frozen_median(values, keys), F(1.5))
        expected_tenth = F(F(0.0) + F(F(3) / F(10)) * F(F(1.0) - F(0.0)))
        self.assertEqual(frozen_quantile_10(values, keys), expected_tenth)
        self.assertEqual(frozen_quantile(values, 0, 1, keys), F(0.0))
        self.assertEqual(frozen_quantile(values, 1, 1, keys), F(3.0))

    def test_quantile_ties_require_explicit_unique_keys_and_invalid_samples_fail(self) -> None:
        values = [F(1), F(1), F(2)]
        self.assertEqual(frozen_median(values, ["z", "a", "m"]), F(1))
        with self.assertRaises(TypeError):
            frozen_median(values)  # type: ignore[call-arg]
        with self.assertRaises(NumericalValidationError):
            frozen_median([], [])
        with self.assertRaises(NumericalValidationError):
            frozen_median([F(1), F(2)], ["same", "same"])
        with self.assertRaises(NumericalValidationError):
            frozen_median([F(1), F(2)], ["a"])
        with self.assertRaises(NumericalValidationError):
            frozen_median([F(1), F(np.nan)], ["a", "b"])
        with self.assertRaises(NumericalValidationError):
            frozen_median(
                [F(-np.finfo(np.float64).max), F(np.finfo(np.float64).max)],
                ["low", "high"],
            )

    def test_strict_threshold_equality_and_one_ulp_boundaries(self) -> None:
        threshold = F(0.05)
        adjusted = F(threshold + EPSILON)
        self.assertFalse(exceeds_epsilon_adjusted(adjusted, threshold))
        self.assertTrue(exceeds_epsilon_adjusted(np.nextafter(adjusted, F(np.inf)), threshold))
        self.assertFalse(exceeds_epsilon_adjusted(np.nextafter(adjusted, F(-np.inf)), threshold))
        right = F(0.02)
        boundary = F(right + EPSILON)
        self.assertFalse(exceeds_by_epsilon(boundary, right))
        self.assertTrue(exceeds_by_epsilon(np.nextafter(boundary, F(np.inf)), right))

    def test_development_feasibility_is_derived_from_every_q10_boundary(self) -> None:
        at_boundary = ParameterScore(
            q10_by_development_grid(DEVELOPMENT_Q10_THRESHOLD), F(0.04), 1, 2
        )
        self.assertTrue(at_boundary.feasible)
        self.assertEqual(at_boundary.minimum_grid_quantile, DEVELOPMENT_Q10_THRESHOLD)
        above = np.nextafter(DEVELOPMENT_Q10_THRESHOLD, F(np.inf))
        below = np.nextafter(DEVELOPMENT_Q10_THRESHOLD, F(-np.inf))
        mixed = q10_by_development_grid(above)
        mixed[DEVELOPMENT_GRID_ORDER[-1]] = below
        below_boundary = ParameterScore(mixed, F(0.04), 1, 2)
        self.assertFalse(below_boundary.feasible)
        self.assertEqual(below_boundary.minimum_grid_quantile, below)
        with self.assertRaises(NumericalValidationError):
            ParameterScore(True, F(0.04), 1, 2)  # type: ignore[arg-type]
        with self.assertRaises(NumericalValidationError):
            ParameterScore(
                {DEVELOPMENT_GRID_ORDER[0]: F(-0.01)}, F(0.04), 1, 2
            )
        nonfinite = q10_by_development_grid(F(-0.01))
        nonfinite[DEVELOPMENT_GRID_ORDER[1]] = F(np.nan)
        with self.assertRaises(NumericalValidationError):
            ParameterScore(nonfinite, F(0.04), 1, 2)

    def test_parameter_selection_requires_complete_grid_and_uses_index_ties(self) -> None:
        scores = complete_parameter_scores({
            (1, 2): (F(-0.01), F(0.04)),
            (5, 3): (F(-0.01), F(0.05)),
        })
        self.assertEqual((select_parameter(scores).theta_index, select_parameter(scores).phi_index), (5, 3))
        tied = complete_parameter_scores({
            (0, 1): (F(-0.01), F(0.05)),
            (0, 3): (F(-0.01), F(0.05)),
            (1, 0): (F(-0.01), F(0.05)),
        })
        self.assertEqual((select_parameter(tied).theta_index, select_parameter(tied).phi_index), (0, 1))
        with self.assertRaises(NumericalValidationError):
            select_parameter(scores[:-1])
        duplicated = list(scores)
        duplicated[-1] = duplicated[0]
        with self.assertRaises(NumericalValidationError):
            select_parameter(duplicated)

    def test_candidate_rank_requires_all_controls_and_places_boundary_ahead(self) -> None:
        candidate = F(0.1)
        boundary = F(candidate - EPSILON)
        below = np.nextafter(boundary, F(-np.inf))
        scores = complete_control_scores()
        scores.update({
            "control-000": boundary,
            "control-001": below,
            "control-002": candidate,
        })
        self.assertEqual(candidate_rank(candidate, scores), 3)
        with self.assertRaises(NumericalValidationError):
            candidate_rank(candidate, {"control-000": boundary})

    def test_control_helpers_require_complete_families_and_preserve_ties(self) -> None:
        scores = complete_control_scores(F(-0.1))
        scores["control-004"] = F(0.2)
        scores["control-000"] = F(0.2)
        self.assertEqual(
            strongest_structured_control(scores, STRUCTURED_CONTROL_FAMILY_IDS),
            "control-000",
        )
        expected = frozen_quantile(scores.values(), 9, 10, scores.keys())
        self.assertEqual(control_score_quantile_90(scores), expected)
        incomplete = dict(scores)
        del incomplete["control-099"]
        with self.assertRaises(NumericalValidationError):
            control_score_quantile_90(incomplete)
        with self.assertRaises(NumericalValidationError):
            strongest_structured_control(scores, STRUCTURED_CONTROL_FAMILY_IDS[:-1])
        nonfinite = dict(scores)
        nonfinite["control-099"] = F(np.inf)
        with self.assertRaises(NumericalValidationError):
            candidate_rank(F(0), nonfinite)
        invalid = dict(scores)
        del invalid["control-099"]
        invalid["control-100"] = F(0)
        with self.assertRaises(NumericalValidationError):
            candidate_rank(F(0), invalid)

    def test_canonical_17g_round_trip_and_zero_rule(self) -> None:
        values = [F(0), F(1), F(0.1), F(np.nextafter(F(1), F(2))), F(-123.5)]
        for value in values:
            encoded = canonical_float64(value)
            self.assertEqual(encoded, format(value, ".17g") if value != F(0) else "0")
            self.assertEqual(parse_canonical_float64(encoded), value)
        self.assertEqual(canonical_float64(F(0)), "0")

    def test_negative_zero_nonfinite_and_noncanonical_strings_are_rejected(self) -> None:
        for value in (F(-0.0), F(np.nan), F(np.inf), F(-np.inf)):
            with self.assertRaises(NumericalValidationError):
                canonical_float64(value)
        for text in ("-0", "-0.0", "0.0", "+1", "1.0", "nan", "inf", " 1", "1e0"):
            with self.assertRaises(NumericalValidationError, msg=text):
                parse_canonical_float64(text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
