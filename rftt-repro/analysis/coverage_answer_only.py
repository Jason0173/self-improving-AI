import re
import sqlite3
from collections import defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 18
LIMIT = 50

def has_answer(text: str) -> bool:
    return re.search(r"Answer:\s*([-+]?\d[\d,]*\.?\d*)", text) is not None

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

    cnt_per_pid = defaultdict(int)

    for pid, text in conn.execute("""
        SELECT problem_id, text
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        if has_answer(text):
            cnt_per_pid[pid] += 1

    have_any = sum(1 for pid in pids if cnt_per_pid.get(pid, 0) > 0)
    all_none = len(pids) - have_any
    avg = sum(cnt_per_pid.get(pid, 0) for pid in pids) / len(pids)

    print(f"traj_run_id={TRAJ_RUN_ID} problems={len(pids)}")
    print(f"have_any_answer={have_any}")
    print(f"all_rollouts_no_answer={all_none}")
    print(f"avg_answer_rollouts_per_problem={avg:.2f}")

    bad = [pid for pid in pids if cnt_per_pid.get(pid, 0) == 0][:10]
    print("first_10_no_answer_pids:", bad)

    conn.close()

if __name__ == "__main__":
    main()