#!/usr/bin/env python3
"""Non-independent integration comparison of production and direct verification paths."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np

import pair_scatter_direct_matrix as direct
import pair_scatter_kernels as production
import pair_scatter_verification as independent

TOLERANCE = independent.TOLERANCE


@dataclass(frozen=True)
class ProductionComparisonResult:
    cases_checked: int
    vectors_checked: int
    full_coverage: bool
    implementation_evidence_complete: bool
    maximum_oracle_error: float
    maximum_production_formula_amplitude_error: float
    maximum_formula_matrix_coordinate_index_error: float
    maximum_norm_drift: float
    maximum_terminal_probability_error: float
    maximum_theta_zero_baseline_error: float


def _require(value: float, description: str) -> None:
    if not math.isfinite(value) or value > float(TOLERANCE):
        raise AssertionError(f"{description} exceeds {TOLERANCE}: {value}")


def _column_norms(state: np.ndarray) -> np.ndarray:
    values = np.sum(
        state.real * state.real + state.imag * state.imag,
        axis=(0, 1, 2), dtype=np.float64,
    )
    if not np.isfinite(values).all():
        raise AssertionError("production norms are non-finite")
    return values

def _compare_case(
    case: independent.VerificationCase,
    initial: np.ndarray,
    caches: independent.IndependentCaches,
) -> tuple[int, tuple[float, ...]]:
    rows = case.rows
    pairs = independent.family_pairs(rows, case.family)
    matrix = caches.terminal_matrix(case)
    maxima = [0.0] * 6

    # Compute the independent coordinate and complete-matrix references once for
    # all canonical vectors. Production still runs only in frozen four-column
    # R x 3 x 4 x 4 tensors below.
    formula_oracle = direct.apply_oracle_formula(
        initial, rows, independent.WIDTH, case.terminal
    )
    formula = initial
    complete = initial
    formula_snapshots: dict[int, np.ndarray] = {}
    for step in range(1, 8):
        formula = direct.apply_candidate_formula(
            formula, rows, independent.WIDTH, case.terminal,
            pairs, case.theta, case.phi,
        )
        with np.errstate(over="raise", invalid="raise"):
            complete = np.ascontiguousarray(matrix @ complete, dtype=np.complex128)
        if step in (1, 7):
            formula_snapshots[step] = formula
            difference = np.abs(formula - complete)
            coordinate_error = 0.0
            for index in range(difference.shape[0]):
                coordinate = direct.basis_coordinate(index, rows, independent.WIDTH)
                if direct.basis_index(*coordinate, rows, independent.WIDTH) != index:
                    raise AssertionError("formula/matrix coordinate mapping is not bijective")
                coordinate_error = max(coordinate_error, float(np.max(difference[index])))
            maxima[2] = max(maxima[2], coordinate_error)
            _require(coordinate_error, "formula/matrix coordinate-index error")

    formula_probabilities = []
    for column in range(formula.shape[1]):
        formula_probabilities.append(
            direct.matrix_terminal_probability(
                np.ascontiguousarray(formula[:, column]), rows, independent.WIDTH,
                case.terminal, TOLERANCE,
            )
        )
        direct.matrix_terminal_probability(
            np.ascontiguousarray(complete[:, column]), rows, independent.WIDTH,
            case.terminal, TOLERANCE,
        )

    checked = 0
    for start in range(0, initial.shape[1], 4):
        columns = np.ascontiguousarray(initial[:, start:start + 4], dtype=np.complex128)
        if columns.shape[1] != 4:
            raise AssertionError("canonical production groups must contain exactly four columns")
        state = np.ascontiguousarray(columns.reshape(rows, independent.WIDTH, 4, 4))
        initial_norms = _column_norms(state)

        production_oracle = production.terminal_phase_oracle(state, case.terminal)
        oracle_error = float(np.max(np.abs(
            production_oracle.reshape(columns.shape) - formula_oracle[:, start:start + 4]
        )))
        maxima[0] = max(maxima[0], oracle_error)
        _require(oracle_error, "production/direct oracle error")

        baseline_state = state if case.theta_index is None else None
        for step in range(1, 8):
            state = production.candidate_step(
                state, case.terminal, pairs, case.theta, case.phi
            )
            norm_drift = float(np.max(np.abs(_column_norms(state) - initial_norms)))
            maxima[3] = max(maxima[3], norm_drift)
            _require(norm_drift, "production per-iteration norm drift")

            if baseline_state is not None:
                baseline_state = production.baseline_step(baseline_state, case.terminal)
                baseline_error = float(np.max(np.abs(state - baseline_state)))
                maxima[5] = max(maxima[5], baseline_error)
                _require(baseline_error, "theta-zero production baseline error")

            if step in (1, 7):
                production_formula = float(np.max(np.abs(
                    state.reshape(columns.shape)
                    - formula_snapshots[step][:, start:start + 4]
                )))
                maxima[1] = max(maxima[1], production_formula)
                _require(production_formula, "production/formula amplitude error")

        flattened = state.reshape(columns.shape)
        for column in range(4):
            production_probability = production.final_terminal_probability(
                np.ascontiguousarray(state[:, :, :, column]), case.terminal
            )
            formula_probability = formula_probabilities[start + column]
            probability_error = abs(float(production_probability - formula_probability))
            maxima[4] = max(maxima[4], probability_error)
            _require(probability_error, "terminal probability error")
            direct.matrix_terminal_probability(
                np.ascontiguousarray(flattened[:, column]), rows, independent.WIDTH,
                case.terminal, TOLERANCE,
            )
        checked += 4
    return checked, tuple(maxima)


def run_production_comparison(
    max_cases: int | None = None,
) -> ProductionComparisonResult:
    """Compare production to the independent oracle as implementation evidence."""
    all_cases = independent.verification_cases()
    limit = independent._checked_limit(max_cases, len(all_cases))
    selected = all_cases[:limit]
    frozen = independent.generate_mt19937_vectors()
    vectors_by_row = {
        rows: independent.vectors_for_rows(rows, frozen)
        for rows in independent.ROWS_TO_VERIFY
    }
    caches = independent.IndependentCaches()
    maxima = [0.0] * 6
    vectors_checked = 0
    for case in selected:
        checked, case_maxima = _compare_case(case, vectors_by_row[case.rows], caches)
        vectors_checked += checked
        maxima = [max(left, right) for left, right in zip(maxima, case_maxima)]
    full_coverage = (
        max_cases is None
        and limit == independent.EXPECTED_CASES
        and vectors_checked == independent.EXPECTED_VECTORS
    )
    return ProductionComparisonResult(
        cases_checked=limit,
        vectors_checked=vectors_checked,
        full_coverage=full_coverage,
        implementation_evidence_complete=full_coverage,
        maximum_oracle_error=maxima[0],
        maximum_production_formula_amplitude_error=maxima[1],
        maximum_formula_matrix_coordinate_index_error=maxima[2],
        maximum_norm_drift=maxima[3],
        maximum_terminal_probability_error=maxima[4],
        maximum_theta_zero_baseline_error=maxima[5],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()
    result = run_production_comparison(args.max_cases)
    verdict = (
        "FULL COVERAGE PASS - IMPLEMENTATION EVIDENCE ONLY"
        if result.implementation_evidence_complete
        else "INCOMPLETE - SMOKE ONLY"
    )
    print(f"Area One production comparison {verdict}")
    for name, value in result.__dict__.items():
        print(f"{name}={value:.3e}" if name.startswith("maximum_") else f"{name}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
