#!/usr/bin/env python3
"""Independent exhaustive tests for the typed-arm stabilizer obstruction."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import permutations
import unittest

from candidate3_typed_arm_stabilizer import (
    TypedArmError,
    assess_control,
    build_seed,
    build_vertex_map,
    certify_similarity,
    common_zero_vector,
    control_adjacency,
    destination_stabilizer,
    endpoint_moment,
    exact_rank,
    find_witness,
    invisible_witnesses,
    projector_formula,
    quotient_matrix,
    repeated_type_obstruction,
    source_stabilizer,
    validate_candidate_rank,
    validate_permutation,
    validate_seed_shape,
)

LOCAL_GRIDS = ((2, 6), (3, 6), (4, 6))
LOCAL_PROFILES = (
    ("neutral-both", (2, 2, 2, 2, 2), (2, 2, 2, 2, 2), 120),
    ("duplicate-both", (2, 2, 3, 4, 5), (2, 2, 3, 4, 5), 2),
    ("source-neutral-destination-distinct", (2, 2, 2, 2, 2), (2, 3, 4, 5, 6), 120),
    ("source-distinct-destination-neutral", (2, 3, 4, 5, 6), (2, 2, 2, 2, 2), 120),
    ("rigid-distinct", (2, 3, 4, 5, 6), (2, 3, 4, 5, 6), 1),
)
LOCAL_IDENTITY = (0, 1, 2, 3, 4)
LOCAL_PERMUTATIONS = tuple(permutations(range(5)))


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_layout(s: int, rows: int, source_types, destination_types):
    count = rows * (s + 1)
    entrance, exit_state = local_index(s, 0, 0), local_index(s, rows - 1, s)
    source_roots = tuple(local_index(s, row, s) for row in range(5))
    destination_roots = tuple(local_index(s, row + 1, 0) for row in range(5))
    reserved = {entrance, exit_state, *source_roots, *destination_roots}
    support = tuple(index for index in range(count) if index not in reserved)
    half = len(support) // 2
    cells = ((entrance,), (count,), *((root,) for root in source_roots), support[:half],
             *((root,) for root in destination_roots), support[half:], (exit_state,))
    labels = [(row, column) for row in range(rows) for column in range(s + 1)]
    labels.append("auxiliary-hub")
    source_gadgets, destination_gadgets, gadget_cells = [], [], []
    next_index = count + 1
    for side, roots, types, target in (
        ("source", source_roots, source_types, source_gadgets),
        ("destination", destination_roots, destination_types, destination_gadgets),
    ):
        for index, (root, arm_type) in enumerate(zip(roots, types, strict=True)):
            anchor, terminal = next_index, next_index + 1
            next_index += 2
            labels.extend((f"{side}-anchor-{index}", f"{side}-terminal-{index}"))
            target.append((root, anchor, terminal, arm_type))
            gadget_cells.extend(((anchor,), (terminal,)))
    return (tuple(labels), cells + tuple(gadget_cells), tuple(source_gadgets),
            tuple(destination_gadgets), entrance, exit_state)


def local_sources(cells):
    return tuple(cell[0] for cell in cells[2:7]) + cells[7]


def local_destinations(cells):
    return tuple(cell[0] for cell in cells[8:13]) + cells[13]


def local_boundary(index: int) -> int:
    return 2 if index < 5 else 1


def local_matrix(s, rows, source_types, destination_types, permutation):
    labels, cells, source_gadgets, destination_gadgets, entrance, exit_state = local_layout(
        s, rows, source_types, destination_types)
    size, p = len(labels), rows * (s + 1) // 2 - 1
    matching_weight = p + 15
    sources, destinations = local_sources(cells), local_destinations(cells)
    full_matching = permutation + tuple(range(5, p))
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]

    def add(left, right, weight):
        if left == right or matrix[left][right]:
            raise AssertionError("independent graph attempted an invalid edge")
        matrix[left][right] = matrix[right][left] = Fraction(weight)

    add(entrance, cells[1][0], 1)
    for index, source in enumerate(sources):
        add(cells[1][0], source, local_boundary(index))
    for index, image in enumerate(full_matching):
        add(sources[index], destinations[image], matching_weight)
    for index, destination in enumerate(destinations):
        add(destination, exit_state, local_boundary(index))
    for root, anchor, terminal, arm_type in source_gadgets + destination_gadgets:
        add(root, anchor, arm_type)
        add(anchor, terminal, matching_weight)
    return tuple(tuple(row) for row in matrix)


def local_product(matrix, vector):
    return tuple(sum((value * item for value, item in zip(row, vector, strict=True)), Fraction(0))
                 for row in matrix)


def local_rank(matrix):
    values = [list(row) for row in matrix]
    columns, rank = (len(values[0]) if values else 0), 0
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
                values[row] = [value - factor * base
                               for value, base in zip(values[row], values[rank], strict=True)]
        rank += 1
    return rank


def local_signs(cells, source_gadgets, destination_gadgets, size):
    signs = [0] * size
    for vertex in (cells[0][0],) + local_sources(cells) + (cells[14][0],):
        signs[vertex] = 1
    for vertex in (cells[1][0],) + local_destinations(cells):
        signs[vertex] = -1
    for root, anchor, terminal, _ in source_gadgets + destination_gadgets:
        signs[anchor], signs[terminal] = -signs[root], signs[root]
    return tuple(signs)


def local_full_rank(matrix, signs):
    positive = tuple(index for index, sign in enumerate(signs) if sign == 1)
    negative = tuple(index for index, sign in enumerate(signs) if sign == -1)
    block = tuple(tuple(matrix[left][right] for right in negative) for left in positive)
    return 2 * local_rank(block)


def local_stabilizer(types):
    return tuple(value for value in LOCAL_PERMUTATIONS
                 if all(types[index] == types[value[index]] for index in range(5)))


def local_inverse(value):
    result = [0] * 5
    for index, image in enumerate(value):
        result[image] = index
    return tuple(result)


def local_compose(left, right):
    return tuple(left[right[index]] for index in range(5))


def local_invisible(source_types, destination_types):
    found = {}
    for alpha in local_stabilizer(source_types):
        for beta in local_stabilizer(destination_types):
            pi = local_compose(beta, local_inverse(alpha))
            found.setdefault(pi, (alpha, beta))
    return found


def local_vertex_map(layout, alpha, beta):
    labels, _cells, source_gadgets, destination_gadgets, _entrance, _exit = layout
    mapping = list(range(len(labels)))
    for gadgets, arm_map in ((source_gadgets, alpha), (destination_gadgets, beta)):
        for index, image in enumerate(arm_map):
            for position in range(3):
                mapping[gadgets[index][position]] = gadgets[image][position]
    return tuple(mapping)


def local_zero(s, rows, source_types, destination_types):
    layout = local_layout(s, rows, source_types, destination_types)
    labels, cells, source_gadgets, _destination_gadgets, entrance, exit_state = layout
    m = rows * (s + 1) // 2 - 1 + 15
    vector = [Fraction(0) for _ in labels]
    vector[entrance] = vector[exit_state] = -Fraction(m * m)
    for index, source in enumerate(local_sources(cells)):
        vector[source] = Fraction(local_boundary(index) * m)
    for _root, _anchor, terminal, arm_type in source_gadgets:
        vector[terminal] = -Fraction(2 * arm_type)
    return tuple(vector)


def local_degrees(matrix):
    return tuple(sum(row, Fraction(0)) for row in matrix)


def local_weights(matrix):
    return tuple(sorted(matrix[left][right] for left in range(len(matrix))
                        for right in range(left + 1, len(matrix)) if matrix[left][right]))


def local_moment(matrix, entrance, exit_state, power):
    state = tuple(Fraction(index == entrance) for index in range(len(matrix)))
    for _ in range(power):
        state = local_product(matrix, state)
    return state[exit_state]


def local_control_rank(matrix, layout, permutation, s, rows):
    labels, cells, source_gadgets, destination_gadgets, _entrance, _exit = layout
    p, m = rows * (s + 1) // 2 - 1, rows * (s + 1) // 2 - 1 + 15
    sources, destinations = local_sources(cells), local_destinations(cells)
    full_matching = permutation + tuple(range(5, p))
    witness_rows = ((cells[0][0],) + tuple(item[2] for item in source_gadgets)
                    + sources + tuple(item[1] for item in destination_gadgets))
    witness_columns = ((cells[1][0],) + tuple(item[1] for item in source_gadgets)
                       + tuple(destinations[index] for index in full_matching)
                       + tuple(item[2] for item in destination_gadgets))
    dimension = p + 11
    if len(witness_rows) != dimension or len(witness_columns) != dimension:
        raise AssertionError("independent rank witness dimension changed")
    diagonal = (Fraction(1),) + (Fraction(m),) * (dimension - 1)
    for index in range(dimension):
        if matrix[witness_rows[index]][witness_columns[index]] != diagonal[index]:
            raise AssertionError("independent rank witness diagonal changed")
        if any(matrix[witness_rows[index]][witness_columns[later]]
               for later in range(index + 1, dimension)):
            raise AssertionError("independent rank witness is not triangular")
    rank = 2 * dimension
    if rank != len(labels) - 1:
        raise AssertionError("independent rank witness is not maximal")
    return rank


def local_quotient(matrix, cells):
    result = []
    for cell in cells:
        signatures = {
            tuple(sum((matrix[vertex][target] for target in targets), Fraction(0))
                  for targets in cells)
            for vertex in cell
        }
        if len(signatures) != 1:
            raise AssertionError("independent quotient closure failed")
        result.append(signatures.pop())
    return tuple(result)


def mutate_edge(matrix, left, right, value):
    result = [list(row) for row in matrix]
    result[left][right] = result[right][left] = value
    return tuple(tuple(row) for row in result)


class TypedArmExhaustiveTests(unittest.TestCase):
    def test_declared_candidates_reconstruct_all_35_cells_and_exact_invariants(self):
        for name, source_types, destination_types, _count in LOCAL_PROFILES:
            for s, rows in LOCAL_GRIDS:
                with self.subTest(profile=name, s=s):
                    seed = build_seed(s, rows, name)
                    layout = local_layout(s, rows, source_types, destination_types)
                    labels, cells, source_gadgets, destination_gadgets, entrance, exit_state = layout
                    candidate = local_matrix(s, rows, source_types, destination_types, LOCAL_IDENTITY)
                    self.assertEqual((seed.labels, seed.cells), (labels, cells))
                    self.assertEqual((seed.source_gadgets, seed.destination_gadgets),
                                     (source_gadgets, destination_gadgets))
                    self.assertEqual((seed.entrance, seed.exit), (entrance, exit_state))
                    self.assertEqual((len(cells), len(labels)), (35, rows * (s + 1) + 21))
                    self.assertEqual(seed.adjacency, candidate)
                    self.assertEqual(quotient_matrix(seed), local_quotient(candidate, cells))
                    zero = local_zero(s, rows, source_types, destination_types)
                    self.assertEqual(common_zero_vector(seed), zero)
                    self.assertEqual(local_product(candidate, zero), (Fraction(0),) * len(labels))
                    signs = local_signs(cells, source_gadgets, destination_gadgets, len(labels))
                    rank = local_full_rank(candidate, signs)
                    self.assertEqual(rank, len(labels) - 1)
                    self.assertEqual(validate_candidate_rank(seed), (rank, 1))
                    self.assertEqual(exact_rank(candidate), rank)
                    m = rows * (s + 1) // 2 - 1 + 15
                    norm = Fraction(m ** 3 * (2 * m + 1) + 4 * sum(q * q for q in source_types))
                    self.assertEqual(projector_formula(seed), (norm, Fraction(m ** 4, norm)))

    def test_stabilizers_and_invisible_sets_match_independent_group_oracle(self):
        swap = (1, 0, 2, 3, 4)
        for name, source_types, destination_types, expected_count in LOCAL_PROFILES:
            seed = build_seed(2, 6, name)
            independent = local_invisible(source_types, destination_types)
            production = {item.permutation: (item.alpha, item.beta)
                          for item in invisible_witnesses(seed)}
            self.assertEqual(source_stabilizer(seed), local_stabilizer(source_types))
            self.assertEqual(destination_stabilizer(seed), local_stabilizer(destination_types))
            self.assertEqual(set(production), set(independent))
            self.assertEqual(len(production), expected_count)
            if name == "duplicate-both":
                self.assertEqual(set(production), {LOCAL_IDENTITY, swap})
            if name == "rigid-distinct":
                self.assertEqual(set(production), {LOCAL_IDENTITY})

    def test_all_120_controls_per_profile_grid_have_fairness_rank_and_decision(self):
        for name, source_types, destination_types, _count in LOCAL_PROFILES:
            independent = local_invisible(source_types, destination_types)
            for s, rows in LOCAL_GRIDS:
                seed = build_seed(s, rows, name)
                layout = local_layout(s, rows, source_types, destination_types)
                labels, cells, source_gadgets, destination_gadgets, _entrance, _exit = layout
                signs = local_signs(cells, source_gadgets, destination_gadgets, len(labels))
                candidate = local_matrix(s, rows, source_types, destination_types, LOCAL_IDENTITY)
                degrees, weights = local_degrees(candidate), local_weights(candidate)
                zero = local_zero(s, rows, source_types, destination_types)
                production_invisible = {item.permutation for item in invisible_witnesses(seed)}
                for permutation in LOCAL_PERMUTATIONS:
                    control = local_matrix(s, rows, source_types, destination_types, permutation)
                    self.assertEqual(control_adjacency(seed, permutation), control)
                    self.assertEqual(local_degrees(control), degrees)
                    self.assertEqual(local_weights(control), weights)
                    self.assertEqual(local_product(control, zero), (Fraction(0),) * len(labels))
                    self.assertEqual(local_control_rank(control, layout, permutation, s, rows),
                                     len(labels) - 1)
                    expected_invisible = permutation in independent
                    self.assertEqual(permutation in production_invisible, expected_invisible)
                    assessment = assess_control(seed, permutation, control)
                    self.assertEqual(assessment.invisible, expected_invisible)
                    self.assertEqual(
                        assessment.status,
                        "obstruction present" if expected_invisible
                        else "obstruction absent / no conclusion",
                    )
                    self.assertEqual((assessment.exact_rank, assessment.exact_nullity),
                                     (len(labels) - 1, 1))

    def test_every_invisible_control_has_exhaustive_entrywise_conjugacy(self):
        for name, source_types, destination_types, _count in LOCAL_PROFILES:
            independent = local_invisible(source_types, destination_types)
            for s, rows in LOCAL_GRIDS:
                seed = build_seed(s, rows, name)
                layout = local_layout(s, rows, source_types, destination_types)
                candidate = local_matrix(s, rows, source_types, destination_types, LOCAL_IDENTITY)
                for permutation, (alpha, beta) in independent.items():
                    witness = find_witness(seed, permutation)
                    self.assertIsNotNone(witness)
                    assert witness is not None
                    expected_map = local_vertex_map(layout, alpha, beta)
                    self.assertEqual(witness.vertex_map, expected_map)
                    control = local_matrix(s, rows, source_types, destination_types, permutation)
                    certified = certify_similarity(seed, permutation, witness.alpha, witness.beta,
                                                   witness.vertex_map)
                    self.assertEqual(certified.vertex_map, expected_map)
                    for left in range(len(candidate)):
                        for right in range(len(candidate)):
                            self.assertEqual(control[expected_map[left]][expected_map[right]],
                                             candidate[left][right])

    def test_sampled_invisible_endpoint_moments_agree_through_h8_exactly(self):
        for name, source_types, destination_types, _count in LOCAL_PROFILES:
            independent = local_invisible(source_types, destination_types)
            permutation = next((value for value in independent if value != LOCAL_IDENTITY), LOCAL_IDENTITY)
            for s, rows in LOCAL_GRIDS:
                seed = build_seed(s, rows, name)
                layout = local_layout(s, rows, source_types, destination_types)
                entrance, exit_state = layout[-2], layout[-1]
                candidate = local_matrix(s, rows, source_types, destination_types, LOCAL_IDENTITY)
                control = local_matrix(s, rows, source_types, destination_types, permutation)
                for power in range(9):
                    expected = local_moment(candidate, entrance, exit_state, power)
                    self.assertEqual(local_moment(control, entrance, exit_state, power), expected)
                    self.assertEqual(endpoint_moment(seed.adjacency, entrance, exit_state, power), expected)
                    self.assertEqual(endpoint_moment(control, entrance, exit_state, power), expected)

    def test_repeated_types_always_supply_a_nonidentity_explicit_witness(self):
        for name, _source, _destination, _count in LOCAL_PROFILES[:-1]:
            for s, rows in LOCAL_GRIDS:
                witness = repeated_type_obstruction(build_seed(s, rows, name))
                self.assertNotEqual(witness.permutation, LOCAL_IDENTITY)
                self.assertEqual(sorted(witness.vertex_map), list(range(len(witness.vertex_map))))

    def test_rigid_nonidentity_controls_are_no_conclusion_not_separation(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows, "rigid-distinct")
            with self.assertRaises(TypedArmError):
                repeated_type_obstruction(seed)
            for permutation in LOCAL_PERMUTATIONS[1:]:
                assessment = assess_control(seed, permutation)
                self.assertFalse(assessment.invisible)
                self.assertIsNone(assessment.witness)
                self.assertEqual(assessment.status, "obstruction absent / no conclusion")


class TypedArmFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rigid = build_seed(2, 6, "rigid-distinct")
        cls.neutral = build_seed(2, 6, "neutral-both")
        cls.swap = (1, 0, 2, 3, 4)

    def test_undeclared_inputs_and_malformed_permutations_are_rejected(self):
        for args in ((1, 6, "neutral-both"), (2, 5, "neutral-both"),
                     (2, 6, "invented"), (2.0, 6, "neutral-both")):
            with self.subTest(args=args), self.assertRaises(TypedArmError):
                build_seed(*args)
        for value in ((0, 1, 2, 3), (0, 1, 2, 3, 3), (0, 1, 2, 3, 5),
                      (0.0, 1, 2, 3, 4)):
            with self.subTest(value=value), self.assertRaises(TypedArmError):
                validate_permutation(value)
        with self.assertRaises(TypedArmError):
            validate_seed_shape(replace(self.rigid, source_types=(2, 2, 3, 4, 5)))
        with self.assertRaises(TypedArmError):
            validate_seed_shape(replace(self.rigid, s=2.0))  # type: ignore[arg-type]
        labels = list(self.rigid.labels)
        labels[-1] = "forged-terminal"
        with self.assertRaises(TypedArmError):
            validate_seed_shape(replace(self.rigid, labels=tuple(labels)))
        gadgets = list(self.rigid.source_gadgets)
        root, anchor, terminal, arm_type = gadgets[0]
        gadgets[0] = (root + 1, anchor, terminal, arm_type)
        with self.assertRaises(TypedArmError):
            validate_seed_shape(replace(self.rigid, source_gadgets=tuple(gadgets)))

    def test_unequal_type_endpoint_moving_and_false_maps_are_rejected(self):
        with self.assertRaises(TypedArmError):
            build_vertex_map(self.rigid, self.swap, LOCAL_IDENTITY)
        witness = find_witness(self.neutral, self.swap)
        self.assertIsNotNone(witness)
        assert witness is not None
        endpoint_moving = list(witness.vertex_map)
        endpoint_moving[self.neutral.entrance], endpoint_moving[self.neutral.exit] = (
            endpoint_moving[self.neutral.exit], endpoint_moving[self.neutral.entrance])
        with self.assertRaises(TypedArmError):
            certify_similarity(self.neutral, self.swap, witness.alpha, witness.beta, endpoint_moving)
        false_map = list(witness.vertex_map)
        support = self.neutral.cells[7]
        false_map[support[0]], false_map[support[1]] = false_map[support[1]], false_map[support[0]]
        with self.assertRaises(TypedArmError):
            certify_similarity(self.neutral, self.swap, witness.alpha, witness.beta, false_map)
        with self.assertRaises(TypedArmError):
            certify_similarity(self.neutral, self.swap, LOCAL_IDENTITY, LOCAL_IDENTITY)

    def test_unequal_matching_weight_foreign_edge_and_false_control_are_rejected(self):
        control = control_adjacency(self.neutral, self.swap)
        forged_candidate = replace(
            self.rigid,
            adjacency=control_adjacency(self.rigid, self.swap),
        )
        with self.assertRaises(TypedArmError):
            assess_control(forged_candidate, self.swap)
        source = local_sources(self.neutral.cells)[0]
        destination = local_destinations(self.neutral.cells)[1]
        unequal = mutate_edge(control, source, destination,
                              Fraction(self.neutral.matching_weight + 1))
        with self.assertRaises(TypedArmError):
            assess_control(self.neutral, self.swap, unequal)
        zero_pair = next((left, right) for left in range(self.neutral.size)
                         for right in range(left + 1, self.neutral.size)
                         if not control[left][right])
        foreign = mutate_edge(control, zero_pair[0], zero_pair[1], Fraction(1))
        with self.assertRaises(TypedArmError):
            assess_control(self.neutral, self.swap, foreign)
        witness = find_witness(self.neutral, self.swap)
        assert witness is not None
        with self.assertRaises(TypedArmError):
            certify_similarity(self.neutral, self.swap, witness.alpha, witness.beta,
                               control_override=self.neutral.adjacency)

    def test_false_separation_claims_for_invisible_controls_fail_closed(self):
        for name in ("neutral-both", "duplicate-both",
                     "source-neutral-destination-distinct",
                     "source-distinct-destination-neutral"):
            seed = build_seed(2, 6, name)
            permutation = repeated_type_obstruction(seed).permutation
            with self.assertRaises(TypedArmError):
                assess_control(seed, permutation, claimed_separation=True)
        with self.assertRaises(TypedArmError):
            assess_control(self.rigid, self.swap, claimed_separation=True)
        with self.assertRaises(TypedArmError):
            assess_control(self.neutral, self.swap, claimed_separation=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
