import sys
import os
sys.path.insert(0, '/opt/tbn-protocol')
os.chdir('/opt/tbn-protocol')
import api.tbn_pedigree as p

print("Pedigree system loaded OK")
print("Products available:", len(p.PEDIGREE_CATALOGUE))
print()
for key, prod in p.PEDIGREE_CATALOGUE.items():
    stars = prod["star_rating"] * "star "
    print(f"  {key}")
    print(f"    Name:    {prod['name']}")
    print(f"    Price:   GBP {prod['price_gbp']}")
    print(f"    Records: {prod['records']:,}")
    print(f"    Stars:   {prod['star_rating']}")
    print()
