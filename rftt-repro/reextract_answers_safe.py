import re
import sqlite3

DB = "runs.sqlite"
TRAJ_RUN_ID = 14

def safe_extract(text: str):
    # 1) 优先 ####
    m = re.search(r"####\s*([-+]?\d[\d,]*\.?\d*)", text)
    if m:
        return m.group(1).replace(",", "")

    # 2) 兜底：只看最后两行（避免抽到题目里的数字/中间步骤）
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tail = "\n".join(lines[-2:]) if len(lines) >= 2 else (lines[-1] if lines else "")
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", tail.replace(",", ""))
    return nums[-1] if nums else None

def main():
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT id, text, final_answer
        FROM trajectories
        WHERE run_id=?
    """, (TRAJ_RUN_ID,)).fetchall()

    updated = 0
    null_before = 0
    null_after = 0

    for tid, text, old in rows:
        if old is None:
            null_before += 1
        new = safe_extract(text)
        if new is None:
            null_after += 1
        if new != old:
            conn.execute("UPDATE trajectories SET final_answer=? WHERE id=?", (new, tid))
            updated += 1

    conn.commit()
    conn.close()
    print(f"✅ re-extracted final_answer for traj_run_id={TRAJ_RUN_ID}")
    print(f"rows={len(rows)} updated={updated} null_before={null_before} null_after={null_after}")

if __name__ == "__main__":
    main()