#!/usr/bin/env python3
"""Summaries of the scoring project's large raw files that the package does not ship. Run by the authors only; its
outputs are in data/scoring/ and are read by code/tables/tabA-measurement.py.

Sources (the scoring project, ~/AI@Work/Research/Occ_AI_Exposure, not distributed: 1.1 GB of model output):
  batches/*_results.jsonl                      Anthropic Message Batches results for Prompt 0 and ratings A, B, C
                                               (Claude Haiku 4.5, April 10, 2026): per-request token usage.
  outputs/prompt_0/production/p0_<task>.json   Prompt 0 decomposition of each of the 19,281 tasks.
Outputs:
  data/scoring/anthropic_usage.csv             per prompt: requests, input, output, cache-write, and cache-read tokens.
  data/scoring/p0_subtasks.csv                 one row per subtask: task_id, subtask_id, activity_type, pct_of_total_time.
"""
import glob, json, os, pandas as pd
O = os.path.expanduser("~/AI@Work/Research/Occ_AI_Exposure"); HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "..", "data", "scoring")
rows = []
for prompt in "0abc":
    files = glob.glob(f"{O}/batches/p0_production_part*_results.jsonl") if prompt == "0" else glob.glob(f"{O}/batches/p{prompt}_haiku_production_part*_results.jsonl")
    u = {}; n = 0
    def find(d):
        if isinstance(d, dict):
            if isinstance(d.get("usage"), dict): return d["usage"]
            for v in d.values():
                r = find(v)
                if r: return r
    for f in sorted(files):
        for line in open(f):
            try: j = json.loads(line)
            except Exception: continue
            n += 1; us = find(j) or {}
            for k, v in us.items():
                if isinstance(v, (int, float)): u[k] = u.get(k, 0) + v
    rows.append({"prompt": prompt, "requests": n, "input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                 "cache_creation_input_tokens": u.get("cache_creation_input_tokens", 0), "cache_read_input_tokens": u.get("cache_read_input_tokens", 0)})
    print(rows[-1])
pd.DataFrame(rows).to_csv(os.path.join(D, "anthropic_usage.csv"), index=False)
sub = []
for f in glob.glob(f"{O}/outputs/prompt_0/production/p0_*.json"):
    j = json.load(open(f)); tid = int(os.path.basename(f)[3:-5])
    for s in j["task_decomposition"]: sub.append((tid, s["subtask_id"], s["activity_type"], s["pct_of_total_time"]))
pd.DataFrame(sub, columns=["task_id", "subtask_id", "activity_type", "pct_of_total_time"]).sort_values(["task_id", "subtask_id"]).to_csv(os.path.join(D, "p0_subtasks.csv"), index=False)
print("subtasks", len(sub), "tasks", len({s[0] for s in sub}))
