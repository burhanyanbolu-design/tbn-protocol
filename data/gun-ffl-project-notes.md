# FFL Compliance Software Project — Notes

## Client
- Friend of Burhan
- Licensed gun manufacturer/importer in Nevada, USA
- FFL Type 07 (Manufacturer) + Type 08 (Importer)

## What He Needs
Two programs:
1. **Inventory/Compliance Tracking System** — tracks every firearm through its lifecycle
2. **TBN Certification Layer** — certifies every transaction as tamper-proof for ATF audits

## Three Flows to Handle

### Flow 1: Manufacturing
- He builds a gun
- Assigns serial number
- Logs: model, serial, caliber, type, date manufactured
- Must mark firearm with: his name, city/state, serial, caliber, model
- Annual report: ATF Form 5 (Manufacturing Report, due April 1)

### Flow 2: Importing
- Gun arrives from overseas
- ATF Form 6 (import permit) required before importing
- Logs: serial, model, manufacturer, country of origin, date imported, who bought from
- Must mark with: importer name, city/state, country of origin

### Flow 3: Sales/Disposition
- Gun sold to buyer (dealer or retail)
- Form 4473 (background check form)
- NICS check (National Instant Criminal Background Check)
- Logs: serial, model, who sold to, date sold, Form 4473 number

## Fields to Track Per Firearm
- Serial number
- Model
- Manufacturer
- Type (pistol, rifle, shotgun, etc.)
- Caliber/gauge
- Country of origin (if imported)
- Date manufactured / date imported
- Who bought from (overseas supplier)
- Import permit # (ATF Form 6)
- Date sold
- Who sold to (name, address, ID)
- Background check status (NICS)
- Form 4473 number

## TBN Integration
- Every acquisition → TBN receipt
- Every disposition/sale → TBN receipt
- Every manufacturing log entry → TBN receipt
- Provides tamper-proof audit trail for ATF inspections
- Independent proof that records were made at the recorded time

## US Federal Regulations (ATF)
- 27 CFR Part 478 — record-keeping requirements
- ATF Form 4473 — buyer background check
- ATF Form 5 — annual manufacturing report
- ATF Form 6 — import permit
- A&D Bound Book — acquisition & disposition records (20 year retention)
- Must record within 1 business day of transaction

## Market Opportunity
- 130,000+ FFLs in the United States
- If 1% use at $50/month = $65k/month recurring
- Existing competitors: FastBound, Orchid eBound — but none with independent TBN certification

## Status
- Waiting for full parameters from client
- Build when parameters received

## Next Steps
- [ ] Client sends full parameter list
- [ ] Verify ATF accepts digital records (precedent exists — FastBound etc.)
- [ ] Design database schema
- [ ] Build Program 1 (inventory/tracking)
- [ ] Build Program 2 (TBN certification layer)
- [ ] Test with client's real data
