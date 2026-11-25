#!/usr/bin/env python3
"""coding_eval.py LABEL [--config CFG]: 20 Python tasks against Kestrel on :8000, each answer's code run against
hidden edge-case tests (a subprocess per task, 20 s, in a temporary directory).  Appends to coding_results.jsonl and
writes the answers to coding_<LABEL>.json."""
import argparse, json, os, re, subprocess, sys, tempfile, time, urllib.request
BENCH = os.environ.get('KESTREL_BENCH_DIR', os.path.expanduser('~/kestrel-bench'))

TASKS = [
    ("parse_duration", "def parse_duration(s: str) -> int: return the seconds in a duration like '1h30m15s', '45s', "
     "'2h', '1d2h' (units d, h, m, s, each at most once, in that order, at least one). Raise ValueError for anything "
     "else, including '', '1x', '1m1h', '1h1h', 'h'.",
     """
assert parse_duration('1h30m15s') == 5415
assert parse_duration('45s') == 45 and parse_duration('2h') == 7200 and parse_duration('1d2h') == 93600
assert parse_duration('0s') == 0 and parse_duration('10m') == 600
for bad in ['', '1x', '1m1h', '1h1h', 'h', '1.5h', ' 1h', '-1s', '1h 2m']:
    try: parse_duration(bad); raise SystemExit('accepted ' + repr(bad))
    except ValueError: pass
"""),
    ("LRUCache", "class LRUCache: __init__(self, capacity: int); get(self, key) -> value or -1; put(self, key, value). "
     "Least recently used eviction; get and put both count as use; put on an existing key updates it. O(1) each.",
     """
c = LRUCache(2); c.put(1, 1); c.put(2, 2); assert c.get(1) == 1
c.put(3, 3); assert c.get(2) == -1; c.put(4, 4); assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
c = LRUCache(2); c.put(1, 1); c.put(2, 2); c.put(1, 10); c.put(3, 3); assert c.get(2) == -1 and c.get(1) == 10
c = LRUCache(1); c.put(1, 1); c.put(2, 2); assert c.get(1) == -1 and c.get(2) == 2
"""),
    ("merge_intervals", "def merge_intervals(iv: list[list[int]]) -> list[list[int]]: merge overlapping or touching "
     "closed intervals ([1,3] and [3,5] merge), return them sorted by start. Do not modify the input.",
     """
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
assert merge_intervals([]) == []
assert merge_intervals([[5,7],[1,2],[2,4],[6,6]]) == [[1,4],[5,7]]
x = [[3,4],[1,2]]; merge_intervals(x); assert x == [[3,4],[1,2]]
assert merge_intervals([[1,10],[2,3],[4,5]]) == [[1,10]]
"""),
    ("int_to_roman", "def int_to_roman(n: int) -> str for 1..3999, and def roman_to_int(s: str) -> int that raises "
     "ValueError for invalid numerals (e.g. 'IIII', 'VV', 'IC', 'MMMM', '', 'IIV').",
     """
assert int_to_roman(1994) == 'MCMXCIV' and int_to_roman(3999) == 'MMMCMXCIX' and int_to_roman(4) == 'IV'
assert all(roman_to_int(int_to_roman(i)) == i for i in range(1, 4000))
for bad in ['IIII', 'VV', 'IC', 'MMMM', '', 'IIV', 'VX', 'XM', 'abc']:
    try: roman_to_int(bad); raise SystemExit('accepted ' + bad)
    except ValueError: pass
"""),
    ("topo_sort", "def topo_sort(deps: dict[str, list[str]]) -> list[str]: deps maps a node to the nodes it depends on "
     "(which may not be keys themselves). Return every node, each after all its dependencies; among nodes that are "
     "ready at the same time, alphabetical order first. Raise ValueError on a cycle.",
     """
assert topo_sort({'b': ['a'], 'c': ['b'], 'a': []}) == ['a', 'b', 'c']
assert topo_sort({'x': ['y', 'z']}) == ['y', 'z', 'x']
assert topo_sort({'d': [], 'c': [], 'b': ['d'], 'a': ['c']}) == ['c', 'a', 'd', 'b']
assert topo_sort({}) == []
for cyc in [{'a': ['b'], 'b': ['a']}, {'a': ['a']}, {'a': ['b'], 'b': ['c'], 'c': ['a']}]:
    try: topo_sort(cyc); raise SystemExit('no cycle found')
    except ValueError: pass
"""),
    ("evaluate", "def evaluate(expr: str) -> float: evaluate + - * / with parentheses, unary minus and decimal numbers, "
     "usual precedence, left to right for equal precedence, spaces allowed. No eval/exec/ast. Raise ValueError on "
     "malformed input; ZeroDivisionError on division by zero.",
     """
assert evaluate('1 + 2 * 3') == 7 and evaluate('(1 + 2) * 3') == 9 and evaluate('10 / 4') == 2.5
assert evaluate('8 - 3 - 2') == 3 and evaluate('-3 + 5') == 2 and evaluate('2 * -(1 + 1)') == -4
assert abs(evaluate('1.5 * 2 + .5') - 3.5) < 1e-9 and evaluate('64 / 4 / 2') == 8
assert evaluate('--2') == 2
for bad in ['1 +', '(1', '1)', '', '2 3', '1 + * 2', 'a + 1']:
    try: evaluate(bad); raise SystemExit('accepted ' + repr(bad))
    except ValueError: pass
try: evaluate('1 / (2 - 2)'); raise SystemExit('no ZeroDivisionError')
except ZeroDivisionError: pass
"""),
    ("wrap", "def wrap(text: str, width: int) -> list[str]: greedy word wrap; words are separated by any whitespace; "
     "each line holds as many words as fit, joined by single spaces; a word longer than width is split into chunks "
     "of width characters (the last chunk may start a line other words follow). Empty or whitespace text: [].",
     """
assert wrap('the quick brown fox', 10) == ['the quick', 'brown fox']
assert wrap('a  b\\n c', 3) == ['a b', 'c']
assert wrap('', 5) == [] and wrap('   ', 5) == []
assert wrap('abcdefghij xy', 4) == ['abcd', 'efgh', 'ij', 'xy'] or wrap('abcdefghij xy', 4) == ['abcd', 'efgh', 'ij xy']
assert wrap('hello', 5) == ['hello']
assert wrap('one two three four', 9) == ['one two', 'three', 'four']
"""),
    ("shortest_path", "def shortest_path(graph: dict[str, dict[str, float]], start: str, goal: str) -> "
     "tuple[float, list[str]] | None: Dijkstra over non-negative edge weights; return (cost, path from start to goal), "
     "or None if unreachable. start == goal: (0, [start]). Nodes may appear only as edge targets.",
     """
g = {'a': {'b': 1, 'c': 4}, 'b': {'c': 2, 'd': 5}, 'c': {'d': 1}}
assert shortest_path(g, 'a', 'd') == (4, ['a', 'b', 'c', 'd'])
assert shortest_path(g, 'a', 'a') == (0, ['a'])
assert shortest_path(g, 'd', 'a') is None
assert shortest_path({'a': {'b': 0}, 'b': {'c': 0}}, 'a', 'c') == (0, ['a', 'b', 'c'])
assert shortest_path(g, 'a', 'zz') is None
"""),
    ("spiral", "def spiral(m: list[list[int]]) -> list[int]: the matrix's elements in clockwise spiral order from the "
     "top left. Works for empty, single-row, single-column and non-square matrices.",
     """
assert spiral([[1,2,3],[4,5,6],[7,8,9]]) == [1,2,3,6,9,8,7,4,5]
assert spiral([[1,2,3,4],[5,6,7,8],[9,10,11,12]]) == [1,2,3,4,8,12,11,10,9,5,6,7]
assert spiral([]) == [] and spiral([[]]) == [] and spiral([[1]]) == [1]
assert spiral([[1],[2],[3]]) == [1,2,3] and spiral([[1,2,3]]) == [1,2,3]
assert spiral([[1,2],[3,4],[5,6]]) == [1,2,4,6,5,3]
"""),
    ("rle", "def rle_encode(s: str) -> str and def rle_decode(s: str) -> str: run-length encoding where each run is "
     "the count then the character ('aaab' -> '3a1b'); counts may have several digits; the text to encode contains "
     "no digits. rle_decode raises ValueError on malformed input.",
     """
assert rle_encode('aaab') == '3a1b' and rle_encode('') == '' and rle_encode('a' * 12) == '12a'
assert rle_decode('3a1b') == 'aaab' and rle_decode('12a') == 'a' * 12 and rle_decode('') == ''
import random
for _ in range(200):
    s = ''.join(random.choice('ab c') for _ in range(random.randint(0, 30)))
    assert rle_decode(rle_encode(s)) == s
for bad in ['a', '3', '3a2', 'x3a']:
    try: rle_decode(bad); raise SystemExit('accepted ' + bad)
    except ValueError: pass
"""),
    ("valid_sudoku", "def valid_sudoku(board: list[list[str]]) -> bool: a 9x9 board of '1'-'9' or '.'; true when no "
     "row, column or 3x3 box repeats a digit (the board need not be solvable).",
     """
b = [list(r) for r in ['53..7....','6..195...','.98....6.','8...6...3','4..8.3..1','7...2...6','.6....28.','...419..5','....8..79']]
assert valid_sudoku(b)
b2 = [r[:] for r in b]; b2[0][0] = '8'; assert not valid_sudoku(b2)
b3 = [r[:] for r in b]; b3[1][1] = '9'; assert not valid_sudoku(b3)
assert valid_sudoku([['.'] * 9 for _ in range(9)])
b4 = [['.'] * 9 for _ in range(9)]; b4[0][0] = '1'; b4[8][0] = '1'; assert not valid_sudoku(b4)
"""),
    ("multiply_strings", "def multiply_strings(a: str, b: str) -> str: the product of two non-negative integers given "
     "as decimal strings (possibly hundreds of digits, possibly with leading zeros), without converting the whole "
     "strings to int. No leading zeros in the result except '0' itself.",
     """
assert multiply_strings('123', '456') == '56088'
assert multiply_strings('0', '999') == '0' and multiply_strings('000', '12') == '0'
assert multiply_strings('0012', '010') == '120'
import random
for _ in range(50):
    x, y = random.randint(0, 10**60), random.randint(0, 10**40)
    assert multiply_strings(str(x), str(y)) == str(x * y)
"""),
    ("semver_cmp", "def semver_cmp(a: str, b: str) -> int: compare two semantic versions (MAJOR.MINOR.PATCH with "
     "optional -prerelease and +build) per semver 2.0: -1, 0 or 1. Build metadata is ignored; a pre-release sorts "
     "before its release; pre-release identifiers compare numerically when both numeric, numeric before alphanumeric, "
     "and a longer list wins when all shared identifiers are equal.",
     """
assert semver_cmp('1.0.0', '2.0.0') == -1 and semver_cmp('2.1.0', '2.0.9') == 1 and semver_cmp('1.0.0', '1.0.0') == 0
assert semver_cmp('1.0.0-alpha', '1.0.0') == -1 and semver_cmp('1.0.0+build.5', '1.0.0') == 0
order = ['1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.beta', '1.0.0-beta', '1.0.0-beta.2', '1.0.0-beta.11', '1.0.0-rc.1', '1.0.0']
for i in range(len(order) - 1):
    assert semver_cmp(order[i], order[i + 1]) == -1, (order[i], order[i + 1])
    assert semver_cmp(order[i + 1], order[i]) == 1
assert semver_cmp('1.10.0', '1.9.0') == 1
"""),
    ("parse_csv_line", "def parse_csv_line(line: str) -> list[str]: split one CSV line on commas; fields may be quoted "
     "with double quotes, inside which commas are literal and a doubled quote \"\" is one quote; unquoted fields are "
     "kept as is (no stripping). Raise ValueError for an unterminated quote or text after a closing quote.",
     """
assert parse_csv_line('a,b,c') == ['a', 'b', 'c']
assert parse_csv_line('"a,b",c') == ['a,b', 'c']
Q = chr(34)
assert parse_csv_line(Q + 'say ' + Q * 2 + 'hi' + Q * 3 + ',x') == ['say ' + Q + 'hi' + Q, 'x']
assert parse_csv_line('') == [''] and parse_csv_line(',') == ['', ''] and parse_csv_line(' a , b') == [' a ', ' b']
assert parse_csv_line('"",x') == ['', 'x']
for bad in ['"abc', '"a"b,c']:
    try: parse_csv_line(bad); raise SystemExit('accepted ' + bad)
    except ValueError: pass
"""),
    ("n_queens", "def n_queens(n: int) -> int: the number of ways to place n non-attacking queens on an n x n board "
     "(n from 0 to 12; n = 0 gives 1). It must finish n = 12 in a few seconds.",
     """
assert [n_queens(i) for i in range(0, 9)] == [1, 1, 0, 0, 2, 10, 4, 40, 92]
assert n_queens(10) == 724
import time; t = time.time(); assert n_queens(12) == 14200; assert time.time() - t < 15
"""),
    ("edit_distance", "def edit_distance(a: str, b: str) -> tuple[int, list[str]]: the Levenshtein distance and one "
     "shortest edit script turning a into b, as operations 'insert X at i', 'delete X at i', 'replace X with Y at i' "
     "(i: the index in the string as edited so far, applied in order). Only the distance and that applying the script "
     "gives b are checked.",
     """
def apply(s, ops):
    import re
    for op in ops:
        m = re.fullmatch(r"insert (.) at (\\d+)", op)
        if m: i = int(m[2]); s = s[:i] + m[1] + s[i:]; continue
        m = re.fullmatch(r"delete (.) at (\\d+)", op)
        if m: i = int(m[2]); assert s[i] == m[1], (s, op); s = s[:i] + s[i+1:]; continue
        m = re.fullmatch(r"replace (.) with (.) at (\\d+)", op)
        if m: i = int(m[3]); assert s[i] == m[1], (s, op); s = s[:i] + m[2] + s[i+1:]; continue
        raise SystemExit('bad op ' + op)
    return s
for a, b, d in [('kitten', 'sitting', 3), ('', 'abc', 3), ('abc', '', 3), ('flaw', 'lawn', 2), ('same', 'same', 0), ('intention', 'execution', 5)]:
    dist, ops = edit_distance(a, b)
    assert dist == d and len(ops) == d, (a, b, dist, ops)
    assert apply(a, ops) == b, (a, b, ops)
"""),
    ("balanced", "def balanced(s: str) -> int: -1 when the brackets ()[]{} in s are balanced (other characters "
     "ignored, but brackets inside single- or double-quoted string literals are ignored too, with backslash escapes "
     "inside literals), else the index of the first character where the text is known to be unbalanced (a closer "
     "that does not match, or len(s) for something left open, including an unterminated literal).",
     """
assert balanced('a(b[c]{d}e)f') == -1 and balanced('') == -1
assert balanced('(]') == 1 and balanced('(()') == 3 and balanced(')') == 0
assert balanced('print("(")') == -1 and balanced("x = ')' + (1)") == -1
assert balanced('s = "a\\\\"(" + ")"') == -1
assert balanced('"abc') == 4 and balanced('{[}]') == 2
"""),
    ("max_non_overlapping", "def max_non_overlapping(iv: list[tuple[int, int]]) -> list[tuple[int, int]]: choose the "
     "largest number of pairwise non-overlapping half-open intervals [start, end) (so (1,3) and (3,5) do not "
     "overlap); among maximum choices return the one picked by earliest end time, ties by earliest start; the result "
     "sorted by start. Zero-length intervals (s == e) are allowed and overlap nothing.",
     """
assert max_non_overlapping([(1,3),(2,4),(3,5)]) == [(1,3),(3,5)]
assert max_non_overlapping([]) == []
assert len(max_non_overlapping([(1,10),(2,3),(3,4),(4,5)])) == 3
assert max_non_overlapping([(1,2),(1,2),(2,3)]) == [(1,2),(2,3)]
r = max_non_overlapping([(5,5),(1,9),(2,3)]); assert len(r) == 2 and (2,3) in r
"""),
    ("group_anagrams", "def group_anagrams(words: list[str]) -> list[list[str]]: group words that are anagrams of "
     "each other, ignoring case and non-letters; each group keeps its words' input order, groups are ordered by "
     "their first word's position in the input; duplicates stay.",
     """
assert group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat']) == [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
assert group_anagrams([]) == []
assert group_anagrams(['Listen', 'Silent!', 'enlist', 'x', 'x']) == [['Listen', 'Silent!', 'enlist'], ['x', 'x']]
assert group_anagrams(['a-b', 'BA', 'c']) == [['a-b', 'BA'], ['c']]
"""),
    ("bank_account", "class Account: __init__(self, owner: str, balance: int = 0) (raise ValueError for a negative "
     "balance); deposit(amount) and withdraw(amount) for positive ints (ValueError otherwise; withdraw beyond the "
     "balance raises InsufficientFunds, an Exception subclass you define, and leaves the balance unchanged); "
     "transfer(other, amount) all-or-nothing; history() returns a list of (kind, amount) tuples in order for "
     "'deposit', 'withdraw', 'transfer_out', 'transfer_in' (the latter on the other account).",
     """
a = Account('a', 100); b = Account('b')
a.deposit(50); a.withdraw(30); a.transfer(b, 20)
assert a.balance == 100 and b.balance == 20
assert a.history() == [('deposit', 50), ('withdraw', 30), ('transfer_out', 20)] and b.history() == [('transfer_in', 20)]
try: b.withdraw(21); raise SystemExit('overdraft')
except InsufficientFunds: pass
assert b.balance == 20 and issubclass(InsufficientFunds, Exception)
try: a.transfer(b, 1000); raise SystemExit('overdraft transfer')
except InsufficientFunds: pass
assert a.balance == 100 and b.balance == 20 and len(a.history()) == 3
for bad in [0, -5, 1.5]:
    try: a.deposit(bad); raise SystemExit('bad deposit')
    except ValueError: pass
try: Account('x', -1); raise SystemExit('negative balance')
except ValueError: pass
"""),
]

