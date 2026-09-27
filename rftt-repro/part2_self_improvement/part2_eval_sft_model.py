import re
import sqlite3
import time

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

DB = "runs.sqlite"
CKPT = "checkpoints/part2_sft_run7"
RUN_NAME = "part2_sft_eval_run7_gsm8k_test"
LIMIT = 50

PROMPT = """You are a helpful assistant.
Solve the problem step by step.
At the end, output the final numeric answer on a new line in exactly this format:
#### <number>

Problem:
{question}
"""

def extract_gold(answer_gold: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*)", answer_gold)
    return m.group(1).replace(",", "") if m else None

def extract_pred(text: str):
    m = re.search(r"####\s*([-+]?\d[\d,]*\.?\d*)", text)
    if m:
        return m.group(1).replace(",", "")
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", text.replace(",", ""))
    return nums[-1] if nums else None

@torch.inference_mode()
def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # create new run row
    conn.execute("INSERT INTO runs(run_name, model_name) VALUES(?,?)", (RUN_NAME, CKPT))
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    print(f"run_id={run_id} evaluating ckpt={CKPT} limit={LIMIT}")

    rows = conn.execute("""
        SELECT p.id, p.question, p.answer_gold
        FROM problems p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT ?
    """, (LIMIT,)).fetchall()

    tok = AutoTokenizer.from_pretrained(CKPT, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        CKPT,
        device_map="auto",
        dtype=torch.bfloat16,
    )
    model.eval()

    correct = 0
    total = 0

    for pid, question, answer_gold in rows:
        prompt = PROMPT.format(question=question)
        inputs = tok(prompt, return_tensors="pt").to(model.device)

        t0 = time.time()
        out = model.generate(
            **inputs,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            max_new_tokens=128,
            pad_token_id=tok.eos_token_id,
        )
        latency_ms = int((time.time() - t0) * 1000)

        text = tok.decode(out[0], skip_special_tokens=True)

        # store generation
        conn.execute("""
            INSERT OR REPLACE INTO generations(run_id, problem_id, output_text)
            VALUES(?,?,?)
        """, (run_id, pid, text))

        gold = extract_gold(answer_gold)
        pred = extract_pred(text)
        is_correct = 1 if (gold is not None and pred is not None and gold == pred) else 0

        conn.execute("""
            INSERT OR REPLACE INTO evaluations(run_id, problem_id, extracted_answer, is_correct, judge_details)
            VALUES(?,?,?,?,?)
        """, (run_id, pid, pred, is_correct, f"gold={gold} pred={pred} latency_ms={latency_ms}"))

        conn.commit()

        correct += is_correct
        total += 1
        print(f"pid={pid} correct={is_correct} pred={pred} gold={gold} ms={latency_ms}")

    acc = correct / total if total else 0.0
    print(f"✅ done run_id={run_id} total={total} correct={correct} acc={acc:.4f}")
    conn.close()

if __name__ == "__main__":
    main()