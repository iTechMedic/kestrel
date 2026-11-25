#!/usr/bin/env python3
"""A coding agent's session against Kestrel on :8000: several tool-loop turns with long answers, then a user turn.
Per turn: wall time, time to the first token (streamed), prompt and answer tokens.  The engine log says what each
turn read (glm vram: prompt N tokens read in S s) and whether the last answer's state went on (glm reuse)."""
import json, sys, time, urllib.request

cfg = json.load(open(sys.argv[1]))
key = cfg.get("api_key") or ""
URL = "http://127.0.0.1:8000/v1/chat/completions"


def call(messages, tools, max_tokens=4000):
    body = {"model": "glm", "messages": messages, "tools": tools, "max_tokens": max_tokens, "temperature": 0,
            "stream": True, "stream_options": {"include_usage": True}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t0 = time.time()
    ttft = None
    content, reasoning, usage, finish = [], [], {}, None
    calls = {}
    with urllib.request.urlopen(req, timeout=1800) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            ev = json.loads(data)
            if ev.get("usage"):
                usage = ev["usage"]
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                if ttft is None and (d.get("content") or d.get("reasoning_content") or d.get("tool_calls")):
                    ttft = time.time() - t0
                content.append(d.get("content") or "")
                reasoning.append(d.get("reasoning_content") or "")
                for tc in d.get("tool_calls") or []:
                    c = calls.setdefault(tc.get("index", 0), {"id": None, "type": "function",
                                                               "function": {"name": "", "arguments": ""}})
                    if tc.get("id"):
                        c["id"] = tc["id"]
                    f = tc.get("function") or {}
                    c["function"]["name"] += f.get("name") or ""
                    c["function"]["arguments"] += f.get("arguments") or ""
                finish = ch.get("finish_reason") or finish
    msg = {"role": "assistant", "content": "".join(content)}
    if "".join(reasoning):
        msg["reasoning_content"] = "".join(reasoning)
    if calls:
        msg["tool_calls"] = [calls[i] for i in sorted(calls)]
    return msg, usage, finish, ttft or 0.0, time.time() - t0


tools = [{"type": "function", "function": {
    "name": "write_file", "description": "Write a file to disk.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                   "required": ["path", "content"]}}}]
rules = "\n".join(f"Rule {i}: keep code small, typed, and documented; prefer the standard library; name things clearly."
                  for i in range(120))
msgs = [{"role": "system", "content": "You are a coding agent. Use the write_file tool to write files; write each "
                                      "file in one call.\n" + rules},
        {"role": "user", "content": "Build a small inventory library in Python, one write_file call per step: "
                                    "(1) inventory.py - an Inventory class with add, remove, find, low_stock and "
                                    "to_json/from_json, fully typed with docstrings; (2) test_inventory.py - pytest "
                                    "tests covering every method and edge case; (3) cli.py - an argparse CLI over "
                                    "it. Do the steps in order, then summarise."}]
turn = 0
while turn < 6:
    turn += 1
    m, u, fin, ttft, wall = call(msgs, tools)
    tcs = m.get("tool_calls") or []
    print(f"turn {turn}: ttft {ttft:5.1f}s wall {wall:6.1f}s | prompt {u.get('prompt_tokens')} answer "
          f"{u.get('completion_tokens')} | {fin} | " + (", ".join(json.loads(tc['function']['arguments'] or '{}')
                                                                 .get('path', '?') for tc in tcs) or "text"),
          flush=True)
    msgs.append(m)
    if not tcs:
        break
    for tc in tcs:
        msgs.append({"role": "tool", "tool_call_id": tc["id"],
                     "content": "wrote " + str(len(tc["function"]["arguments"])) + " bytes"})
msgs.append({"role": "user", "content": "Thanks. Which method has the most edge cases, in one sentence?"})
m, u, fin, ttft, wall = call(msgs, tools, 300)
print(f"user turn: ttft {ttft:5.1f}s wall {wall:6.1f}s | prompt {u.get('prompt_tokens')} answer "
      f"{u.get('completion_tokens')} | {(m.get('content') or '')[:160]!r}")
