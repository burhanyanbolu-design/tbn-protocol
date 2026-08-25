"""
One-off check: for the surviving (non-magnetic) top candidates, verify
whether each has actually been experimentally synthesized (ICSD-backed)
or is a purely theoretical/predicted structure that has never been made
in a real lab. This is a distinct, important status that stability and
magnetism checks don't capture.
"""
import os
from mp_api.client import MPRester

API_KEY = os.environ.get("MP_API_KEY")
if not API_KEY:
    raise SystemExit("MP_API_KEY not set")

material_ids = [
    "mp-869",     # TaAl3
    "mp-1193531", # Ta2Al
    "mp-1217893", # TaNbAl6
    "mp-1217891", # TaTiAl6
    "mp-39020",   # LiTa3N4
    "mp-39105",   # MgTa2N3
    "mp-1192944", # Ta4Ni2N (survived magnetism check)
    "mp-1279",    # TaN -- known control, should show experimentally verified
    "mp-1079438", # Ta2N -- known control, should show experimentally verified
]

with MPRester(API_KEY) as mpr:
    docs = mpr.materials.summary.search(
        material_ids=material_ids,
        fields=["material_id", "formula_pretty", "theoretical",
                "database_IDs"],
    )

print(f"{'Material ID':<14}{'Formula':<14}{'Theoretical?':<14}{'Has ICSD/experimental ID?'}")
print("-" * 80)
for d in sorted(docs, key=lambda x: x.material_id):
    db_ids = d.database_IDs or {}
    has_icsd = bool(db_ids.get("icsd"))
    print(f"{d.material_id:<14}{d.formula_pretty:<14}{str(d.theoretical):<14}{has_icsd}")
