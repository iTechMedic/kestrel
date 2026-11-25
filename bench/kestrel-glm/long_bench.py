#!/usr/bin/env python3
"""A long prompt (about N thousand tokens, the agent sessions' size) against Kestrel on :8000: the read's speed and
the decode after it.  Each run starts with a fresh nonce, so nothing is reused.  Appends to long_results.jsonl."""
import os
import argparse, json, sys, time, urllib.request
BENCH = os.environ.get('KESTREL_BENCH_DIR', os.path.expanduser('~/kestrel-bench'))
os.makedirs(BENCH, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glm_bench import long_doc  # noqa: E402  (13.7K tokens of tabular text)

ap = argparse.ArgumentParser()
ap.add_argument("label")
ap.add_argument("--config", default=os.environ.get("KESTREL_CONFIG"), required=not os.environ.get("KESTREL_CONFIG"), help="the server's config (or KESTREL_CONFIG)")
ap.add_argument("--reps", type=int, default=4, help="copies of the 13.7K document (4: about 55K tokens)")
ap.add_argument("--out", type=int, default=256)
a = ap.parse_args()
key = json.load(open(a.config)).get("api_key") or ""
doc = "\n\n".join(f"Part {i + 1}.\n" + long_doc() for i in range(a.reps))
prompt = (f"Run {time.time_ns()}.\n" + doc +
          "\n\nWhich carrier appears most often across all parts? Answer briefly, then summarise the data.")
body = {"model": "glm", "messages": [{"role": "user", "content": prompt}], "max_tokens": a.out, "temperature": 0,
        "stream": True, "stream_options": {"include_usage": True}}
req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                             {"Content-Type": "application/json", "Authorization": "Bearer " + key})
t0 = time.time()
ttft, usage, n = None, {}, 0
with urllib.request.urlopen(req, timeout=3600) as r:
    for raw in r:
        line = raw.decode().strip()
        if not line.startswith("data:") or line[5:].strip() == "[DONE]":
            continue
        ev = json.loads(line[5:])
        usage = ev.get("usage") or usage
        for ch in ev.get("choices") or []:
            d = ch.get("delta") or {}
            if d.get("content") or d.get("reasoning_content"):
                if ttft is None:
                    ttft = time.time() - t0
                n += 1
t1 = time.time()
pt, ct = usage.get("prompt_tokens", 0), usage.get("completion_tokens", n)
dec = (ct - 1) / max(1e-9, t1 - t0 - ttft) if ttft else 0.0
res = {"label": a.label, "prompt_tokens": pt, "ttft_s": round(ttft or 0, 2), "read_tok_s": round(pt / (ttft or 1), 1),
       "completion_tokens": ct, "decode_tok_s": round(dec, 2), "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
print(f"{a.label}: prompt {pt} tok read in {res['ttft_s']} s ({res['read_tok_s']} tok/s) | decode after {dec:.2f} tok/s "
      f"({ct} tok)")
open(os.path.join(BENCH, "long_results.jsonl"), "a").write(json.dumps(res) + "\n")
