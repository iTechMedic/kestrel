"""Reference solutions: every coding_eval.py task's tests must pass with these."""
REF = {}
REF["parse_duration"] = r'''
import re
def parse_duration(s):
    m = re.fullmatch(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", s)
    if not s or not m or not any(m.groups()): raise ValueError(s)
    d, h, mi, se = (int(x) if x else 0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se
'''
REF["LRUCache"] = r'''
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity): self.c, self.d = capacity, OrderedDict()
    def get(self, k):
        if k not in self.d: return -1
        self.d.move_to_end(k); return self.d[k]
    def put(self, k, v):
        self.d[k] = v; self.d.move_to_end(k)
        if len(self.d) > self.c: self.d.popitem(last=False)
'''
REF["merge_intervals"] = r'''
def merge_intervals(iv):
    out = []
    for s, e in sorted(map(list, iv)):
        if out and s <= out[-1][1]: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return out
'''
REF["int_to_roman"] = r'''
V = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def int_to_roman(n):
    out = ''
    for v, r in V:
        while n >= v: out += r; n -= v
    return out
TABLE = {int_to_roman(i): i for i in range(1, 4000)}
def roman_to_int(s):
    if s not in TABLE: raise ValueError(s)
    return TABLE[s]
'''
REF["topo_sort"] = r'''
import heapq
def topo_sort(deps):
    nodes = set(deps) | {d for v in deps.values() for d in v}
    indeg = {n: 0 for n in nodes}; users = {n: [] for n in nodes}
    for n, ds in deps.items():
        for d in ds: indeg[n] += 1; users[d].append(n)
    h = [n for n in nodes if indeg[n] == 0]; heapq.heapify(h); out = []
    while h:
        n = heapq.heappop(h); out.append(n)
        for u in users[n]:
            indeg[u] -= 1
            if indeg[u] == 0: heapq.heappush(h, u)
    if len(out) != len(nodes): raise ValueError('cycle')
    return out
'''
REF["evaluate"] = r'''
import re
def evaluate(expr):
    toks = re.findall(r"\d+\.?\d*|\.\d+|[-+*/()]|\S", expr); i = 0
    def peek(): return toks[i] if i < len(toks) else None
    def take():
        nonlocal i; i += 1; return toks[i - 1]
    def atom():
        t = peek()
        if t is None: raise ValueError('end')
        if t == '-': take(); return -atom()
        if t == '(':
            take(); v = add()
            if peek() != ')': raise ValueError(')')
            take(); return v
        if re.fullmatch(r"\d+\.?\d*|\.\d+", t): take(); return float(t)
        raise ValueError(t)
    def mul():
        v = atom()
        while peek() in ('*', '/'):
            op = take(); r = atom(); v = v * r if op == '*' else v / r
        return v
    def add():
        v = mul()
        while peek() in ('+', '-'):
            op = take(); r = mul(); v = v + r if op == '+' else v - r
        return v
    v = add()
    if i != len(toks): raise ValueError('trailing')
    return v
'''
REF["wrap"] = r'''
def wrap(text, width):
    lines, cur = [], ''
    for w in text.split():
        while len(w) > width:
            if cur: lines.append(cur); cur = ''
            lines.append(w[:width]); w = w[width:]
        if not w: continue
        if cur and len(cur) + 1 + len(w) <= width: cur += ' ' + w
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines
'''
REF["shortest_path"] = r'''
import heapq
def shortest_path(g, s, t):
    dist, prev, h = {s: 0}, {}, [(0, s)]
    while h:
        d, u = heapq.heappop(h)
        if u == t:
            p = [t]
            while p[-1] != s: p.append(prev[p[-1]])
            return d, p[::-1]
        if d > dist[u]: continue
        for v, w in g.get(u, {}).items():
            if d + w < dist.get(v, float('inf')): dist[v] = d + w; prev[v] = u; heapq.heappush(h, (d + w, v))
    return None
'''
REF["spiral"] = r'''
def spiral(m):
    m = [r[:] for r in m if r]; out = []
    while m:
        out += m.pop(0)
        m = [list(r) for r in zip(*m)][::-1]
    return out
'''
REF["rle"] = r'''
import re
def rle_encode(s):
    return ''.join(f"{len(m.group(0))}{m.group(1)}" for m in re.finditer(r"(.)\1*", s, re.S))
def rle_decode(s):
    if not re.fullmatch(r"(?:\d+\D)*", s, re.S): raise ValueError(s)
    return ''.join(c * int(n) for n, c in re.findall(r"(\d+)(\D)", s, re.S))
'''
REF["valid_sudoku"] = r'''
def valid_sudoku(b):
    seen = set()
    for r in range(9):
        for c in range(9):
            v = b[r][c]
            if v == '.': continue
            for k in ((0, r, v), (1, c, v), (2, r // 3, c // 3, v)):
                if k in seen: return False
                seen.add(k)
    return True
'''
REF["multiply_strings"] = r'''
def multiply_strings(a, b):
    res = [0] * (len(a) + len(b))
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            p = (ord(a[i]) - 48) * (ord(b[j]) - 48) + res[i + j + 1]
            res[i + j + 1] = p % 10; res[i + j] += p // 10
    s = ''.join(map(str, res)).lstrip('0')
    return s or '0'
'''
REF["semver_cmp"] = r'''
def semver_cmp(a, b):
    def key(v):
        v = v.split('+')[0]; core, _, pre = v.partition('-')
        nums = tuple(int(x) for x in core.split('.'))
        if not pre: return (nums, 1, ())
        ids = tuple((0, int(x), '') if x.isdigit() else (1, 0, x) for x in pre.split('.'))
        return (nums, 0, ids)
    ka, kb = key(a), key(b)
    return (ka > kb) - (ka < kb)
'''
REF["parse_csv_line"] = r'''
def parse_csv_line(line):
    out, i, n = [], 0, len(line)
    while True:
        if i < n and line[i] == '"':
            i += 1; f = ''
            while True:
                if i >= n: raise ValueError('unterminated')
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"': f += '"'; i += 2; continue
                    i += 1; break
                f += line[i]; i += 1
            if i < n and line[i] != ',': raise ValueError('after quote')
        else:
            j = line.find(',', i); j = n if j < 0 else j; f = line[i:j]; i = j
        out.append(f)
        if i >= n: return out
        i += 1
'''
REF["n_queens"] = r'''
def n_queens(n):
    full = (1 << n) - 1
    def go(cols, d1, d2):
        if cols == full: return 1
        cnt, free = 0, full & ~(cols | d1 | d2)
        while free:
            b = free & -free; free -= b
            cnt += go(cols | b, ((d1 | b) << 1) & full, (d2 | b) >> 1)
        return cnt
    return go(0, 0, 0)
'''
REF["edit_distance"] = r'''
def edit_distance(a, b):
    n, m = len(a), len(b)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i-1][j] + 1, D[i][j-1] + 1, D[i-1][j-1] + (a[i-1] != b[j-1]))
    ops, i, j = [], n, m
    while i or j:
        if i and j and a[i-1] == b[j-1] and D[i][j] == D[i-1][j-1]: i -= 1; j -= 1
        elif i and j and D[i][j] == D[i-1][j-1] + 1: ops.append(('r', i - 1, a[i-1], b[j-1])); i -= 1; j -= 1
        elif i and D[i][j] == D[i-1][j] + 1: ops.append(('d', i - 1, a[i-1])); i -= 1
        else: ops.append(('i', i, b[j-1])); j -= 1
    out = []   # applied right to left: indices to the left are unaffected
    for o in ops:
        if o[0] == 'r': out.append(f"replace {o[2]} with {o[3]} at {o[1]}")
        elif o[0] == 'd': out.append(f"delete {o[2]} at {o[1]}")
        else: out.append(f"insert {o[2]} at {o[1]}")
    return D[n][m], out
'''
REF["balanced"] = r'''
def balanced(s):
    st, i, pairs = [], 0, {')': '(', ']': '[', '}': '{'}
    while i < len(s):
        c = s[i]
        if c in '"\'':
            q = c; i += 1
            while i < len(s) and s[i] != q: i += 2 if s[i] == '\\' else 1
            if i >= len(s): return len(s)
        elif c in '([{': st.append(c)
        elif c in ')]}':
            if not st or st[-1] != pairs[c]: return i
            st.pop()
        i += 1
    return -1 if not st else len(s)
'''
REF["max_non_overlapping"] = r'''
def max_non_overlapping(iv):
    out, end = [], None
    for s, e in sorted(iv, key=lambda x: (x[1], x[0])):
        if end is None or s >= end: out.append((s, e)); end = e
    return sorted(out)
'''
REF["group_anagrams"] = r'''
def group_anagrams(words):
    g = {}
    for w in words: g.setdefault(''.join(sorted(c for c in w.lower() if c.isalpha())), []).append(w)
    return list(g.values())
'''
REF["bank_account"] = r'''
class InsufficientFunds(Exception): pass
class Account:
    def __init__(self, owner, balance=0):
        if balance < 0: raise ValueError('negative')
        self.owner, self.balance, self._h = owner, balance, []
    @staticmethod
    def _chk(a):
        if not isinstance(a, int) or isinstance(a, bool) or a <= 0: raise ValueError(a)
    def deposit(self, a): self._chk(a); self.balance += a; self._h.append(('deposit', a))
    def withdraw(self, a):
        self._chk(a)
        if a > self.balance: raise InsufficientFunds(a)
        self.balance -= a; self._h.append(('withdraw', a))
    def transfer(self, other, a):
        self._chk(a)
        if a > self.balance: raise InsufficientFunds(a)
        self.balance -= a; other.balance += a
        self._h.append(('transfer_out', a)); other._h.append(('transfer_in', a))
    def history(self): return list(self._h)
'''
