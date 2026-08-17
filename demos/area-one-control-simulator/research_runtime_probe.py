#!/usr/bin/env python3
"""Fail-closed runtime probe for the pinned Area One research container."""

from __future__ import annotations

import os
import sys

import pair_scatter_runtime as runtime


def main() -> int:
    expected = os.environ.get("AREA_ONE_EXPECTED_OCI_DIGEST", "")
    actual = os.environ.get("AREA_ONE_ACTUAL_OCI_DIGEST", "")
    metadata = runtime.bootstrap_runtime(expected, actual, runtime.WORKER_COUNT)
    diagnostics = runtime.complete_diagnostics(metadata)
    sys.stdout.buffer.write(runtime.serialize_diagnostics(diagnostics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
