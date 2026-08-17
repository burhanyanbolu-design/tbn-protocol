#!/usr/bin/env python3
"""Independent theorem tests for the zero-mode-neutral anchor family."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import permutations
import math
import unittest

from candidate3_zero_mode_neutral_anchor import (
    ANCHOR_WEIGHTS,
    NeutralAnchorError,
    all_genuine_permutations,
    build_seed,
    common_zero_vector,
    control_adjacency,
    control_certificate,
    edge_degree_profile,
    edge_weight_multiset,
    endpoint_moment,
    exact_rank,
    expected_eighth_difference,
    expected_fourth_moment,
    expected_sixth_moment,
    matrix_vector,
    quotient_matrix,
    validate_candidate,
    validate_chiral,
    validate_permutation,
    validate_seed,
    validate_seed_shape,
    validate_zero_rank_gap,
    weighted_degrees,
)

LOCAL_GRIDS = ((2, 6), (3, 6), (4, 6))
LOCAL_Q = (2, 3, 4, 5, 6)
LOCAL_HUB_LABEL = "auxiliary-hub"


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_rank(matrix) -> int:
    values = [list(row) for row in matrix]
    columns = len(values[0]) if values else 0
    rank = 0
    for column in range(columns):

        pivot = next((row for row in range(rank, len(values)) if values[row][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        divisor = values[rank][column]
        values[rank] = [value / divisor for value in values[rank]]
        for row in range(rank + 1, len(values)):
            factor = values[row][column]
            if factor:
                values[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(values[row], values[rank], strict=True)
                ]
        rank += 1
    return rank


def local_layout(s: int, rows: int):
    count = rows * (s + 1)
    entrance = local_index(s, 0, 0)
    exit_state = local_index(s, rows - 1, s)
    genuine_sources = tuple(local_index(s, row, s) for row in range(rows - 1))
    genuine_destinations = tuple(local_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *genuine_sources, *genuine_destinations}
    support = tuple(index for index in range(count) if index not in reserved)
    half = len(support) // 2
    base_cells = (
        (entrance,),
        (count,),
        *((vertex,) for vertex in genuine_sources),
        support[:half],
        *((vertex,) for vertex in genuine_destinations),
        support[half:],
        (exit_state,),
    )
    labels = [(row, column) for row in range(rows) for column in range(s + 1)] + [LOCAL_HUB_LABEL]
    source_gadgets = []
    destination_gadgets = []
    gadget_cells = []
    next_index = count + 1
    for side, vertices, target in (
        ("source", genuine_sources, source_gadgets),
        ("destination", genuine_destinations, destination_gadgets),
    ):
        for row, (vertex, weight) in enumerate(zip(vertices, LOCAL_Q, strict=True)):
            anchor, terminal = next_index, next_index + 1
            next_index += 2
            labels.extend((f"{side}-anchor-{row}", f"{side}-terminal-{row}"))
            target.append((vertex, anchor, terminal, weight))
            gadget_cells.extend(((anchor,), (terminal,)))
    return (
        tuple(labels),
        base_cells + tuple(gadget_cells),
        tuple(source_gadgets),
        tuple(destination_gadgets),
    )


def local_sources(s: int, rows: int) -> tuple[int, ...]:
    cells = local_layout(s, rows)[1]
    return tuple(cell[0] for cell in cells[2:7]) + cells[7]


def local_destinations(s: int, rows: int) -> tuple[int, ...]:
    cells = local_layout(s, rows)[1]
    return tuple(cell[0] for cell in cells[8:13]) + cells[13]


def local_boundary(position: int) -> int:
    return 2 if position < 5 else 1


def local_adjacency(s: int, rows: int, permutation: tuple[int, ...]):
    labels, cells, source_gadgets, destination_gadgets = local_layout(s, rows)
    size = len(labels)
    p = rows * (s + 1) // 2 - 1
    matched_weight = p + 15
    sources = local_sources(s, rows)
    destinations = local_destinations(s, rows)
    full_matching = permutation + tuple(range(5, p))
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]

    def add(left: int, right: int, weight: int) -> None:
        matrix[left][right] = Fraction(weight)
        matrix[right][left] = Fraction(weight)

    add(cells[0][0], cells[1][0], 1)
    for position, source in enumerate(sources):
        add(cells[1][0], source, local_boundary(position))
    for source_position, destination_position in enumerate(full_matching):
        add(sources[source_position], destinations[destination_position], matched_weight)
    for position, destination in enumerate(destinations):
        add(destination, cells[14][0], local_boundary(position))
    for vertex, anchor, terminal, weight in source_gadgets + destination_gadgets:
        add(vertex, anchor, weight)
        add(anchor, terminal, matched_weight)
    return tuple(tuple(row) for row in matrix)


def local_product(matrix, vector) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def local_moment(matrix, entrance: int, exit_state: int, power: int) -> Fraction:
    state = tuple(Fraction(1) if vertex == entrance else Fraction(0) for vertex in range(len(matrix)))
    for _ in range(power):
        state = local_product(matrix, state)
    return state[exit_state]


def local_degrees(matrix) -> tuple[Fraction, ...]:
    return tuple(sum(row, Fraction(0)) for row in matrix)


def local_weights(matrix) -> tuple[Fraction, ...]:
    return tuple(sorted(
        matrix[left][right]
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def local_profile(matrix) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    degrees = local_degrees(matrix)
    return tuple(sorted(
        (matrix[left][right], min(degrees[left], degrees[right]), max(degrees[left], degrees[right]))
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def local_signs(s: int, rows: int) -> tuple[int, ...]:
    labels, cells, source_gadgets, destination_gadgets = local_layout(s, rows)
    signs = [0] * len(labels)
    for vertex in (cells[0][0],) + local_sources(s, rows) + (cells[14][0],):
        signs[vertex] = 1
    for vertex in (cells[1][0],) + local_destinations(s, rows):
        signs[vertex] = -1
    for vertex, anchor, terminal, _weight in source_gadgets + destination_gadgets:
        signs[anchor] = -signs[vertex]
        signs[terminal] = signs[vertex]
    return tuple(signs)


def local_determinant(matrix) -> Fraction:
    values = [list(row) for row in matrix]
    result = Fraction(1)
    sign = 1
    for column in range(len(values)):
        pivot = next((row for row in range(column, len(values)) if values[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            values[column], values[pivot] = values[pivot], values[column]
            sign *= -1
        pivot_value = values[column][column]
        result *= pivot_value
        for row in range(column + 1, len(values)):
            factor = values[row][column] / pivot_value
            for target in range(column, len(values)):
                values[row][target] -= factor * values[column][target]
    return sign * result


def local_witness_determinant(s: int, rows: int, permutation: tuple[int, ...], matrix) -> Fraction:
    _labels, cells, source_gadgets, destination_gadgets = local_layout(s, rows)
    p = rows * (s + 1) // 2 - 1
    sources = local_sources(s, rows)
    destinations = local_destinations(s, rows)
    full_matching = permutation + tuple(range(5, p))
    witness_rows = (
        (cells[0][0],)
        + tuple(item[2] for item in source_gadgets)
        + sources
        + tuple(item[1] for item in destination_gadgets)
    )
    witness_columns = (
        (cells[1][0],)
        + tuple(item[1] for item in source_gadgets)
        + tuple(destinations[index] for index in full_matching)
        + tuple(item[2] for item in destination_gadgets)
    )
    minor = tuple(tuple(matrix[left][right] for right in witness_columns) for left in witness_rows)
    for row in range(len(minor)):
        if any(minor[row][column] for column in range(row + 1, len(minor))):
            raise AssertionError("independent rank-witness minor is not triangular")
    return math.prod(minor[index][index] for index in range(len(minor)))


def changed_seed(seed, left: int, right: int, value: Fraction):
    matrix = [list(row) for row in seed.adjacency]
    matrix[left][right] = value
    matrix[right][left] = value
    return replace(seed, adjacency=tuple(tuple(row) for row in matrix))



class NeutralAnchorPositiveTests(unittest.TestCase):
    def test_declared_candidates_pass_independent_exact_certificates(self) -> None:
        for s, rows in LOCAL_GRIDS:
            with self.subTest(s=s):
                seed = build_seed(s, rows)
                certificate = validate_seed(seed)
                labels, cells, source_gadgets, destination_gadgets = local_layout(s, rows)
                p = rows * (s + 1) // 2 - 1
                h = p - 5
                m = 20 + h
                expected_pairs = tuple(
                    (local_index(s, row, s), local_index(s, row + 1, 0))
                    for row in range(rows - 1)
                )
                self.assertEqual(seed.labels, labels)
                self.assertEqual(seed.cells, cells)
                self.assertEqual(seed.source_gadgets, source_gadgets)
                self.assertEqual(seed.destination_gadgets, destination_gadgets)
                self.assertEqual(seed.genuine_pairs, expected_pairs)
                self.assertEqual(seed.entrance, local_index(s, 0, 0))
                self.assertEqual(seed.exit, local_index(s, rows - 1, s))
                self.assertEqual((seed.size, len(seed.cells)), (rows * (s + 1) + 21, 35))
                self.assertGreater(seed.size, len(seed.cells))
                self.assertEqual((seed.p, seed.h, seed.matched_weight), (p, h, m))
                self.assertEqual(tuple(item[3] for item in seed.source_gadgets), LOCAL_Q)
                self.assertEqual(tuple(item[3] for item in seed.destination_gadgets), LOCAL_Q)
                self.assertEqual(seed.adjacency, local_adjacency(s, rows, tuple(range(5))))
                self.assertEqual(certificate.controls_checked, 119)

                quotient = quotient_matrix(seed)
                cell_of = {vertex: index for index, cell in enumerate(seed.cells) for vertex in cell}
                for vertex in range(seed.size):
                    for target_cell, targets in enumerate(seed.cells):
                        self.assertEqual(
                            sum((seed.adjacency[vertex][target] for target in targets), Fraction(0)),
                            quotient[cell_of[vertex]][target_cell],
                        )

                signs = local_signs(s, rows)
                self.assertEqual(signs.count(1) - signs.count(-1), 1)
                for left in range(seed.size):
                    for right in range(left + 1, seed.size):
                        if seed.adjacency[left][right]:
                            self.assertEqual(signs[left], -signs[right])

                local_zero = [Fraction(0) for _ in range(seed.size)]
                local_zero[seed.entrance] = local_zero[seed.exit] = -Fraction(m * m)
                for position, source in enumerate(local_sources(s, rows)):
                    local_zero[source] = Fraction(local_boundary(position) * m)
                for _vertex, _anchor, terminal, weight in source_gadgets:
                    local_zero[terminal] = -Fraction(2 * weight)
                vector = tuple(local_zero)
                self.assertEqual(common_zero_vector(seed), vector)
                self.assertEqual(local_product(seed.adjacency, vector), (Fraction(0),) * seed.size)
                self.assertEqual(local_rank(seed.adjacency), seed.size - 1)
                self.assertEqual(exact_rank(seed.adjacency), seed.size - 1)

                positive = tuple(index for index, sign in enumerate(signs) if sign == 1)
                negative = tuple(index for index, sign in enumerate(signs) if sign == -1)
                block = tuple(tuple(seed.adjacency[left][right] for right in negative) for left in positive)
                self.assertEqual(local_rank(block), p + 11)
                gram = tuple(tuple(
                    sum((block[row][left] * block[row][right] for row in range(len(block))), Fraction(0))
                    for right in range(len(negative))
                ) for left in range(len(negative)))
                self.assertTrue(all(value.denominator == 1 for row in gram for value in row))
                gram_determinant = local_determinant(gram)
                self.assertEqual(gram_determinant.denominator, 1)
                self.assertGreaterEqual(gram_determinant, 1)
                gram_trace = sum((gram[index][index] for index in range(len(gram))), Fraction(0))
                expected_trace = 181 + 2 * m + p * m * m + 10 * m * m
                self.assertEqual(gram_trace, Fraction(expected_trace))
                self.assertEqual(certificate.gram_trace, expected_trace)
                self.assertEqual(certificate.gram_dimension, p + 11)
                self.assertEqual(certificate.gap_bound_exponent, Fraction(p + 10, 2))

                norm = sum((value * value for value in vector), Fraction(0))
                expected_norm = m ** 3 * (2 * m + 1) + 360
                projector = Fraction(m ** 4, expected_norm)
                self.assertEqual(norm, Fraction(expected_norm))
                self.assertEqual(certificate.norm_squared, norm)
                self.assertEqual(certificate.endpoint_weight, projector)
                self.assertEqual(certificate.zero_projector_endpoint_element, projector)
                self.assertGreater(certificate.numerical_gap, 0.0)
                self.assertTrue(math.isfinite(certificate.numerical_gap))

                fourth = local_moment(seed.adjacency, seed.entrance, seed.exit, 4)
                sixth = local_moment(seed.adjacency, seed.entrance, seed.exit, 6)
                self.assertEqual(fourth, Fraction(m * m))
                self.assertEqual(sixth, Fraction(m * m * (m + 1) ** 2 + 720 * m))
                self.assertEqual(certificate.fourth_moment, fourth)
                self.assertEqual(certificate.sixth_moment, sixth)
                self.assertEqual(expected_fourth_moment(seed), fourth)
                self.assertEqual(expected_sixth_moment(seed), sixth)

    def test_all_119_controls_preserve_zero_sector_and_separate_first_at_eight(self) -> None:
        local_controls = tuple(value for value in permutations(range(5)) if value != tuple(range(5)))
        self.assertEqual(all_genuine_permutations(), local_controls)
        self.assertEqual(len(local_controls), 119)
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            labels, cells, source_gadgets, _destination_gadgets = local_layout(s, rows)
            p = rows * (s + 1) // 2 - 1
            matched_weight = p + 15
            candidate = local_adjacency(s, rows, tuple(range(5)))
            self.assertEqual(seed.adjacency, candidate)
            local_zero = [Fraction(0) for _ in labels]
            local_zero[cells[0][0]] = local_zero[cells[14][0]] = -Fraction(matched_weight ** 2)
            for position, source in enumerate(local_sources(s, rows)):
                local_zero[source] = Fraction(local_boundary(position) * matched_weight)
            for _vertex, _anchor, terminal, weight in source_gadgets:
                local_zero[terminal] = -Fraction(2 * weight)
            candidate_zero = tuple(local_zero)
            self.assertEqual(common_zero_vector(seed), candidate_zero)
            candidate_degrees = local_degrees(candidate)
            candidate_weights = local_weights(candidate)
            candidate_profile = local_profile(candidate)
            candidate_eighth = local_moment(candidate, cells[0][0], cells[14][0], 8)
            candidate_fourth = local_moment(candidate, cells[0][0], cells[14][0], 4)
            candidate_sixth = local_moment(candidate, cells[0][0], cells[14][0], 6)
            for permutation in local_controls:
                with self.subTest(s=s, permutation=permutation):
                    control = local_adjacency(s, rows, permutation)
                    self.assertEqual(control_adjacency(seed, permutation), control)
                    self.assertEqual(local_degrees(control), candidate_degrees)
                    self.assertEqual(local_weights(control), candidate_weights)
                    self.assertNotEqual(local_profile(control), candidate_profile)
                    self.assertEqual(local_product(control, candidate_zero), (Fraction(0),) * seed.size)
                    self.assertEqual(local_rank(control), seed.size - 1)
                    self.assertEqual(
                        local_witness_determinant(s, rows, permutation, control),
                        Fraction(seed.matched_weight ** (seed.p + 10)),
                    )
                    quotient_matrix(seed, control)

                    for power in (0, 1, 2, 3, 5, 7):
                        self.assertEqual(local_moment(control, seed.entrance, seed.exit, power), 0)
                    fourth = local_moment(control, seed.entrance, seed.exit, 4)
                    sixth = local_moment(control, seed.entrance, seed.exit, 6)
                    eighth = local_moment(control, seed.entrance, seed.exit, 8)
                    self.assertEqual(fourth, candidate_fourth)
                    self.assertEqual(sixth, candidate_sixth)
                    difference = Fraction(2 * seed.matched_weight * sum(
                        (LOCAL_Q[index] ** 2 - LOCAL_Q[permutation[index]] ** 2) ** 2
                        for index in range(5)
                    ))
                    self.assertGreater(difference, 0)
                    self.assertEqual(candidate_eighth - eighth, difference)
                    self.assertEqual(expected_eighth_difference(seed, permutation), difference)
                    certificate = control_certificate(seed, permutation, control, eighth)
                    self.assertTrue(certificate.fair_weight_multiset)
                    self.assertTrue(certificate.fair_vertex_weighted_degrees)
                    self.assertTrue(certificate.edge_degree_profile_differs)
                    self.assertTrue(certificate.zero_vector_identical)
                    self.assertEqual(certificate.fourth_moment, fourth)
                    self.assertEqual(certificate.sixth_moment, sixth)
                    self.assertEqual(certificate.eighth_moment_difference, difference)

    def test_undeclared_grids_are_rejected(self) -> None:
        for args in ((1, 6), (2, 5), (5, 6), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(NeutralAnchorError):
                build_seed(*args)  # type: ignore[arg-type]



class NeutralAnchorMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = build_seed(2, 6)
        cls.permutation = (1, 0, 2, 3, 4)

    def test_malformed_partition_and_gadget_metadata_are_rejected(self) -> None:
        cells = list(self.seed.cells)
        cells[-1] = cells[-2]
        malformed = replace(self.seed, cells=tuple(cells))
        with self.assertRaises(NeutralAnchorError):
            validate_seed_shape(malformed)
        gadgets = list(self.seed.source_gadgets)
        vertex, anchor, terminal, weight = gadgets[0]
        gadgets[0] = (vertex, anchor, terminal, weight + 1)
        malformed_gadget = replace(self.seed, source_gadgets=tuple(gadgets))
        with self.assertRaises(NeutralAnchorError):
            validate_seed_shape(malformed_gadget)
        with self.assertRaises(NeutralAnchorError):
            validate_seed_shape(replace(self.seed, s=2.0))  # type: ignore[arg-type]

    def test_wrong_weight_and_false_periodic_edge_are_rejected(self) -> None:
        source, destination = self.seed.genuine_pairs[0]
        malformed = changed_seed(self.seed, source, destination, Fraction(self.seed.matched_weight + 1))
        with self.assertRaises(NeutralAnchorError):
            validate_candidate(malformed)
        periodic = changed_seed(self.seed, self.seed.exit, self.seed.entrance, Fraction(1))
        with self.assertRaises(NeutralAnchorError):
            validate_candidate(periodic)

    def test_same_sublattice_edge_is_rejected(self) -> None:
        malformed = changed_seed(
            self.seed,
            self.seed.entrance,
            local_sources(self.seed.s, self.seed.rows)[0],
            Fraction(1),
        )
        with self.assertRaises(NeutralAnchorError):
            validate_chiral(malformed)
        with self.assertRaises(NeutralAnchorError):
            validate_zero_rank_gap(malformed)

        cells = local_layout(self.seed.s, self.seed.rows)[1]
        closure_break = changed_seed(self.seed, cells[1][0], cells[7][0], Fraction(2))
        with self.assertRaises(NeutralAnchorError):
            quotient_matrix(closure_break)

    def test_invalid_and_identity_permutations_are_rejected(self) -> None:
        bad = ((0, 1, 2, 3), (0, 1, 2, 3, 3), (0, 1, 2, 3, 5), (0.0, 1, 2, 3, 4))
        for permutation in bad:
            with self.subTest(permutation=permutation), self.assertRaises(NeutralAnchorError):
                validate_permutation(permutation)  # type: ignore[arg-type]
        with self.assertRaises(NeutralAnchorError):
            control_certificate(self.seed, tuple(range(5)))
        with self.assertRaises(NeutralAnchorError):
            all_genuine_permutations(1)  # type: ignore[arg-type]

    def test_unfair_override_and_false_eighth_claim_fail_closed(self) -> None:
        control = control_adjacency(self.seed, self.permutation)
        matrix = [list(row) for row in control]
        left, right = next(
            (left, right)
            for left in range(self.seed.size)
            for right in range(left + 1, self.seed.size)
            if matrix[left][right]
        )
        matrix[left][right] += 1
        matrix[right][left] += 1
        unfair = tuple(tuple(row) for row in matrix)
        with self.assertRaises(NeutralAnchorError):
            control_certificate(self.seed, self.permutation, unfair)
        eighth = endpoint_moment(control, self.seed.entrance, self.seed.exit, 8)
        with self.assertRaises(NeutralAnchorError):
            control_certificate(self.seed, self.permutation, control, eighth + 1)
        with self.assertRaises(NeutralAnchorError):
            control_certificate(self.seed, self.permutation, control, int(eighth))  # type: ignore[arg-type]

    def test_extra_nullity_is_rejected(self) -> None:
        _vertex, anchor, terminal, _weight = self.seed.destination_gadgets[0]
        disconnected = changed_seed(self.seed, anchor, terminal, Fraction(0))
        vector = common_zero_vector(self.seed)
        self.assertEqual(local_product(disconnected.adjacency, vector), (Fraction(0),) * disconnected.size)
        self.assertEqual(local_rank(disconnected.adjacency), disconnected.size - 3)
        with self.assertRaises(NeutralAnchorError):
            validate_zero_rank_gap(disconnected)

    def test_public_helpers_match_independent_values(self) -> None:
        control = local_adjacency(self.seed.s, self.seed.rows, self.permutation)
        self.assertEqual(edge_weight_multiset(control), local_weights(control))
        self.assertEqual(weighted_degrees(control), local_degrees(control))
        self.assertEqual(edge_degree_profile(control), local_profile(control))
        vector = common_zero_vector(self.seed)
        self.assertEqual(matrix_vector(self.seed.adjacency, vector), local_product(self.seed.adjacency, vector))
        self.assertEqual(endpoint_moment(control, self.seed.entrance, self.seed.exit, 8), local_moment(control, self.seed.entrance, self.seed.exit, 8))

        matrix = [list(row) for row in control]
        left, right = next(
            (left, right)
            for left in range(self.seed.size)
            for right in range(left + 1, self.seed.size)
            if matrix[left][right]
        )
        matrix[left][right] += 1
        matrix[right][left] += 1
        changed = tuple(tuple(row) for row in matrix)
        self.assertNotEqual(local_weights(changed), local_weights(control))
        self.assertNotEqual(local_degrees(changed), local_degrees(control))
        self.assertNotEqual(local_profile(changed), local_profile(control))
        self.assertEqual(edge_weight_multiset(changed), local_weights(changed))
        self.assertEqual(weighted_degrees(changed), local_degrees(changed))
        self.assertEqual(edge_degree_profile(changed), local_profile(changed))


if __name__ == "__main__":
    unittest.main(verbosity=2)