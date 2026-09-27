import sqlite3

DB = "runs.sqlite"
RUNS = [5, 9]  # baseline, proposed vote

def main():
    conn = sqlite3.connect(DB)

    print("run_id | run_name | model_name | n | correct | acc")
    print("-"*80)

    for rid in RUNS:
        run = conn.execute("SELECT run_name, model_name FROM runs WHERE id=?", (rid,)).fetchone()
        if not run:
            print(f"{rid} not found")
            continue
        run_name, model_name = run

        n, correct = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(is_correct),0)
            FROM evaluations
            WHERE run_id=?
        """, (rid,)).fetchone()

        acc = (correct / n) if n else 0.0
        print(f"{rid} | {run_name} | {model_name} | {n} | {correct} | {acc:.4f}")

    conn.close()

if __name__ == "__main__":
    main()