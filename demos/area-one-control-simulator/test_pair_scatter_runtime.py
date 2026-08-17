#!/usr/bin/env python3
"""Focused tests for the frozen Area One runtime contract."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import pair_scatter_runtime as runtime

DIGEST = "sha256:" + "a" * 64


class RuntimeBootstrapTests(unittest.TestCase):
    def test_sets_all_thread_variables_before_numpy(self) -> None:
        environment: dict[str, str] = {}
        metadata = runtime.bootstrap_runtime(
            DIGEST, DIGEST, 4, environ=environment,
            imported_module_names=(), system="Linux", machine="x86_64",
            python_implementation="CPython", python_version=runtime.CPYTHON_VERSION,
        )
        self.assertEqual(environment, {name: "1" for name in runtime.THREAD_ENVIRONMENT})
        self.assertEqual(metadata["worker_count"], 4)
        self.assertEqual(metadata["python_implementation"], "CPython")
        self.assertEqual(metadata["python_version"], runtime.CPYTHON_VERSION)

    def test_rejects_python_implementation_and_version_mismatch(self) -> None:
        common = dict(
            environ={}, imported_module_names=(), system="Linux", machine="x86_64",
            python_version=runtime.CPYTHON_VERSION,
        )
        with self.assertRaisesRegex(RuntimeError, "CPython"):
            runtime.bootstrap_runtime(
                DIGEST, DIGEST, 4, python_implementation="PyPy", **common
            )
        with self.assertRaisesRegex(RuntimeError, runtime.CPYTHON_VERSION):
            runtime.bootstrap_runtime(
                DIGEST, DIGEST, 4, python_implementation="CPython",
                **{**common, "python_version": "3.13.6"},
            )

    def test_rejects_environment_mismatch_without_partial_mutation(self) -> None:
        environment = {"OMP_NUM_THREADS": "2"}
        with self.assertRaisesRegex(RuntimeError, "OMP_NUM_THREADS"):
            runtime.configure_thread_environment(environment, imported_module_names=())
        self.assertNotIn("MKL_NUM_THREADS", environment)

    def test_rejects_numpy_already_imported(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "before any NumPy import"):
            runtime.configure_thread_environment({}, imported_module_names=("numpy",))

    def test_rejects_worker_count_platform_and_digest(self) -> None:
        common = dict(
            environ={}, imported_module_names=(), system="Linux", machine="x86_64",
            python_implementation="CPython", python_version=runtime.CPYTHON_VERSION,
        )
        with self.assertRaises(ValueError):
            runtime.bootstrap_runtime(DIGEST, DIGEST, 3, **common)
        with self.assertRaisesRegex(RuntimeError, "Linux"):
            runtime.bootstrap_runtime(DIGEST, DIGEST, 4, **{**common, "system": "Windows"})
        with self.assertRaisesRegex(RuntimeError, "x86_64"):
            runtime.bootstrap_runtime(DIGEST, DIGEST, 4, **{**common, "machine": "aarch64"})
        with self.assertRaisesRegex(RuntimeError, "digest"):
            runtime.bootstrap_runtime(DIGEST, "sha256:" + "b" * 64, 4, **common)
        with self.assertRaises(ValueError):
            runtime.bootstrap_runtime("latest", "latest", 4, **common)


class ThreadPoolTests(unittest.TestCase):
    def test_thread_pools_are_lazy_sorted_and_single_threaded(self) -> None:
        pools = [
            {"user_api": "blas", "internal_api": "z", "prefix": "z", "filepath": "/z", "version": "1", "num_threads": 1},
            {"user_api": "openmp", "internal_api": "a", "prefix": "a", "filepath": "/a", "version": "2", "num_threads": 1},
        ]
        result = runtime.inspect_thread_pools(
            lambda: pools,
            installed_threadpoolctl_version=runtime.THREADPOOLCTL_VERSION,
        )
        self.assertEqual(result[0]["internal_api"], "a")
        self.assertEqual(result[1]["num_threads"], 1)

    def test_rejects_threadpoolctl_version_mismatch_or_omission(self) -> None:
        provider = lambda: []
        with self.assertRaisesRegex(RuntimeError, "threadpoolctl version mismatch"):
            runtime.inspect_thread_pools(
                provider, installed_threadpoolctl_version="3.5.0"
            )
        with self.assertRaisesRegex(RuntimeError, "threadpoolctl version mismatch"):
            runtime.inspect_thread_pools(provider)

    def test_lazy_threadpoolctl_import_validates_module_version(self) -> None:
        class ThreadPoolCtl:
            __version__ = runtime.THREADPOOLCTL_VERSION

            @staticmethod
            def threadpool_info() -> list[dict[str, object]]:
                return [{"internal_api": "openblas", "num_threads": 1}]

        with patch.object(runtime.importlib, "import_module", return_value=ThreadPoolCtl):
            pools = runtime.inspect_thread_pools()
        self.assertEqual(pools[0]["internal_api"], "openblas")

        ThreadPoolCtl.__version__ = "3.5.0"
        with patch.object(runtime.importlib, "import_module", return_value=ThreadPoolCtl):
            with self.assertRaisesRegex(RuntimeError, "expected 3.6.0"):
                runtime.inspect_thread_pools()

    def test_rejects_any_pool_not_using_one_thread(self) -> None:
        options = {"installed_threadpoolctl_version": runtime.THREADPOOLCTL_VERSION}
        with self.assertRaisesRegex(RuntimeError, "2 threads"):
            runtime.inspect_thread_pools(
                lambda: [{"internal_api": "openblas", "num_threads": 2}],
                **options,
            )
        with self.assertRaises(ValueError):
            runtime.inspect_thread_pools(
                lambda: [{"internal_api": "bad"}], **options
            )

    def test_complete_diagnostics_captures_numpy_configuration(self) -> None:
        class NumPy:
            __version__ = runtime.NUMPY_VERSION

            @staticmethod
            def show_config() -> None:
                print("Build Dependencies:")
                print("  blas: openblas")

        original = {"worker_count": 4}
        result = runtime.complete_diagnostics(
            original,
            lambda: [{"internal_api": "openblas", "num_threads": 1}],
            numpy_module=NumPy,
            installed_threadpoolctl_version=runtime.THREADPOOLCTL_VERSION,
        )
        self.assertEqual(original, {"worker_count": 4})
        self.assertEqual(result["numpy_version"], runtime.NUMPY_VERSION)
        self.assertEqual(
            result["numpy_configuration"],
            "Build Dependencies:\n  blas: openblas",
        )
        self.assertEqual(
            result["threadpoolctl_version"], runtime.THREADPOOLCTL_VERSION
        )
        self.assertEqual(result["thread_pools"][0]["num_threads"], 1)

    def test_rejects_numpy_version_mismatch_and_empty_configuration(self) -> None:
        class NumPy:
            __version__ = "2.4.1"

            @staticmethod
            def show_config() -> None:
                print("not reached")

        options = dict(
            pool_info_provider=lambda: [],
            installed_threadpoolctl_version=runtime.THREADPOOLCTL_VERSION,
        )
        with self.assertRaisesRegex(RuntimeError, "NumPy version mismatch"):
            runtime.complete_diagnostics({}, numpy_module=NumPy, **options)

        NumPy.__version__ = runtime.NUMPY_VERSION
        NumPy.show_config = staticmethod(lambda: None)
        with self.assertRaisesRegex(RuntimeError, "must not be empty"):
            runtime.complete_diagnostics({}, numpy_module=NumPy, **options)

    def test_diagnostics_serialization_is_deterministic(self) -> None:
        metadata = {"worker_count": 4, "thread_pools": [{"num_threads": 1}], "oci_digest": DIGEST}
        first = runtime.serialize_diagnostics(metadata)
        self.assertEqual(first, runtime.serialize_diagnostics(metadata))
        self.assertTrue(first.endswith(b"\n"))
        self.assertEqual(json.loads(first), metadata)


if __name__ == "__main__":
    unittest.main(verbosity=2)
