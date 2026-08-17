#!/usr/bin/env python3
"""Verify an Area One release wheel from source through clean installation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import venv
from pathlib import Path
from typing import Callable

from normalize_wheel import normalize_wheel


ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "requirements-lock.txt"
CHECKSUMS = ROOT / "dist" / "SHA256SUMS.txt"
ANCHORS = ROOT / "area-one-evidence-bundle-fixture-anchors.json"
FIXTURE = ROOT / "area-one-evidence-bundle-fixture.zip"
SOURCE_DATE_EPOCH = "1767225600"
SCHEMA_VERSION = "area-one-release-verification/1.0"
PACKAGE_NAME = "area-one-evidence-verifier"
BUILD_VERSIONS = {
    "build": "1.5.0",
    "colorama": "0.4.6",
    "packaging": "26.0",
    "pyproject-hooks": "1.2.0",
}


class ReleaseVerificationError(RuntimeError):
    """Raised when a release invariant fails."""


def _normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _run(
    command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None
) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        rendered = subprocess.list2cmdline(command)
        raise ReleaseVerificationError(
            f"command failed ({result.returncode}): {rendered}\n{result.stdout[-4000:]}"
        )
    return result.stdout


def _load_metadata() -> tuple[dict, list[str], str, Path]:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = metadata["project"]
    version = project["version"]
    modules = metadata["tool"]["setuptools"]["py-modules"]
    wheel = ROOT / "dist" / (
        f"{PACKAGE_NAME.replace('-', '_')}-{version}-py3-none-any.whl"
    )
    return metadata, modules, version, wheel


def _load_lock() -> dict[str, str]:
    locked: dict[str, str] = {}
    for line in LOCKFILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.count("==") != 1:
            raise ReleaseVerificationError(f"lock entry is not exact: {line}")
        name, version = line.split("==", 1)
        normalized = _normalize_name(name)
        if normalized in locked:
            raise ReleaseVerificationError(f"duplicate lock package: {name}")
        locked[normalized] = version
    return locked


def _artifact_check(wheel: Path) -> str:
    fields = CHECKSUMS.read_text(encoding="utf-8").strip().split()
    if len(fields) != 2 or fields[1] != wheel.name:
        raise ReleaseVerificationError("SHA256SUMS.txt does not name the release wheel")
    actual = _sha256(wheel)
    if fields[0] != actual:
        raise ReleaseVerificationError("release wheel checksum does not match")
    return f"sha256:{actual}; size={wheel.stat().st_size}"


def _compile_check(modules: list[str]) -> str:
    paths = [ROOT / f"{module}.py" for module in modules]
    paths.extend((Path(__file__).resolve(), ROOT / "normalize_wheel.py"))
    for path in paths:
        py_compile.compile(str(path), doraise=True)
    return f"compiled_files={len(paths)}"


def _source_tests_check() -> str:
    output = _run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"]
    )
    match = re.search(r"Ran (\d+) tests", output)
    if not match:
        raise ReleaseVerificationError("unittest output did not report a test count")
    return f"tests={match.group(1)}"

def _build_tools_check() -> str:
    actual: dict[str, str] = {}
    for name, expected in BUILD_VERSIONS.items():
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ReleaseVerificationError(
                f"missing build dependency {name}=={expected}; "
                "install requirements-build.txt"
            ) from exc
        actual[name] = version
        if version != expected:
            raise ReleaseVerificationError(
                f"build dependency mismatch: {name}=={version}, expected {expected}"
            )
    return ", ".join(f"{name}=={actual[name]}" for name in sorted(actual))


def _reproducible_build_check(wheel: Path, modules: list[str]) -> str:
    hashes: list[str] = []
    with tempfile.TemporaryDirectory(prefix="area-one-build-") as temporary:
        temporary_root = Path(temporary)
        for index in range(2):
            source = temporary_root / f"source-{index}"
            output = temporary_root / f"dist-{index}"
            source.mkdir()
            output.mkdir()
            shutil.copy2(PYPROJECT, source / PYPROJECT.name)
            for module in modules:
                shutil.copy2(ROOT / f"{module}.py", source / f"{module}.py")
            environment = os.environ.copy()
            environment["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
            _run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(output)],
                cwd=source,
                env=environment,
            )
            built = list(output.glob("*.whl"))
            if len(built) != 1:
                raise ReleaseVerificationError("build did not create exactly one wheel")
            normalize_wheel(built[0], int(SOURCE_DATE_EPOCH))
            hashes.append(_sha256(built[0]))
    release_hash = _sha256(wheel)
    if hashes != [release_hash, release_hash]:
        raise ReleaseVerificationError(
            f"rebuild hashes differ: release={release_hash}, builds={hashes}"
        )
    return f"builds=2; sha256:{release_hash}; epoch={SOURCE_DATE_EPOCH}"


def _venv_commands(environment: Path) -> tuple[Path, Path]:
    if os.name == "nt":
        scripts = environment / "Scripts"
        return scripts / "python.exe", scripts / "area-one-verify.exe"
    scripts = environment / "bin"
    return scripts / "python", scripts / "area-one-verify"


def _installed_versions(python: Path) -> dict[str, str]:
    program = (
        "import importlib.metadata as m,json,re;"
        "n=lambda s:re.sub(r'[-_.]+','-',s).lower();"
        "print(json.dumps({n(d.metadata['Name']):d.version for d in m.distributions()}))"
    )
    return json.loads(_run([str(python), "-c", program]).strip())

def _clean_install_check(wheel: Path, version: str) -> str:
    lock = _load_lock()
    package_key = _normalize_name(PACKAGE_NAME)
    if lock.get(package_key) != version:
        raise ReleaseVerificationError("lockfile package version differs from pyproject")
    with tempfile.TemporaryDirectory(prefix="area-one-install-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python, executable = _venv_commands(environment)
        dependency_lock = Path(temporary) / "dependencies.txt"
        dependency_lock.write_text(
            "\n".join(
                f"{name}=={locked_version}"
                for name, locked_version in lock.items()
                if name != package_key
            )
            + "\n",
            encoding="utf-8",
        )
        _run(
            [
                str(python), "-m", "pip", "install", "--disable-pip-version-check",
                "-r", str(dependency_lock),
            ]
        )
        _run(
            [
                str(python), "-m", "pip", "install", "--disable-pip-version-check",
                "--no-deps", str(wheel),
            ]
        )
        _run([str(python), "-m", "pip", "check"])
        installed = _installed_versions(python)
        selected = {name: installed.get(name) for name in lock}
        extras = set(installed) - set(lock) - {"pip", "setuptools", "wheel"}
        if selected != lock or extras:
            raise ReleaseVerificationError(
                f"installed set differs from lock: versions={selected}, extras={sorted(extras)}"
            )
        imported = _run(
            [str(python), "-c", "import evidence_bundle; print(evidence_bundle.__file__)"],
            cwd=Path(temporary),
        ).strip()
        if "site-packages" not in imported.replace("\\", "/").lower():
            raise ReleaseVerificationError("installed verifier was not imported from site-packages")
        reported_version = _run([str(executable), "--version"]).strip()
        if reported_version != f"area-one-verify {version}":
            raise ReleaseVerificationError("installed CLI reported the wrong version")
        anchors = json.loads(ANCHORS.read_text(encoding="utf-8"))
        command = [
            str(executable), "verify", str(FIXTURE),
            "--expected-report-hash", anchors["expected_report_hash"],
            "--expected-issuer-trust-hash", anchors["expected_issuer_trust_hash"],
            "--expected-witness-policy-hash", anchors["expected_witness_policy_hash"],
            "--expected-checkpoint-hash", anchors["expected_checkpoint_hash"],
            "--expected-tsa-root-sha256", anchors["expected_tsa_root_sha256"],
        ]
        verification = _run(command)
        if "bundle_valid=true" not in verification:
            raise ReleaseVerificationError("installed CLI did not validate the fixture")
    return f"locked_packages={len(lock)}; cli={version}; bundle_valid=true"

def _execute_check(
    checks: list[dict[str, object]], name: str, action: Callable[[], str]
) -> None:
    try:
        detail = action()
    except Exception as exc:  # keep the report useful when one stage fails
        checks.append({"name": name, "passed": False, "detail": str(exc)})
    else:
        checks.append({"name": name, "passed": True, "detail": detail})


def _canonical_json(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def verify_release(output: Path) -> dict:
    _, modules, version, wheel = _load_metadata()
    checks: list[dict[str, object]] = []
    actions: list[tuple[str, Callable[[], str]]] = [
        ("artifact_checksum", lambda: _artifact_check(wheel)),
        ("source_compilation", lambda: _compile_check(modules)),
        ("source_tests", _source_tests_check),
        ("build_tool_versions", _build_tools_check),
        ("reproducible_build", lambda: _reproducible_build_check(wheel, modules)),
        ("clean_install_and_fixture", lambda: _clean_install_check(wheel, version)),
    ]
    for name, action in actions:
        _execute_check(checks, name, action)
    report = {
        "schema_version": SCHEMA_VERSION,
        "verdict": "passed" if all(check["passed"] for check in checks) else "failed",
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "distribution": {
            "name": PACKAGE_NAME,
            "version": version,
            "wheel": wheel.name,
            "wheel_sha256": "sha256:" + _sha256(wheel),
        },
        "checks": checks,
        "limitations": [
            "This report covers only the named interpreter and operating system.",
            "The release wheel is not published to PyPI and has no production signature.",
            "RFC 3161 verification does not perform CRL or OCSP checks.",
        ],
    }
    report["report_hash"] = "sha256:" + hashlib.sha256(
        b"AREA-ONE-RELEASE-VERIFICATION\x00" + _canonical_json(report)
    ).hexdigest()
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_name = (
        f"release-verification-{platform.system().lower()}-"
        f"python{sys.version_info.major}{sys.version_info.minor}.json"
    )
    parser.add_argument("--output", type=Path, default=ROOT / default_name)
    args = parser.parse_args()
    report = verify_release(args.output)
    print(f"release_verdict={report['verdict']}")
    print(f"report={args.output}")
    print(f"report_hash={report['report_hash']}")
    for check in report["checks"]:
        print(f"check_{check['name']}={str(check['passed']).lower()}")
        if not check["passed"]:
            print(f"error_{check['name']}={check['detail']}")
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
