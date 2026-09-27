import sqlite3

DB = "runs.sqlite"
RUN_ID = 7

def main():
    conn = sqlite3.connect(DB)

    rows = conn.execute("""
        SELECT id, prompt, completion
        FROM sft_samples
        WHERE run_id=?
        ORDER BY id
    """, (RUN_ID,)).fetchall()

    fixed = 0

    for sid, prompt, completion in rows:
        # 如果 completion 里包含了 prompt，就把 prompt 前缀裁掉
        if completion.startswith(prompt):
            new_completion = completion[len(prompt):].lstrip()
        else:
            # 有些模型 decode 后可能略有差异：再尝试用 prompt 的最后一部分定位
            anchor = prompt[-200:]
            idx = completion.find(anchor)
            if idx != -1:
                new_completion = completion[idx + len(anchor):].lstrip()
            else:
                new_completion = completion  # 找不到就先不动

        if new_completion != completion:
            conn.execute(
                "UPDATE sft_samples SET completion=? WHERE id=?",
                (new_completion, sid),
            )
            fixed += 1

    conn.commit()
    conn.close()
    print(f"✅ fixed completions for run_id={RUN_ID}, updated_rows={fixed}")

if __name__ == "__main__":
    main()