import json
import re
import sqlite3
from collections import Counter, defaultdict

DB = "runs.sqlite"
TRAJ_RUN_ID = 18
NEW_RUN_NAME = "part2_majority_vote_eval_from_traj18_last_sentence_extract"
MODEL_NAME = "vote_over_rollouts"

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # create new run
    conn.execute("INSERT INTO runs(run_name, model_name) VALUES(?,?)", (NEW_RUN_NAME, MODEL_NAME))
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    print(f"new_vote_run_id={run_id} (from trajectories run_id={TRAJ_RUN_ID})")

    # gold per problem
    gold_map = {}
    for pid, gold in conn.execute("""
        SELECT p.id, p.answer_gold
        FROM problems p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
    """):
        gold_map[pid] = extract_gold(gold)

    # collect answers per problem from trajectories
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
        gold = gold_map.get(pid)
        if gold is None or len(ans_list) == 0:
            continue

        vote_pred, vote_n = Counter(ans_list).most_common(1)[0]
        is_correct = 1 if vote_pred == gold else 0

        # store a "generation" record (compact)
        out_text = f"#### {vote_pred}"
        conn.execute("""
            INSERT OR REPLACE INTO generations(run_id, problem_id, output_text)
            VALUES(?,?,?)
        """, (run_id, pid, out_text))

        meta = {"vote_count": vote_n, "rollouts": len(ans_list), "source_traj_run_id": TRAJ_RUN_ID}
        conn.execute("""
            INSERT OR REPLACE INTO evaluations(run_id, problem_id, extracted_answer, is_correct, judge_details)
            VALUES(?,?,?,?,?)
        """, (run_id, pid, vote_pred, is_correct, json.dumps({"gold": gold, "pred": vote_pred, **meta})))

        total += 1
        correct += is_correct

    conn.commit()
    conn.close()

    acc = correct / total if total else 0.0
    print(f"✅ wrote vote results: run_id={run_id} total={total} correct={correct} acc={acc:.4f}")

if __name__ == "__main__":
    main()