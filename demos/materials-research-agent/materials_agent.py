"""
TBN Materials Research Agent (local demo)
==========================================
A governed research agent that searches the Materials Project database
for candidate qubit materials (stable + metallic compounds), signs every
search as a receipt, remembers what it has already searched, and builds
a persistent, ranked "league table" of the best candidates found so far.

This is a STANDALONE LOCAL DEMO. It reuses TBN's real signing primitive
(api/tbn_signing.py) so every receipt is genuinely RSA-PSS-SHA256 signed
and independently verifiable, but it does NOT register against the live
production TBN server, agent network, or Hardin AI Labs. That is a
deliberate, separate decision -- see the session record for why.

Usage:
    python materials_agent.py Ta N
    python materials_agent.py Nb Ti
    python materials_agent.py --show-league     (print the league table)

Requires:
    MP_API_KEY environment variable set to a valid Materials Project API key.

(c) 2026 Hardin Enterprises Ltd. Local research demo, not a production service.
"""

import os
import sys
import json
import hashlib
import datetime

# Import TBN's real signing primitive rather than reinventing signing logic.
# tbn_signing.py resolves its key paths relative to the CURRENT WORKING
# DIRECTORY (data/tbn_signing_key.pem), not this script's location, so we
# give this demo its own local data/ folder to avoid touching the real
# production signing key at the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "api"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from api.tbn_signing import sign_response, verify_signature  # noqa: E402

AGENT_ID = "tbn-agent-materials-researcher"
AGENT_NAME = "TBN Materials Research Agent"
AGENT_PURPOSE = (
    "Searches the Materials Project database for stable, metallic "
    "compound candidates relevant to superconducting qubit fabrication, "
    "and maintains a signed, ranked league table of findings."
)

GOVERNANCE_POLICY = {
    "max_searches_per_run": 10,
    "allowed_data_source": "materialsproject.org (public API)",
    "max_results_shown_per_search": 25,
    "scoring_basis": "energy_above_hull (stability) + band_gap (metallicity)",
    "no_physical_synthesis_claims": True,  # this agent never claims a
    # material has been built or measured -- only that it exists as a
    # stable, computed structure in the database.
    "attestation_frequency": "per_search",
}

MEMORY_FILE = "materials_agent_memory.json"
LEAGUE_FILE = "materials_league_table.json"
RECEIPTS_FILE = "materials_agent_receipts.jsonl"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _append_receipt(receipt):
    with open(RECEIPTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(receipt) + "\n")


def attest_search(elements, result_count, top_candidates):
    """Create and persist a signed receipt for this search action.
    Mirrors the pattern in api/register_tbn_agents.py's attest_action(),
    but signs locally with the real TBN signing key rather than calling
    the live /api/v1/attest endpoint (this agent is not registered on the
    live network -- see module docstring)."""
    body = {
        "agent_id": AGENT_ID,
        "action": "materials_search",
        "elements_searched": sorted(elements),
        "result_count": result_count,
        "top_candidate_ids": [c["material_id"] for c in top_candidates[:5]],
        "timestamp": _now(),
    }
    signature = sign_response(body)
    receipt = dict(body, signature=signature)
    _append_receipt(receipt)
    return receipt


def already_searched(elements):
    """Check this agent's memory for whether this exact element
    combination has already been searched, to avoid repeat API calls."""
    memory = _load_json(MEMORY_FILE, {"searches": []})
    key = "-".join(sorted(elements))
    for entry in memory["searches"]:
        if entry["key"] == key:
            return entry
    return None


def remember_search(elements, result_count, top_candidates):
    memory = _load_json(MEMORY_FILE, {"searches": []})
    key = "-".join(sorted(elements))
    memory["searches"].append({
        "key": key,
        "elements": sorted(elements),
        "result_count": result_count,
        "searched_at": _now(),
        "top_5": [
            {"material_id": c["material_id"], "formula": c["formula_pretty"],
             "score": c["score"]}
            for c in top_candidates[:5]
        ],
    })
    _save_json(MEMORY_FILE, memory)


# ── Practicality filter ──────────────────────────────────────────────
# Stability and metallicity are NECESSARY but nowhere near SUFFICIENT
# for a usable qubit material -- they say nothing about whether the
# element is radioactive, actually available, or affordable. This
# penalizes compounds containing elements no real lab would build with,
# so the top of the league table reflects "worth chasing" rather than
# just "mathematically perfect in an idealized database."

