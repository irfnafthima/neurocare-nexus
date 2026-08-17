import psycopg2

conn = psycopg2.connect(dbname='neurocare_nexus', user='postgres', password='irfu123', host='localhost', port='5432')
cur = conn.cursor()

legacy_tables = ['users', 'patients', 'synthetic_patients', 'synthetic_npis', 'synthetic_caregivers', 'appointments', 'connection_requests']

for t in legacy_tables:
    try:
        cur.execute(f'SELECT * FROM "{t}" LIMIT 10;')
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        print(f"\n=== Legacy Table '{t}' ({len(rows)} rows) ===")
        print("Columns:", colnames)
        for r in rows:
            print("  ", r)
    except Exception as e:
        conn.rollback()
        print(f"Error inspecting '{t}':", e)
