import psycopg2
DB = dict(dbname="hardin_data_network", user="hardin_admin", password="hardin2026", host="localhost", port=5433)

def q(sql, p=None):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    if p:
        cur.execute(sql, p)
    else:
        cur.execute(sql)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

print("=== FOOTBALL TEAMS (Manchester/Chelsea) ===")
for r in q("SELECT DISTINCT home_team FROM football_matches WHERE home_team ILIKE '%manchester%' OR home_team ILIKE '%chelsea%' OR home_team ILIKE '%united%' LIMIT 15"):
    print(" ", r[0])

print("\n=== UNIVERSITIES (first 5) ===")
for r in q("SELECT name, city FROM uk_universities LIMIT 5"):
    print(" ", r[0], "|", r[1])

print("\n=== LOTTERY (first 3) ===")
for r in q("SELECT draw_name, draw_date, numbers FROM lottery_draws LIMIT 3"):
    print(" ", r[0], "|", str(r[1])[:10], "|", r[2])

print("\n=== HORSE RACES (first 3) ===")
for r in q("SELECT race_name, course, winner FROM horse_races LIMIT 3"):
    print(" ", r[0], "|", r[1], "|", r[2])

print("\n=== WEATHER CITIES ===")
for r in q("SELECT DISTINCT city FROM weather_data LIMIT 15"):
    print(" ", r[0])

print("\n=== CURRENCY (USD sample) ===")
for r in q("SELECT target_currency, rate_date, rate FROM currency_rates WHERE target_currency='USD' LIMIT 3"):
    print(" ", r[0], "|", str(r[1])[:10], "|", r[2])
