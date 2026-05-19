import psycopg2
DB = dict(dbname="hardin_data_network", user="hardin_admin", password="hardin2026", host="localhost", port=5433)
conn = psycopg2.connect(**DB)
cur = conn.cursor()
cur.execute("SELECT indicator, value, unit, year, quarter FROM government_statistics WHERE country='United Kingdom' ORDER BY year DESC, indicator LIMIT 20")
for r in cur.fetchall():
    print(f"{r[0]}: {r[1]} {r[2]} ({r[3]} {r[4]})")
cur.close(); conn.close()