ap = argparse.ArgumentParser()
ap.add_argument("label")
ap.add_argument("--config", default=os.path.expanduser("~/kestrel/maya-glm-exl3-sc260-hip.json"))
ap.add_argument("--max-tokens", type=int, default=12000)
ap.add_argument("--effort", default="low", help="reasoning_effort (GLM: low / high)")
a = ap.parse_args()
key = json.load(open(a.config)).get("api_key") or ""


def ask(prompt):
    body = {"model": "glm", "messages": [{"role": "user", "content": prompt}], "max_tokens": a.max_tokens,
            "temperature": 0, "reasoning_effort": a.effort}
    req = urllib.request.Request("http://127.0.0.1:8000/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    return r["choices"][0]["message"].get("content") or "", r.get("usage", {}), time.time() - t


def code_of(text):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return max(blocks, key=len) if blocks else text


results, passed = [], 0
for name, spec, tests in TASKS:
    prompt = ("Write Python 3 code for this, standard library only:\n" + spec +
              "\nReply with one ```python code block containing the complete implementation (no tests, no example "
              "usage, no input()).")
    text, usage, dt = ask(prompt)
    code = code_of(text)
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.py"), "w").write(code + "\n\n# ---- tests\n" + tests)
        try:
            p = subprocess.run([sys.executable, "-I", "t.py"], cwd=d, capture_output=True, text=True, timeout=20)
            ok, err = p.returncode == 0, (p.stderr or p.stdout)[-300:]
        except subprocess.TimeoutExpired:
            ok, err = False, "timeout"
    passed += ok
    results.append({"task": name, "ok": ok, "err": "" if ok else err, "tokens": usage.get("completion_tokens"),
                    "s": round(dt, 1), "answer": text})
    print(f"{'PASS' if ok else 'FAIL'} {name:20} {usage.get('completion_tokens'):>5} tok {dt:6.1f} s"
          + ("" if ok else "  | " + err.strip().splitlines()[-1][:110] if err.strip() else ""), flush=True)
print(f"== {a.label}: {passed}/{len(TASKS)} passed")
json.dump(results, open(os.path.join(BENCH, f"coding_{a.label}.json"), "w"), indent=1)
open(os.path.join(BENCH, "coding_results.jsonl"), "a").write(
    json.dumps({"label": a.label, "passed": passed, "of": len(TASKS), "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "failed": [r["task"] for r in results if not r["ok"]]}) + "\n")
