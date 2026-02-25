import sqlite3
from transformers import AutoTokenizer

DB = "runs.sqlite"
RUN_ID = 7
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

def main():
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT problem_id, prompt, completion
        FROM sft_samples
        WHERE run_id=?
        ORDER BY problem_id
    """, (RUN_ID,)).fetchall()
    conn.close()

    print(f"Loaded sft_samples: {len(rows)} (run_id={RUN_ID})")

    tok = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

    # 取第一条做检查
    pid, prompt, completion = rows[0]
    text = prompt + "\n" + completion

    enc = tok(text, return_tensors="pt", truncation=True, max_length=2048)
    print(f"Example problem_id={pid}")
    print(f"token_count={enc['input_ids'].shape[-1]}")
    print("prompt_preview:", prompt[:200].replace("\n", "\\n"))
    print("completion_preview:", completion[:200].replace("\n", "\\n"))
    print("✅ tokenize ok")

if __name__ == "__main__":
    main()