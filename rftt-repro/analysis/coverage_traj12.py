import sqlite3
from collections import defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 14

def main():
    conn = sqlite3.connect(DB)
    ans = defaultdict(int)
    total_probs = 0
    # 50题列表（与你生成 trajectories 的 LIMIT 一致）
    pids = [r[0] for r in conn.execute("""
        SELECT p.id
        FROM problems p
        JOIN datasets d ON d.id=p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT 50
    """).fetchall()]
    total_probs = len(pids)

    # 统计每题有多少条 final_answer 非空
    for pid, c in conn.execute("""
        SELECT problem_id, SUM(CASE WHEN final_answer IS NOT NULL THEN 1 ELSE 0 END) AS cnt
        FROM trajectories
        WHERE run_id=?
        GROUP BY problem_id
    """, (TRAJ_RUN_ID,)):
        ans[pid] = c or 0

    have_any = sum(1 for pid in pids if ans.get(pid, 0) > 0)
    all_none = total_probs - have_any
    avg_valid = sum(ans.get(pid, 0) for pid in pids) / total_probs

    print(f"problems={total_probs}")
    print(f"have_any_valid_answer={have_any}")
    print(f"all_rollouts_invalid={all_none}")
    print(f"avg_valid_rollouts_per_problem={avg_valid:.2f}")

    # 列出前 10 个完全无效的题 id
    bad = [pid for pid in pids if ans.get(pid, 0) == 0][:10]
    print("first_10_no_valid_answer_pids:", bad)

    conn.close()

if __name__ == "__main__":
    main()