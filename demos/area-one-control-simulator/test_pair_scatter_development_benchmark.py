#!/usr/bin/env python3
"""Focused tests for the T3 pair-scatter implementation smoke."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

MODULE_NAME = "pair_scatter_development_benchmark"
HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / f"{MODULE_NAME}.py"
THREAD_NAMES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in THREAD_NAMES:
        environment[name] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run_python(source: str, *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=HERE,
        env=_clean_environment(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


class DevelopmentBenchmarkTests(unittest.TestCase):
    def test_exact_declared_constants_and_formulas(self) -> None:
        source = textwrap.dedent(
            f"""
            import json
            import {MODULE_NAME} as subject
            print(json.dumps({{
                "primary_rows": subject.PRIMARY_ROWS,
                "secondary_rows": subject.SECONDARY_ROWS,
                "total_rows": subject.TOTAL_ROWS,
                "primary_work": subject.PRIMARY_FOUR_COLUMN_WORK_UNITS,
                "secondary_work": subject.SECONDARY_FOUR_COLUMN_WORK_UNITS,
                "total_work": subject.TOTAL_FOUR_COLUMN_WORK_UNITS,
                "row_work": subject.WORK_UNITS_PER_ROW,
                "benchmark_work": subject.BENCHMARK_WORK_UNITS,
                "genuine_pairs": subject.GENUINE_PAIRS,
                "row_formula": subject.WORK_UNITS_PER_ROW == 6 * 3 * 4 * 4 * 1,
                "rows_formula": subject.TOTAL_ROWS == subject.PRIMARY_ROWS + subject.SECONDARY_ROWS,
                "work_formula": subject.TOTAL_FOUR_COLUMN_WORK_UNITS == subject.PRIMARY_FOUR_COLUMN_WORK_UNITS + subject.SECONDARY_FOUR_COLUMN_WORK_UNITS,
            }}, sort_keys=True))
            """
        )
        completed = _run_python(source)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        values = json.loads(completed.stdout)
        self.assertEqual(values["primary_rows"], 17_382_024)
        self.assertEqual(values["secondary_rows"], 681_648)
        self.assertEqual(values["total_rows"], 18_063_672)
        self.assertEqual(values["primary_work"], 42_245_038_080)
        self.assertEqual(values["secondary_work"], 2_085_873_536)
        self.assertEqual(values["total_work"], 44_330_911_616)
        self.assertEqual(values["row_work"], 288)
        self.assertEqual(values["benchmark_work"], 1152)
        self.assertEqual(
            values["genuine_pairs"],
            [[[row, 2], [row + 1, 0]] for row in range(5)],
        )
        self.assertTrue(values["row_formula"])
        self.assertTrue(values["rows_formula"])
        self.assertTrue(values["work_formula"])

    def test_module_imports_only_standard_library_runtime_and_not_numpy(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
        allowed = set(sys.stdlib_module_names) | {"__future__", "pair_scatter_runtime"}
        self.assertEqual(imported_roots - allowed, set())
        completed = _run_python(
            f"import sys; import {MODULE_NAME}; print('numpy' in sys.modules)"
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "False")

    def test_mocked_stage_flow_dispatches_and_cleanup_removes_artifacts(self) -> None:
        source = textwrap.dedent(
            f"""
            import tempfile
            from pathlib import Path
            from unittest import mock
            import {MODULE_NAME} as subject

            with tempfile.TemporaryDirectory() as directory:
                pipeline = subject.DevelopmentSmokePipeline(directory)
                calls = []
                patches = []
                for stage in subject.STAGES[:-1]:
                    patched = mock.Mock(side_effect=lambda repetition, name=stage: calls.append((repetition, name)))
                    patches.append(mock.patch.object(pipeline, stage, patched))
                for patcher in patches:
                    patcher.start()
                try:
                    for stage in subject.STAGES[:-1]:
                        pipeline(0, stage)
                    temp_path = pipeline.repetition_temp_path(0)
                    final_path = pipeline.repetition_final_path(0)
                    temp_path.mkdir(parents=True, exist_ok=True)
                    final_path.mkdir(parents=True, exist_ok=True)
                    (temp_path / "temporary.bin").write_bytes(b"temp")
                    (final_path / "final.bin").write_bytes(b"final")
                    pipeline(0, "cleanup")
                finally:
                    for patcher in reversed(patches):
                        patcher.stop()
                assert calls == [(0, stage) for stage in subject.STAGES[:-1]]
                assert not temp_path.exists()
                assert not final_path.exists()
            """
        )
        completed = _run_python(source)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipUnless(
        os.environ.get("AREA_ONE_RUN_PROCESS_SMOKE") == "1",
        "set AREA_ONE_RUN_PROCESS_SMOKE=1 to run the four-process integration smoke",
    )
    def test_actual_four_process_smoke_once(self) -> None:
        source = textwrap.dedent(
            f"""
            import tempfile
            from pathlib import Path
            import {MODULE_NAME} as subject

            with tempfile.TemporaryDirectory() as directory:
                report = subject.run_development_smoke(directory)
                assert len(report.repetitions) == 3
                assert report.benchmark_rows == 4
                assert report.benchmark_work_units == 1152
                assert report.holdout_rows == 18_063_672
                assert report.holdout_work_units == 44_330_911_616
                assert all(not any((Path(directory) / name).iterdir()) for name in ("temporary", "final"))
            """
        )
        completed = _run_python(source, timeout=180)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
