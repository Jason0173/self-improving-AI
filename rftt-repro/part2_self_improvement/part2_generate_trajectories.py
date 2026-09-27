import json
import re
import sqlite3
import time
from collections import Counter

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

DB = "runs.sqlite"

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
RUN_NAME = "part2_rollouts_vote_strict_hash_qwen2.5-3b_gsm8k_test"

LIMIT_PROBLEMS = 50
N_ROLLOUTS = 6

PROMPT = """You are a helpful assistant.
Solve the problem step by step.

At the very end, output the final answer as a number, then output the token <FINAL> on the same line.
Example: 42 <FINAL>

Problem:
{question}
"""

DECODE = dict(
    do_sample=True,
    temperature=0.3,
    top_p=0.9,
    max_new_tokens=128,
)

def extract_pred(text: str):
    if "<FINAL>" not in text:
        return None
    prefix = text.split("<FINAL>")[0][-200:]  # only look near the end
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", prefix.replace(",", ""))
    return nums[-1] if nums else None
def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # create a run row in existing runs table (your runs table has: run_name, model_name)
    conn.execute("INSERT INTO runs(run_name, model_name) VALUES(?,?)", (RUN_NAME, MODEL_NAME))
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()

    # load problems
    rows = conn.execute("""
        SELECT p.id, p.question
        FROM problems p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT ?
    """, (LIMIT_PROBLEMS,)).fetchall()

    print(f"run_id={run_id} problems={len(rows)} rollouts_per_problem={N_ROLLOUTS}")

    tok = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    model.eval()

    for (problem_id, question) in rows:
        prompt = PROMPT.format(question=question)

        texts = []
        answers = []

        t0 = time.time()
        for k in range(N_ROLLOUTS):
            inputs = tok(prompt, return_tensors="pt").to(model.device)
            with torch.inference_mode():
                out = model.generate(
                    **inputs,
                    do_sample=DECODE["do_sample"],
                    temperature=DECODE["temperature"],
                    top_p=DECODE["top_p"],
                    max_new_tokens=DECODE["max_new_tokens"],
                    pad_token_id=tok.eos_token_id,
                )
            text = tok.decode(out[0], skip_special_tokens=True)
            ans = extract_pred(text)

            texts.append(text)
            answers.append(ans)

        # majority vote consistency reward: top_answer fraction
        cnt = Counter([a for a in answers if a is not None])
        if cnt:
            top_ans, top_n = cnt.most_common(1)[0]
            consensus = top_n / N_ROLLOUTS
        else:
            top_ans, consensus = None, 0.0

        # store each rollout as a trajectory row
        for idx, (text, ans) in enumerate(zip(texts, answers)):
            # simple reward: 1.0 if matches majority answer else 0.0 (or 0.5 if tie not handled)
            r = 1.0 if (top_ans is not None and ans == top_ans) else 0.0
            meta = {
                "majority_answer": top_ans,
                "consensus": consensus,
                "rollouts": N_ROLLOUTS,
            }
            conn.execute("""
                INSERT OR REPLACE INTO trajectories(
                    run_id, problem_id, traj_index, text, final_answer, reward, meta_json
                ) VALUES (?,?,?,?,?,?,?)
            """, (run_id, problem_id, idx, text, ans, r, json.dumps(meta)))

        conn.commit()
        ms = int((time.time() - t0) * 1000)
        print(f"problem_id={problem_id} stored={N_ROLLOUTS} majority={top_ans} consensus={consensus:.2f} time_ms={ms}")

    conn.close()
    print("✅ trajectories stored")

if __name__ == "__main__":
    main()