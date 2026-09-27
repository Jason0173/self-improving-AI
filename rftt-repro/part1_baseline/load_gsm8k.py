import sqlite3
from datasets import load_dataset

DB = "runs.sqlite"

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # 1) 在 datasets 表登记
    name, split = "gsm8k", "test"
    conn.execute(
        "INSERT OR IGNORE INTO datasets(name, split) VALUES(?,?)",
        (name, split),
    )
    dataset_id = conn.execute(
        "SELECT id FROM datasets WHERE name=? AND split=?",
        (name, split),
    ).fetchone()[0]

    # 2) 从 HF 下载 GSM8K test 并写入 problems
    ds = load_dataset("gsm8k", "main", split="test")
    inserted = 0
    for ex in ds:
        q = ex["question"]
        a = ex["answer"]  # 含推理 + 最终 #### 数字
        conn.execute(
            "INSERT INTO problems(dataset_id, question, answer_gold) VALUES(?,?,?)",
            (dataset_id, q, a),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ inserted {inserted} rows into problems for {name}/{split}")

if __name__ == "__main__":
    main()