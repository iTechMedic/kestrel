#!/usr/bin/env python3
"""Speed benchmark for a running Kestrel server (OpenAI chat API, streamed).

Greedy, thinking off, fixed prompts, so runs are comparable across settings.
Usage: glm_bench.py LABEL [--runs N] [--max-tokens N] [--url URL] [--config PATH]
Appends one JSON line per run to ~/kestrel-bench/results.jsonl and prints a summary.
"""
import argparse, json, os, statistics, time, urllib.request

PROMPTS = {
    "code": "Write a Python function that parses an ISO 8601 date string without using datetime.fromisoformat, with tests.",
    "explain": "Explain how a transformer language model generates text, step by step, for a curious engineer.",
    "html": "Write a complete single-file HTML page with CSS and JavaScript for a working to-do list app.",
}

def long_doc():
    # ~8K tokens of varied, non-repeating-looking text (numbers break up repetition)
    parts = []
    for i in range(320):
        parts.append(f"Section {i}: The warehouse at site {i*7 % 113} logged {i*37 % 991} units of item "
                     f"SKU-{(i*131) % 10007}, shipped by carrier {['north','south','east','west'][i % 4]} "
                     f"on day {i % 28 + 1}, with a defect rate of {(i*13 % 97)/10:.1f} percent.")
    return " ".join(parts)

def run_one(url, key, model, prompt, max_tokens):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "reasoning_effort": "none",
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(url + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    first = None
    chunks = 0
    usage = None
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            ev = json.loads(data)
            if ev.get("usage"):
                usage = ev["usage"]
            for ch in ev.get("choices", []):
                d = ch.get("delta", {})
                if d.get("content") or d.get("reasoning_content"):
                    if first is None:
                        first = time.perf_counter()
                    chunks += 1
    t1 = time.perf_counter()
    out_toks = (usage or {}).get("completion_tokens", chunks)
    in_toks = (usage or {}).get("prompt_tokens", 0)
    ttft = (first or t1) - t0
    decode_s = max(t1 - (first or t1), 1e-9)
    return {"prompt_tokens": in_toks, "completion_tokens": out_toks, "ttft_s": round(ttft, 3),
            "decode_tok_s": round((out_toks - 1) / decode_s, 2) if out_toks > 1 else 0.0,
            "prompt_tok_s": round(in_toks / ttft, 1) if ttft > 0 else 0.0, "wall_s": round(t1 - t0, 2)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--config", default=os.path.expanduser("~/kestrel/maya-maya-s24-hip.json"))
    ap.add_argument("--no-long", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    key, model = cfg["api_key"], cfg.get("model_name", "glm-5.3-flash")

    # warm-up, not counted
    run_one(a.url, key, model, "Say hello.", 16)

    tests = dict(PROMPTS)
    if not a.no_long:
        tests["long8k"] = long_doc() + "\n\nWhich carrier appears most often above? Answer briefly, then summarise the data."
    os.makedirs(os.path.expanduser("~/kestrel-bench"), exist_ok=True)
    out = open(os.path.expanduser("~/kestrel-bench/results.jsonl"), "a")
    summary = {}
    for name, prompt in tests.items():
        for i in range(a.runs):
            # vary the long prompt per run so the server's prompt cache can't skip the read
            p = prompt if name != "long8k" else f"Run {time.time_ns()}.\n" + prompt
            res = run_one(a.url, key, model, p, a.max_tokens)
            res.update({"label": a.label, "test": name, "run": i, "ts": time.strftime("%Y-%m-%d %H:%M:%S")})
            out.write(json.dumps(res) + "\n"); out.flush()
            summary.setdefault(name, []).append(res)
            print(f"{a.label:>14} {name:>8} run{i}: decode {res['decode_tok_s']:6.2f} tok/s | "
                  f"ttft {res['ttft_s']:6.2f}s | prompt {res['prompt_tokens']:5d} tok @ {res['prompt_tok_s']:7.1f} tok/s | "
                  f"out {res['completion_tokens']}", flush=True)
    short = [r["decode_tok_s"] for n in PROMPTS for r in summary.get(n, [])]
    print(f"== {a.label}: short-prompt decode median {statistics.median(short):.2f} tok/s, "
          f"mean {statistics.mean(short):.2f}")
    if "long8k" in summary:
        L = summary["long8k"]
        print(f"== {a.label}: 8K prompt read {statistics.median(r['prompt_tok_s'] for r in L):.1f} tok/s, "
              f"decode after it {statistics.median(r['decode_tok_s'] for r in L):.2f} tok/s")

if __name__ == "__main__":
    main()
