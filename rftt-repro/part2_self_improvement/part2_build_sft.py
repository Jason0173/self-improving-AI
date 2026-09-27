import sqlite3

DB = "runs.sqlite"
RUN_ID = 7

PROMPT = """You are a helpful assistant.
Solve the problem step by step.
At the end, output the final numeric answer on a new line in exactly this format:
#### <number>

Problem:
{question}
"""

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # 取出该 run 下涉及的题目
    problems = conn.execute("""
        SELECT DISTINCT p.id, p.question
        FROM trajectories t
        JOIN problems p ON p.id = t.problem_id
        WHERE t.run_id=?
        ORDER BY p.id
    """, (RUN_ID,)).fetchall()

    inserted = 0

    for pid, question in problems:
        # 选 reward 最大、traj_index 最小的轨迹
        row = conn.execute("""
            SELECT id, text
            FROM trajectories
            WHERE run_id=? AND problem_id=?
            ORDER BY reward DESC, traj_index ASC
            LIMIT 1
        """, (RUN_ID, pid)).fetchone()

        if row is None:
            continue

        traj_id, traj_text = row
        prompt = PROMPT.format(question=question)

        # 简化：completion 先直接用完整轨迹文本
        completion = traj_text

        conn.execute("""
            INSERT OR REPLACE INTO sft_samples(run_id, problem_id, prompt, completion, source_traj_id)
            VALUES(?,?,?,?,?)
        """, (RUN_ID, pid, prompt, completion, traj_id))

        inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ built sft_samples for run_id={RUN_ID}, inserted={inserted}")

if __name__ == "__main__":
    main()