"""
Local demo page for the TBN Materials Research Agent.

Reads materials_league_table.json and materials_agent_receipts.jsonl
directly off disk (no live production TBN server involved) and serves
a simple dark-themed dashboard: the ranked league table, receipt
verification status, and search history.

Run:
    python demo_server.py
Then open:
    http://127.0.0.1:5099

(c) 2026 Hardin Enterprises Ltd. Local research demo, not a production service.
"""

import os
import re
import sys
import json
from flask import Flask, render_template, request, redirect, url_for

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from api.tbn_signing import verify_signature  # noqa: E402
import materials_agent  # noqa: E402

# Only allow real element symbols (1-2 letters, first capital) as input --
# this form runs a real search against a real external API on submit, so
# input must be constrained rather than passed through unchecked.
_ELEMENT_PATTERN = re.compile(r"^[A-Z][a-z]?$")

app = Flask(__name__, template_folder="templates")

LEAGUE_FILE = "materials_league_table.json"
MEMORY_FILE = "materials_agent_memory.json"
RECEIPTS_FILE = "materials_agent_receipts.jsonl"


def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _load_receipts():
    receipts = []
    if not os.path.exists(RECEIPTS_FILE):
        return receipts
    with open(RECEIPTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            sig = r.get("signature")
            body = {k: v for k, v in r.items() if k != "signature"}
            r["_verified"] = verify_signature(body, sig) if sig else False
            receipts.append(r)
    return receipts


@app.route("/")
def dashboard():
    league = _load_json(LEAGUE_FILE, {"entries": {}, "last_updated": None})
    memory = _load_json(MEMORY_FILE, {"searches": []})
    receipts = _load_receipts()

    all_entries = list(league["entries"].values())
    disqualified_count = sum(1 for e in all_entries if e.get("disqualified"))
    entries = [e for e in all_entries if not e.get("disqualified")]
    entries.sort(key=lambda e: e["score"])

    best_count = sum(1 for e in entries if e["score"] == 0.0)
    verified_count = sum(1 for r in receipts if r.get("_verified"))

    return render_template(
        "materials_demo.html",
        entries=entries,
        total_candidates=len(all_entries),
        shown_candidates=len(entries),
        disqualified_count=disqualified_count,
        best_count=best_count,
        last_updated=league.get("last_updated"),
        searches=list(reversed(memory.get("searches", []))),
        receipts=list(reversed(receipts)),
        verified_count=verified_count,
        total_receipts=len(receipts),
        search_error=request.args.get("error"),
        search_ran=request.args.get("ran"),
    )


@app.route("/search", methods=["POST"])
def trigger_search():
    """Runs a real search via materials_agent.py's own functions (not a
    subprocess -- calls the same code the CLI uses) and redirects back to
    the dashboard, which re-reads the updated files fresh."""
    raw = (request.form.get("elements") or "").strip()
    if not raw:
        return redirect(url_for("dashboard", error="Enter at least one element symbol."))

    elements = [e.strip() for e in raw.replace(",", " ").split() if e.strip()]
    invalid = [e for e in elements if not _ELEMENT_PATTERN.match(e)]
    if invalid:
        return redirect(url_for(
            "dashboard",
            error=f"Not valid element symbols: {', '.join(invalid)} "
                  f"(use real symbols like Ta, N, Nb -- capital first letter)."
        ))
    if len(elements) > 4:
        return redirect(url_for("dashboard", error="Limit is 4 elements per search."))

    if not os.environ.get("MP_API_KEY"):
        return redirect(url_for("dashboard", error="MP_API_KEY environment variable not set on this server."))

    try:
        materials_agent.run_search(elements)
    except SystemExit as e:
        return redirect(url_for("dashboard", error=str(e)))
    except Exception as e:
        return redirect(url_for("dashboard", error=f"Search failed: {str(e)[:200]}"))

    return redirect(url_for("dashboard", ran="-".join(elements)))


if __name__ == "__main__":
    print("Materials Research Agent demo running at http://127.0.0.1:5099")
    app.run(host="127.0.0.1", port=5099, debug=False)
