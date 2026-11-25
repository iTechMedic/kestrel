#!/bin/bash
# srv.sh start|stop|set KEY=VAL...|unset KEY...|exe PATH - starts and stops a test server from a config, and edits
# that config's engine env and engine binary.
#   CFG          the config (required)
#   KESTREL_DIR  the Kestrel checkout (default: this script's ../..), run with its .venv if there is one
#   LOG          the engine log to watch for "ready:" (default: the config's "log", else <config>.log)
#   PORT         default 8000
: "${CFG:?set CFG to the config of the server to test}"
KESTREL_DIR=${KESTREL_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}
BENCH=${KESTREL_BENCH_DIR:-$HOME/kestrel-bench}
PORT=${PORT:-8000}
LOG=${LOG:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("log") or sys.argv[1].rsplit(".",1)[0]+".log")' "$CFG")}
PY=$KESTREL_DIR/.venv/bin/python; [ -x "$PY" ] || PY=python3
EXE=$(python3 -c 'import json,os,sys; print(os.path.basename(json.load(open(sys.argv[1])).get("exe") or "kestrel"))' "$CFG")
br() { echo "[${1:0:1}]${1:1}"; }   # "[k]estrel-glm": a pkill pattern that cannot match the shell running it
case "$1" in
start)
  mkdir -p "$BENCH"
  n=$(wc -l < "$LOG" 2>/dev/null || echo 0)
  setsid nohup "$PY" "$KESTREL_DIR/maya.py" --config "$CFG" --port "$PORT" > "$BENCH/server.out" 2>&1 < /dev/null &
  for i in $(seq 1 120); do
    sleep 5
    if tail -n +$((n+1)) "$LOG" 2>/dev/null | grep -q "^ready:"; then echo "ready after $((i*5)) s"; exit 0; fi
    if ! pgrep -f "maya.py --config $CFG" >/dev/null; then echo "server exited:"; tail -5 "$BENCH/server.out"; exit 1; fi
  done; echo "not ready after 600 s"; exit 1;;
stop)
  # SIGTERM: a server started in the background ignores SIGINT; the engine still ends cleanly
  pkill -TERM -f "[s]erve/server.py"
  for i in $(seq 1 120); do sleep 2
    if ! ss -ltn | grep -q ":$PORT " && ! pgrep -f "[s]erve/server.py|$(br "$EXE")" >/dev/null; then echo "stopped after $((i*2)) s"; exit 0; fi
  done
  pkill -TERM -f "[s]erve/server.py|$(br "$EXE")"; sleep 10; pkill -KILL -f "[s]erve/server.py|$(br "$EXE")"; sleep 3; echo "stopped (forced)";;
set|unset|exe)
  python3 - "$CFG" "$@" <<'PY'
import json, sys
f, op = sys.argv[1], sys.argv[2]; c = json.load(open(f)); c.setdefault("env", {})
for kv in sys.argv[3:]:
    if op == "set": k, v = kv.split("=", 1); c["env"][k] = v
    elif op == "unset": c["env"].pop(kv, None)
    elif op == "exe": c["exe"] = kv
json.dump(c, open(f, "w"), indent=2); open(f, "a").write("\n")
print("exe:", c.get("exe")); print({k: v for k, v in sorted(c["env"].items()) if k.startswith("MAYA_GLM")})
PY
;;
*) echo "usage: CFG=<config> $0 start|stop|set KEY=VAL...|unset KEY...|exe PATH"; exit 2;;
esac
