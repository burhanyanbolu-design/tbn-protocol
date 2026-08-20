#!/usr/bin/env python3
"""Acquire the frozen Stage Sixteen corpus with bounded allowlisted HTTPS."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 30 * 1024 * 1024
TIMEOUT_SECONDS = 30
USER_AGENT = "Stage16ConfirmationAcquirer/1.0"
ALLOWED_HOSTS = frozenset({"www.rfc-editor.org"})
RIGHTS_URL = "https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/"
ARTIFACTS: tuple[dict[str, str], ...] = (
    {"artifact_id": "rfc791", "title": "Internet Protocol", "publisher": "RFC Editor", "version": "RFC 791", "url": "https://www.rfc-editor.org/rfc/rfc791.txt", "raw_file": "rfc791.txt", "rights_url": RIGHTS_URL},
    {"artifact_id": "rfc2131", "title": "Dynamic Host Configuration Protocol", "publisher": "RFC Editor", "version": "RFC 2131", "url": "https://www.rfc-editor.org/rfc/rfc2131.txt", "raw_file": "rfc2131.txt", "rights_url": RIGHTS_URL},
    {"artifact_id": "rfc5849", "title": "The OAuth 1.0 Protocol", "publisher": "RFC Editor", "version": "RFC 5849", "url": "https://www.rfc-editor.org/rfc/rfc5849.txt", "raw_file": "rfc5849.txt", "rights_url": RIGHTS_URL},
    {"artifact_id": "rfc6376", "title": "DomainKeys Identified Mail (DKIM) Signatures", "publisher": "RFC Editor", "version": "RFC 6376", "url": "https://www.rfc-editor.org/rfc/rfc6376.txt", "raw_file": "rfc6376.txt", "rights_url": RIGHTS_URL},
    {"artifact_id": "rfc7230", "title": "Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing", "publisher": "RFC Editor", "version": "RFC 7230", "url": "https://www.rfc-editor.org/rfc/rfc7230.txt", "raw_file": "rfc7230.txt", "rights_url": RIGHTS_URL},
    {"artifact_id": "rfc3261", "title": "SIP: Session Initiation Protocol", "publisher": "RFC Editor", "version": "RFC 3261", "url": "https://www.rfc-editor.org/rfc/rfc3261.txt", "raw_file": "rfc3261.txt", "rights_url": RIGHTS_URL},
)

def validate_source_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"refusing non-HTTPS or non-allowlisted source URL: {url}")
    if parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError(f"refusing source URL with query, fragment, credentials, or nonstandard port: {url}")


def validate_rights_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"invalid HTTPS rights URL: {url}")
    if parsed.port not in (None, 443):
        raise ValueError(f"invalid rights URL port: {url}")


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> urllib.request.Request | None:
        absolute = urllib.parse.urljoin(req.full_url, newurl)
        validate_source_url(absolute)
        return super().redirect_request(req, fp, code, msg, headers, absolute)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def acquisition_plan() -> dict[str, Any]:
    if len(ARTIFACTS) != 6:
        raise AssertionError("the frozen corpus must contain exactly six artifacts")
    for field in ("artifact_id", "url", "raw_file"):
        values = [item[field] for item in ARTIFACTS]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field} in acquisition specification")
    for item in ARTIFACTS:
        validate_source_url(item["url"])
        validate_rights_url(item["rights_url"])
        if Path(item["raw_file"]).name != item["raw_file"]:
            raise ValueError(f"unsafe raw filename: {item['raw_file']!r}")
        if not item["raw_file"].endswith(".txt"):
            raise ValueError(f"frozen source extension mismatch: {item['artifact_id']}")
    return {
        "artifact_count": 6,
        "allowed_hosts": sorted(ALLOWED_HOSTS),
        "https_only": True,
        "max_bytes_per_artifact": MAX_BYTES,
        "max_total_bytes": MAX_TOTAL_BYTES,
        "timeout_seconds": TIMEOUT_SECONDS,
        "sequential": True,
        "content_types": {"txt": "text/plain", "html": "text/html"},
        "artifacts": [{key: item[key] for key in ("artifact_id", "url", "raw_file")} for item in ARTIFACTS],
    }


def download(opener: urllib.request.OpenerDirector, url: str) -> tuple[bytes, str, str]:
    validate_source_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        retrieved_url = response.geturl()
        validate_source_url(retrieved_url)
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > MAX_BYTES:
            raise ValueError(f"content exceeds {MAX_BYTES} bytes: {url}")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = response.read(min(65536, MAX_BYTES + 1 - total))
            if not block:
                break
            blocks.append(block); total += len(block)
            if total > MAX_BYTES:
                raise ValueError(f"content exceeds {MAX_BYTES} bytes: {url}")
        content = b"".join(blocks)
        if not content:
            raise ValueError(f"empty response: {url}")
        return content, retrieved_url, response.headers.get_content_type().lower()


def acquire(output_dir: Path) -> dict[str, Any]:
    acquisition_plan()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Stage Sixteen acquisition directory is not empty; a second attempt is forbidden")
    output_dir.mkdir(parents=True, exist_ok=True)
    completion = output_dir / "acquisition-manifest.json"
    opener = urllib.request.build_opener(AllowlistedRedirectHandler())
    acquired: list[dict[str, Any]] = []
    total = 0
    for item in ARTIFACTS:
        content, retrieved_url, media_type = download(opener, item["url"])
        expected_type = "text/plain" if item["raw_file"].endswith(".txt") else "text/html"
        if media_type != expected_type:
            raise ValueError(f"unexpected media type for {item['artifact_id']}: {media_type!r}, expected {expected_type!r}")
        total += len(content)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("corpus exceeds 30 MiB total byte ceiling")
        digest = hashlib.sha256(content).hexdigest()
        atomic_write(output_dir / "raw" / item["raw_file"], content)
        acquired.append({
            **item, "retrieved_url": retrieved_url, "media_type": media_type,
            "byte_size": len(content), "sha256": digest,
            "retrieval_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        })
        print(f"{item['artifact_id']} bytes={len(content)} sha256={digest}")
    manifest = {
        "schema_version": 1, "stage": 16, "state": "complete",
        "transport": {
            "allowed_hosts": sorted(ALLOWED_HOSTS), "https_only": True,
            "max_bytes_per_artifact": MAX_BYTES, "max_total_bytes": MAX_TOTAL_BYTES,
            "timeout_seconds": TIMEOUT_SECONDS, "user_agent": USER_AGENT,
            "sequential": True, "content_types": {"txt": "text/plain", "html": "text/html"},
        },
        "artifact_count": len(acquired), "total_bytes": total, "artifacts": acquired,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    atomic_write(completion, encoded)  # completion marker is deliberately written last
    print(f"acquisition-complete bytes={total} manifest_sha256={hashlib.sha256(encoded).hexdigest()}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="print the frozen plan without network access or writes")
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(acquisition_plan(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        acquire((Path(__file__).resolve().parent / "stage16-corpus").resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
