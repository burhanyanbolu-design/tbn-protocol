#!/usr/bin/env python3
"""Production local tensor kernels for the Area One pair-scatter walk."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

DIRECTION_COUNT = 4
INPUT_BASIS_COUNT = 4
PROBABILITY_TOLERANCE = np.float64(1e-12)
Position = tuple[int, int]
Pair = tuple[Position, Position]


def _canonical_strides(shape: tuple[int, ...]) -> tuple[int, ...]:
    stride = np.dtype(np.complex128).itemsize
    result: list[int] = []
    for size in reversed(shape):
        result.append(stride)
        stride *= size
    return tuple(reversed(result))


def validate_state(state: np.ndarray) -> tuple[int, int]:
    """Validate the protocol's direct or four-column tensor layout."""
    if not isinstance(state, np.ndarray):
        raise TypeError("state must be a numpy.ndarray")
    if state.dtype != np.dtype(np.complex128):
        raise TypeError("state dtype must be numpy.complex128")
    if state.ndim == 3:
        valid_tail = state.shape[2:] == (DIRECTION_COUNT,)
    elif state.ndim == 4:
        valid_tail = state.shape[2:] == (DIRECTION_COUNT, INPUT_BASIS_COUNT)
    else:
        valid_tail = False
    if not valid_tail or state.shape[0] < 1 or state.shape[1] < 1:
        raise ValueError("state shape must be (R, s+1, 4) or (R, s+1, 4, 4)")
    if not state.flags.c_contiguous or state.strides != _canonical_strides(state.shape):
        raise ValueError("state must have canonical C-contiguous strides")
    if not np.isfinite(state).all():
        raise ValueError("state contains a non-finite value")
    return state.shape[0], state.shape[1]


def _position(value: Position, rows: int, width: int, name: str) -> Position:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(f"{name} must be a (row, column) tuple")
    row, column = value
    if not isinstance(row, int) or isinstance(row, bool) or not isinstance(column, int) or isinstance(column, bool):
        raise TypeError(f"{name} coordinates must be integers")
    if not (0 <= row < rows and 0 <= column < width):
        raise ValueError(f"{name} is outside the state grid")
    return row, column

def validate_pairs(
    pairs: Iterable[Pair], rows: int, width: int
) -> tuple[Pair, ...]:
    """Return validated arbitrary disjoint position pairs."""
    try:
        materialized = tuple(pairs)
    except TypeError as exc:
        raise TypeError("pairs must be iterable") from exc
    used: set[Position] = set()
    validated: list[Pair] = []
    for pair_index, pair in enumerate(materialized):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError(f"pair {pair_index} must contain two positions")
        left = _position(pair[0], rows, width, f"pair {pair_index} left")
        right = _position(pair[1], rows, width, f"pair {pair_index} right")
        if left == right or left in used or right in used:
            raise ValueError("pairs must contain distinct, disjoint positions")
        used.update((left, right))
        validated.append((left, right))
    return tuple(validated)


def require_float64_scalar(value: object, name: str) -> np.float64:
    """Require an exact finite binary64 scalar; never coerce or accept subclasses."""
    if type(value) is not np.float64:
        raise TypeError(f"{name} must be numpy.float64")
    if not bool(np.isfinite(value)):
        raise ValueError(f"{name} must be finite")
    return value


def require_complex128_scalar(value: object, name: str) -> np.complex128:
    """Require an exact finite binary64-complex scalar; never coerce or promote."""
    if type(value) is not np.complex128:
        raise TypeError(f"{name} must be numpy.complex128")
    if not bool(np.isfinite(value.real)) or not bool(np.isfinite(value.imag)):
        raise ValueError(f"{name} must have finite components")
    return value


# Compatibility name retained only for scalar validation, never verdict production.
_finite_scalar = require_float64_scalar


def _finite_complex_intermediate(value: np.ndarray, name: str) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.complex128):
        raise RuntimeError(f"{name} did not preserve numpy.complex128")
    if not bool(np.all(np.isfinite(value.real))) or not bool(np.all(np.isfinite(value.imag))):
        raise FloatingPointError(f"{name} produced a non-finite component")
    return value


