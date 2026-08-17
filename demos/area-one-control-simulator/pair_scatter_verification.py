#!/usr/bin/env python3
"""Independent finite verifier for the Area One pair-scatter walk."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
from dataclasses import dataclass

import numpy as np

import pair_scatter_direct_matrix as direct

TOLERANCE = np.float64(1e-12)
WIDTH = 3
ROWS_TO_VERIFY = (6, 7, 8, 9)
FAMILIES = ("candidate", "control-000", "control-004", "control-009", "control-099")
THETA_INDICES = (1, 2, 3, 4, 6, 8)
PHI_INDICES = (0, 1, 2, 3)
PARAMETER_INDICES = ((None, None),) + tuple(
    (theta_index, phi_index)
    for theta_index in THETA_INDICES
    for phi_index in PHI_INDICES
)
IDENTITY_PARAMETER = (None, None)
PARAMETERS = PARAMETER_INDICES[1:]
EXPECTED_CASES_PER_ROW = {6: 1375, 7: 1625, 8: 1875, 9: 2125}
EXPECTED_CASES = 7000
EXPECTED_VECTORS = 869000

Position = tuple[int, int]
Pair = tuple[Position, Position]
_RANKING_CACHE: dict[int, tuple[tuple[int, ...], ...]] = {}
_PERMUTATION_CACHE: dict[tuple[int, str], tuple[int, ...]] = {}

@dataclass(frozen=True)
class VerificationCase:
    rows: int
    family: str
    theta_index: int | None
    phi_index: int | None
    terminal: Position
    width: int = WIDTH

    @property
    def theta(self) -> np.float64:
        return parameter_values(self.theta_index, self.phi_index)[0]

    @property
    def phi(self) -> np.float64:
        return parameter_values(self.theta_index, self.phi_index)[1]

    @property
    def parameter(self) -> tuple[int | None, int | None]:
        return self.theta_index, self.phi_index


@dataclass(frozen=True)
class VerificationResult:
    cases_checked: int
    vectors_checked: int
    full_coverage: bool
    implementation_evidence_complete: bool
    maximum_pair_unitarity_error: float
    maximum_step_unitarity_error: float
    maximum_oracle_error: float
    maximum_theta_zero_baseline_error: float
    maximum_amplitude_error: float
    maximum_coordinate_index_error: float
    maximum_norm_drift: float


@dataclass(frozen=True)
class OperatorBundle:
    pair: np.ndarray
    core: np.ndarray
    pair_unitarity_error: float
    step_unitarity_error: float


class IndependentCaches:
    """Run-local numerical caches; control rankings are separately cached by R."""

    def __init__(self) -> None:
        self.dimension_operators: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self.operators: dict[tuple[int, str, int | None, int | None], OperatorBundle] = {}
        self.terminals: dict[tuple[int, str, int | None, int | None, Position], np.ndarray] = {}
        self._terminal_group: tuple[int, str, int | None, int | None] | None = None

    def coin_shift(self, rows: int) -> tuple[np.ndarray, np.ndarray]:
        if rows not in self.dimension_operators:
            self.dimension_operators[rows] = (
                direct.grover_coin_matrix(rows, WIDTH), direct.shift_matrix(rows, WIDTH)
            )
        return self.dimension_operators[rows]

    def operator(self, case: VerificationCase) -> OperatorBundle:
        key = (case.rows, case.family, case.theta_index, case.phi_index)
        if key not in self.operators:
            pairs = family_pairs(case.rows, case.family)
            pair = direct.pair_matrix(case.rows, WIDTH, pairs, case.theta, case.phi)
            pair_error = float(direct.maximum_unitarity_error(pair))
            _require_tolerance(pair_error, "P-dagger P error")
            coin, shift = self.coin_shift(case.rows)
            with np.errstate(over="raise", invalid="raise"):
                core = np.ascontiguousarray(shift @ coin @ pair, dtype=np.complex128)
            _require_finite(core, "core matrix")
            # U = core @ O_t and O_t is a diagonal +/-1 matrix, so right-side
            # oracle column signs preserve U-dagger-U exactly for every terminal.
            step_error = float(direct.maximum_unitarity_error(core))
            _require_tolerance(step_error, "U-dagger U error")
            self.operators[key] = OperatorBundle(pair, core, pair_error, step_error)
        return self.operators[key]

    def terminal_matrix(self, case: VerificationCase) -> np.ndarray:
        group = (case.rows, case.family, case.theta_index, case.phi_index)
        if group != self._terminal_group:
            self.terminals.clear()
            self._terminal_group = group
        key = (*group, case.terminal)
        if key not in self.terminals:
            core = self.operator(case).core
            matrix = core.copy(order="C")
            for direction in range(direct.DIRECTION_COUNT):
                column = direct.basis_index(*case.terminal, direction, case.rows, WIDTH)
                matrix[:, column] *= np.complex128(-1.0)
            _require_finite(matrix, "terminal step matrix")
            self.terminals[key] = matrix
        return self.terminals[key]


def parameter_values(
    theta_index: int | None, phi_index: int | None
) -> tuple[np.float64, np.float64]:
    if theta_index is None or phi_index is None:
        if theta_index is not None or phi_index is not None:
            raise ValueError("identity parameter indices must both be None")
        return np.float64(0.0), np.float64(0.0)
    if theta_index not in THETA_INDICES or phi_index not in PHI_INDICES:
        raise ValueError("unknown theta/phi index pair")
    return (
        np.float64(theta_index * math.pi / 16.0),
        np.float64(phi_index * math.pi / 2.0),
    )


def _left_rotate(values: tuple[int, ...], offset: int) -> tuple[int, ...]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def _canonical_permutation(permutation: tuple[int, ...]) -> str:
    return json.dumps(list(permutation), separators=(",", ":"))

def _ranked_random_permutations(rows: int) -> tuple[tuple[int, ...], ...]:
    if rows not in ROWS_TO_VERIFY:
        raise ValueError("rows must be one of 6, 7, 8, 9")
    if rows not in _RANKING_CACHE:
        destinations = tuple(range(1, rows))
        reflected = tuple(reversed(destinations))
        excluded = {
            _left_rotate(base, offset)
            for base in (destinations, reflected)
            for offset in range(len(destinations))
        }
        ranked: list[tuple[str, str, tuple[int, ...]]] = []
        prefix = f"area-one-control-random-v1|{rows}|"
        for permutation in itertools.permutations(destinations):
            if permutation in excluded:
                continue
            canonical = _canonical_permutation(permutation)
            digest = hashlib.sha256((prefix + canonical).encode("utf-8")).hexdigest()
            ranked.append((digest, canonical, permutation))
        ranked.sort(key=lambda item: (item[0], item[1]))
        if len(ranked) < 91:
            raise RuntimeError("fewer than 91 eligible random controls")
        _RANKING_CACHE[rows] = tuple(item[2] for item in ranked)
    return _RANKING_CACHE[rows]


def destination_permutation(rows: int, family: str) -> tuple[int, ...]:
    """Independently reconstruct a candidate/control destination permutation."""
    key = (rows, family)
    if key in _PERMUTATION_CACHE:
        return _PERMUTATION_CACHE[key]
    if rows not in ROWS_TO_VERIFY:
        raise ValueError("rows must be one of 6, 7, 8, 9")
    destinations = tuple(range(1, rows))
    if family == "candidate":
        permutation = destinations
    elif family.startswith("control-") and len(family) == len("control-000"):
        try:
            ordinal = int(family[8:])
        except ValueError as error:
            raise ValueError("unknown family") from error
        if 0 <= ordinal <= 3:
            permutation = _left_rotate(destinations, ordinal + 1)
        elif 4 <= ordinal <= 8:
            permutation = _left_rotate(tuple(reversed(destinations)), ordinal - 4)
        elif 9 <= ordinal <= 99:
            permutation = _ranked_random_permutations(rows)[ordinal - 9]
        else:
            raise ValueError("unknown family")
    else:
        raise ValueError("unknown family")
    _PERMUTATION_CACHE[key] = permutation
    return permutation

def genuine_pairs(rows: int) -> tuple[Pair, ...]:
    if rows not in ROWS_TO_VERIFY:
        raise ValueError("rows must be one of 6, 7, 8, 9")
    return tuple(((row, 2), (row + 1, 0)) for row in range(rows - 1))


def family_pairs(
    rows: int,
    width: int | str = WIDTH,
    family: str | None = None,
) -> tuple[Pair, ...]:
    if family is None:
        selected_family = width
        selected_width = WIDTH
    else:
        selected_family = family
        selected_width = width
    if selected_width != WIDTH:
        raise ValueError("width is fixed at three")
    if not isinstance(selected_family, str):
        raise TypeError("family must be a string")
    permutation = destination_permutation(rows, selected_family)
    pairs = tuple(
        ((source, 2), (destination, 0))
        for source, destination in enumerate(permutation)
    )
    positions = {position for pair in pairs for position in pair}
    if len(pairs) != rows - 1 or len(positions) != 2 * (rows - 1):
        raise AssertionError("pair cardinality or disjointness is invalid")
    if selected_family == "candidate" and pairs != genuine_pairs(rows):
        raise AssertionError("candidate pairs are not exactly the genuine pairs")
    return pairs


def terminals(rows: int) -> tuple[Position, ...]:
    pairs = genuine_pairs(rows)
    result = tuple(pair[0] for pair in pairs) + tuple(pair[1] for pair in pairs) + ((2, 1),)
    if len(result) != 2 * rows - 1 or len(set(result)) != len(result):
        raise AssertionError("terminal set contains a duplicate or omission")
    return result


def verification_cases() -> tuple[VerificationCase, ...]:
    cases = tuple(
        VerificationCase(rows, family, theta_index, phi_index, terminal)
        for rows in ROWS_TO_VERIFY
        for family in FAMILIES
        for theta_index, phi_index in PARAMETER_INDICES
        for terminal in terminals(rows)
    )
    counts = {rows: sum(case.rows == rows for case in cases) for rows in ROWS_TO_VERIFY}
    if len(cases) != EXPECTED_CASES or counts != EXPECTED_CASES_PER_ROW:
        raise AssertionError("verification case accounting is not the frozen 7,000-case set")
    return cases


def generate_mt19937_vectors(
    dimensions: tuple[int, ...] = tuple(12 * rows for rows in ROWS_TO_VERIFY),
) -> dict[int, tuple[np.ndarray, ...]]:
    """Generate frozen vectors from one Python-MT19937 stream, without redraws."""
    if tuple(sorted(set(dimensions))) != dimensions or any(
        not isinstance(size, int) or isinstance(size, bool) or size < 1 for size in dimensions
    ):
        raise ValueError("dimensions must be unique positive integers in ascending order")
    rng = random.Random(20260815)
    result: dict[int, tuple[np.ndarray, ...]] = {}
    for size in dimensions:
        vectors: list[np.ndarray] = []
        for _ in range(32):
            components = tuple(
                (2.0 * rng.random() - 1.0, 2.0 * rng.random() - 1.0)
                for _ in range(size)
            )
            squared_norm = math.fsum(real * real + imaginary * imaginary for real, imaginary in components)
            norm = math.sqrt(squared_norm)
            if norm == 0.0 or not math.isfinite(norm):
                raise RuntimeError("MT19937 vector has zero or non-finite norm")
            vector = np.ascontiguousarray(
                np.asarray([complex(real / norm, imaginary / norm) for real, imaginary in components], dtype=np.complex128)
            )
            _require_finite(vector, "MT19937 vector")
            vectors.append(vector)
        result[size] = tuple(vectors)
    return result

def vectors_for_rows(
    rows: int, frozen: dict[int, tuple[np.ndarray, ...]]
) -> np.ndarray:
    size = direct.dimension(rows, WIDTH)
    random_columns = np.column_stack(frozen[size])
    return np.ascontiguousarray(
        np.concatenate((np.eye(size, dtype=np.complex128), random_columns), axis=1),
        dtype=np.complex128,
    )


def _require_finite(value: np.ndarray, description: str) -> None:
    if not np.isfinite(value).all():
        raise AssertionError(f"{description} contains a non-finite value")


def _require_tolerance(value: float, description: str) -> None:
    if not math.isfinite(value) or value > float(TOLERANCE):
        raise AssertionError(f"{description} exceeds {TOLERANCE}: {value}")


def _basis_bijection(rows: int) -> None:
    size = direct.dimension(rows, WIDTH)
    coordinates = set()
    for index in range(size):
        coordinate = direct.basis_coordinate(index, rows, WIDTH)
        coordinates.add(coordinate)
        if direct.basis_index(*coordinate, rows, WIDTH) != index:
            raise AssertionError("coordinate/index basis order is not bijective")
    if len(coordinates) != size:
        raise AssertionError("coordinate/index basis order is not injective")


def _verify_case(
    case: VerificationCase,
    initial: np.ndarray,
    caches: IndependentCaches,
) -> tuple[int, tuple[float, ...]]:
    pairs = family_pairs(case.rows, case.family)
    bundle = caches.operator(case)
    matrix = caches.terminal_matrix(case)
    # The terminal oracle only flips matrix columns, so U-dagger-U equals the
    # cached core-step product for every terminal in this operator group.
    step_error = bundle.step_unitarity_error

    baseline_error = 0.0
    if case.theta_index is None:
        baseline = direct.baseline_step_matrix(case.rows, WIDTH, case.terminal)
        baseline_error = float(np.max(np.abs(matrix - baseline)))
        _require_tolerance(baseline_error, "theta-zero baseline error")

    oracle_formula = direct.apply_oracle_formula(initial, case.rows, WIDTH, case.terminal)
    expected_oracle = initial.copy(order="C")
    for direction in range(direct.DIRECTION_COUNT):
        index = direct.basis_index(*case.terminal, direction, case.rows, WIDTH)
        expected_oracle[index] *= np.complex128(-1.0)
    oracle_error = float(np.max(np.abs(oracle_formula - expected_oracle)))
    oracle_error = max(oracle_error, float(np.max(np.abs(np.abs(oracle_formula) - np.abs(initial)))))
    _require_tolerance(oracle_error, "phase-only oracle error")

    formula = initial
    complete = initial
    initial_norms = np.sum(initial.real * initial.real + initial.imag * initial.imag, axis=0, dtype=np.float64)
    amplitude_error = coordinate_error = norm_drift = 0.0
    for step in range(1, 8):
        formula = direct.apply_candidate_formula(
            formula, case.rows, WIDTH, case.terminal, pairs, case.theta, case.phi
        )
        with np.errstate(over="raise", invalid="raise"):
            complete = np.ascontiguousarray(matrix @ complete, dtype=np.complex128)
        _require_finite(formula, "sequential coordinate formula")
        _require_finite(complete, "full matrix evolution")
        norms = np.sum(formula.real * formula.real + formula.imag * formula.imag, axis=0, dtype=np.float64)
        norm_drift = max(norm_drift, float(np.max(np.abs(norms - initial_norms))))
        if step in (1, 7):
            difference = np.abs(formula - complete)
            amplitude_error = max(amplitude_error, float(np.max(difference)))
            for index in range(difference.shape[0]):
                coordinate = direct.basis_coordinate(index, case.rows, WIDTH)
                if direct.basis_index(*coordinate, case.rows, WIDTH) != index:
                    raise AssertionError("coordinate/index changed during evolution")
                coordinate_error = max(coordinate_error, float(np.max(difference[index])))

    for column in range(formula.shape[1]):
        direct.matrix_terminal_probability(
            np.ascontiguousarray(formula[:, column]), case.rows, WIDTH,
            case.terminal, TOLERANCE,
        )
    for value, description in (
        (amplitude_error, "sequential/full-matrix amplitude error"),
        (coordinate_error, "coordinate/index formula error"),
        (norm_drift, "formula norm drift"),
    ):
        _require_tolerance(value, description)
    maxima = (
        bundle.pair_unitarity_error, step_error, oracle_error, baseline_error,
        amplitude_error, coordinate_error, norm_drift,
    )
    return initial.shape[1], maxima


def _checked_limit(max_cases: int | None, total: int) -> int:
    if max_cases is None:
        return total
    if not isinstance(max_cases, int) or isinstance(max_cases, bool) or not 1 <= max_cases <= total:
        raise ValueError(f"max_cases must be a positive integer no greater than {total}")
    return max_cases


def run_bounded_verification(max_cases: int | None = None) -> VerificationResult:
    """Run the finite verifier; truncation is smoke-only implementation evidence."""
    all_cases = verification_cases()
    limit = _checked_limit(max_cases, len(all_cases))
    selected = all_cases[:limit]
    frozen = generate_mt19937_vectors()
    vectors_by_row = {rows: vectors_for_rows(rows, frozen) for rows in ROWS_TO_VERIFY}
    for rows in ROWS_TO_VERIFY:
        _basis_bijection(rows)
    caches = IndependentCaches()
    maxima = [0.0] * 7
    vectors_checked = 0
    for case in selected:
        checked, case_maxima = _verify_case(case, vectors_by_row[case.rows], caches)
        vectors_checked += checked
        maxima = [max(left, right) for left, right in zip(maxima, case_maxima)]
    full_coverage = (
        max_cases is None
        and limit == EXPECTED_CASES
        and vectors_checked == EXPECTED_VECTORS
    )
    return VerificationResult(
        cases_checked=limit,
        vectors_checked=vectors_checked,
        full_coverage=full_coverage,
        implementation_evidence_complete=full_coverage,
        maximum_pair_unitarity_error=maxima[0],
        maximum_step_unitarity_error=maxima[1],
        maximum_oracle_error=maxima[2],
        maximum_theta_zero_baseline_error=maxima[3],
        maximum_amplitude_error=maxima[4],
        maximum_coordinate_index_error=maxima[5],
        maximum_norm_drift=maxima[6],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()
    result = run_bounded_verification(args.max_cases)
    verdict = (
        "FULL COVERAGE PASS - IMPLEMENTATION EVIDENCE ONLY"
        if result.implementation_evidence_complete
        else "INCOMPLETE - SMOKE ONLY"
    )
    print(f"Area One independent verification {verdict}")
    for name, value in result.__dict__.items():
        print(f"{name}={value:.3e}" if name.startswith("maximum_") else f"{name}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
