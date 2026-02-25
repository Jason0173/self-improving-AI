PRAGMA foreign_keys=ON;

-- 1) Record configuration for the proposed method (e.g.: rollouts, depth, token set, reward type)
CREATE TABLE IF NOT EXISTS proposed_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  config_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2) Trajectories/candidate solutions generated per MCTS/search run (multiple per problem)
CREATE TABLE IF NOT EXISTS trajectories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  problem_id INTEGER NOT NULL,
  traj_index INTEGER NOT NULL,          -- Index of this trajectory
  text TEXT NOT NULL,                   -- Full output/reasoning of this trajectory
  final_answer TEXT,                    -- Extracted answer (nullable)
  reward REAL,                          -- Reward for this trajectory (nullable)
  meta_json TEXT,                       -- e.g.: token path / tree stats
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(run_id) REFERENCES runs(id),
  FOREIGN KEY(problem_id) REFERENCES problems(id),
  UNIQUE(run_id, problem_id, traj_index)
);

-- 3) Convert selected good trajectories into SFT data (prompt/completion)
CREATE TABLE IF NOT EXISTS sft_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  problem_id INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  completion TEXT NOT NULL,
  source_traj_id INTEGER,               -- Source trajectory id (nullable)
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(run_id) REFERENCES runs(id),
  FOREIGN KEY(problem_id) REFERENCES problems(id),
  FOREIGN KEY(source_traj_id) REFERENCES trajectories(id),
  UNIQUE(run_id, problem_id)
);

-- 4) Batch records for RL training (no framework; we only store data and statistics)
CREATE TABLE IF NOT EXISTS rl_batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  step INTEGER NOT NULL,
  batch_json TEXT NOT NULL,             -- Sampled trajectory ids / advantages / logprobs, etc.
  stats_json TEXT,                      -- loss/kl/reward mean, etc.
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(run_id) REFERENCES runs(id),
  UNIQUE(run_id, step)
);