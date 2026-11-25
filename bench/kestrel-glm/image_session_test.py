#!/usr/bin/env python3
"""A long conversation with a picture (a coding agent's screenshot) against Kestrel on :8000.
  turns:  N user turns, each sending the whole conversation back (the agent's way); prints the wait before the first
          token of each.  --state <file>: the conversation is saved there after the run and, if the file exists,
          continued from it - so a run after a restart sends the same conversation (does the engine take it back?)."""
import argparse, base64, json, os, struct, sys, time, urllib.request, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glm_bench import long_doc  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config", default=os.path.expanduser("~/kestrel/maya-glm-exl3-sc260-hip.json"))
ap.add_argument("--reps", type=int, default=2, help="copies of the 13.7K document in the first message")
ap.add_argument("--turns", type=int, default=2)
ap.add_argument("--state", default="")
a = ap.parse_args()
key = json.load(open(a.config)).get("api_key") or ""


def png(w=96, h=64):
    raw =b"".join(b"\x00" + b"".join(bytes(((x * 255 // w), (y * 255 // h), 128)) for x in range(w)) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def call(messages, max_tokens=200):
    body = {"model": "glm", "messages": messages, "max_tokens": max_tokens, "temperature": 0, "stream": True,
            "stream_options": {"include_usage": True}}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t0, ttft, usage, content, reasoning = time.time(), None, {}, [], []
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                continue
            ev = json.loads(line[5:])
            usage = ev.get("usage") or usage
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                if (d.get("content") or d.get("reasoning_content")) and ttft is None:
                    ttft = time.time() - t0
                content.append(d.get("content") or "")
                reasoning.append(d.get("reasoning_content") or "")
    m = {"role": "assistant", "content": "".join(content)}
    if "".join(reasoning):
        m["reasoning_content"] = "".join(reasoning)
    return m, usage, ttft or 0.0, time.time() - t0


if a.state and os.path.exists(a.state):
    msgs = json.load(open(a.state))
    print(f"continuing a saved conversation of {len(msgs)} messages")
else:
    img = "data:image/png;base64," + base64.b64encode(png()).decode()
    doc = "\n\n".join(f"Log part {i + 1}.\n" + long_doc() for i in range(a.reps))
    msgs = [{"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": "Here is a screenshot of the dashboard and the service log below.\n\n" + doc},
                {"type": "image_url", "image_url": {"url": img}},
                {"type": "text", "text": "Describe the screenshot's colours in one line, then name the carrier that "
                                         "appears most often in the log."}]}]
qs = ["Which carrier appears least often? One line.", "Summarise the log's date range in one line.",
      "Name two columns the log has. One line."]
for t in range(a.turns):
    if msgs[-1]["role"] == "assistant":
        msgs.append({"role": "user", "content": qs[t % len(qs)]})
    m, u, ttft, wall = call(msgs)
    print(f"turn {t + 1}: waited {ttft:6.1f} s for the first token | prompt {u.get('prompt_tokens')} | answer "
          f"{u.get('completion_tokens')} in {wall - ttft:.1f} s | {m['content'][:90]!r}", flush=True)
    msgs.append(m)
if a.state:
    json.dump(msgs, open(a.state, "w"))
