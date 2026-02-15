import re
import sqlite3

DB = "runs.sqlite"
RUN_ID = 5 # 你的 run_id

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def extract_pred(text: str):
    # 1) 优先匹配 #### <number>
    m = re.search(r"####\s*([-+]?\d[\d,]*\.?\d*)", text)
    if m:
        return m.group(1).replace(",", "")

    # 2) fallback：抽最后一个数字
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", text.replace(",", ""))
    return nums[-1] if nums else None

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    rows = conn.execute("""
        SELECT g.problem_id, g.output_text, p.answer_gold
        FROM generations g
        JOIN problems p ON p.id = g.problem_id
        JOIN datasets d ON d.id = p.dataset_id
        WHERE g.run_id = ? AND d.name='gsm8k' AND d.split='test'
        ORDER BY g.problem_id
    """, (RUN_ID,)).fetchall()

    correct = 0
    total = 0

    for problem_id, output_text, answer_gold in rows:
        gold = extract_gold(answer_gold)
        pred = extract_pred(output_text)

        is_correct = 1 if (gold is not None and pred is not None and str(gold) == str(pred)) else 0
        correct += is_correct
        total += 1

        details = f"gold={gold} pred={pred}"
        conn.execute("""
            INSERT OR REPLACE INTO evaluations(run_id, problem_id, extracted_answer, is_correct, judge_details)
            VALUES(?,?,?,?,?)
        """, (RUN_ID, problem_id, pred, is_correct, details))

    conn.commit()
    conn.close()

    acc = correct / total if total else 0.0
    print(f"✅ evaluated run_id={RUN_ID} total={total} correct={correct} acc={acc:.4f}")

if __name__ == "__main__":
    main()