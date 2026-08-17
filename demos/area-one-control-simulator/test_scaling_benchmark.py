#!/usr/bin/env python3
"""Verification for bounded local scaling benchmarks."""

import unittest

from scaling_benchmark import (
    benchmark_configuration,
    format_bytes,
    parse_configurations,
)


class ScalingBenchmarkTests(unittest.TestCase):
    def test_configuration_parser(self) -> None:
        self.assertEqual(parse_configurations("2:3,3:5"), ((2, 3), (3, 5)))

    def test_dimension_and_dense_storage_calculation(self) -> None:
        result = benchmark_configuration(2, 3, evolution_steps=2, repeats=1)
        self.assertEqual(result.width, 3)
        self.assertEqual(result.hilbert_dimension, 36)
        self.assertEqual(result.density_matrix_entries, 36 * 36)
        self.assertEqual(result.minimum_numeric_density_bytes, 36 * 36 * 16)

    def test_runtime_and_peak_allocation_are_recorded(self) -> None:
        result = benchmark_configuration(1, 2, evolution_steps=2, repeats=2)
        self.assertGreaterEqual(result.median_runtime_seconds, 0.0)
        self.assertGreater(result.peak_python_bytes, 0)

    def test_byte_formatting(self) -> None:
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(2048), "2.00 KiB")
        self.assertEqual(format_bytes(2 * 1024 * 1024), "2.00 MiB")

    def test_invalid_benchmark_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            benchmark_configuration(0, 3, evolution_steps=2, repeats=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
