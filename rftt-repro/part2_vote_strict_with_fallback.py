import json
import re
import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"

TRAJ_RUN_ID = 14          # 你的 rollouts 轨迹 run
BASELINE_RUN_ID = 5       # 你的 greedy baseline run（50题）
NEW_RUN_NAME = "part2_vote_strict_hash_fallback_baseline_r5_traj14"
MODEL_NAME = "strict_vote_over_rollouts_with_baseline_fallback"

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def extract_hash_only(text: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*\.?\d*)", text)
    return m.group(1).replace(",", "") if m else None

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # create new run
    conn.execute("INSERT INTO runs(run_name, model_name) VALUES(?,?)", (NEW_RUN_NAME, MODEL_NAME))
    new_run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    print(f"new_run_id={new_run_id} (traj_run_id={TRAJ_RUN_ID}, baseline_run_id={BASELINE_RUN_ID})")

    # gold per problem (limit 50, same as your baseline setting)
    problems = conn.execute("""
        SELECT p.id, p.answer_gold
        FROM problems p
        JOIN datasets d ON d.id=p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT 50
    """).fetchall()
    gold = {pid: extract_gold(g) for pid, g in problems}

    # baseline predictions from evaluations (already extracted_answer)
    baseline_pred = dict(conn.execute("""
        SELECT problem_id, extracted_answer
        FROM evaluations
        WHERE run_id=?
    """, (BASELINE_RUN_ID,)).fetchall())

    # collect STRICT answers from trajectories text (only those with ####)
    strict_answers = defaultdict(list)
    for pid, text in conn.execute("""
        SELECT problem_id, text
        FROM trajectories
        WHERE run_id=?
        ORDER BY problem_id, traj_index
    """, (TRAJ_RUN_ID,)):
        a = extract_hash_only(text)
        if a is not None:
            strict_answers[pid].append(a)

    total = 0
    correct = 0
    used_fallback = 0
    used_vote = 0

    for pid in [pid for pid, _ in problems]:
        g = gold.get(pid)
        if g is None:
            continue

        cand = strict_answers.get(pid, [])
        meta = {
            "source_traj_run_id": TRAJ_RUN_ID,
            "baseline_run_id": BASELINE_RUN_ID,
            "n_strict": len(cand),
            "rollouts_total": 6,
        }

        if len(cand) > 0:
            # majority vote on strict answers
            pred, n = Counter(cand).most_common(1)[0]
            meta["mode"] = "strict_vote"
            meta["vote_count"] = n
            used_vote += 1
        else:
            # fallback to baseline
            pred = baseline_pred.get(pid)
            meta["mode"] = "fallback_baseline"
            used_fallback += 1

        is_correct = 1 if (pred is not None and pred == g) else 0

        conn.execute("""
            INSERT OR REPLACE INTO generations(run_id, problem_id, output_text)
            VALUES (?,?,?)
        """, (new_run_id, pid, f"#### {pred}" if pred is not None else ""))

        conn.execute("""
            INSERT OR REPLACE INTO evaluations(run_id, problem_id, extracted_answer, is_correct, judge_details)
            VALUES (?,?,?,?,?)
        """, (new_run_id, pid, pred, is_correct, json.dumps({"gold": g, "pred": pred, **meta})))

        total += 1
        correct += is_correct

    conn.commit()
    conn.close()

    acc = correct / total if total else 0.0
    print(f"✅ strict-vote+fallback done: run_id={new_run_id} total={total} correct={correct} acc={acc:.4f}")
    print(f"used_vote={used_vote} used_fallback={used_fallback}")

if __name__ == "__main__":
    main()