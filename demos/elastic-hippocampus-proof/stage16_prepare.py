#!/usr/bin/env python3
"""Verify and prepare Stage Sixteen offline; create no adjudication artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from stage16_acquire import (
    ALLOWED_HOSTS, ARTIFACTS, MAX_BYTES, MAX_TOTAL_BYTES, TIMEOUT_SECONDS,
    USER_AGENT, validate_source_url,
)

MAX_TOKENS = 320
OVERLAP_TOKENS = 40
RESOURCE_LIMITS = {
    "max_total_raw_bytes": 30 * 1024 * 1024,
    "max_chunks": 20_000,
    "max_analyzed_terms": 5_000_000,
    "max_features": 250_000,
    "max_sparse_matrix_bytes": 512 * 1024 * 1024,
    "max_lsa_working_bytes": 512 * 1024 * 1024,
}
QUERIES: tuple[dict[str, str], ...] = (
    {"query_id":"q01","kind":"positive","artifact_id":"rfc791","query":"What fields make up the IPv4 header, and what do the Total Length, Identification, and Time to Live fields represent?"},
    {"query_id":"q02","kind":"positive","artifact_id":"rfc791","query":"How does IP fragmentation use the Identification, Flags, and Fragment Offset fields to allow reassembly at the destination?"},
    {"query_id":"q03","kind":"positive","artifact_id":"rfc791","query":"How does the Time to Live field limit a datagram's lifetime, and what must a gateway do when it decrements TTL to zero?"},
    {"query_id":"q04","kind":"positive","artifact_id":"rfc2131","query":"What sequence of DHCPDISCOVER, DHCPOFFER, DHCPREQUEST, and DHCPACK messages makes up the DHCP DORA lease-allocation process?"},
    {"query_id":"q05","kind":"positive","artifact_id":"rfc2131","query":"Which client lease states does a DHCP client cycle through, and what triggers transitions among INIT, SELECTING, REQUESTING, BOUND, RENEWING, and REBINDING?"},
    {"query_id":"q06","kind":"positive","artifact_id":"rfc2131","query":"How do the T1 and T2 timers derived from a DHCP lease duration determine when a client attempts renewal or rebinding?"},
    {"query_id":"q07","kind":"positive","artifact_id":"rfc5849","query":"How is the OAuth 1.0 signature base string constructed from the HTTP method, base URI, and normalized request parameters?"},
    {"query_id":"q08","kind":"positive","artifact_id":"rfc5849","query":"How does the HMAC-SHA1 signature method combine the client shared secret and token secret to sign an OAuth 1.0 request?"},
    {"query_id":"q09","kind":"positive","artifact_id":"rfc5849","query":"What role do the oauth_nonce and oauth_timestamp parameters play in preventing replay of an OAuth 1.0 signed request?"},
    {"query_id":"q10","kind":"positive","artifact_id":"rfc6376","query":"Which tags in a DKIM-Signature header field identify the signing domain, selector, and signed header list?"},
    {"query_id":"q11","kind":"positive","artifact_id":"rfc6376","query":"How do the simple and relaxed canonicalization algorithms normalize header and body content before DKIM signing?"},
    {"query_id":"q12","kind":"positive","artifact_id":"rfc6376","query":"How does a DKIM verifier use the selector record published in DNS to retrieve the public key for signature validation?"},
    {"query_id":"q13","kind":"positive","artifact_id":"rfc7230","query":"How does a recipient distinguish framing that uses Content-Length from framing that uses chunked transfer coding when parsing an HTTP/1.1 message?"},
    {"query_id":"q14","kind":"positive","artifact_id":"rfc7230","query":"How is a chunked transfer coded body terminated, and what rules govern the chunk-size line that begins each chunk?"},
    {"query_id":"q15","kind":"positive","artifact_id":"rfc3261","query":"Which SIP headers, including Via, To, From, Call-ID, and CSeq, must appear in a request that establishes a new dialog?"},
    {"query_id":"q16","kind":"positive","artifact_id":"rfc3261","query":"How does an INVITE transaction combined with an ACK request establish a SIP dialog between a user agent client and server?"},
    {"query_id":"q17","kind":"control","artifact_id":"","query":"Which cyclin-CDK complex triggers the G1/S checkpoint transition in the eukaryotic cell cycle?"},
    {"query_id":"q18","kind":"control","artifact_id":"","query":"What mineral phase transition marks the boundary between the upper and lower mantle at roughly 660 km depth?"},
    {"query_id":"q19","kind":"control","artifact_id":"","query":"How does the Chandrasekhar limit constrain the maximum mass of a stable white dwarf star?"},
    {"query_id":"q20","kind":"control","artifact_id":"","query":"What condition defines a trembling-hand perfect equilibrium in an extensive-form game?"},
)

@dataclass(frozen=True)
class Section:
    heading: str
    text: str


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def atomic_json(path: Path, value: Any) -> str:
    encoded = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True); raise
    return hashlib.sha256(encoded).hexdigest()


class VisibleHTMLParser(HTMLParser):
    SKIP = frozenset({"script", "style", "nav", "header", "footer", "aside", "noscript", "svg", "form"})
    BLOCK = frozenset({"p", "li", "pre", "blockquote", "dt", "dd", "tr", "td", "th", "div", "section", "article", "br"})
    VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})
    def __init__(self, fallback: str) -> None:
        super().__init__(convert_charrefs=True)
        self.fallback = fallback; self.body = False; self.skip = 0; self.level: int | None = None
        self.heading_parts: list[str] = []; self.stack: list[tuple[int, str]] = []
        self.parts: list[str] = []; self.sections: list[Section] = []
    def breadcrumb(self) -> str:
        return " > ".join(text for _, text in self.stack) or self.fallback
    def flush(self) -> None:
        text = normalize(" ".join(self.parts)); self.parts = []
        if text: self.sections.append(Section(self.breadcrumb(), text))
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs; tag = tag.lower()
        if tag == "body": self.body = True; return
        if not self.body: return
        if self.skip:
            if tag not in self.VOID: self.skip += 1
            return
        if tag in self.SKIP: self.skip = 1; return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.flush(); self.level = int(tag[1]); self.heading_parts = []
        elif tag in self.BLOCK: self.parts.append(" ")
    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.body: return
        if self.skip: self.skip -= 1; return
        if self.level is not None and tag == f"h{self.level}":
            heading = normalize(" ".join(self.heading_parts)); level = self.level
            self.stack = [item for item in self.stack if item[0] < level]
            if heading: self.stack.append((level, heading))
            self.level = None; self.heading_parts = []
        elif tag in self.BLOCK: self.parts.append(" ")
        if tag == "body": self.flush(); self.body = False
    def handle_data(self, data: str) -> None:
        if self.body and not self.skip:
            (self.heading_parts if self.level is not None else self.parts).append(data)
    def close(self) -> None:
        super().close(); self.flush()


RFC_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?[ \t]{1,3}(\S.*)$")

def parse_rfc(content: bytes) -> list[Section]:
    sections: list[Section] = []; heading = ""; lines: list[str] = []; titles: dict[str, str] = {}
    for line in unicodedata.normalize("NFC", content.decode("utf-8-sig")).splitlines():
        match = RFC_HEADING.match(line.rstrip())
        if match:
            body = normalize("\n".join(lines))
            if heading and body: sections.append(Section(heading, body))
            number, title = match.group(1), normalize(match.group(2)); titles[number] = title
            parts = number.split(".")
            heading = " > ".join(f"{p} {titles[p]}" for p in (".".join(parts[:i]) for i in range(1, len(parts) + 1)) if p in titles)
            lines = []
        elif heading: lines.append(line)
    body = normalize("\n".join(lines))
    if heading and body: sections.append(Section(heading, body))
    if not sections: raise ValueError("RFC input contains no numbered sections")
    return sections


def parse_html(content: bytes, title: str) -> list[Section]:
    parser = VisibleHTMLParser(title); parser.feed(content.decode("utf-8-sig")); parser.close()
    if not parser.sections: raise ValueError("HTML input contains no visible sections")
    return parser.sections

def load_and_verify(corpus_dir: Path) -> tuple[dict[str, Any], list[tuple[dict[str, Any], bytes]], str]:
    manifest_path = corpus_dir / "acquisition-manifest.json"; raw = manifest_path.read_bytes(); manifest = json.loads(raw)
    if manifest.get("schema_version") != 1 or manifest.get("stage") != 16 or manifest.get("state") != "complete":
        raise ValueError("incomplete Stage Sixteen acquisition manifest")
    expected_transport = {
        "allowed_hosts": sorted(ALLOWED_HOSTS),
        "https_only": True, "max_bytes_per_artifact": MAX_BYTES, "max_total_bytes": MAX_TOTAL_BYTES,
        "timeout_seconds": TIMEOUT_SECONDS, "user_agent": USER_AGENT, "sequential": True,
        "content_types": {"txt": "text/plain", "html": "text/html"},
    }
    if manifest.get("transport") != expected_transport: raise ValueError("frozen transport mismatch")
    expected = {item["artifact_id"]: item for item in ARTIFACTS}; artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or {item.get("artifact_id") for item in artifacts} != set(expected):
        raise ValueError("frozen artifact set mismatch")
    verified: list[tuple[dict[str, Any], bytes]] = []
    for artifact in artifacts:
        specification = expected[artifact["artifact_id"]]
        for field in ("title", "publisher", "version", "url", "raw_file", "rights_url"):
            if artifact.get(field) != specification[field]: raise ValueError(f"{artifact['artifact_id']} unexpected {field}")
        validate_source_url(artifact["url"]); validate_source_url(artifact["retrieved_url"])
        expected_type = "text/plain" if artifact["raw_file"].endswith(".txt") else "text/html"
        if artifact.get("media_type") != expected_type: raise ValueError(f"media type mismatch: {artifact['artifact_id']}")
        name = artifact["raw_file"]
        if Path(name).name != name: raise ValueError("unsafe raw filename")
        content = (corpus_dir / "raw" / name).read_bytes(); digest = hashlib.sha256(content).hexdigest()
        if not content or len(content) != artifact.get("byte_size") or digest != artifact.get("sha256"):
            raise ValueError(f"raw hash/size mismatch: {artifact['artifact_id']}")
        if len(content) > MAX_BYTES: raise ValueError("per-artifact ceiling exceeded")
        verified.append((artifact, content))
    total = sum(len(content) for _, content in verified)
    if manifest.get("artifact_count") != 6 or total != manifest.get("total_bytes") or total > MAX_TOTAL_BYTES:
        raise ValueError("artifact count or total byte binding failure")
    files = {path.name for path in (corpus_dir / "raw").iterdir() if path.is_file() and not path.name.startswith(".")}
    if files != {item["raw_file"] for item in ARTIFACTS}: raise ValueError("raw directory has missing or unexpected files")
    return manifest, verified, hashlib.sha256(raw).hexdigest()


def chunk_sections(verified: list[tuple[dict[str, Any], bytes]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for artifact, content in verified:
        sections = parse_rfc(content) if artifact["raw_file"].endswith(".txt") else parse_html(content, artifact["title"])
        for section in sections:
            tokens = section.text.split(); start = 0; ordinal = 1
            while start < len(tokens):
                end = min(start + MAX_TOKENS, len(tokens)); text = normalize(" ".join(tokens[start:end])); digest = hashlib.sha256(text.encode()).hexdigest()
                chunks.append({
                    "chunk_id": f"{artifact['artifact_id']}|{section.heading}|{ordinal}|{digest}",
                    "artifact_id": artifact["artifact_id"],
                    "source": {key: artifact[key] for key in ("title", "publisher", "version", "url", "retrieved_url", "media_type", "byte_size", "sha256", "retrieval_utc", "rights_url", "raw_file")},
                    "heading": section.heading, "ordinal": ordinal, "text": text,
                    "token_count": end - start, "text_sha256": digest,
                    "previous_chunk_id": None, "next_chunk_id": None,
                })
                if end == len(tokens): break
                start = end - OVERLAP_TOKENS; ordinal += 1
    ids = [chunk["chunk_id"] for chunk in chunks]
    if not chunks or len(ids) != len(set(ids)): raise ValueError("empty corpus or duplicate chunk IDs")
    for index, chunk in enumerate(chunks):
        if index and chunks[index - 1]["artifact_id"] == chunk["artifact_id"]:
            chunk["previous_chunk_id"] = chunks[index - 1]["chunk_id"]
        if index + 1 < len(chunks) and chunks[index + 1]["artifact_id"] == chunk["artifact_id"]:
            chunk["next_chunk_id"] = chunks[index + 1]["chunk_id"]
    return chunks


def add_merkle_hashes(chunks: list[dict[str, Any]]) -> str:
    level: list[bytes] = []
    for chunk in chunks:
        leaf = canonical_hash(chunk); chunk["merkle_leaf_sha256"] = leaf; level.append(bytes.fromhex(leaf))
    while len(level) > 1:
        if len(level) % 2: level.append(level[-1])
        level = [hashlib.sha256(level[index] + level[index + 1]).digest() for index in range(0, len(level), 2)]
    return level[0].hex()


def resource_preflight(verified: list[tuple[dict[str, Any], bytes]], chunks: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as error:
        raise RuntimeError("locally installed scikit-learn is required; preparation is offline") from error
    if len(chunks) > RESOURCE_LIMITS["max_chunks"]: raise ValueError("chunk ceiling exceeded")
    vectorizer = TfidfVectorizer(analyzer="word", lowercase=True, norm="l2", smooth_idf=True, sublinear_tf=False, token_pattern=r"(?u)\b\w\w+\b", use_idf=True)
    analyzer = vectorizer.build_analyzer(); analyzed_terms = 0; features: set[str] = set()
    for chunk in chunks:
        terms = analyzer(chunk["text"]); analyzed_terms += len(terms); features.update(terms)
        if analyzed_terms > RESOURCE_LIMITS["max_analyzed_terms"] or len(features) > RESOURCE_LIMITS["max_features"]:
            raise ValueError("analysis ceiling exceeded")
    rows = len(chunks); columns = len(features)
    if min(rows, columns) <= 64: raise ValueError("exactly 64 LSA components require both dimensions > 64")
    sparse = min(analyzed_terms, rows * columns) * 16 + (rows + 1) * 8
    working = (rows + columns) * 64 * 8 * 4 + sparse
    if sparse > RESOURCE_LIMITS["max_sparse_matrix_bytes"] or working > RESOURCE_LIMITS["max_lsa_working_bytes"]:
        raise ValueError("matrix working ceiling exceeded")
    return {
        "status": "PASS", "network_step": False, "artifact_count": len(verified),
        "total_raw_bytes": sum(len(content) for _, content in verified), "chunk_count": rows,
        "analyzed_terms": analyzed_terms, "tfidf_matrix_rows": rows, "tfidf_matrix_features": columns,
        "tfidf_matrix_dimensions": [rows, columns], "lsa_components": 64,
        "estimated_sparse_matrix_bytes_upper_bound": sparse,
        "estimated_lsa_working_bytes_upper_bound": working, "limits": dict(RESOURCE_LIMITS),
    }


def prepare(corpus_dir: Path, *, preflight_only: bool = False) -> None:
    if len(QUERIES) != 20 or sum(q["kind"] == "positive" for q in QUERIES) != 16 or sum(q["kind"] == "control" for q in QUERIES) != 4:
        raise AssertionError("query split drift")
    expected_assignments = (
        "rfc791", "rfc791", "rfc791", "rfc2131", "rfc2131", "rfc2131",
        "rfc5849", "rfc5849", "rfc5849", "rfc6376", "rfc6376", "rfc6376",
        "rfc7230", "rfc7230", "rfc3261", "rfc3261", "", "", "", "",
    )
    if tuple(q["artifact_id"] for q in QUERIES) != expected_assignments:
        raise AssertionError("frozen 3/3/3/3/2/2 artifact distribution drift")
    if [q["query_id"] for q in QUERIES] != [f"q{i:02d}" for i in range(1, 21)]: raise AssertionError("query IDs drift")
    query_hash = canonical_hash([q["query"] for q in QUERIES])
    _, verified, manifest_hash = load_and_verify(corpus_dir); chunks = chunk_sections(verified); preflight = resource_preflight(verified, chunks)
    print("resource-preflight " + json.dumps(preflight, sort_keys=True))
    if preflight_only: print("preflight-only: no preparation outputs written"); return
    if not 400 <= len(chunks) <= 2000:
        raise ValueError("chunk count outside frozen 400..2000 gate")
    outputs = tuple(corpus_dir / name for name in ("chunks.json", "runtime-inventory.json", "preparation-complete.json"))
    if any(path.exists() for path in outputs):
        raise FileExistsError("Stage Sixteen preparation output already exists; a second preparation is forbidden")
    completion = corpus_dir / "preparation-complete.json"
    root = add_merkle_hashes(chunks)
    config = {
        "offline": True, "network_step": False, "normalization": {"unicode": "NFC", "whitespace": "collapse"},
        "chunking": {"boundary": "artifact and heading", "max_tokens": MAX_TOKENS, "overlap_tokens": OVERLAP_TOKENS, "token_definition": "normalized whitespace", "chunk_id": "artifact_id|heading|ordinal|text SHA-256"},
        "merkle": {"hash": "SHA-256", "leaf": "canonical compact JSON before leaf field", "parent": "SHA-256(left || right)", "odd_level": "duplicate final digest"},
        "queries": list(QUERIES), "query_strings_sha256": query_hash,
        "preparation_candidates": False, "resource_preflight": preflight,
    }
    chunks_doc = {"schema_version": 1, "stage": 16, "acquisition_manifest_sha256": manifest_hash, "artifact_count": 6, "chunk_count": len(chunks), "corpus_merkle_root": root, "config": config, "chunks": chunks}
    import platform, numpy, sklearn
    runtime = {"schema_version": 1, "stage": 16, "python": platform.python_version(), "numpy": numpy.__version__, "sklearn": sklearn.__version__, "network_step": False, "candidate_generation": False, "resource_preflight": preflight, "confirmation": "Offline preparation reads only completed local acquisition and creates no adjudication or label artifact."}
    chunk_hash = atomic_json(corpus_dir / "chunks.json", chunks_doc); runtime_hash = atomic_json(corpus_dir / "runtime-inventory.json", runtime)
    marker = {"schema_version": 1, "stage": 16, "state": "complete", "acquisition_manifest_sha256": manifest_hash, "corpus_merkle_root": root, "outputs": {"chunks.json": chunk_hash, "runtime-inventory.json": runtime_hash}, "forbidden_outputs": ["adjudication-pool.json", "adjudication-review.json", "blind-label-proposal.json", "relevance-labels.json"]}
    marker_hash = atomic_json(completion, marker)  # completion marker written last
    print(f"artifacts=6 chunks={len(chunks)} queries=20 adjudication_outputs=0")
    print(f"query-strings {query_hash}"); print(f"corpus-merkle-root {root}"); print(f"preparation-complete {marker_hash}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    prepare((Path(__file__).resolve().parent / "stage16-corpus").resolve(), preflight_only=args.preflight_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
