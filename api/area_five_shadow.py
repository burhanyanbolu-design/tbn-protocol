"""Disposable Area Five candidate router for Hardin Memory.

This index is never authoritative. It stores opaque local token cells and
returns shard IDs plus routing traces. Hardin reauthorizes, reloads, verifies,
and ranks every candidate before any memory text is returned.
"""
import collections
import datetime
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import sqlite3
import threading

SCHEMA_VERSION = "area-five-shadow/1"
PROJECTION_VERSION = "hardin-area-five/2"
DEFAULT_ROOT = "data/memory_area_five"
MAX_CANDIDATES = 200
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def enabled(principal: dict = None) -> bool:
    """Whether the shadow router is armed for this caller.

    `AREA_FIVE_SHADOW_ENABLED=1` arms the router at process level.
    `AREA_FIVE_SHADOW_TENANTS`, when set to a comma-separated list of tenant
    IDs, additionally restricts it to exactly those tenants, so a pilot can be
    scoped to one tenant instead of every tenant on the instance. An unset or
    empty allowlist means every tenant, which is the original behaviour.

    Fails CLOSED: if an allowlist is configured but no principal is supplied,
    the router stays off rather than silently applying to an unknown caller.
    """
    if os.environ.get("AREA_FIVE_SHADOW_ENABLED", "0") != "1":
        return False
    allowlist = {entry.strip() for entry in
                 os.environ.get("AREA_FIVE_SHADOW_TENANTS", "").split(",")
                 if entry.strip()}
    if not allowlist:
        return True
    if not principal:
        return False
    return str(principal.get("tenant_id") or "") in allowlist


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _safe_tenant(principal: dict) -> str:
    tenant_id = str(principal.get("tenant_id") or "")
    if not re.fullmatch(r"ten_[A-Za-z0-9_-]{4,64}", tenant_id):
        raise ValueError("invalid Area Five tenant identity")
    return tenant_id


def index_path(principal: dict, root: str = None) -> str:
    return os.path.join(root or os.environ.get("AREA_FIVE_SHADOW_ROOT", DEFAULT_ROOT),
                        _safe_tenant(principal) + ".sqlite")

def _lock(path: str):
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(path, threading.RLock())


def _connect(path: str):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _create_schema(con):
    con.executescript("""
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE projected_shards(
      shard_id TEXT PRIMARY KEY, chain_index INTEGER UNIQUE NOT NULL,
      shard_hash TEXT NOT NULL, created TEXT NOT NULL,
      tenant_id TEXT NOT NULL, agent_id TEXT NOT NULL,
      store_scope TEXT NOT NULL, status TEXT NOT NULL, expires_at TEXT,
      poisoned INTEGER NOT NULL, private INTEGER NOT NULL,
      token_count INTEGER NOT NULL, projection_digest TEXT NOT NULL);
    CREATE TABLE postings(
      cell_id BLOB NOT NULL, shard_id TEXT NOT NULL, tf INTEGER NOT NULL,
      PRIMARY KEY(cell_id, shard_id));
    CREATE INDEX postings_cell_idx ON postings(cell_id);
    CREATE INDEX postings_shard_idx ON postings(shard_id);
    CREATE TABLE supersession(
      superseder_id TEXT NOT NULL, target_id TEXT NOT NULL,
      PRIMARY KEY(superseder_id, target_id));
    CREATE INDEX supersession_target_idx ON supersession(target_id);
    """)


def _tokens(text: str):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _cell(salt: bytes, token: str) -> bytes:
    return hmac.new(salt, token.encode(), hashlib.sha256).digest()


def _meta(con) -> dict:
    return {row["key"]: row["value"] for row in con.execute("SELECT key,value FROM meta")}


def _put_meta(con, values: dict):
    con.executemany("INSERT INTO meta(key,value) VALUES(?,?)",
                    [(key, str(value)) for key, value in values.items()])


def _principal_binding(principal: dict) -> dict:
    return {key: principal.get(key) for key in ("tenant_id", "agent_id", "store_scope")}


