import sqlite3
from pathlib import Path

db = Path('output/grid_data.db')
conn = sqlite3.connect(str(db))
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('Tables in DB:', tables)
for t in tables:
    count = conn.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]
    print('  ' + t.ljust(30) + str(count).rjust(10) + ' rows')
conn.close()
