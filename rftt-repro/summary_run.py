import sqlite3

DB = "runs.sqlite"
RUN_ID = 5

def main():
    conn = sqlite3.connect(DB)

    # 总体
    total, correct = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(is_correct),0)
        FROM evaluations
        WHERE run_id=?
    """, (RUN_ID,)).fetchone()

    acc = (correct / total) if total else 0.0

    # 数据集信息（因为你的表里 datasets/split 存了 gsm8k/test）
    ds = conn.execute("""
        SELECT d.name, d.split, COUNT(*)
        FROM evaluations e
        JOIN problems p ON p.id = e.problem_id
        JOIN datasets d ON d.id = p.dataset_id
        WHERE e.run_id=?
        GROUP BY d.name, d.split
    """, (RUN_ID,)).fetchall()

    print(f"RUN_ID={RUN_ID}")
    print(f"TOTAL={total}")
    print(f"CORRECT={correct}")
    print(f"ACCURACY={acc:.4f}\n")

    print("By dataset:")
    for name, split, n in ds:
        c = conn.execute("""
            SELECT COALESCE(SUM(is_correct),0)
            FROM evaluations e
            JOIN problems p ON p.id = e.problem_id
            JOIN datasets d ON d.id = p.dataset_id
            WHERE e.run_id=? AND d.name=? AND d.split=?
        """, (RUN_ID, name, split)).fetchone()[0]
        print(f"  {name}/{split}: n={n} correct={c} acc={c/n:.4f}")

    conn.close()

if __name__ == "__main__":
    main()