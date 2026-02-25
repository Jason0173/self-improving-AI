import re
import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 10

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def main():
    conn = sqlite3.connect(DB)

    # gold
    gold = {}
    for pid, ans in conn.execute("""
        SELECT p.id, p.answer_gold
        FROM problems p
        JOIN datasets d ON d.id=p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT 50
    """):
        gold[pid] = extract_gold(ans)

    # answers from trajectories
    answers = defaultdict(list)
    for pid, a in conn.execute("""
        SELECT problem_id, final_answer
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        answers[pid].append(a)

    # 1) 全局答案分布（看看是不是 2/3/4/5 特别多）
    all_ans = [a for pid in answers for a in answers[pid] if a is not None]
    cnt = Counter(all_ans).most_common(20)
    print("Top-20 most common final_answer across ALL rollouts:")
    for a, n in cnt:
        print(f"  {a}: {n}")

    # 2) 打印前 10 个题的：gold、vote、6个rollouts答案
    print("\nSample per-problem (first 10 problems):")
    for pid in sorted(list(answers.keys()))[:10]:
        lst = [a for a in answers[pid] if a is not None]
        if not lst:
            print(f"pid={pid} gold={gold.get(pid)} [no answers]")
            continue
        vote, vn = Counter(lst).most_common(1)[0]
        print(f"\npid={pid} gold={gold.get(pid)} vote={vote} (count={vn}/{len(lst)})")
        print("  rollouts:", lst)

    conn.close()

if __name__ == "__main__":
    main()