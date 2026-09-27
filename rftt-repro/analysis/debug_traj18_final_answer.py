import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 18
LIMIT = 50

def main():
    conn = sqlite3.connect(DB)

    # 50题列表
    pids = [r[0] for r in conn.execute("""
        SELECT p.id
        FROM problems p
        JOIN datasets d ON d.id=p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT ?
    """, (LIMIT,)).fetchall()]

    # 每题收集 final_answer
    per = defaultdict(list)
    all_ans = []
    for pid, ans in conn.execute("""
        SELECT problem_id, final_answer
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        if pid in set(pids):
            per[pid].append(ans)
            if ans is not None:
                all_ans.append(ans)

    # 全局 top-20
    print("Top-20 most common final_answer across ALL rollouts:")
    for a, n in Counter(all_ans).most_common(20):
        print(f"  {a}: {n}")

    # 哪些题 6 条里全是 None
    none_pids = [pid for pid in pids if all(x is None for x in per.get(pid, []))]
    print(f"\nproblems={len(pids)} all_rollouts_none={len(none_pids)}")
    print("first_15_all_none_pids:", none_pids[:15])

    # 打印前 5 个题的 6 条答案看看像不像污染
    print("\nSample per-problem answers (first 5 problems):")
    for pid in pids[:5]:
        print(f"pid={pid} answers={per.get(pid)}")

    conn.close()

if __name__ == "__main__":
    main()