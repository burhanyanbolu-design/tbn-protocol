"""Fail-closed, consumed-attempt atomic publication for Area One.

The production durability path is deliberately pinned to Linux and rejects
network filesystems. Tests on other platforms must explicitly inject both a directory-sync function and a device
resolver; neither operation is ever silently skipped.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import secrets
import stat
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

MARKER_NAME = "attempt-consumed.json"
STAGING_NAME = "atomic-publication-staging"
ATTEMPT_SCHEMA = "area-one-attempt-consumed/1.0"
FAILURE_SCHEMA = "area-one-pair-results-failure/1.0"
_SAFE_FAILURE_MESSAGE = "Publication attempt was consumed but did not complete."
_HASH_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}\Z")
_DATASET_KINDS = frozenset(("holdout", "development-fixture"))
_REMOTE_FILESYSTEM_TYPES = frozenset(
    ("nfs", "nfs4", "cifs", "smb3", "9p", "ceph", "glusterfs", "fuse.sshfs")
)
_MOUNTINFO_ESCAPE_RE = re.compile(r"\\([0-7]{3})")

Hook = Callable[[str], None]
DirectorySync = Callable[[Path], None]
DeviceResolver = Callable[[Path], int]


class AtomicPublicationError(RuntimeError):
    """Base class for explicit fail-closed publication errors."""


class ConfigurationError(AtomicPublicationError):
    """The caller supplied an invalid or unsafe publication configuration."""


class DurabilityUnavailableError(AtomicPublicationError):
    """Required filesystem durability primitives are unavailable."""


class UnsafePathError(AtomicPublicationError):
    """A root, staging entry, or final path is unsafe."""


class CrossDeviceError(AtomicPublicationError):
    """Atomic replacement would cross a filesystem device boundary."""


class AttemptConsumedError(AtomicPublicationError):
    """The one permitted attempt has already been consumed."""


class VerificationError(AtomicPublicationError):
    """A caller-supplied verification rejected publication state."""


class StagingError(AtomicPublicationError):
    """The staging writer or staging tree violated its closed contract."""


class PlanError(AtomicPublicationError):
    """The producer returned an invalid publication plan."""


class PublicationState(str, Enum):
    LOCK_VERIFIED = "LOCK_VERIFIED"
    ATTEMPT_CONSUMED = "ATTEMPT_CONSUMED"
    STAGING = "STAGING"
    STAGING_VERIFIED = "STAGING_VERIFIED"
    LOCK_REVERIFIED = "LOCK_REVERIFIED"
    ARTIFACTS_COMMITTED = "ARTIFACTS_COMMITTED"
    COMPLETION_PUBLISHED = "COMPLETION_PUBLISHED"


class StartupClassification(str, Enum):
    FRESH = "FRESH"
    COMPLETED = "COMPLETED"
    CONSUMED_INCOMPLETE = "CONSUMED_INCOMPLETE"


@dataclass(frozen=True)
class PublicationPlan:
    """Explicit artifact replacement order and separately named completion."""

    artifact_names: tuple[str, ...]
    completion_name: str

    def __post_init__(self) -> None:
        names = tuple(self.artifact_names)
        object.__setattr__(self, "artifact_names", names)
        _validate_name(self.completion_name, "completion name")
        if not names:
            raise PlanError("publication plan must contain at least one artifact")
        for name in names:
            _validate_name(name, "artifact name")
        if len(set(names)) != len(names) or self.completion_name in names:
            raise PlanError("publication plan contains duplicate names")


@dataclass(frozen=True)
class PublicationResult:
    state: PublicationState
    attempt_id: str
    committed_artifacts: tuple[str, ...]
    completion_name: str


@dataclass(frozen=True)
class StartupResult:
    classification: StartupClassification
    failure_metadata_published: bool = False


def _validate_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
        raise ConfigurationError(f"{label} must be lowercase sha256:<64-hex>")


def _validate_attempt_id(value: str) -> None:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ConfigurationError("attempt ID must be exactly 32 lowercase hex characters")


def _validate_name(value: str, label: str = "managed filename") -> None:
    if (
        not isinstance(value, str)
        or _NAME_RE.fullmatch(value) is None
        or value in (".", "..", MARKER_NAME, STAGING_NAME)
        or Path(value).name != value
    ):
        raise ConfigurationError(f"{label} must be a simple managed basename")


def _validate_configuration(
    expected_lock_hash: str,
    expected_holdout_hash: str,
    dataset_kind: str,
    completion_filename: str,
    managed_artifact_names: Sequence[str],
) -> tuple[str, ...]:
    _validate_hash(expected_lock_hash, "lock hash")
    _validate_hash(expected_holdout_hash, "holdout hash")
    if dataset_kind not in _DATASET_KINDS:
        raise ConfigurationError("unsupported dataset kind")
    _validate_name(completion_filename, "completion filename")
    names = tuple(managed_artifact_names)
    if not names or completion_filename not in names:
        raise ConfigurationError("managed names must include completion filename")
    for name in names:
        _validate_name(name)
    if len(set(names)) != len(names):
        raise ConfigurationError("managed artifact names must be unique")
    return names


def _emit(hook: Optional[Hook], event: str) -> None:
    if hook is not None:
        hook(event)


def _around(hook: Optional[Hook], operation: str, action: Callable[[], object]) -> object:
    _emit(hook, f"before:{operation}")
    result = action()
    _emit(hook, f"after:{operation}")
    return result


def _transition(hook: Optional[Hook], state: PublicationState) -> None:
    _around(hook, f"transition:{state.value}", lambda: None)


def _is_link(path: Path) -> bool:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse and attributes & reparse)


def _safe_existing_root(root: os.PathLike[str] | str) -> Path:
    path = Path(root).absolute()
    if not path.exists() or not path.is_dir():
        raise UnsafePathError("publication root must be an existing directory")
    chain: list[Path] = []
    cursor = path
    while True:
        chain.append(cursor)
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    for component in reversed(chain):
        try:
            if _is_link(component):
                raise UnsafePathError("publication root has a symlink/reparse component")
        except OSError as exc:
            raise UnsafePathError("publication root component cannot be inspected") from exc
    return path


def _posix_directory_sync(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _default_device(path: Path) -> int:
    return path.stat(follow_symlinks=False).st_dev


@dataclass(frozen=True)
class _Filesystem:
    directory_sync: DirectorySync
    device: DeviceResolver


def _decode_mountinfo_path(value: str) -> str:
    return _MOUNTINFO_ESCAPE_RE.sub(lambda match: chr(int(match.group(1), 8)), value)


def _mount_filesystem_type(path: Path, mountinfo: str) -> Optional[str]:
    target = posixpath.abspath(os.fspath(path).replace("\\", "/"))
    matches: list[tuple[int, str]] = []
    for line in mountinfo.splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
            mount_point = _decode_mountinfo_path(fields[4])
            filesystem_type = fields[separator + 1].lower()
        except (IndexError, ValueError):
            continue
        if not posixpath.isabs(mount_point) or not filesystem_type:
            continue
        normalized_mount = posixpath.normpath(mount_point)
        try:
            contains = posixpath.commonpath((target, normalized_mount)) == normalized_mount
        except ValueError:
            contains = False
        if contains:
            matches.append((len(normalized_mount), filesystem_type))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def _require_pinned_linux_local_filesystem(root: Path) -> None:
    if sys.platform != "linux":
        raise DurabilityUnavailableError("production atomic publication requires Linux")
    try:
        mountinfo = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DurabilityUnavailableError("cannot determine publication filesystem type") from exc
    filesystem_type = _mount_filesystem_type(root, mountinfo)
    if filesystem_type is None:
        raise DurabilityUnavailableError("cannot determine publication filesystem type")
    if filesystem_type in _REMOTE_FILESYSTEM_TYPES:
        raise DurabilityUnavailableError(
            f"remote publication filesystem is unsupported: {filesystem_type}"
        )


def _filesystem(
    root: Path,
    test_directory_sync: Optional[DirectorySync],
    test_device_resolver: Optional[DeviceResolver],
) -> _Filesystem:
    injected = test_directory_sync is not None or test_device_resolver is not None
    if injected:
        if test_directory_sync is None or test_device_resolver is None:
            raise ConfigurationError("test durability injection requires both callbacks")
        return _Filesystem(test_directory_sync, test_device_resolver)
    _require_pinned_linux_local_filesystem(root)
    return _Filesystem(_posix_directory_sync, _default_device)


def _sync_file(fd: int, hook: Optional[Hook], label: str) -> None:
    _around(hook, f"file-sync:{label}", lambda: os.fsync(fd))


def _sync_directory(fs: _Filesystem, path: Path, hook: Optional[Hook], label: str) -> None:
    _around(hook, f"directory-sync:{label}", lambda: fs.directory_sync(path))


def _assert_same_device(fs: _Filesystem, root_device: int, path: Path) -> None:
    if fs.device(path) != root_device:
        raise CrossDeviceError(f"cross-device publication path rejected: {path.name}")


def _canonical_bytes(document: dict[str, object]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def _marker_document(
    lock_hash: str, holdout_hash: str, dataset_kind: str, attempt_id: str
) -> dict[str, object]:
    return {
        "schema_version": ATTEMPT_SCHEMA,
        "dataset_kind": dataset_kind,
        "lock_hash": lock_hash,
        "holdout_hash": holdout_hash,
        "attempt_id": attempt_id,
    }


def _open_exclusive(path: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    return os.open(path, flags, 0o600)


def _open_exclusive_hooked(path: Path, hook: Optional[Hook], label: str) -> int:
    _emit(hook, f"before:exclusive-create:{label}")
    fd = _open_exclusive(path)
    try:
        _emit(hook, f"after:exclusive-create:{label}")
    except BaseException:
        os.close(fd)
        raise
    return fd


class StagingWriter:
    """Exclusive, write-once byte writer restricted to configured names."""

    def __init__(
        self,
        staging: Path,
        managed_names: Iterable[str],
        fs: _Filesystem,
        root_device: int,
        hook: Optional[Hook],
    ) -> None:
        self._staging = staging
        self._managed = frozenset(managed_names)
        self._written: set[str] = set()
        self._fs = fs
        self._root_device = root_device
        self._hook = hook

    @property
    def written_names(self) -> frozenset[str]:
        return frozenset(self._written)

    @property
    def staging_path(self) -> Path:
        return self._staging

    def write(self, name: str, data: bytes) -> None:
        _validate_name(name)
        if name not in self._managed:
            raise StagingError("writer rejected unmanaged artifact name")
        if name in self._written:
            raise StagingError("writer rejected duplicate artifact name")
        if type(data) is not bytes:
            raise StagingError("staged artifacts must be opaque bytes")
        destination = self._staging / name
        try:
            fd = _open_exclusive_hooked(destination, self._hook, name)
        except FileExistsError as exc:
            raise StagingError("staging entry already exists") from exc
        try:
            _around(self._hook, f"write:{name}", lambda: _write_all(fd, data))
            _sync_file(fd, self._hook, name)
        finally:
            os.close(fd)
        info = destination.lstat()
        if _is_link(destination) or not stat.S_ISREG(info.st_mode):
            raise StagingError("staged artifact is not a regular file")
        _assert_same_device(self._fs, self._root_device, destination)
        _sync_directory(self._fs, self._staging, self._hook, "staging")
        self._written.add(name)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            raise OSError("short artifact write")
        view = view[count:]


def _verify_callback(
    hook: Optional[Hook], label: str, callback: Callable[..., object], *args: object
) -> None:
    result = _around(hook, f"verification:{label}", lambda: callback(*args))
    if result is not True:
        raise VerificationError(f"{label} verification rejected publication")


def _validate_plan(
    plan: object,
    configured_names: tuple[str, ...],
    completion_filename: str,
    written_names: frozenset[str],
) -> PublicationPlan:
    if not isinstance(plan, PublicationPlan):
        raise PlanError("producer must return PublicationPlan")
    if plan.completion_name != completion_filename:
        raise PlanError("plan completion does not match configured completion")
    planned = plan.artifact_names + (plan.completion_name,)
    if set(planned) != set(configured_names) or len(planned) != len(configured_names):
        raise PlanError("plan must name exactly the configured managed artifacts")
    if written_names != set(configured_names):
        raise PlanError("producer must write every configured managed artifact exactly once")
    return plan


def execute(
    *,
    root: os.PathLike[str] | str,
    expected_lock_hash: str,
    expected_holdout_hash: str,
    dataset_kind: str,
    completion_filename: str,
    managed_artifact_names: Sequence[str],
    lock_verifier: Callable[[str, str, str], object],
    producer: Callable[[StagingWriter], PublicationPlan],
    staging_verifier: Callable[[Path, PublicationPlan], object],
    completion_validator: Callable[[Path], object],
    hook: Optional[Hook] = None,
    attempt_id_factory: Callable[[], str] = lambda: secrets.token_hex(16),
    test_directory_sync: Optional[DirectorySync] = None,
    test_device_resolver: Optional[DeviceResolver] = None,
) -> PublicationResult:
    """Consume one attempt and atomically publish a fully verified artifact set."""
    names = _validate_configuration(
        expected_lock_hash,
        expected_holdout_hash,
        dataset_kind,
        completion_filename,
        managed_artifact_names,
    )
    root_path = _safe_existing_root(root)
    fs = _filesystem(root_path, test_directory_sync, test_device_resolver)
    root_device = fs.device(root_path)
    marker = root_path / MARKER_NAME
    if marker.exists() or marker.is_symlink():
        raise AttemptConsumedError("attempt marker already exists")
    for name in names:
        candidate = root_path / name
        if candidate.exists() or candidate.is_symlink():
            raise UnsafePathError("dedicated publication root contains a managed final")

    _verify_callback(
        hook,
        "lock-initial",
        lock_verifier,
        expected_lock_hash,
        expected_holdout_hash,
        dataset_kind,
    )
    _transition(hook, PublicationState.LOCK_VERIFIED)
    attempt_id = attempt_id_factory()
    _validate_attempt_id(attempt_id)
    marker_bytes = _canonical_bytes(
        _marker_document(expected_lock_hash, expected_holdout_hash, dataset_kind, attempt_id)
    )
    try:
        marker_fd = _open_exclusive_hooked(marker, hook, MARKER_NAME)
    except FileExistsError as exc:
        raise AttemptConsumedError("attempt marker already exists") from exc
    try:
        _around(hook, f"write:{MARKER_NAME}", lambda: _write_all(marker_fd, marker_bytes))
        _sync_file(marker_fd, hook, MARKER_NAME)
    finally:
        os.close(marker_fd)
    _assert_same_device(fs, root_device, marker)
    _sync_directory(fs, root_path, hook, "root")
    _transition(hook, PublicationState.ATTEMPT_CONSUMED)

    staging = root_path / STAGING_NAME
    try:
        _around(hook, f"staging-create:{STAGING_NAME}", lambda: staging.mkdir(mode=0o700))
    except FileExistsError as exc:
        raise StagingError("residual staging exists after attempt consumption") from exc
    _assert_same_device(fs, root_device, staging)
    _sync_directory(fs, root_path, hook, "root")
    _transition(hook, PublicationState.STAGING)
    writer = StagingWriter(staging, names, fs, root_device, hook)
    produced_plan = _around(hook, "producer-execution", lambda: producer(writer))
    plan = _around(
        hook,
        "plan-validation",
        lambda: _validate_plan(
            produced_plan, names, completion_filename, writer.written_names
        ),
    )
    assert isinstance(plan, PublicationPlan)
    _verify_callback(hook, "staging", staging_verifier, staging, plan)
    _verify_callback(
        hook, "completion-staged", completion_validator, staging / completion_filename
    )
    _transition(hook, PublicationState.STAGING_VERIFIED)
    _verify_callback(
        hook,
        "lock-final",
        lock_verifier,
        expected_lock_hash,
        expected_holdout_hash,
        dataset_kind,
    )
    _transition(hook, PublicationState.LOCK_REVERIFIED)

    for name in plan.artifact_names:
        _commit_one(staging, root_path, name, fs, root_device, hook, False)
    _transition(hook, PublicationState.ARTIFACTS_COMMITTED)
    _commit_one(
        staging, root_path, plan.completion_name, fs, root_device, hook, True
    )
    _transition(hook, PublicationState.COMPLETION_PUBLISHED)
    return PublicationResult(
        PublicationState.COMPLETION_PUBLISHED,
        attempt_id,
        plan.artifact_names,
        plan.completion_name,
    )


def _commit_one(
    staging: Path,
    root: Path,
    name: str,
    fs: _Filesystem,
    root_device: int,
    hook: Optional[Hook],
    completion: bool,
) -> None:
    source = staging / name
    destination = root / name
    info = source.lstat()
    if _is_link(source) or not stat.S_ISREG(info.st_mode):
        raise StagingError("commit source is not a regular file")
    _assert_same_device(fs, root_device, source)
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise UnsafePathError("final destination cannot be safely inspected") from exc
    else:
        raise UnsafePathError("final destination already exists")
    prefix = "completion-publication" if completion else "artifact-publication"
    _emit(hook, f"before:{prefix}:{name}")
    _around(hook, f"rename:{name}", lambda: os.replace(source, destination))
    _assert_same_device(fs, root_device, destination)
    fd = os.open(
        destination,
        os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0),
    )
    try:
        _sync_file(fd, hook, name)
    finally:
        os.close(fd)
    _sync_directory(fs, root, hook, "root")
    _emit(hook, f"after:{prefix}:{name}")


def _strict_json_bytes(path: Path) -> tuple[dict[str, object], bytes]:
    try:
        initial = path.lstat()
    except OSError:
        raise
    if _is_link(path) or not stat.S_ISREG(initial.st_mode):
        raise ValueError("JSON input is not a regular non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != initial.st_dev
            or opened.st_ino != initial.st_ino
        ):
            raise ValueError("JSON input changed during no-follow open")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ValueError("non-canonical final LF")
    text = raw.decode("utf-8", errors="strict")

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict) or _canonical_bytes(value) != raw:
        raise ValueError("non-canonical JSON")
    return value, raw


def _read_canonical_marker(path: Path) -> Optional[dict[str, object]]:
    try:
        document, _ = _strict_json_bytes(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return None
    if set(document) != {
        "schema_version",
        "dataset_kind",
        "lock_hash",
        "holdout_hash",
        "attempt_id",
    }:
        return None
    if document.get("schema_version") != ATTEMPT_SCHEMA:
        return None
    try:
        _validate_hash(document.get("lock_hash"), "lock hash")  # type: ignore[arg-type]
        _validate_hash(document.get("holdout_hash"), "holdout hash")  # type: ignore[arg-type]
        _validate_attempt_id(document.get("attempt_id"))  # type: ignore[arg-type]
    except ConfigurationError:
        return None
    if document.get("dataset_kind") not in _DATASET_KINDS:
        return None
    return document


def _regular_non_symlink(path: Path) -> bool:
    try:
        info = path.lstat()
        return not _is_link(path) and stat.S_ISREG(info.st_mode)
    except OSError:
        return False


def _cleanup_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _remove_entry_without_reading(
    path: Path, root: Path, fs: _Filesystem, hook: Optional[Hook]
) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISDIR(info.st_mode) and not _is_link(path):
        with os.scandir(path) as entries:
            children = sorted((Path(entry.path) for entry in entries), key=lambda child: child.name)
        for child in children:
            _remove_entry_without_reading(child, root, fs, hook)
        _sync_directory(fs, path, hook, f"cleanup-directory:{_cleanup_label(path, root)}")
        _around(
            hook,
            f"cleanup-rmdir:{_cleanup_label(path, root)}",
            path.rmdir,
        )
    else:
        _around(
            hook,
            f"cleanup-unlink:{_cleanup_label(path, root)}",
            path.unlink,
        )
    _sync_directory(
        fs,
        path.parent,
        hook,
        f"cleanup-parent:{_cleanup_label(path.parent, root) or '.'}",
    )


def _failure_document(
    dataset_kind: str, lock_hash: str, holdout_hash: str, attempt_id: str
) -> dict[str, object]:
    return {
        "schema_version": FAILURE_SCHEMA,
        "dataset_kind": dataset_kind,
        "lock_hash": lock_hash,
        "holdout_hash": holdout_hash,
        "attempt_id": attempt_id,
        "stage": "completion-publication",
        "reason_code": "interrupted",
        "message": _SAFE_FAILURE_MESSAGE,
    }


def _valid_failure_document(
    path: Path,
    dataset_kind: str,
    lock_hash: str,
    holdout_hash: str,
    attempt_id: str,
) -> bool:
    try:
        document, _ = _strict_json_bytes(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return False
    return document == _failure_document(
        dataset_kind, lock_hash, holdout_hash, attempt_id
    )


def startup_recover(
    *,
    root: os.PathLike[str] | str,
    expected_lock_hash: str,
    expected_holdout_hash: str,
    dataset_kind: str,
    expected_attempt_id: Optional[str],
    completion_filename: str,
    managed_artifact_names: Sequence[str],
    failure_filename: Optional[str] = None,
    completion_validator: Optional[Callable[[Path], object]] = None,
    hook: Optional[Hook] = None,
    test_directory_sync: Optional[DirectorySync] = None,
    test_device_resolver: Optional[DeviceResolver] = None,
) -> StartupResult:
    """Classify startup and invalidate incomplete state without outcome reads.

    Managed partial finals and residual staging are removed by name/type only.
    Completion is accepted only when both the closed marker and final file pass
    their structural checks and the caller's validator returns exactly True.
    """
    names = _validate_configuration(
        expected_lock_hash,
        expected_holdout_hash,
        dataset_kind,
        completion_filename,
        managed_artifact_names,
    )
    if expected_attempt_id is not None:
        _validate_attempt_id(expected_attempt_id)
    if failure_filename is not None:
        _validate_name(failure_filename, "failure filename")
        if failure_filename == completion_filename:
            raise ConfigurationError("failure filename cannot be completion filename")
        if failure_filename not in names:
            raise ConfigurationError("failure filename must be a configured managed name")
    root_path = _safe_existing_root(root)
    fs = _filesystem(root_path, test_directory_sync, test_device_resolver)
    root_device = fs.device(root_path)
    marker_path = root_path / MARKER_NAME
    try:
        marker_path.lstat()
    except FileNotFoundError:
        return StartupResult(StartupClassification.FRESH)

    marker = _read_canonical_marker(marker_path)
    marker_matches = (
        marker is not None
        and marker.get("lock_hash") == expected_lock_hash
        and marker.get("holdout_hash") == expected_holdout_hash
        and marker.get("dataset_kind") == dataset_kind
        and (
            expected_attempt_id is None
            or marker.get("attempt_id") == expected_attempt_id
        )
    )

    marker_attempt_id = marker.get("attempt_id") if marker_matches and marker else None
    failure_path = root_path / failure_filename if failure_filename is not None else None
    failure_present = False
    if failure_path is not None:
        try:
            failure_path.lstat()
            failure_present = True
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise UnsafePathError("failure metadata cannot be safely inspected") from exc
    existing_failure_valid = bool(
        marker_matches
        and isinstance(marker_attempt_id, str)
        and failure_path is not None
        and _valid_failure_document(
            failure_path,
            dataset_kind,
            expected_lock_hash,
            expected_holdout_hash,
            marker_attempt_id,
        )
    )

    completion_path = root_path / completion_filename
    valid_completion = False
    if (
        marker_matches
        and not failure_present
        and completion_validator is not None
        and _regular_non_symlink(completion_path)
    ):
        try:
            result = _around(
                hook,
                "verification:completion-final",
                lambda: completion_validator(completion_path),
            )
            valid_completion = result is True and _regular_non_symlink(completion_path)
        except Exception:
            valid_completion = False
    if valid_completion:
        _assert_same_device(fs, root_device, marker_path)
        _assert_same_device(fs, root_device, completion_path)
        return StartupResult(StartupClassification.COMPLETED)

    staging = root_path / STAGING_NAME
    _remove_entry_without_reading(staging, root_path, fs, hook)
    for name in names:
        if failure_filename is not None and name == failure_filename and existing_failure_valid:
            continue
        _remove_entry_without_reading(root_path / name, root_path, fs, hook)
    _sync_directory(fs, root_path, hook, "root")

    published = False
    if (
        marker_matches
        and isinstance(marker_attempt_id, str)
        and failure_path is not None
        and not existing_failure_valid
    ):
        payload = _canonical_bytes(
            _failure_document(
                dataset_kind,
                expected_lock_hash,
                expected_holdout_hash,
                marker_attempt_id,
            )
        )
        fd = _open_exclusive_hooked(failure_path, hook, failure_filename)
        try:
            _around(hook, f"write:{failure_filename}", lambda: _write_all(fd, payload))
            _sync_file(fd, hook, failure_filename)
        finally:
            os.close(fd)
        _assert_same_device(fs, root_device, failure_path)
        _sync_directory(fs, root_path, hook, "root")
        published = True
    return StartupResult(StartupClassification.CONSUMED_INCOMPLETE, published)


__all__ = [
    "AtomicPublicationError",
    "AttemptConsumedError",
    "ConfigurationError",
    "CrossDeviceError",
    "DurabilityUnavailableError",
    "PlanError",
    "PublicationPlan",
    "PublicationResult",
    "PublicationState",
    "StagingError",
    "StagingWriter",
    "StartupClassification",
    "StartupResult",
    "UnsafePathError",
    "VerificationError",
    "execute",
    "startup_recover",
]
