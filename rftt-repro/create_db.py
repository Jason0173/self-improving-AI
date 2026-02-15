import sqlite3

conn = sqlite3.connect("test.sqlite")

conn.execute("""
CREATE TABLE IF NOT EXISTS test_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
""")

conn.commit()
conn.close()

print("✅ created test.sqlite with table test_table")