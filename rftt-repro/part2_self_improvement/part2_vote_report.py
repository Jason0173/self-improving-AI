import re
import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 7  # trajectories 的 run_id（你刚才生成轨迹用的）

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def main():
    conn = sqlite3.connect(DB)

    # 取 gold
    gold_map = {}
    for pid, gold in conn.execute("""
        SELECT p.id, p.answer_gold
        FROM problems p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
    """):
        gold_map[pid] = extract_gold(gold)

    # 按 problem 收集 rollouts 的 final_answer
    preds = defaultdict(list)
    for pid, ans in conn.execute("""
        SELECT problem_id, final_answer
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        if ans is not None:
            preds[pid].append(ans)

    total = 0
    correct = 0

    for pid, ans_list in preds.items():
        if pid not in gold_map:
            continue
        gold = gold_map[pid]
        if gold is None or len(ans_list) == 0:
            continue

        top_ans, top_n = Counter(ans_list).most_common(1)[0]
        is_correct = 1 if top_ans == gold else 0

        total += 1
        correct += is_correct

        print(f"pid={pid} vote={top_ans} gold={gold} n={len(ans_list)} correct={is_correct}")

    acc = correct / total if total else 0.0
    print(f"\n✅ majority-vote accuracy on trajectories run_id={TRAJ_RUN_ID}: total={total} correct={correct} acc={acc:.4f}")

    conn.close()

if __name__ == "__main__":
    main()