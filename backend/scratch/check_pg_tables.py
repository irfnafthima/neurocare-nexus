import psycopg2

conn = psycopg2.connect(dbname='neurocare_nexus', user='postgres', password='irfu123', host='localhost', port='5432')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
tables = [row[0] for row in cur.fetchall()]

print("Tables in PostgreSQL database 'neurocare_nexus':")
for t in sorted(tables):
    cur.execute(f'SELECT COUNT(*) FROM "{t}";')
    count = cur.fetchone()[0]
    print(f"  - {t}: {count} rows")
