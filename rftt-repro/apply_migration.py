import sqlite3

DB = "runs.sqlite"
SQL = "migrate_part2.sql"

def main():
    conn = sqlite3.connect(DB)
    with open(SQL, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✅ Part 2 migration applied")

if __name__ == "__main__":
    main()