def _checked_result(state: np.ndarray, operation: str) -> np.ndarray:
    if state.dtype != np.dtype(np.complex128) or not state.flags.c_contiguous:
        raise RuntimeError(f"{operation} produced an invalid tensor layout")
    if state.strides != _canonical_strides(state.shape) or not np.isfinite(state).all():
        raise FloatingPointError(f"{operation} produced a non-finite or strided state")
    return state


def terminal_phase_oracle(state: np.ndarray, terminal: Position) -> np.ndarray:
    """Apply the marked-coordinate phase oracle ``I - 2 Pi_t``."""
    rows, width = validate_state(state)
    terminal = _position(terminal, rows, width, "terminal")
    result = state.copy(order="C")
    result[terminal[0], terminal[1], ...] *= np.complex128(-1.0)
    return _checked_result(result, "terminal oracle")


def pair_scatter(
    state: np.ndarray,
    pairs: Iterable[Pair],
    theta: np.float64,
    phi: np.float64,
) -> np.ndarray:
    """Apply one identical two-state unitary using exact binary64 inputs."""
    rows, width = validate_state(state)
    validated_pairs = validate_pairs(pairs, rows, width)
    theta64 = require_float64_scalar(theta, "theta")
    phi64 = require_float64_scalar(phi, "phi")
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        cosine = require_float64_scalar(np.cos(theta64), "cos(theta)")
        sine = require_float64_scalar(np.sin(theta64), "sin(theta)")
        phase_real = require_float64_scalar(np.cos(phi64), "cos(phi)")
        phase_imag = require_float64_scalar(np.sin(phi64), "sin(phi)")
        phase = require_complex128_scalar(
            np.complex128(phase_real) + np.complex128(1j) * np.complex128(phase_imag),
            "phase",
        )
        phase_conjugate = require_complex128_scalar(np.conjugate(phase), "conjugate phase")
        conjugate_sine = require_complex128_scalar(
            np.complex128(phase_conjugate * sine), "conjugate phase times sine"
        )
        phase_sine = require_complex128_scalar(
            np.complex128(phase * sine), "phase times sine"
        )
    result = state.copy(order="C")
    if not validated_pairs:
        return _checked_result(result, "pair scatter")
    left_rows = np.fromiter(
        (left[0] for left, _right in validated_pairs),
        dtype=np.intp,
        count=len(validated_pairs),
    )
    left_columns = np.fromiter(
        (left[1] for left, _right in validated_pairs),
        dtype=np.intp,
        count=len(validated_pairs),
    )
    right_rows = np.fromiter(
        (right[0] for _left, right in validated_pairs),
        dtype=np.intp,
        count=len(validated_pairs),
    )
    right_columns = np.fromiter(
        (right[1] for _left, right in validated_pairs),
        dtype=np.intp,
        count=len(validated_pairs),
    )
    left_amplitude = state[left_rows, left_columns, ...]
    right_amplitude = state[right_rows, right_columns, ...]
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        left_cosine = _finite_complex_intermediate(
            cosine * left_amplitude, "left cosine product"
        )
        right_coupling = _finite_complex_intermediate(
            conjugate_sine * right_amplitude, "right coupling product"
        )
        new_left = _finite_complex_intermediate(
            left_cosine - right_coupling, "left pair result"
        )
        left_coupling = _finite_complex_intermediate(
            phase_sine * left_amplitude, "left coupling product"
        )
        right_cosine = _finite_complex_intermediate(
            cosine * right_amplitude, "right cosine product"
        )
        new_right = _finite_complex_intermediate(
            left_coupling + right_cosine, "right pair result"
        )
    result[left_rows, left_columns, ...] = new_left
    result[right_rows, right_columns, ...] = new_right
    return _checked_result(result, "pair scatter")


overlap_pair_scatter = pair_scatter

def grover_coin(state: np.ndarray) -> np.ndarray:
    """Apply ``2|u><u| - I`` on the direction axis."""
    validate_state(state)
    with np.errstate(over="raise", invalid="raise"):
        try:
            direction_sum = np.sum(state, axis=2, dtype=np.complex128)
            _finite_complex_intermediate(direction_sum, "Grover coin direction sum")
            twice_mean = direction_sum * np.float64(0.5)
            _finite_complex_intermediate(twice_mean, "Grover coin twice mean")
            result = twice_mean[:, :, np.newaxis, ...] - state
            _finite_complex_intermediate(result, "Grover coin subtraction")
        except FloatingPointError as exc:
            raise FloatingPointError("Grover coin produced a non-finite value") from exc
    return _checked_result(np.ascontiguousarray(result, dtype=np.complex128), "Grover coin")


