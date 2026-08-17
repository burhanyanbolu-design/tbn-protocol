#!/usr/bin/env python3
"""Frozen runtime checks for Area One pair-scatter production runs.

This module intentionally imports only Python standard-library modules.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import platform
import re
import sys
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from contextlib import redirect_stdout

CPYTHON_VERSION = "3.13.7"
NUMPY_VERSION = "2.4.2"
THREADPOOLCTL_VERSION = "3.6.0"
THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
WORKER_COUNT = 4
_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _require_digest(value: object, name: str) -> str:
    if not isinstance(value, str) or _DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase sha256 OCI digest")
    return value


def _require_worker_count(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("worker_count must be an integer")
    if value != WORKER_COUNT:
        raise ValueError(f"worker_count must be exactly {WORKER_COUNT}")
    return value


def configure_thread_environment(
    environ: MutableMapping[str, str] | None = None,
    *,
    imported_module_names: Sequence[str] | None = None,
) -> dict[str, str]:
    """Set missing thread limits and reject mismatches before NumPy import."""
    target = os.environ if environ is None else environ
    names = tuple(sys.modules) if imported_module_names is None else tuple(imported_module_names)
    if any(name == "numpy" or name.startswith("numpy.") for name in names):
        raise RuntimeError("thread environment must be configured before any NumPy import")
    mismatches = {
        name: target[name]
        for name in THREAD_ENVIRONMENT
        if name in target and target[name] != "1"
    }
    if mismatches:
        detail = ", ".join(f"{name}={mismatches[name]!r}" for name in sorted(mismatches))
        raise RuntimeError(f"thread environment mismatch: {detail}")
    for name in THREAD_ENVIRONMENT:
        target[name] = "1"
    return {name: target[name] for name in THREAD_ENVIRONMENT}


def _cpu_metadata() -> tuple[str, tuple[str, ...]]:
    model = platform.processor().strip()
    flags: tuple[str, ...] = ()
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as handle:
            fields: dict[str, str] = {}
            for line in handle:
                if not line.strip():
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    fields[key.strip().lower()] = value.strip()
        model = fields.get("model name", model)
        flags = tuple(sorted(fields.get("flags", "").split()))
    except OSError:
        pass
    return model, flags


def bootstrap_runtime(
    expected_oci_digest: str,
    actual_oci_digest: str,
    worker_count: int,
    *,
    environ: MutableMapping[str, str] | None = None,
    imported_module_names: Sequence[str] | None = None,
    system: str | None = None,
    machine: str | None = None,
    python_implementation: str | None = None,
    python_version: str | None = None,
) -> dict[str, object]:
    """Validate the pre-NumPy frozen runtime and return deterministic metadata."""
    thread_environment = configure_thread_environment(
        environ, imported_module_names=imported_module_names
    )
    workers = _require_worker_count(worker_count)
    expected = _require_digest(expected_oci_digest, "expected_oci_digest")
    actual = _require_digest(actual_oci_digest, "actual_oci_digest")
    if expected != actual:
        raise RuntimeError("OCI image digest does not match the caller-supplied digest")
    detected_system = platform.system() if system is None else system
    detected_machine = platform.machine() if machine is None else machine
    if detected_system != "Linux":
        raise RuntimeError("pair-scatter production requires Linux")
    if detected_machine.lower() not in {"x86_64", "amd64"}:
        raise RuntimeError("pair-scatter production requires x86_64")
    detected_implementation = (
        platform.python_implementation()
        if python_implementation is None
        else python_implementation
    )
    detected_python_version = (
        platform.python_version() if python_version is None else python_version
    )
    if detected_implementation != "CPython":
        raise RuntimeError("pair-scatter production requires CPython")
    if detected_python_version != CPYTHON_VERSION:
        raise RuntimeError(
            f"pair-scatter production requires CPython {CPYTHON_VERSION}"
        )
    cpu_model, cpu_flags = _cpu_metadata()
    return {
        "cpu_flags": list(cpu_flags),
        "cpu_model": cpu_model,
        "machine": "x86_64",
        "oci_digest": actual,
        "platform": "Linux",
        "python_build": list(platform.python_build()),
        "python_implementation": detected_implementation,
        "python_version": detected_python_version,
        "thread_environment": thread_environment,
        "worker_count": workers,
    }


def _resolve_pool_info_provider(
    pool_info_provider: Callable[[], Sequence[Mapping[str, object]]] | None,
    installed_threadpoolctl_version: str | None,
) -> tuple[Callable[[], Sequence[Mapping[str, object]]], str]:
    if pool_info_provider is None:
        module = importlib.import_module("threadpoolctl")
        detected_version = getattr(module, "__version__", None)
        provider = module.threadpool_info
    else:
        detected_version = installed_threadpoolctl_version
        provider = pool_info_provider
    if detected_version != THREADPOOLCTL_VERSION:
        raise RuntimeError(
            "threadpoolctl version mismatch: "
            f"expected {THREADPOOLCTL_VERSION}, found {detected_version!r}"
        )
    return provider, detected_version


def _normalize_thread_pools(
    raw_pools: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    normalized: list[dict[str, object]] = []
    for index, pool in enumerate(raw_pools):
        if not isinstance(pool, Mapping):
            raise TypeError(f"thread pool {index} metadata must be a mapping")
        count = pool.get("num_threads")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError(f"thread pool {index} has invalid num_threads")
        identity = str(pool.get("internal_api", pool.get("prefix", index)))
        if count != 1:
            raise RuntimeError(f"thread pool {identity!r} reports {count} threads; expected 1")
        normalized.append(
            {
                "filepath": str(pool.get("filepath", "")),
                "internal_api": str(pool.get("internal_api", "")),
                "num_threads": count,
                "prefix": str(pool.get("prefix", "")),
                "user_api": str(pool.get("user_api", "")),
                "version": str(pool.get("version", "")),
            }
        )
    normalized.sort(
        key=lambda item: (
            item["internal_api"], item["user_api"], item["prefix"],
            item["filepath"], item["version"]
        )
    )
    return tuple(normalized)


def inspect_thread_pools(
    pool_info_provider: Callable[[], Sequence[Mapping[str, object]]] | None = None,
    *,
    installed_threadpoolctl_version: str | None = None,
) -> tuple[dict[str, object], ...]:
    """Lazily inspect exact-version native pools and require one thread each."""
    provider, _ = _resolve_pool_info_provider(
        pool_info_provider, installed_threadpoolctl_version
    )
    return _normalize_thread_pools(provider())


def complete_diagnostics(
    pre_numpy_metadata: Mapping[str, object],
    pool_info_provider: Callable[[], Sequence[Mapping[str, object]]] | None = None,
    *,
    numpy_module: object | None = None,
    installed_threadpoolctl_version: str | None = None,
) -> dict[str, object]:
    """Attach exact-version NumPy configuration and native pool diagnostics."""
    module = importlib.import_module("numpy") if numpy_module is None else numpy_module
    detected_numpy_version = getattr(module, "__version__", None)
    if detected_numpy_version != NUMPY_VERSION:
        raise RuntimeError(
            f"NumPy version mismatch: expected {NUMPY_VERSION}, "
            f"found {detected_numpy_version!r}"
        )
    configuration_stream = io.StringIO()
    with redirect_stdout(configuration_stream):
        module.show_config()
    numpy_configuration = "\n".join(
        line.rstrip() for line in configuration_stream.getvalue().splitlines()
    ).strip()
    if not numpy_configuration:
        raise RuntimeError("NumPy configuration output must not be empty")

    provider, detected_threadpoolctl_version = _resolve_pool_info_provider(
        pool_info_provider, installed_threadpoolctl_version
    )
    result = dict(pre_numpy_metadata)
    result["numpy_version"] = detected_numpy_version
    result["numpy_configuration"] = numpy_configuration
    result["threadpoolctl_version"] = detected_threadpoolctl_version
    result["thread_pools"] = list(_normalize_thread_pools(provider()))
    return result


def serialize_diagnostics(metadata: Mapping[str, object]) -> bytes:
    """Return deterministic compact sorted-key UTF-8 JSON with final LF."""
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")
    try:
        encoded = json.dumps(
            metadata, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("diagnostics metadata is not deterministic JSON") from exc
    return encoded + b"\n"
