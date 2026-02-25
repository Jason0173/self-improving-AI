import os
import sqlite3
from dataclasses import dataclass
from typing import Dict, List

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)

DB = "runs.sqlite"
RUN_ID = 7
BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
OUT_DIR = "checkpoints/part2_sft_run7"

MAX_LEN = 512

def load_samples() -> List[Dict[str, str]]:
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT prompt, completion
        FROM sft_samples
        WHERE run_id=?
        ORDER BY problem_id
    """, (RUN_ID,)).fetchall()
    conn.close()
    return [{"prompt": p, "completion": c} for (p, c) in rows]

class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, data, tok):
        self.data = data
        self.tok = tok

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        ex = self.data[idx]
        text = ex["prompt"] + "\n" + ex["completion"]

        enc = self.tok(
            text,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"][0]
        attn = enc["attention_mask"][0]

        # labels = input_ids (standard causal LM SFT)
        return {"input_ids": input_ids, "attention_mask": attn, "labels": input_ids.clone()}

@dataclass
class Collator:
    tok: AutoTokenizer
    def __call__(self, features):
        return self.tok.pad(features, padding=True, return_tensors="pt")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    data = load_samples()
    print(f"Loaded {len(data)} SFT samples from SQLite (run_id={RUN_ID})")

    tok = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        dtype=torch.bfloat16,
    )
    model.train()

    ds = SimpleDataset(data, tok)
    collator = Collator(tok)

    args = TrainingArguments(
        output_dir=OUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=1,
        max_steps=30,                # ✅ 很短，先验证能训练
        learning_rate=1e-5,
        logging_steps=5,
        save_steps=30,
        save_total_limit=1,
        report_to=[],
        bf16=True,
        fp16=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=collator,
    )

    trainer.train()
    trainer.save_model(OUT_DIR)
    tok.save_pretrained(OUT_DIR)
    print(f"✅ saved checkpoint to {OUT_DIR}")

if __name__ == "__main__":
    main()