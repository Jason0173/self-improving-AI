# Part 1: Baseline Replication (SQLite-first Implementation)

## Overview

This project replicates the baseline performance of a reasoning model on GSM8K.

All datasets, model outputs, intermediate artifacts, and evaluation results are stored in a **single SQLite database (`runs.sqlite`)**. No intermediate JSON or CSV files are generated.

---

## Dependencies

Minimal dependencies only:

- torch
- transformers
- datasets
- accelerate

No RL frameworks.
No agent frameworks.
No external evaluation tools.

---

## Database Design

All data is stored in `runs.sqlite`.

### Tables

- `datasets`
- `problems`
- `runs`
- `generations`
- `evaluations`

This ensures full reproducibility and traceability.

---

## Baseline Configuration

- Model: `Qwen/Qwen2.5-3B-Instruct`
- Dataset: GSM8K (test split)
- Decoding: greedy (temperature=0, do_sample=False)
- Max tokens: 128
- Prompt: step-by-step reasoning + enforce `#### <number>` format

---

## Evaluation Method

Gold answer extracted from:

    #### <number>

Prediction extraction:

1. First match `#### <number>` in model output
2. If not found, fallback to last number in output

Correctness: exact match after removing commas.

---

## Result

Run ID: 5  
Dataset: gsm8k/test  
Total evaluated: 50  
Correct: 22  
Accuracy: 0.4400  

All results stored in SQLite.

---

## How to Reproduce

Initialize DB:

    python init_runs_db.py

Load dataset:

    python load_gsm8k.py

Run baseline:

    python run_baseline_hf.py

Evaluate:

    python eval_gsm8k.py

Generate summary:

    python summary_run.py

---

## Notes

- All intermediate results are stored in SQLite.
- No temporary data files are created.
- Fully reproducible using only Python + SQLite.