#!/usr/bin/env python3
"""Tool-loop turns and a user turn against Kestrel on :8000 - does the next turn reuse the last answer's state?"""
import json, sys, time, urllib.request

cfg = json.load(open(sys.argv[1]))
key = cfg.get("api_key") or ""
URL = "http://127.0.0.1:8000/v1/chat/completions"


def call(messages, tools):
    body = {"model": "glm", "messages": messages, "tools": tools, "max_tokens": 1500, "temperature": 0}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=900))
    return r, time.time() - t


tools = [{"type": "function", "function": {
    "name": "write_file", "description": "Write a file to disk.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                   "required": ["path", "content"]}}}]
rules = "\n".join(f"Rule {i}: keep code small, typed, and documented; prefer the standard library; name things clearly."
                  for i in range(120))
msgs = [{"role": "system", "content": "You are a coding agent. Use tools to write files.\n" + rules},
        {"role": "user", "content": "Write a Python module primes.py with a function primes(n) returning the primes "
                                    "below n (a sieve), using write_file. Then tell me it is done."}]
for turn in (1, 2, 3):
    r, dt = call(msgs, tools)
    ch = r["choices"][0]
    m, u = ch["message"], r.get("usage", {})
    tcs = m.get("tool_calls") or []
    print(f"turn {turn}: {dt:.1f}s prompt {u.get('prompt_tokens')} out {u.get('completion_tokens')} "
          f"finish {ch['finish_reason']} tool_calls {len(tcs)} reasoning {len(m.get('reasoning_content') or '')} chars")
    a = {"role": "assistant", "content": m.get("content") or ""}
    if m.get("reasoning_content"):
        a["reasoning_content"] = m["reasoning_content"]
    if tcs:
        a["tool_calls"] = tcs
    msgs.append(a)
    if not tcs:
        print("  answer:", (m.get("content") or "")[:200].replace("\n", " "))
        break
    for tc in tcs:
        msgs.append({"role": "tool", "tool_call_id": tc["id"],
                     "content": "wrote " + str(len(tc["function"]["arguments"])) + " bytes"})
msgs.append({"role": "user", "content": "Thanks. In one sentence, what is the sieve's time complexity?"})
r, dt = call(msgs, tools)
u = r.get("usage", {})
print(f"user turn: {dt:.1f}s prompt {u.get('prompt_tokens')} out {u.get('completion_tokens')}:",
      (r["choices"][0]["message"].get("content") or "")[:200].replace("\n", " "))
