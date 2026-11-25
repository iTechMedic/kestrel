#!/usr/bin/env python3
"""Quick accuracy probe: questions with known answers, greedy, thinking off.
Usage: glm_quality.py LABEL --config PATH   (appends to ~/kestrel-bench/quality.jsonl)"""
import argparse, json, os, re, urllib.request

QS = [
    ("What is 347 * 29? Reply with the number only.", r"\b10063\b"),
    ("What is the capital of Australia? One word.", r"canberra"),
    ("How many days are in a leap year? Number only.", r"\b366\b"),
    ("What is the chemical symbol for tungsten? Symbol only.", r"\bW\b"),
    ("If a train leaves at 14:35 and the trip takes 2 hours 50 minutes, when does it arrive (24h HH:MM)? Time only.", r"17:25"),
    ("Spell the word 'necessary' backwards. Letters only.", r"yrassecen"),
    ("What is the derivative of x^3 * sin(x)? Short answer.", r"3x(\^?2|²).{0,12}sin.{0,20}x(\^?3|³).{0,12}cos|x(\^?3|³).{0,12}cos.{0,20}3x(\^?2|²).{0,12}sin"),
    ("Who wrote 'Pride and Prejudice'? Name only.", r"austen"),
    ("Sort these numbers ascending: 42, 7, 19, 3, 88, 21. Comma-separated only.", r"3,\s*7,\s*19,\s*21,\s*42,\s*88"),
    ("What is the largest prime number below 100? Number only.", r"\b97\b"),
    ("Convert 0x1F4 to decimal. Number only.", r"\b500\b"),
    ("In Python, what does len({1, 2, 2, 3}) return? Number only.", r"\b3\b"),
]

def ask(url, key, model, q):
    body = {"model": model, "messages": [{"role": "user", "content": q}], "max_tokens": 120,
            "temperature": 0, "reasoning_effort": "none"}
    req = urllib.request.Request(url + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("label")
    ap.add_argument("--config", default=os.path.expanduser("~/kestrel/maya-maya-s24-hip.json"))
    ap.add_argument("--url", default="http://127.0.0.1:8000/v1")
    a = ap.parse_args(); cfg = json.load(open(a.config))
    out = open(os.path.expanduser("~/kestrel-bench/quality.jsonl"), "a"); ok = 0
    for q, pat in QS:
        ans = ask(a.url, cfg["api_key"], cfg.get("model_name", "glm-5.3-flash"), q).strip()
        good = re.search(pat, ans, re.I | re.S) is not None; ok += good
        out.write(json.dumps({"label": a.label, "q": q, "answer": ans, "ok": good}) + "\n")
        print(f"{'OK ' if good else 'BAD'} | {q[:55]:55} | {ans[:70]!r}")
    print(f"== {a.label}: {ok}/{len(QS)} correct")

if __name__ == "__main__":
    main()
