import re
import sqlite3

DB = "runs.sqlite"
TRAJ_RUN_ID = 18

ANCHORS = [
    r"####\s*([-+]?\d[\d,]*\.?\d*)",
    r"Answer:\s*([-+]?\d[\d,]*\.?\d*)",
    r"Final answer:\s*([-+]?\d[\d,]*\.?\d*)",
    r"The answer is\s*([-+]?\d[\d,]*\.?\d*)",
]

def extract_anchored(text: str):
    if not text:
        return None

    # 1) direct patterns
    for pat in ANCHORS:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace(",", "")

    # 2) keyword-near tail window
    # take last ~600 chars to avoid grabbing question text
    tail = text[-600:]

    # If tail contains an "answer-ish" keyword, extract last number from tail
    if re.search(r"(answer|final|therefore|thus|so)\b", tail, flags=re.IGNORECASE):
        nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", tail.replace(",", ""))
        if nums:
            return nums[-1]

    # 3) safer fallback: last 3 non-empty lines, but only if a line has keyword
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in reversed(lines[-3:]):
        if re.search(r"(answer|final|therefore|thus|so)\b", ln, flags=re.IGNORECASE):
            nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", ln.replace(",", ""))
            if nums:
                return nums[-1]

    return None

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
        new = extract_anchored(text)
        if new is None:
            null_after += 1
        if new != old:
            conn.execute("UPDATE trajectories SET final_answer=? WHERE id=?", (new, tid))
            updated += 1

    conn.commit()
    conn.close()

    print(f"✅ re-extracted (anchored) final_answer for traj_run_id={TRAJ_RUN_ID}")
    print(f"rows={len(rows)} updated={updated} null_before={null_before} null_after={null_after}")

if __name__ == "__main__":
    main()