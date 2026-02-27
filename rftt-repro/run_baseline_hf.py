import json
import time
import sqlite3

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

DB = "runs.sqlite"

PROMPT = """You are a helpful assistant.
Solve the problem step by step.
At the end, output the final numeric answer on a new line in exactly this format:
#### <number>

Problem:
{question}
"""
def main():
    # 1) 选择一个小模型先跑通（下载快、显存压力小）
    model_name = "Qwen/Qwen2.5-3B-Instruct"  # 非常小，适合先验证流程
    run_name = "baseline_cot_hash_qwen2.5-3b_gsm8k_test"

    decoding = {
        "do_sample": False,
        "temperature": 0.0,
        "top_p": 1.0,
        "max_new_tokens": 256
    }

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON;")

    # 2) 新建 run 记录
    conn.execute(
        "INSERT INTO runs(run_name, model_name) VALUES(?, ?)",
        (run_name, model_name),
    )
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()

    # 3) 取 GSM8K test 前 50 题
    rows = conn.execute("""
        SELECT p.id, p.question
        FROM problems p
        JOIN datasets d ON d.id = p.dataset_id
        WHERE d.name='gsm8k' AND d.split='test'
        ORDER BY p.id
        LIMIT 50
    """).fetchall()

    print(f"Loaded {len(rows)} problems. Loading model: {model_name}")

    tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )
    model.eval()

    for (problem_id, question) in rows:
        prompt = PROMPT.format(question=question)

        t0 = time.time()
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            out = model.generate(
                **inputs,
                do_sample=decoding["do_sample"],
                temperature=decoding["temperature"],
                top_p=decoding["top_p"],
                max_new_tokens=decoding["max_new_tokens"],
                pad_token_id=tok.eos_token_id,
            )
        latency_ms = int((time.time() - t0) * 1000)

        text = tok.decode(out[0], skip_special_tokens=True)

        conn.execute(
            """
            INSERT OR REPLACE INTO generations(run_id, problem_id, output_text)
            VALUES(?,?,?)
            """,
            (run_id, problem_id, text),
        )
        conn.commit()

        print(f"done problem_id={problem_id} latency_ms={latency_ms}")

    # 保存一些 run 元信息（可选：我们先简单放在 runs 表里，后面再扩展）
    print(f"✅ Generation finished. run_id={run_id}")

if __name__ == "__main__":
    main()