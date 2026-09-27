import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 20
LIMIT = 50

def main():
    conn = sqlite3.connect(DB)

    pids = [r[0] for r in conn.execute("""
        SELECT p.id
        FROM problems p
        JOIN datasets d ON d.id=p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT ?
    """, (LIMIT,)).fetchall()]
    pid_set = set(pids)

    per = defaultdict(list)
    all_ans = []
    for pid, ans in conn.execute("""
        SELECT problem_id, final_answer
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        if pid in pid_set:
            per[pid].append(ans)
            if ans is not None:
                all_ans.append(ans)

    none_pids = [pid for pid in pids if all(x is None for x in per.get(pid, []))]
    print(f"traj_run_id={TRAJ_RUN_ID} problems={len(pids)} all_rollouts_none={len(none_pids)}")
    print("first_10_all_none_pids:", none_pids[:10])

    print("\nTop-20 most common final_answer across ALL rollouts:")
    for a, n in Counter(all_ans).most_common(20):
        print(f"  {a}: {n}")

    print("\nSample per-problem answers (first 5 problems):")
    for pid in pids[:5]:
        print(f"pid={pid} answers={per.get(pid)}")

    conn.close()

if __name__ == "__main__":
    main()