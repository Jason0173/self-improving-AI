# Self-Improving Math Reasoning on GSM8K (RFTT-inspired)

Can a small instruction-tuned LLM improve its own math reasoning without human labels?

This project is a compute-limited take on the idea behind *RFTT: Reinforced Functional Token Tuning*. Instead of MCTS with functional tokens, it uses a simpler self-improvement loop on **Qwen2.5-3B-Instruct** and the **GSM8K** test set:

1. **Part 1, baseline.** Measure greedy accuracy under different prompts.
2. **Part 2, self-improvement.** Sample several rollouts per problem, use majority-vote agreement as a self-generated reward, keep the best trajectories as SFT data, fine-tune, and re-evaluate.

Every dataset row, generation, trajectory, SFT sample and evaluation is stored in one SQLite database (`runs.sqlite`), so each number below can be traced back to the exact model outputs that produced it.

## Results

All runs use the first 50 problems of the GSM8K test split. Run IDs refer to the `runs` table in `runs.sqlite`.

**Part 1: baselines (greedy decoding)**

| Run | Model | Prompt | Correct | Accuracy |
|---|---|---|---|---|
| 3 | Qwen2.5-0.5B-Instruct | direct answer | 7 / 50 | 14% |
| 4 | Qwen2.5-3B-Instruct | direct answer | 15 / 50 | 30% |
| 5 | Qwen2.5-3B-Instruct | step-by-step + `#### <number>` format | **22 / 50** | **44%** |

**Part 2: self-improvement (Qwen2.5-3B-Instruct, 6 rollouts per problem, temperature 0.3)**

| Run | Method | Correct | Accuracy |
|---|---|---|---|
| 11 | Majority vote over rollouts | 8 / 50 | 16% |
| 15 | Majority vote, stricter answer extraction | 9 / 50 | 18% |
| 16 | Vote on rollouts with a `####` answer, fall back to the greedy baseline otherwise | 22 / 50 | 44% |
| 8 | SFT on self-selected trajectories (5 samples, 30 steps), greedy eval | 5 / 50 | 10% |

## What I learned

- **Prompt format was the biggest lever.** Asking for step-by-step reasoning plus a fixed `#### <number>` answer line took the 3B model from 30% to 44% with no training.
- **In Part 2 the bottleneck was answer extraction, not voting.** Only 39 of 300 rollouts (18 of 50 problems) ended with a parseable `#### <number>` answer. The generation budget (128 new tokens) cut many rollouts off before the final line, and the decoded text also contains the prompt, so looser parsers could pick up numbers from the question. On the 18 problems where voting applied, voting and the greedy baseline were each right on 8, so run 16 matches the baseline rather than beating it.
- **SFT on a handful of self-labelled samples hurt.** Five trajectories and 30 steps were not enough signal, and the first version of the SFT data still contained the prompt inside the completion (see `part2_self_improvement/part2_fix_sft_completion.py`). The SFT evaluation also used a shorter generation budget than the baseline, so it is not a like-for-like comparison.
- **Next steps:** decode only the newly generated tokens, raise the token budget, and scale up the number of voted trajectories before trying SFT again.

## Project structure

```
rftt-repro/
├── runs.sqlite                  # all data, generations and evaluations
├── requirements.txt
├── db/                          # schema and migrations
│   ├── init_runs_db.py
│   ├── migrate_part2.sql
│   └── apply_migration.py
├── part1_baseline/              # load GSM8K, run and score the greedy baseline
│   ├── load_gsm8k.py
│   ├── run_baseline_hf.py
│   ├── eval_gsm8k.py
│   ├── summary_run.py
│   └── report_run.py
├── part2_self_improvement/      # rollouts, voting, SFT data, training, eval
│   ├── part2_generate_trajectories.py
│   ├── part2_vote_report.py
│   ├── part2_write_vote_to_db.py
│   ├── part2_vote_strict_with_fallback.py
│   ├── part2_build_sft.py
│   ├── part2_fix_sft_completion.py
│   ├── part2_check_sft_data.py
│   ├── part2_sft_train.py
│   └── part2_eval_sft_model.py
├── analysis/                    # answer-coverage checks, re-extraction, run comparison
└── tests/
```

### Database schema

| Table | Holds |
|---|---|
| `datasets`, `problems` | GSM8K test split (1,319 problems) with gold answers |
| `runs` | one row per experiment (name, model, timestamp) |
| `generations`, `evaluations` | model output, extracted answer and correctness per problem |
| `trajectories` | sampled rollouts with extracted answer, vote-based reward and metadata |
| `sft_samples` | prompt / completion pairs selected from trajectories |

## How to run

Run every command from the `rftt-repro/` folder, since the scripts open `runs.sqlite` in the current directory. The committed `runs.sqlite` already contains all the runs above; to start from scratch, move it aside first.

```bash
pip install -r requirements.txt

# Part 1
python db/init_runs_db.py
python part1_baseline/load_gsm8k.py
python part1_baseline/run_baseline_hf.py
python part1_baseline/eval_gsm8k.py        # set RUN_ID at the top of the file
python part1_baseline/summary_run.py

# Part 2
python db/apply_migration.py
python part2_self_improvement/part2_generate_trajectories.py
python part2_self_improvement/part2_vote_strict_with_fallback.py
python part2_self_improvement/part2_build_sft.py
python part2_self_improvement/part2_fix_sft_completion.py
python part2_self_improvement/part2_sft_train.py
python part2_self_improvement/part2_eval_sft_model.py

# Compare runs
python analysis/compare_runs.py

# Tests (no GPU needed)
pytest tests
```

Run IDs are set as constants at the top of each script. Update them to match the IDs printed by the previous step.

## Tech

Python, PyTorch, Hugging Face Transformers and Datasets, SQLite, pytest
