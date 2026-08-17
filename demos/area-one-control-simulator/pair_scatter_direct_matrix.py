#!/usr/bin/env python3
"""Independent coordinate formulas for the Area One pair-scatter walk."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

DIRECTION_COUNT = 4
Position = tuple[int, int]
Pair = tuple[Position, Position]


def dimension(rows: int, width: int) -> int:
    if not isinstance(rows, int) or isinstance(rows, bool) or rows < 1:
        raise ValueError("rows must be a positive integer")
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("width must be a positive integer")
    return rows * width * DIRECTION_COUNT


def basis_index(row: int, column: int, direction: int, rows: int, width: int) -> int:
    dimension(rows, width)
    if not (0 <= row < rows and 0 <= column < width and 0 <= direction < DIRECTION_COUNT):
        raise ValueError("basis coordinate is outside the grid")
    return (row * width + column) * DIRECTION_COUNT + direction


def basis_coordinate(index: int, rows: int, width: int) -> tuple[int, int, int]:
    size = dimension(rows, width)
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < size:
        raise ValueError("basis index is outside the grid")
    position, direction = divmod(index, DIRECTION_COUNT)
    row, column = divmod(position, width)
    return row, column, direction


def _position(position: Position, rows: int, width: int) -> Position:
    if not isinstance(position, tuple) or len(position) != 2:
        raise TypeError("position must be a (row, column) tuple")
    row, column = position
    if (not isinstance(row, int) or isinstance(row, bool)
            or not isinstance(column, int) or isinstance(column, bool)):
        raise TypeError("position coordinates must be integers")
    if not (0 <= row < rows and 0 <= column < width):
        raise ValueError("position is outside the grid")
    return row, column


def _pairs(pairs: Iterable[Pair], rows: int, width: int) -> tuple[Pair, ...]:
    result: list[Pair] = []
    used: set[Position] = set()
    try:
        iterator = iter(pairs)
    except TypeError as error:
        raise TypeError("pairs must be iterable") from error
    for pair in iterator:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("each pair must contain two positions")
        left = _position(pair[0], rows, width)
        right = _position(pair[1], rows, width)
        if left == right or left in used or right in used:
            raise ValueError("pairs must contain distinct, disjoint positions")
        used.update((left, right))
        result.append((left, right))
    return tuple(result)


def _float64(value: object, name: str) -> np.float64:
    if type(value) is not np.float64:
        raise TypeError(f"{name} must be an exact np.float64 scalar")
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _vector(vector: np.ndarray, rows: int, width: int) -> np.ndarray:
    if not isinstance(vector, np.ndarray) or vector.dtype != np.dtype(np.complex128):
        raise TypeError("vector must be a complex128 numpy array")
    if vector.ndim not in (1, 2) or vector.shape[0] != dimension(rows, width):
        raise ValueError("vector must have dimension on axis 0 and be one- or two-dimensional")
    if not vector.flags.c_contiguous:
        raise ValueError("vector must be C-contiguous")
    if not np.isfinite(vector).all():
        raise ValueError("vector contains a non-finite value")
    return vector


def _finite(value: np.ndarray, name: str) -> np.ndarray:
    if not np.isfinite(value).all():
        raise FloatingPointError(f"{name} contains a non-finite value")
    return value


def _matrix(matrix: np.ndarray, name: str) -> np.ndarray:
    if not isinstance(matrix, np.ndarray) or matrix.dtype != np.dtype(np.complex128):
        raise TypeError(f"{name} must be a complex128 numpy array")
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 1:
        raise ValueError(f"{name} must be a nonempty square matrix")
    if not matrix.flags.c_contiguous:
        raise ValueError(f"{name} must be C-contiguous")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} contains a non-finite value")
    return matrix


def _trigonometry(theta: object, phi: object) -> tuple[np.float64, np.float64, np.complex128]:
    theta64 = _float64(theta, "theta")
    phi64 = _float64(phi, "phi")
    with np.errstate(all="raise"):
        cosine = np.float64(np.cos(theta64))
        sine = np.float64(np.sin(theta64))
        phase = np.complex128(np.cos(phi64) + np.complex128(1j) * np.sin(phi64))
    if not np.isfinite(cosine) or not np.isfinite(sine) or not np.isfinite(phase):
        raise FloatingPointError("trigonometric intermediate is non-finite")
    return cosine, sine, phase


def oracle_matrix(rows: int, width: int, terminal: Position) -> np.ndarray:
    terminal = _position(terminal, rows, width)
    matrix = np.eye(dimension(rows, width), dtype=np.complex128)
    for direction in range(DIRECTION_COUNT):
        matrix[basis_index(*terminal, direction, rows, width),
               basis_index(*terminal, direction, rows, width)] = np.complex128(-1.0)
    return _matrix(matrix, "oracle matrix")


def pair_matrix(rows: int, width: int, pairs: Iterable[Pair], theta: np.float64,
                phi: np.float64) -> np.ndarray:
    checked_pairs = _pairs(pairs, rows, width)
    cosine, sine, phase = _trigonometry(theta, phi)
    matrix = np.eye(dimension(rows, width), dtype=np.complex128)
    with np.errstate(over="raise", invalid="raise"):
        upper = np.complex128(-phase.conjugate() * sine)
        lower = np.complex128(phase * sine)
    if not np.isfinite(upper) or not np.isfinite(lower):
        raise FloatingPointError("pair block contains a non-finite value")
    for left, right in checked_pairs:
        for direction in range(DIRECTION_COUNT):
            left_index = basis_index(*left, direction, rows, width)
            right_index = basis_index(*right, direction, rows, width)
            matrix[left_index, left_index] = cosine
            matrix[left_index, right_index] = upper
            matrix[right_index, left_index] = lower
            matrix[right_index, right_index] = cosine
    return _matrix(matrix, "pair matrix")


def grover_coin_matrix(rows: int, width: int) -> np.ndarray:
    matrix = np.zeros((dimension(rows, width),) * 2, dtype=np.complex128)
    for row in range(rows):
        for column in range(width):
            for output_direction in range(DIRECTION_COUNT):
                output = basis_index(row, column, output_direction, rows, width)
                for input_direction in range(DIRECTION_COUNT):
                    source = basis_index(row, column, input_direction, rows, width)
                    matrix[output, source] = np.complex128(
                        np.float64(-0.5 if output_direction == input_direction else 0.5)
                    )
    return _matrix(matrix, "Grover matrix")


def shift_matrix(rows: int, width: int) -> np.ndarray:
    matrix = np.zeros((dimension(rows, width),) * 2, dtype=np.complex128)
    changes = ((-1, 0, 2), (0, 1, 3), (1, 0, 0), (0, -1, 1))
    for row in range(rows):
        for column in range(width):
            for direction, (row_change, column_change, reverse) in enumerate(changes):
                source = basis_index(row, column, direction, rows, width)
                target = basis_index((row + row_change) % rows,
                                     (column + column_change) % width,
                                     reverse, rows, width)
                matrix[target, source] = np.complex128(1.0)
    return _matrix(matrix, "shift matrix")


def _compose(factors: tuple[np.ndarray, ...], name: str) -> np.ndarray:
    checked = tuple(_matrix(factor, f"{name} factor") for factor in factors)
    result = checked[-1]
    for factor in reversed(checked[:-1]):
        with np.errstate(over="raise", invalid="raise"):
            result = np.ascontiguousarray(factor @ result, dtype=np.complex128)
        _finite(result, f"{name} composition intermediate")
    return _matrix(result, name)


def candidate_step_matrix(rows: int, width: int, terminal: Position,
                          pairs: Iterable[Pair], theta: np.float64,
                          phi: np.float64) -> np.ndarray:
    return _compose((shift_matrix(rows, width), grover_coin_matrix(rows, width),
                     pair_matrix(rows, width, pairs, theta, phi),
                     oracle_matrix(rows, width, terminal)), "candidate matrix")


def baseline_step_matrix(rows: int, width: int, terminal: Position) -> np.ndarray:
    return _compose((shift_matrix(rows, width), grover_coin_matrix(rows, width),
                     oracle_matrix(rows, width, terminal)), "baseline matrix")


def apply_oracle_formula(vector: np.ndarray, rows: int, width: int,
                         terminal: Position) -> np.ndarray:
    source = _vector(vector, rows, width)
    terminal = _position(terminal, rows, width)
    result = source.copy(order="C")
    with np.errstate(over="raise", invalid="raise"):
        for direction in range(DIRECTION_COUNT):
            index = basis_index(*terminal, direction, rows, width)
            result[index] = -source[index]
    return _finite(result, "oracle result")


def apply_pair_formula(vector: np.ndarray, rows: int, width: int,
                       pairs: Iterable[Pair], theta: np.float64,
                       phi: np.float64) -> np.ndarray:
    source = _vector(vector, rows, width)
    checked_pairs = _pairs(pairs, rows, width)
    cosine, sine, phase = _trigonometry(theta, phi)
    result = source.copy(order="C")
    with np.errstate(over="raise", invalid="raise"):
        for left, right in checked_pairs:
            for direction in range(DIRECTION_COUNT):
                left_index = basis_index(*left, direction, rows, width)
                right_index = basis_index(*right, direction, rows, width)
                left_diagonal = cosine * source[left_index]
                left_cross = phase.conjugate() * sine * source[right_index]
                right_cross = phase * sine * source[left_index]
                right_diagonal = cosine * source[right_index]
                _finite(np.asarray(left_diagonal), "pair product")
                _finite(np.asarray(left_cross), "pair product")
                _finite(np.asarray(right_cross), "pair product")
                _finite(np.asarray(right_diagonal), "pair product")
                result[left_index] = left_diagonal - left_cross
                result[right_index] = right_cross + right_diagonal
                _finite(np.asarray(result[left_index]), "pair sum")
                _finite(np.asarray(result[right_index]), "pair sum")
    return _finite(result, "pair result")


def apply_grover_formula(vector: np.ndarray, rows: int, width: int) -> np.ndarray:
    source = _vector(vector, rows, width)
    result = np.empty_like(source, order="C")
    with np.errstate(over="raise", invalid="raise"):
        for row in range(rows):
            for column in range(width):
                local_sum = np.zeros(source.shape[1:], dtype=np.complex128)
                for direction in range(DIRECTION_COUNT):
                    index = basis_index(row, column, direction, rows, width)
                    local_sum = local_sum + source[index]
                    _finite(local_sum, "Grover sum")
                half_sum = np.float64(0.5) * local_sum
                _finite(half_sum, "Grover half-sum")
                for direction in range(DIRECTION_COUNT):
                    index = basis_index(row, column, direction, rows, width)
                    result[index] = half_sum - source[index]
                    _finite(np.asarray(result[index]), "Grover subtraction")
    return _finite(result, "Grover result")


def apply_shift_formula(vector: np.ndarray, rows: int, width: int) -> np.ndarray:
    source = _vector(vector, rows, width)
    result = np.empty_like(source, order="C")
    changes = ((-1, 0, 2), (0, 1, 3), (1, 0, 0), (0, -1, 1))
    for row in range(rows):
        for column in range(width):
            for direction, (row_change, column_change, reverse) in enumerate(changes):
                source_index = basis_index(row, column, direction, rows, width)
                target_index = basis_index((row + row_change) % rows,
                                           (column + column_change) % width,
                                           reverse, rows, width)
                result[target_index] = source[source_index]
    return _finite(result, "shift result")


def apply_candidate_formula(vector: np.ndarray, rows: int, width: int,
                            terminal: Position, pairs: Iterable[Pair],
                            theta: np.float64, phi: np.float64) -> np.ndarray:
    checked_pairs = _pairs(pairs, rows, width)
    first = apply_oracle_formula(vector, rows, width, terminal)
    second = apply_pair_formula(first, rows, width, checked_pairs, theta, phi)
    third = apply_grover_formula(second, rows, width)
    return apply_shift_formula(third, rows, width)


def apply_baseline_formula(vector: np.ndarray, rows: int, width: int,
                           terminal: Position) -> np.ndarray:
    first = apply_oracle_formula(vector, rows, width, terminal)
    second = apply_grover_formula(first, rows, width)
    return apply_shift_formula(second, rows, width)


def maximum_unitarity_error(matrix: np.ndarray) -> np.float64:
    checked = _matrix(matrix, "matrix")
    identity = np.eye(checked.shape[0], dtype=np.complex128)
    with np.errstate(over="raise", invalid="raise"):
        product = np.ascontiguousarray(checked.conjugate().T @ checked,
                                       dtype=np.complex128)
        _finite(product, "unitarity product")
        difference = product - identity
        _finite(difference, "unitarity difference")
        magnitudes = np.abs(difference)
        _finite(magnitudes, "unitarity magnitudes")
        result = np.float64(np.max(magnitudes))
    if not np.isfinite(result):
        raise FloatingPointError("unitarity error is non-finite")
    return result


def matrix_terminal_probability(vector: np.ndarray, rows: int, width: int,
                                terminal: Position,
                                tolerance: np.float64) -> np.float64:
    source = _vector(vector, rows, width)
    if source.ndim != 1:
        raise ValueError("terminal probability requires one vector")
    terminal = _position(terminal, rows, width)
    tolerance64 = _float64(tolerance, "tolerance")
    if tolerance64 < np.float64(0.0):
        raise ValueError("tolerance must be nonnegative")
    total = np.float64(0.0)
    with np.errstate(over="raise", invalid="raise", under="ignore"):
        for direction in range(DIRECTION_COUNT):
            value = source[basis_index(*terminal, direction, rows, width)]
            real_square = np.float64(value.real * value.real)
            if not np.isfinite(real_square):
                raise FloatingPointError("real square is non-finite")
            imaginary_square = np.float64(value.imag * value.imag)
            if not np.isfinite(imaginary_square):
                raise FloatingPointError("imaginary square is non-finite")
            component = np.float64(real_square + imaginary_square)
            if not np.isfinite(component):
                raise FloatingPointError("component probability is non-finite")
            total = np.float64(total + component)
            if not np.isfinite(total):
                raise FloatingPointError("probability sum is non-finite")
    lower = np.float64(-tolerance64)
    upper = np.float64(np.float64(1.0) + tolerance64)
    if not np.isfinite(lower) or not np.isfinite(upper):
        raise FloatingPointError("probability bound is non-finite")
    if total < lower or total > upper:
        raise ValueError("terminal probability is outside physical bounds")
    return total
