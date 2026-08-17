#!/usr/bin/env python3
"""Run the local and Docker Linux Area One release-verification matrix."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LINUX_IMAGES = {
    "311": "python:3.11-slim",
    "312": "python:3.12-slim",
    "313": "python:3.13-slim",
}


def _run(command: list[str]) -> None:
    print("+", subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _docker_target(minor: str, image: str) -> None:
    container_command = (
        "python -m pip install --disable-pip-version-check "
        "--find-links /workspace/dist -r requirements-lock.txt "
        "-r requirements-build.txt >/tmp/install.log && "
        "python release_verification.py "
        f"--output release-verification-linux-python{minor}.json"
    )
    _run(
        [
            "docker", "run", "--rm", "--pull=missing",
            "-v", f"{ROOT}:/workspace", "-w", "/workspace",
            image, "sh", "-c", container_command,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-local", action="store_true")
    parser.add_argument("--skip-containers", action="store_true")
    args = parser.parse_args()
    if not args.skip_local:
        _run([sys.executable, "release_verification.py"])
    if not args.skip_containers:
        _run(["docker", "info", "--format", "{{.ServerVersion}}"])
        for minor, image in LINUX_IMAGES.items():
            _docker_target(minor, image)
    _run([sys.executable, "aggregate_release_matrix.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
