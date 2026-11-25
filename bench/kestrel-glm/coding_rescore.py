#!/usr/bin/env python3
"""coding_rescore.py coding_<label>.json ...: score saved answers again with one extraction rule for every model -
the LAST fenced code block (fences at a line's start) that parses and defines the task's name; else the last block;
else the whole text.  Prints each label's score and its failures."""
import ast, json, os, re, subprocess, sys, tempfile

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "coding_eval.py")).read()
ns = {}
exec(src[src.index("TASKS = ["):src.index("\nap = argparse")], ns)
TESTS = {name: tests for name, _, tests in ns["TASKS"]}
IDENT = {"rle": "rle_encode", "bank_account": "Account"}
FENCE = re.compile(r"^```[ \t]*([\w+-]*)[ \t]*\n(.*?)^```", re.M | re.S)


def defines(code, ident):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == ident for n in ast.walk(tree))


def code_of(text, ident):
    blocks = [b for lang, b in FENCE.findall(text) if lang.lower() in ("", "python", "py", "python3")]
    for b in reversed(blocks):
        if defines(b, ident):
            return b
    return blocks[-1] if blocks else text


def run(code, tests):
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.py"), "w").write(code + "\n\n# ---- tests\n" + tests)
        try:
            p = subprocess.run([sys.executable, "-I", "t.py"], cwd=d, capture_output=True, text=True, timeout=20)
            return p.returncode == 0, (p.stderr or p.stdout).strip().splitlines()[-1:] or [""]
        except subprocess.TimeoutExpired:
            return False, ["timeout"]


for path in sys.argv[1:]:
    label = os.path.basename(path)[len("coding_"):-len(".json")]
    res = json.load(open(path))
    fails = []
    for r in res:
        ok, err = run(code_of(r["answer"], IDENT.get(r["task"], r["task"])), TESTS[r["task"]])
        if not ok:
            fails.append(f"{r['task']} ({err[0][:70]})")
    print(f"{label:24} {len(res) - len(fails)}/{len(res)}" + ("  | failed: " + "; ".join(fails) if fails else ""))