def _snapshot(authority_db: str, principal: dict,
              metadata_only: bool = False,
              legacy_store_approval=None) -> dict:
    try:
        from . import tbn_memory
    except Exception:
        from api import tbn_memory
    return tbn_memory.area_five_projection(
        db_path=authority_db, principal=principal, require_governance=True,
        metadata_only=metadata_only,
        legacy_store_approval=legacy_store_approval)


def _same_source(path: str, snapshot: dict, principal: dict) -> bool:
    if not os.path.exists(path):
        return False
    con = None
    try:
        con = _connect(path)
        meta = _meta(con)
    except Exception:
        return False
    finally:
        if con is not None:
            con.close()
    binding = _principal_binding(principal)
    return (meta.get("schema_version") == SCHEMA_VERSION
            and meta.get("projection_version") == PROJECTION_VERSION
            and meta.get("tenant_id") == str(binding["tenant_id"])
            and meta.get("agent_id") == str(binding["agent_id"])
            and meta.get("store_scope") == str(binding["store_scope"])
            and meta.get("source_head") == str(snapshot.get("head"))
            and meta.get("source_count") == str(snapshot.get("count"))
            and meta.get("legacy_compatibility_id")
            == str(snapshot.get("legacy_compatibility_id", "none")))


def rebuild(authority_db: str, principal: dict, root: str = None,
            snapshot: dict = None, legacy_store_approval=None) -> dict:
    """Atomically replace one tenant's disposable index from Hardin truth."""
    path = index_path(principal, root)
    snapshot = snapshot or _snapshot(
        authority_db, principal,
        legacy_store_approval=legacy_store_approval)
    if snapshot.get("error"):
        return {"status": "governance_error", "error_code": snapshot.get("error_code")}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    temp = f"{path}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    salt = secrets.token_bytes(32)
    generation = secrets.token_hex(16)
    try:
        con = _connect(temp)
        _create_schema(con)
        con.execute("BEGIN")
        for row in snapshot.get("records", []):
            counts = collections.Counter(_tokens(row.pop("text", "")))
            digest_input = {**row, "cells": sorted(
                (hashlib.sha256(_cell(salt, token)).hexdigest(), tf)
                for token, tf in counts.items())}
            projection_digest = hashlib.sha256(_canonical(digest_input)).hexdigest()
            con.execute("""INSERT INTO projected_shards VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                row["shard_id"], row["chain_index"], row["shard_hash"], row["created"],
                row["tenant_id"], row["agent_id"], row["store_scope"], row["status"],
                row.get("expires_at"), int(bool(row.get("poisoned"))),
                int(bool(row.get("private"))), sum(counts.values()), projection_digest))
            con.executemany("INSERT INTO postings VALUES(?,?,?)", [
                (_cell(salt, token), row["shard_id"], tf)
                for token, tf in counts.items()])
            con.executemany("INSERT OR IGNORE INTO supersession VALUES(?,?)", [
                (row["shard_id"], target) for target in row.get("supersedes", [])])
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        _put_meta(con, {
            "schema_version": SCHEMA_VERSION,
            "projection_version": PROJECTION_VERSION,
            "legacy_compatibility_id": snapshot.get(
                "legacy_compatibility_id", "none"),
            "generation": generation,
            "salt": salt.hex(),
            **_principal_binding(principal),
            "source_head": snapshot.get("head"),
            "source_count": snapshot.get("count", 0),
            "last_chain_index": snapshot.get("last_chain_index", -1),
            "built_at": now,
        })
        con.commit()
        con.close()
        with open(temp, "rb+") as persisted:
            persisted.flush()
            os.fsync(persisted.fileno())
        os.replace(temp, path)
        return {"status": "rebuilt", "generation": generation,
                "projected": len(snapshot.get("records", [])),
                "legacy_compatibility_id": snapshot.get(
                    "legacy_compatibility_id", "none")}
    except Exception as exc:
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except OSError:
            pass
        return {"status": "degraded", "reason": type(exc).__name__}


def sync(authority_db: str, principal: dict, root: str = None,
         legacy_store_approval=None) -> dict:
    """Check the authoritative cursor cheaply; rebuild only after a change."""
    path = index_path(principal, root)
    with _lock(path):
        state = _snapshot(
            authority_db, principal, metadata_only=True,
            legacy_store_approval=legacy_store_approval)
        if state.get("error"):
            return {"status": "governance_error",
                    "error_code": state.get("error_code")}
        if _same_source(path, state, principal):
            return {"status": "current", "source_count": state.get("count", 0),
                    "legacy_compatibility_id": state.get(
                        "legacy_compatibility_id", "none")}
        snapshot = _snapshot(
            authority_db, principal,
            legacy_store_approval=legacy_store_approval)
        if snapshot.get("error"):
            return {"status": "governance_error",
                    "error_code": snapshot.get("error_code")}
        return rebuild(authority_db, principal, root=root, snapshot=snapshot,
                       legacy_store_approval=legacy_store_approval)


def _active_ids(con, principal: dict):
    now = datetime.datetime.now(datetime.timezone.utc)
    active = set()
    for row in con.execute("SELECT * FROM projected_shards"):
        if (row["tenant_id"] != principal.get("tenant_id")
                or row["agent_id"] != principal.get("agent_id")
                or row["store_scope"] != principal.get("store_scope")
                or row["status"] != "active" or row["poisoned"]):
            continue
        if row["expires_at"]:
            try:
                expiry = datetime.datetime.fromisoformat(
                    row["expires_at"].replace("Z", "+00:00"))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=datetime.timezone.utc)
                if expiry <= now:
                    continue
            except Exception:
                continue
        active.add(row["shard_id"])
    return active


def route(query: str, k: int, principal: dict, root: str = None) -> dict:
    """Return text-free, non-authoritative candidate IDs and routing evidence."""
    path = index_path(principal, root)
    budget = min(MAX_CANDIDATES, max(40, max(1, int(k)) * 4))
    if not os.path.exists(path):
        return {"candidate_shard_ids": [], "routing_trace": {
            "router": SCHEMA_VERSION, "stop_reason": "index_missing",
            "candidate_budget": budget, "routing_work": 0}}
    with _lock(path):
        con = _connect(path)
        meta = _meta(con)
        binding = _principal_binding(principal)
        if any(meta.get(key) != str(value) for key, value in binding.items()):
            con.close()
            raise PermissionError("Area Five index scope mismatch")
        salt = bytes.fromhex(meta["salt"])
        query_counts = collections.Counter(_tokens(query))
        if not query_counts:
            con.close()
            return {"candidate_shard_ids": [], "routing_trace": {
                "router": SCHEMA_VERSION, "generation": meta.get("generation"),
                "stop_reason": "no_local_terms", "candidate_budget": budget,
                "routing_work": 0}}
        active = _active_ids(con, principal)
        superseded = {row["target_id"] for row in con.execute(
            "SELECT superseder_id,target_id FROM supersession")
            if row["superseder_id"] in active}
        eligible = active - superseded
        scores = collections.defaultdict(float)
        routing_work = 0
        total = max(1, len(eligible))
        for token, query_tf in query_counts.items():
            rows = con.execute("SELECT shard_id,tf FROM postings WHERE cell_id=?",
                               (_cell(salt, token),)).fetchall()
            valid_rows = [row for row in rows if row["shard_id"] in eligible]
            routing_work += len(rows)
            idf = math.log((total + 1) / (len(valid_rows) + 1)) + 1.0
            for row in valid_rows:
                scores[row["shard_id"]] += query_tf * row["tf"] * idf
        chain = {row["shard_id"]: row["chain_index"] for row in con.execute(
            "SELECT shard_id,chain_index FROM projected_shards")}
        ordered = sorted(scores, key=lambda sid: (-scores[sid], chain.get(sid, 0), sid))[:budget]
        con.close()
    trace = {
        "router": SCHEMA_VERSION,
        "projection_version": meta.get("projection_version"),
        "generation": meta.get("generation"),
        "candidate_budget": budget,
        "candidate_count": len(ordered),
        "query_cell_count": len(query_counts),
        "routing_work": routing_work,
        "source_count": int(meta.get("source_count", 0)),
        "stop_reason": "candidates_found" if ordered else "no_candidates",
        "scores": [{"shard_id": sid, "score": round(scores[sid], 8)} for sid in ordered],
    }
    return {"candidate_shard_ids": ordered, "routing_trace": trace}


def discard(principal: dict, root: str = None) -> bool:
    path = index_path(principal, root)
    with _lock(path):
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True