def periodic_flip_flop_shift(state: np.ndarray) -> np.ndarray:
    """Apply the periodic flip-flop shift on the first three axes."""
    validate_state(state)
    result = np.empty_like(state, order="C")
    result[:, :, 2, ...] = np.roll(state[:, :, 0, ...], -1, axis=0)
    result[:, :, 3, ...] = np.roll(state[:, :, 1, ...], 1, axis=1)
    result[:, :, 0, ...] = np.roll(state[:, :, 2, ...], 1, axis=0)
    result[:, :, 1, ...] = np.roll(state[:, :, 3, ...], -1, axis=1)
    return _checked_result(result, "periodic shift")


def baseline_step(state: np.ndarray, terminal: Position) -> np.ndarray:
    """Apply the no-pair baseline ``S C_G O_t`` in immutable order."""
    after_oracle = terminal_phase_oracle(state, terminal)
    after_coin = grover_coin(after_oracle)
    return periodic_flip_flop_shift(after_coin)


def candidate_step(
    state: np.ndarray,
    terminal: Position,
    pairs: Iterable[Pair],
    theta: np.float64,
    phi: np.float64,
) -> np.ndarray:
    """Apply ``S C_G P O_t`` in the protocol's immutable order."""
    validated_pairs = tuple(pairs)
    after_oracle = terminal_phase_oracle(state, terminal)
    after_pairs = pair_scatter(after_oracle, validated_pairs, theta, phi)
    after_coin = grover_coin(after_pairs)
    return periodic_flip_flop_shift(after_coin)


def state_norm(state: np.ndarray) -> np.float64:
    """Return the unmodified binary64 squared norm of a protocol tensor."""
    validate_state(state)
    with np.errstate(over="raise", invalid="raise"):
        try:
            squared_real = state.real * state.real
            squared_imag = state.imag * state.imag
            if not bool(np.all(np.isfinite(squared_real))) or not bool(np.all(np.isfinite(squared_imag))):
                raise FloatingPointError("state norm square is non-finite")
            squared_magnitude = squared_real + squared_imag
            if not bool(np.all(np.isfinite(squared_magnitude))):
                raise FloatingPointError("state squared magnitude is non-finite")
            value = np.float64(np.sum(squared_magnitude, dtype=np.float64))
        except FloatingPointError as exc:
            raise FloatingPointError("state norm is non-finite") from exc
    return require_float64_scalar(value, "state norm")


def final_terminal_probability(
    state: np.ndarray,
    terminal: Position,
    tolerance: np.float64 = PROBABILITY_TOLERANCE,
) -> np.float64:
    """Return final-only terminal probability, rejecting nonphysical values."""
    rows, width = validate_state(state)
    terminal = _position(terminal, rows, width, "terminal")
    tolerance64 = require_float64_scalar(tolerance, "tolerance")
    if tolerance64 < np.float64(0.0):
        raise ValueError("tolerance must be non-negative")
    amplitudes = state[terminal[0], terminal[1], ...]
    with np.errstate(over="raise", invalid="raise"):
        try:
            squared_real = amplitudes.real * amplitudes.real
            squared_imag = amplitudes.imag * amplitudes.imag
            if not bool(np.all(np.isfinite(squared_real))) or not bool(np.all(np.isfinite(squared_imag))):
                raise FloatingPointError("terminal probability square is non-finite")
            squared_magnitude = squared_real + squared_imag
            if not bool(np.all(np.isfinite(squared_magnitude))):
                raise FloatingPointError("terminal squared magnitude is non-finite")
            probability = np.float64(np.sum(squared_magnitude, dtype=np.float64))
            upper_bound = require_float64_scalar(
                np.float64(np.float64(1.0) + tolerance64), "probability upper bound"
            )
            lower_bound = require_float64_scalar(
                np.float64(-tolerance64), "probability lower bound"
            )
        except FloatingPointError as exc:
            raise FloatingPointError("terminal probability is non-finite") from exc
    require_float64_scalar(probability, "terminal probability")
    if probability < lower_bound or probability > upper_bound:
        raise ValueError("terminal probability is outside physical bounds")
    return probability


terminal_probability = final_terminal_probability
