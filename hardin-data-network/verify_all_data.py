"""
Data Verification Script
Checks all tables for obviously wrong/fake data
"""
import psycopg2

DB = dict(dbname="hardin_data_network", user="hardin_admin",
          password="hardin2026", host="localhost", port=5433)

def q(sql):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

print("=" * 60)
print("  HARDIN DATA NETWORK — DATA QUALITY AUDIT")
print("=" * 60)

issues = []
ok     = []

# ── 1. Currency Rates ─────────────────────────────────────
print("\n[1] Currency Rates (GBP vs major currencies)")
rows = q("SELECT target_currency, MIN(exchange_rate), MAX(exchange_rate), AVG(exchange_rate) FROM currency_rates GROUP BY target_currency ORDER BY target_currency")
for r in rows:
    currency, mn, mx, avg = r[0], float(r[1]), float(r[2]), float(r[3])
    # Sanity checks
    if currency == 'USD' and not (0.5 < avg < 3.0):
        issues.append(f"  ❌ GBP/USD avg={avg:.4f} — WRONG (should be ~1.25-1.35)")
    elif currency == 'EUR' and not (0.5 < avg < 2.0):
        issues.append(f"  ❌ GBP/EUR avg={avg:.4f} — WRONG (should be ~1.15-1.20)")
    elif currency == 'JPY' and not (100 < avg < 300):
        issues.append(f"  ❌ GBP/JPY avg={avg:.4f} — WRONG (should be ~180-200)")
    else:
        print(f"  ✅ GBP/{currency}: avg={avg:.4f} (min={mn:.4f}, max={mx:.4f})")

# ── 2. Commodities ────────────────────────────────────────
print("\n[2] Commodities (price ranges)")
rows = q("SELECT commodity_name, unit, MIN(price), MAX(price), AVG(price) FROM commodities GROUP BY commodity_name, unit ORDER BY commodity_name")
EXPECTED = {
    'Gold':        (1500, 3500, 'USD/oz'),
    'Silver':      (15, 50, 'USD/oz'),
    'Crude Oil':   (40, 150, 'USD/barrel'),
    'Copper':      (2, 10, 'USD/lb'),
    'Natural Gas': (1, 15, 'USD/MMBtu'),
    'Platinum':    (800, 1500, 'USD/oz'),
    'Coffee':      (100, 400, 'USD/lb'),
    'Corn':        (200, 800, 'USD/bushel'),
    'Aluminum':    (0.5, 3, 'USD/lb'),
}
for r in rows:
    name, unit, mn, mx, avg = r[0], r[1], float(r[2]), float(r[3]), float(r[4])
    if name in EXPECTED:
        lo, hi, expected_unit = EXPECTED[name]
        if lo <= avg <= hi:
            print(f"  ✅ {name}: avg=${avg:.2f} {unit}")
        else:
            issues.append(f"  ❌ {name}: avg=${avg:.2f} {unit} — WRONG (expected ${lo}-${hi})")
    else:
        print(f"  ℹ️  {name}: avg=${avg:.2f} {unit}")

# ── 3. Football Matches ───────────────────────────────────
print("\n[3] Football Matches (score ranges)")
rows = q("SELECT MIN(home_score), MAX(home_score), AVG(home_score), COUNT(*) FROM football_matches")
mn, mx, avg, cnt = float(rows[0][0]), float(rows[0][1]), float(rows[0][2]), rows[0][3]
if 0 <= avg <= 5 and mx <= 15:
    print(f"  ✅ Scores look realistic: avg={avg:.1f}, max={mx}, total={cnt} matches")
else:
    issues.append(f"  ❌ Football scores look wrong: avg={avg:.1f}, max={mx}")

# ── 4. Restaurants ────────────────────────────────────────
print("\n[4] Restaurants (rating ranges)")
rows = q("SELECT MIN(overall_rating), MAX(overall_rating), AVG(overall_rating), COUNT(*) FROM restaurants")
mn, mx, avg, cnt = float(rows[0][0]), float(rows[0][1]), float(rows[0][2]), rows[0][3]
if 1 <= avg <= 5 and mx <= 5:
    print(f"  ✅ Ratings look realistic: avg={avg:.2f}/5, total={cnt} restaurants")
else:
    issues.append(f"  ❌ Restaurant ratings wrong: avg={avg:.2f}, max={mx}")

