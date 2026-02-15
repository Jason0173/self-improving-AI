import sqlite3

DB = "runs.sqlite"
RUN_ID = 4

def main():
    conn = sqlite3.connect(DB)

    # 1) summary
    row = conn.execute("""
        SELECT COUNT(*), SUM(is_correct)
        FROM evaluations
        WHERE run_id=?
    """, (RUN_ID,)).fetchone()

    total = row[0] or 0
    correct = row[1] or 0
    acc = correct / total if total else 0.0
    print(f"Run {RUN_ID}: total={total} correct={correct} acc={acc:.4f}\n")

    # 2) show some errors
    rows = conn.execute("""
        SELECT
            p.id,
            p.question,
            p.answer_gold,
            e.extracted_answer,
            e.judge_details
        FROM evaluations e
        JOIN problems p ON p.id = e.problem_id
        WHERE e.run_id=? AND e.is_correct=0
        ORDER BY p.id
        LIMIT 5
    """, (RUN_ID,)).fetchall()

    print("Top 5 wrong cases:\n")
    for pid, q, gold, pred, details in rows:
        print("="*80)
        print(f"problem_id: {pid}")
        print("\n[QUESTION]\n", q)
        print("\n[GOLD]\n", gold)
        print("\n[PRED]\n", pred)
        print("\n[DETAILS]\n", details)

    conn.close()

if __name__ == "__main__":
    main()