# Radioactive / unavailable in normal quantities -- disqualifying, not
# just a penalty, since these are not buildable at all in practice.
RADIOACTIVE_ELEMENTS = {
    "Tc", "Pm",  # no stable isotopes, not naturally available
    "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu",
    "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr",
    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn",
    "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
}

# Extremely rare / expensive precious and platinum-group metals -- not
# disqualifying, but a real cost/availability penalty since these
# materially raise fabrication cost and complicate sourcing.
RARE_EXPENSIVE_ELEMENTS = {
    "Ru", "Rh", "Pd", "Os", "Ir", "Pt", "Au",  # platinum group + gold
    "Re",  # one of the rarest stable elements in Earth's crust
}

# Rare-earth elements -- not disqualifying, but a moderate penalty:
# usable and stable, but genuinely harder and costlier to source and
# purify than common transition metals.
RARE_EARTH_ELEMENTS = {
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu", "Sc", "Y",
}

DISQUALIFYING_PENALTY = 1000.0  # pushes radioactive-containing compounds
# to the very bottom of any ranking -- these should never rank above
# any buildable compound, regardless of how "stable" the database says
# they are, since they cannot be sourced/handled in a normal lab.
RARE_EXPENSIVE_PENALTY = 0.5
RARE_EARTH_PENALTY = 0.2


def _formula_elements(formula_pretty):
    """Extract element symbols from a formula string like 'Ta4AlN3' or
    'Sr4Li2Ta2Al2N8O' using a simple regex (capital letter, optional
    lowercase letter)."""
    import re
    return set(re.findall(r"[A-Z][a-z]?", formula_pretty))


def practicality_penalty(formula_pretty):
    """Returns (penalty, disqualified, reasons) for a formula string."""
    elems = _formula_elements(formula_pretty)
    reasons = []
    penalty = 0.0
    disqualified = False

    radioactive_hits = elems & RADIOACTIVE_ELEMENTS
    if radioactive_hits:
        disqualified = True
        penalty += DISQUALIFYING_PENALTY
        reasons.append(f"contains radioactive/unavailable element(s): {', '.join(sorted(radioactive_hits))}")

    rare_hits = elems & RARE_EXPENSIVE_ELEMENTS
    if rare_hits:
        penalty += RARE_EXPENSIVE_PENALTY
        reasons.append(f"contains rare/expensive element(s): {', '.join(sorted(rare_hits))}")

    rare_earth_hits = elems & RARE_EARTH_ELEMENTS
    if rare_earth_hits:
        penalty += RARE_EARTH_PENALTY
        reasons.append(f"contains rare-earth element(s): {', '.join(sorted(rare_earth_hits))}")

    return penalty, disqualified, reasons


def score_candidate(doc):
    """Score a candidate for qubit-material promise.
    Lower energy_above_hull is better (more stable). Metallic (band_gap
    == 0) is required for a superconducting qubit circuit material.
    A practicality penalty is added for radioactive, rare, or expensive
    elements, so the ranking reflects real-world buildability, not just
    idealized database stability.
    This is a simple, transparent heuristic -- NOT a physics simulation
    of actual qubit coherence, which this agent has no way to compute."""
    metallic_bonus = 0.0 if doc.energy_above_hull is not None and doc.band_gap == 0.0 else 10.0
    stability_penalty = doc.energy_above_hull if doc.energy_above_hull is not None else 999.0
    practicality, _, _ = practicality_penalty(doc.formula_pretty)
    return round(stability_penalty + metallic_bonus + practicality, 6)


def update_league_table(elements, candidates):
    """Merge newly found candidates into the persistent league table,
    keyed by material_id so re-searching never creates duplicate entries,
    and re-sort by score."""
    league = _load_json(LEAGUE_FILE, {"entries": {}, "last_updated": None})
    for c in candidates:
        league["entries"][c["material_id"]] = {
            "material_id": c["material_id"],
            "formula": c["formula_pretty"],
            "energy_above_hull": c["energy_above_hull"],
            "band_gap": c["band_gap"],
            "is_stable": c["is_stable"],
            "crystal_system": c["crystal_system"],
            "score": c["score"],
            "disqualified": c.get("disqualified", False),
            "practicality_notes": c.get("practicality_notes", []),
            "found_via_search": "-".join(sorted(elements)),
            "first_seen": league["entries"].get(c["material_id"], {}).get(
                "first_seen", _now()),
        }
    league["last_updated"] = _now()
    _save_json(LEAGUE_FILE, league)
    return league


