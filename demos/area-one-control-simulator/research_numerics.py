#!/usr/bin/env python3
"""Frozen binary64 numerical and decision semantics for Area One research."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

EPSILON = np.float64(1e-12)
DEVELOPMENT_Q10_THRESHOLD = np.float64(-0.02)
DEVELOPMENT_GRID_ORDER = ((2, 6), (3, 6), (4, 6))
PARAMETER_INDEX_PAIRS = frozenset(
    (theta_index, phi_index)
    for theta_index in range(6)
    for phi_index in range(4)
)
CONTROL_FAMILY_IDS = tuple(f"control-{index:03d}" for index in range(100))
STRUCTURED_CONTROL_FAMILY_IDS = CONTROL_FAMILY_IDS[:9]
_FAMILY_ID = re.compile(r"control-(\d{3})\Z")


class NumericalValidationError(ValueError):
    """Raised when a value violates the frozen numerical contract."""


def require_float64(value: Any, name: str = "value") -> np.float64:
    """Require an exact finite numpy.float64 scalar without coercion."""
    if not isinstance(value, np.float64):
        raise NumericalValidationError(f"{name} must be numpy.float64")
    if not bool(np.isfinite(value)):
        raise NumericalValidationError(f"{name} must be finite")
    return value


def require_complex128(value: Any, name: str = "value") -> np.complex128:
    """Require an exact finite numpy.complex128 scalar without coercion."""
    if not isinstance(value, np.complex128):
        raise NumericalValidationError(f"{name} must be numpy.complex128")
    if not bool(np.isfinite(value.real)) or not bool(np.isfinite(value.imag)):
        raise NumericalValidationError(f"{name} must have finite components")
    return value


def require_float64_array(value: Any, name: str = "array") -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.float64):
        raise NumericalValidationError(f"{name} must be a float64 ndarray")
    if not bool(np.all(np.isfinite(value))):
        raise NumericalValidationError(f"{name} contains a non-finite value")
    return value


def require_complex128_array(value: Any, name: str = "state") -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.complex128):
        raise NumericalValidationError(f"{name} must be a complex128 ndarray")
    if not bool(np.all(np.isfinite(value.real))) or not bool(np.all(np.isfinite(value.imag))):
        raise NumericalValidationError(f"{name} contains a non-finite component")
    return value

def subtract_float64(left: np.float64, right: np.float64, name: str = "difference") -> np.float64:
    left = require_float64(left, f"{name}.left")
    right = require_float64(right, f"{name}.right")
    with np.errstate(all="ignore"):
        result = np.float64(left - right)
    return require_float64(result, name)


def add_float64(left: np.float64, right: np.float64, name: str = "sum") -> np.float64:
    left = require_float64(left, f"{name}.left")
    right = require_float64(right, f"{name}.right")
    with np.errstate(all="ignore"):
        result = np.float64(left + right)
    return require_float64(result, name)


def classify_lift(delta: np.float64) -> str:
    """Classify strictly outside ±epsilon; both equality boundaries are zero."""
    delta = require_float64(delta, "delta")
    if bool(delta > EPSILON):
        return "positive"
    if bool(delta < np.float64(-EPSILON)):
        return "negative"
    return "zero"


def count_lifts(deltas: Iterable[np.float64]) -> tuple[int, int]:
    positive = 0
    total = 0
    for total, delta in enumerate(deltas, start=1):
        positive += classify_lift(delta) == "positive"
    if total == 0:
        raise NumericalValidationError("lift sample must not be empty")
    return positive, total


def exact_fraction(positive_count: int, total_count: int) -> Fraction:
    if type(positive_count) is not int or type(total_count) is not int:
        raise NumericalValidationError("counts must be exact integers")
    if total_count <= 0 or not 0 <= positive_count <= total_count:
        raise NumericalValidationError("counts must satisfy 0 <= positive <= total and total > 0")
    return Fraction(positive_count, total_count)


def overall_positive_fraction(
    counts: Mapping[str, tuple[int, int]], canonical_grid_order: Sequence[str]
) -> Fraction:
    if len(canonical_grid_order) != 9 or len(set(canonical_grid_order)) != 9:
        raise NumericalValidationError("canonical_grid_order must contain nine unique grids")
    if set(counts) != set(canonical_grid_order):
        raise NumericalValidationError("counts must exactly match canonical_grid_order")
    return sum(
        (exact_fraction(*counts[grid]) for grid in canonical_grid_order), Fraction(0, 1)
    ) / 9


def positive_fraction_conditions(
    counts: Mapping[str, tuple[int, int]], canonical_grid_order: Sequence[str]
) -> bool:
    overall = overall_positive_fraction(counts, canonical_grid_order)
    every_grid = all(exact_fraction(*counts[grid]) > Fraction(3, 5) for grid in canonical_grid_order)
    return overall > Fraction(7, 10) and every_grid

def _ordered_sample(
    values: Iterable[np.float64], keys: Iterable[str]
) -> list[tuple[np.float64, str]]:
    value_list = list(values)
    key_list = list(keys)
    if len(value_list) != len(key_list) or not value_list:
        raise NumericalValidationError("quantile values and keys must have equal nonzero length")
    if any(not isinstance(key, str) or not key for key in key_list):
        raise NumericalValidationError("every quantile key must be a nonempty canonical string")
    if len(set(key_list)) != len(key_list):
        raise NumericalValidationError("quantile keys must be unique")
    sample = [
        (require_float64(value, f"sample[{index}]"), key_list[index])
        for index, value in enumerate(value_list)
    ]
    sample.sort(key=lambda item: (item[0], item[1]))
    return sample


def frozen_quantile(
    values: Iterable[np.float64], numerator: int, denominator: int,
    keys: Iterable[str],
) -> np.float64:
    """Apply the normative interpolation with explicit caller-supplied tie keys."""
    if (
        type(numerator) is not int or type(denominator) is not int
        or denominator <= 0 or numerator < 0 or numerator > denominator
    ):
        raise NumericalValidationError("quantile must be an exact fraction in [0,1]")
    sample = _ordered_sample(values, keys)
    lo, remainder = divmod((len(sample) - 1) * numerator, denominator)
    hi = min(lo + 1, len(sample) - 1)
    x_lo, x_hi = sample[lo][0], sample[hi][0]
    with np.errstate(all="ignore"):
        weight = np.float64(np.float64(remainder) / np.float64(denominator))
        difference = np.float64(x_hi - x_lo)
        weighted = np.float64(weight * difference)
        result = np.float64(x_lo + weighted)
    require_float64(weight, "quantile weight")
    require_float64(difference, "quantile difference")
    require_float64(weighted, "quantile weighted difference")
    return require_float64(result, "quantile result")


def frozen_median(values: Iterable[np.float64], keys: Iterable[str]) -> np.float64:
    return frozen_quantile(values, 1, 2, keys)


def frozen_quantile_10(values: Iterable[np.float64], keys: Iterable[str]) -> np.float64:
    return frozen_quantile(values, 1, 10, keys)


def frozen_quantile_90(values: Iterable[np.float64], keys: Iterable[str]) -> np.float64:
    return frozen_quantile(values, 9, 10, keys)

def exceeds_epsilon_adjusted(value: np.float64, threshold: np.float64) -> bool:
    """Return value > float64(threshold + epsilon); equality fails."""
    value = require_float64(value, "value")
    threshold = require_float64(threshold, "threshold")
    adjusted = add_float64(threshold, EPSILON, "adjusted threshold")
    return bool(value > adjusted)


def exceeds_by_epsilon(left: np.float64, right: np.float64) -> bool:
    """Return left > float64(right + epsilon); equality fails."""
    left = require_float64(left, "left")
    right = require_float64(right, "right")
    adjusted = add_float64(right, EPSILON, "epsilon-adjusted right")
    return bool(left > adjusted)


@dataclass(frozen=True, init=False)
class ParameterScore:
    grid_quantiles_10: tuple[np.float64, ...]
    aggregate_median: np.float64
    theta_index: int
    phi_index: int
    minimum_grid_quantile: np.float64
    feasible: bool

    def __init__(
        self,
        grid_quantiles_10: Mapping[tuple[int, int], np.float64],
        aggregate_median: np.float64,
        theta_index: int,
        phi_index: int,
    ) -> None:
        if not isinstance(grid_quantiles_10, Mapping):
            raise NumericalValidationError("grid_quantiles_10 must be a mapping")
        for key in grid_quantiles_10:
            if (
                not isinstance(key, tuple) or len(key) != 2
                or type(key[0]) is not int or type(key[1]) is not int
            ):
                raise NumericalValidationError("development grid keys must be exact (s, R) integers")
        if set(grid_quantiles_10) != set(DEVELOPMENT_GRID_ORDER):
            raise NumericalValidationError("grid_quantiles_10 must contain every development grid exactly")
        quantiles = tuple(
            require_float64(grid_quantiles_10[grid], f"grid_quantiles_10[{grid}]")
            for grid in DEVELOPMENT_GRID_ORDER
        )
        aggregate = require_float64(aggregate_median, "aggregate_median")
        if type(theta_index) is not int or not 0 <= theta_index <= 5:
            raise NumericalValidationError("theta_index must be an integer from 0 through 5")
        if type(phi_index) is not int or not 0 <= phi_index <= 3:
            raise NumericalValidationError("phi_index must be an integer from 0 through 3")
        minimum = quantiles[0]
        for quantile_value in quantiles[1:]:
            if bool(quantile_value < minimum):
                minimum = quantile_value
        feasible = all(
            bool(quantile_value >= DEVELOPMENT_Q10_THRESHOLD)
            for quantile_value in quantiles
        )
        object.__setattr__(self, "grid_quantiles_10", quantiles)
        object.__setattr__(self, "aggregate_median", aggregate)
        object.__setattr__(self, "theta_index", theta_index)
        object.__setattr__(self, "phi_index", phi_index)
        object.__setattr__(self, "minimum_grid_quantile", minimum)
        object.__setattr__(self, "feasible", feasible)


def select_parameter(scores: Iterable[ParameterScore]) -> ParameterScore:
    """Select from the complete 6-by-4 parameter grid using frozen tie rules."""
    values = list(scores)
    if any(not isinstance(score, ParameterScore) for score in values):
        raise NumericalValidationError("all parameter scores must be ParameterScore")
    indices = {(score.theta_index, score.phi_index) for score in values}
    if len(values) != 24 or indices != PARAMETER_INDEX_PAIRS:
        raise NumericalValidationError("parameter scores must contain exactly theta 0..5 x phi 0..3")
    return max(values, key=lambda score: (
        int(score.feasible), score.minimum_grid_quantile, score.aggregate_median,
        -score.theta_index, -score.phi_index,
    ))


def family_ordinal(family_id: str) -> int:
    if not isinstance(family_id, str):
        raise NumericalValidationError("family_id must be a string")
    match = _FAMILY_ID.fullmatch(family_id)
    if match is None or int(match.group(1)) >= 100:
        raise NumericalValidationError("family_id must be control-000 through control-099")
    return int(match.group(1))

def _validated_control_scores(scores: Mapping[str, np.float64]) -> list[tuple[str, np.float64]]:
    if not isinstance(scores, Mapping):
        raise NumericalValidationError("control scores must be a mapping")
    for family_id in scores:
        family_ordinal(family_id)
    if set(scores) != set(CONTROL_FAMILY_IDS):
        raise NumericalValidationError("control scores must contain exactly control-000 through control-099")
    return [
        (family_id, require_float64(scores[family_id], f"score[{family_id}]"))
        for family_id in CONTROL_FAMILY_IDS
    ]


def candidate_rank(candidate_score: np.float64, control_scores: Mapping[str, np.float64]) -> int:
    candidate_score = require_float64(candidate_score, "candidate_score")
    boundary = subtract_float64(candidate_score, EPSILON, "candidate rank boundary")
    controls = _validated_control_scores(control_scores)
    return 1 + sum(bool(score >= boundary) for _family_id, score in controls)


def strongest_structured_control(
    control_scores: Mapping[str, np.float64], structured_family_ids: Iterable[str]
) -> str:
    controls = dict(_validated_control_scores(control_scores))
    structured = list(structured_family_ids)
    for family_id in structured:
        family_ordinal(family_id)
    if (
        len(structured) != len(STRUCTURED_CONTROL_FAMILY_IDS)
        or set(structured) != set(STRUCTURED_CONTROL_FAMILY_IDS)
    ):
        raise NumericalValidationError(
            "structured family IDs must be exactly control-000 through control-008"
        )
    return min(structured, key=lambda family_id: (-controls[family_id], family_ordinal(family_id)))


def control_score_quantile_90(control_scores: Mapping[str, np.float64]) -> np.float64:
    controls = _validated_control_scores(control_scores)
    return frozen_quantile_90(
        (score for _family_id, score in controls),
        (family_id for family_id, _score in controls),
    )


def canonical_float64(value: np.float64) -> str:
    value = require_float64(value, "serialized scalar")
    if value == np.float64(0.0):
        if bool(np.signbit(value)):
            raise NumericalValidationError("negative zero cannot be serialized")
        return "0"
    result = format(value, ".17g")
    try:
        with np.errstate(all="ignore"):
            reparsed = np.float64(result)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NumericalValidationError("serialized scalar is not binary64") from exc
    require_float64(reparsed, "serialized scalar round-trip")
    if reparsed != value:
        raise NumericalValidationError("serialized scalar did not round-trip exactly")
    return result


def parse_canonical_float64(text: str) -> np.float64:
    if not isinstance(text, str) or not text:
        raise NumericalValidationError("serialized scalar must be a nonempty string")
    try:
        with np.errstate(all="ignore"):
            value = np.float64(text)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NumericalValidationError("serialized scalar is not binary64") from exc
    require_float64(value, "parsed scalar")
    if value == np.float64(0.0) and bool(np.signbit(value)):
        raise NumericalValidationError("negative zero is prohibited")
    expected = canonical_float64(value)
    if text != expected:
        raise NumericalValidationError(f"scalar is not canonical .17g; expected {expected!r}")
    return value


# Concise aliases for consumers that name the protocol operations directly.
quantile = frozen_quantile
median = frozen_median
quantile_10 = frozen_quantile_10
quantile_90 = frozen_quantile_90
serialize_float64 = canonical_float64
deserialize_float64 = parse_canonical_float64
