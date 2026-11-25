#!/usr/bin/env python3
"""coding_selfcheck.py: every coding_eval.py task's hidden tests must pass with coding_ref.py's reference solutions -
run it after changing a task, so a model is never failed by a wrong test."""
import os, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "coding_eval.py")).read()
ns = {}
exec(src[src.index("TASKS = ["):src.index("\nap = argparse")], ns)
sys.path.insert(0, here)
from coding_ref import REF  # noqa: E402

broken = 0
for name, _, tests in ns["TASKS"]:
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.py"), "w").write(REF[name] + "\n" + tests)
        p = subprocess.run([sys.executable, "-I", "t.py"], cwd=d, capture_output=True, text=True, timeout=60)
        if p.returncode:
            broken += 1
            print("BROKEN", name, (p.stderr or p.stdout)[-400:])
print(f"{len(ns['TASKS'])} tasks, {broken} broken")
sys.exit(1 if broken else 0)
