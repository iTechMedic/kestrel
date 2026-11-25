#!/usr/bin/env python3
"""bench_summary.py [prefix...]: each label's short-prompt decode median and long-prompt read/decode from results.jsonl."""
import os
import json, statistics as st, sys
BENCH = os.environ.get('KESTREL_BENCH_DIR', os.path.expanduser('~/kestrel-bench'))

rows = [json.loads(l) for l in open(os.path.join(BENCH, "results.jsonl"))]
labs = {}
for r in rows:
    labs.setdefault(r["label"], []).append(r)
pre = tuple(sys.argv[1:]) or ("",)
for lab, rs in labs.items():
    if not lab.startswith(pre):
        continue
    short = [r["decode_tok_s"] for r in rs if r["test"] != "long8k"]
    lg = [r for r in rs if r["test"] == "long8k"]
    s = f"{lab:28} short median {st.median(short):5.1f}" if short else f"{lab:28}"
    if lg:
        s += f" | long read {st.mean(r['prompt_tok_s'] for r in lg):5.0f} decode {st.mean(r['decode_tok_s'] for r in lg):5.1f}"
    print(s, rs[-1].get("ts", "")[:16])