def print_league_table(top_n=25, include_disqualified=False):
    league = _load_json(LEAGUE_FILE, {"entries": {}, "last_updated": None})
    entries = list(league["entries"].values())
    if not include_disqualified:
        entries = [e for e in entries if not e.get("disqualified")]
    entries.sort(key=lambda e: e["score"])

    print("=" * 110)
    print(f"MATERIALS LEAGUE TABLE  (last updated: {league['last_updated']})")
    print(f"Total distinct candidates ever found: {len(league['entries'])} "
          f"({sum(1 for e in league['entries'].values() if e.get('disqualified'))} "
          f"disqualified as radioactive/unavailable, hidden by default)")
    print("=" * 110)
    print(f"{'Rank':<6}{'Material ID':<14}{'Formula':<16}{'Score':<10}"
          f"{'E above hull':<15}{'Band gap':<12}{'Notes'}")
    print("-" * 110)
    for i, e in enumerate(entries[:top_n], start=1):
        notes = "; ".join(e.get("practicality_notes", [])) or "-"
        print(f"{i:<6}{e['material_id']:<14}{e['formula']:<16}{e['score']:<10.4f}"
              f"{e['energy_above_hull']:<15.4f}{e['band_gap']:<12.4f}{notes}")
    print()
    print("Score = energy_above_hull, +10 if not metallic, +0.5 if rare/expensive")
    print("element present, +0.2 if rare-earth element present. Lower is better.")
    print("Compounds containing radioactive/unavailable elements are disqualified")
    print("and hidden by default (pass include_disqualified=True to show them).")


def run_search(elements):
    cached = already_searched(elements)
    if cached:
        print(f"[MEMORY] Already searched {'-'.join(sorted(elements))} on "
              f"{cached['searched_at']} -- {cached['result_count']} results found. "
              f"Skipping API call. (delete {MEMORY_FILE} to force a re-search)")
        return

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise SystemExit("MP_API_KEY environment variable not set.")

    from mp_api.client import MPRester

    print(f"[SEARCH] Querying Materials Project for: {', '.join(elements)}")
    with MPRester(api_key) as mpr:
        docs = mpr.materials.summary.search(
            elements=elements,
            fields=["material_id", "formula_pretty", "energy_above_hull",
                    "band_gap", "is_stable", "symmetry"],
        )

    candidates = []
    for d in docs:
        _, disqualified, reasons = practicality_penalty(d.formula_pretty)
        candidates.append({
            "material_id": d.material_id,
            "formula_pretty": d.formula_pretty,
            "energy_above_hull": d.energy_above_hull,
            "band_gap": d.band_gap,
            "is_stable": d.is_stable,
            "crystal_system": str(d.symmetry.crystal_system) if d.symmetry else "?",
            "score": score_candidate(d),
            "disqualified": disqualified,
            "practicality_notes": reasons,
        })
    candidates.sort(key=lambda c: c["score"])

    print(f"[SEARCH] Found {len(candidates)} materials.")

    receipt = attest_search(elements, len(candidates), candidates)
    print(f"[RECEIPT] Signed attestation recorded "
          f"(signature prefix: {receipt['signature'][:24]}...)")

    remember_search(elements, len(candidates), candidates)
    league = update_league_table(elements, candidates)
    print(f"[LEAGUE] Table updated. Total distinct candidates tracked: "
          f"{len(league['entries'])}")

    print()
    print("Top 10 candidates from THIS search:")
    print(f"{'Material ID':<14}{'Formula':<16}{'Score':<10}"
          f"{'E above hull':<15}{'Band gap':<12}")
    print("-" * 70)
    for c in candidates[:10]:
        print(f"{c['material_id']:<14}{c['formula_pretty']:<16}{c['score']:<10.4f}"
              f"{c['energy_above_hull']:<15.4f}{c['band_gap']:<12.4f}")


def verify_all_receipts():
    """Independently re-verify every signed receipt this agent has ever
    written, using TBN's public verify_signature() function -- proving
    the receipts are genuinely tamper-evident, not just trust-me JSON."""
    if not os.path.exists(RECEIPTS_FILE):
        print("No receipts recorded yet.")
        return
    total = 0
    ok = 0
    with open(RECEIPTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            receipt = json.loads(line)
            sig = receipt.pop("signature")
            if verify_signature(receipt, sig):
                ok += 1
            receipt["signature"] = sig  # restore for display purposes
    print(f"Verified {ok}/{total} receipts as authentic and untampered.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    if args[0] == "--show-league":
        print_league_table()
    elif args[0] == "--verify-receipts":
        verify_all_receipts()
    else:
        run_search(args)
