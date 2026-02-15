import sqlite3

conn = sqlite3.connect("runs.sqlite")

conn.executescript("""
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    split TEXT NOT NULL,
    UNIQUE(name, split)
);

CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer_gold TEXT,
    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    output_text TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id),
    FOREIGN KEY(problem_id) REFERENCES problems(id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id),
    FOREIGN KEY(problem_id) REFERENCES problems(id)
);
""")

conn.commit()
conn.close()

print("✅ runs.sqlite created with experiment tables")