# ── 5. Car Sales ──────────────────────────────────────────
print("\n[5] Car Sales (unit ranges)")
rows = q("SELECT manufacturer, SUM(units_sold) FROM uk_car_sales GROUP BY manufacturer ORDER BY SUM(units_sold) DESC LIMIT 5")
for r in rows:
    mfr, units = r[0], int(r[1])
    if 10000 <= units <= 2000000:
        print(f"  ✅ {mfr}: {units:,} units")
    else:
        issues.append(f"  ❌ {mfr}: {units:,} units — looks wrong")

# ── 6. Universities ───────────────────────────────────────
print("\n[6] Universities (ranking & fees)")
rows = q("SELECT name, ranking_uk, tuition_fees_gbp, graduate_employment_rate FROM uk_universities ORDER BY ranking_uk LIMIT 5")
for r in rows:
    name, rank, fees, emp = r[0], r[1], r[2], float(r[3])
    if 1 <= rank <= 200 and 5000 <= fees <= 50000 and 50 <= emp <= 100:
        print(f"  ✅ #{rank} {name}: fees=£{fees:,}, employment={emp}%")
    else:
        issues.append(f"  ❌ {name}: rank={rank}, fees=£{fees}, employment={emp}% — check values")

# ── 7. Lottery ────────────────────────────────────────────
print("\n[7] Lottery (jackpot ranges)")
rows = q("SELECT lottery_name, MIN(jackpot_amount), MAX(jackpot_amount), COUNT(*) FROM lottery_draws GROUP BY lottery_name")
for r in rows:
    name, mn, mx, cnt = r[0], float(r[1]), float(r[2]), r[3]
    if 100000 <= mx <= 500000000:
        print(f"  ✅ {name}: jackpots £{mn:,.0f}-£{mx:,.0f}, {cnt} draws")
    else:
        issues.append(f"  ❌ {name}: jackpot max=£{mx:,.0f} — looks wrong")

# ── 8. Horse Racing ───────────────────────────────────────
print("\n[8] Horse Racing")
rows = q("SELECT COUNT(*), COUNT(DISTINCT racecourse) FROM horse_races")
cnt, courses = rows[0]
if cnt > 0 and courses > 0:
    print(f"  ✅ {cnt} races at {courses} different courses")
else:
    issues.append(f"  ❌ Horse racing data missing")

# ── 9. Weather ────────────────────────────────────────────
print("\n[9] Weather (temperature ranges)")
rows = q("SELECT MIN(temperature), MAX(temperature), AVG(temperature), COUNT(DISTINCT city) FROM weather_data")
mn, mx, avg, cities = float(rows[0][0]), float(rows[0][1]), float(rows[0][2]), rows[0][3]
if -20 <= mn and mx <= 50 and cities > 0:
    print(f"  ✅ Temperatures: {mn}°C to {mx}°C, avg={avg:.1f}°C, {cities} cities")
else:
    issues.append(f"  ❌ Weather temps wrong: {mn}°C to {mx}°C")

# ── 10. Economic Data ─────────────────────────────────────
print("\n[10] Economic Data (after fix)")
rows = q("SELECT indicator, value, unit FROM government_statistics WHERE country='United Kingdom' AND year=2026 ORDER BY indicator")
for r in rows:
    ind, val, unit = r[0], float(r[1]), r[2]
    print(f"  ✅ {ind}: {val} {unit}")

# ── 11. Trade Data ────────────────────────────────────────
print("\n[11] Trade Data")
rows = q("SELECT trade_type, COUNT(*), MIN(value_usd), MAX(value_usd) FROM trade_data GROUP BY trade_type")
for r in rows:
    ttype, cnt, mn, mx = r[0], r[1], float(r[2]), float(r[3])
    if mx > 0:
        print(f"  ✅ {ttype}: {cnt} records, values £{mn:,.0f}-£{mx:,.0f}")
    else:
        issues.append(f"  ❌ {ttype}: values look wrong")

# ── Summary ───────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  DATA QUALITY SUMMARY")
print("=" * 60)
print(f"  ✅ Passed: {11 - len(issues)} checks")
print(f"  ❌ Issues: {len(issues)} found")

if issues:
    print("\n  ISSUES TO FIX:")
    for issue in issues:
        print(issue)
else:
    print("\n  🎉 All data looks correct!")

print("=" * 60)
