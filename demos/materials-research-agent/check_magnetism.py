"""
One-off check: pull real computed magnetic moment data for the top
unexplored league-table candidates, to verify (not just assume from
general chemistry knowledge) which ones are likely pair-breaking risks
for superconductivity.
"""
import os
from mp_api.client import MPRester

API_KEY = os.environ.get("MP_API_KEY")
if not API_KEY:
    raise SystemExit("MP_API_KEY not set")

material_ids = [
    "mp-39105",   # MgTa2N3
    "mp-1193113", # Ta3Cr3N
    "mp-39020",   # LiTa3N4
    "mp-1192944", # Ta4Ni2N
    "mp-1193305", # Ta4Co2N
    "mp-1217893", # TaNbAl6
    "mp-1217891", # TaTiAl6
    "mp-869",     # TaAl3
    "mp-1193531", # Ta2Al
]

with MPRester(API_KEY) as mpr:
    docs = mpr.materials.summary.search(
        material_ids=material_ids,
        fields=["material_id", "formula_pretty", "total_magnetization",
                "is_magnetic", "ordering"],
    )

print(f"{'Material ID':<14}{'Formula':<14}{'Total mag (mu_B)':<18}{'Is magnetic?':<14}{'Ordering'}")
print("-" * 80)
for d in sorted(docs, key=lambda x: x.material_id):
    print(f"{d.material_id:<14}{d.formula_pretty:<14}"
          f"{d.total_magnetization:<18.4f}{str(d.is_magnetic):<14}{d.ordering}")
