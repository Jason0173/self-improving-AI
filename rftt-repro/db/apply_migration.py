import sqlite3
from pathlib import Path

DB = "runs.sqlite"
# The migration file lives next to this script in db/.
SQL = Path(__file__).resolve().parent / "migrate_part2.sql"

def main():
    conn = sqlite3.connect(DB)
    with open(SQL, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✅ Part 2 migration applied")

if __name__ == "__main__":
    main()