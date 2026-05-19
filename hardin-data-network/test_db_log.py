"""Test direct DB logging"""
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="hardin_data_network",
        user="hardin_admin",
        password="hardin2026",
        host="localhost"
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tbn_handshake_log 
        (initiator_bot_id, responder_bot_id, status, ip_address, notes)
        VALUES (%s, %s, %s, %s, %s)
    """, ("test-bot-001", "test-bot-002", "SUCCESS", "127.0.0.1", "Test handshake"))
    conn.commit()
    print("INSERT OK")

    cur.execute("SELECT * FROM tbn_handshake_log ORDER BY initiated_at DESC LIMIT 3")
    rows = cur.fetchall()
    print(f"Rows in log: {len(rows)}")
    for r in rows:
        print(f"  {r}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
