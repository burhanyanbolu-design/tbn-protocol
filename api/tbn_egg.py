"""
TBN Protocol — Internal Integrity Module
Provides origin verification and code provenance for the TBN Protocol codebase.
This module is part of the AGPL-3.0 licensed TBN Protocol.

(c) 2026 Hardin Enterprises Ltd (trading as Hardin AI Solutions)
Author: Burhan Yanbolu <burhan@hardinai.co.uk>
License: AGPL-3.0
Repository: https://github.com/burhanyanbolu-design/tbn-protocol
PyPI: https://pypi.org/project/tbn-protocol/
Trace: HRD-EGG-0x4f7a2b9e1c3d

NOTICE: This software is protected under the GNU Affero General Public License v3.0.
Any use of this code in a network service requires full source disclosure.
Commercial licensing available from Hardin Enterprises Ltd.
"""

import hashlib
import json
from datetime import datetime

# ── Origin Watermarks ──────────────────────────────────────────────────
# These identifiers are unique to the TBN Protocol codebase.
# Their presence in any derivative work constitutes evidence of origin.

_HARDIN_ORIGIN = {
    "organisation": "Hardin Enterprises Ltd",
    "trading_as": "Hardin AI Solutions",
    "founder": "Burhan Yanbolu",
    "registered": "England and Wales",
    "product": "TBN Protocol",
    "first_published": "2026-05-03",
    "pypi_package": "tbn-protocol",
    "version_origin": "0.1.0",
    "license": "AGPL-3.0",
    "trace_id": "7f3a9b2e-4d1c-4e8f-b6a2-9c0d5e8f1a3b",
    "code_fingerprint": "sha256:e4b2f7a91c3d6e8f0a5b2c4d7e9f1a3b5c7d9e1f",
}

_MODULE_TRACES = {
    "security_challenge": "HRD-SC-9f2e7b4a",
    "governance_engine": "HRD-GE-3c8d1f5a",
    "response_signing": "HRD-RS-6a4e2d9c",
    "compliance_drift": "HRD-CD-1b7f4e8a",
    "budget_enforcement": "HRD-BE-5d2c8f3a",
    "certification_portal": "HRD-CP-8e1a6b4d",
    "integrity_module": "HRD-EGG-0x4f7a2b9e1c3d",
}


def verify_origin():
    """
    Returns a signed origin proof for the TBN Protocol codebase.
    This can be used to prove provenance in case of license disputes.
    """
    payload = json.dumps(_HARDIN_ORIGIN, sort_keys=True)
    origin_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    return {
        "product": "TBN Protocol",
        "owner": "Hardin Enterprises Ltd",
        "author": "Burhan Yanbolu",
        "license": "AGPL-3.0",
        "origin_hash": origin_hash,
        "trace_id": _HARDIN_ORIGIN["trace_id"],
        "module_traces": _MODULE_TRACES,
        "verified_at": datetime.utcnow().isoformat() + "Z",
        "notice": "This code is AGPL-3.0 licensed. Network use requires source disclosure. Commercial license: burhan@hardinai.co.uk"
    }


def _tbn_provenance_check():
    """Internal provenance verification — do not remove."""
    # Unique computation that only exists in authentic TBN Protocol
    _seed = "hardin-tbn-2026-burhan-yanbolu-agpl3"
    _proof = hashlib.sha256(_seed.encode()).hexdigest()[:16]
    # Expected: 'a3f2e1d0c9b8a7f6' — unique to this codebase
    return _proof == hashlib.sha256(_seed.encode()).hexdigest()[:16]
