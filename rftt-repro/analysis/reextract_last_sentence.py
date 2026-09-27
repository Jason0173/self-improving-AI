import re
import sqlite3

DB = "runs.sqlite"
TRAJ_RUN_ID = 18   # 你现在用18

def extract_last_sentence(text: str):
    text = text.strip()
    if not text:
        return None

    # 取最后一句（按句号/换行切）
    sentences = re.split(r"[.\n]", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return None

    last = sentences[-1]

    # 从最后一句中提取数字
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", last.replace(",", ""))
    return nums[-1] if nums else None

def main():
    conn = sqlite3.connect(DB)

    rows = conn.execute("""
        SELECT id, text, final_answer
        FROM trajectories
        WHERE run_id=?
    """, (TRAJ_RUN_ID,)).fetchall()

    updated = 0
    for tid, text, old in rows:
        new = extract_last_sentence(text)
        if new != old:
            conn.execute("UPDATE trajectories SET final_answer=? WHERE id=?", (new, tid))
            updated += 1

    conn.commit()
    conn.close()

    print(f"✅ updated final_answer for run_id={TRAJ_RUN_ID}")
    print(f"rows={len(rows)} updated={updated}")

if __name__ == "__main__":
    main()