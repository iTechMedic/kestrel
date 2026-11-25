#!/bin/bash
# srv.sh start|stop|set KEY=VAL...|unset KEY... - the sc_2.60 test server (config maya-glm-exl3-sc260-hip.json)
CFG=${CFG:-$HOME/kestrel/maya-glm-exl3-sc260-hip.json}
LOG=${LOG:-$HOME/kestrel/maya-glm-exl3-sc260-hip.log}
case "$1" in
start)
  n=$(wc -l < $LOG 2>/dev/null || echo 0)
  setsid nohup $HOME/kestrel/.venv/bin/python $HOME/kestrel/maya.py --config $CFG --port 8000 > $HOME/kestrel-bench/server.out 2>&1 < /dev/null &
  for i in $(seq 1 120); do
    sleep 5
    if tail -n +$((n+1)) $LOG | grep -q "^ready:"; then echo "ready after $((i*5)) s"; exit 0; fi
    if ! pgrep -f "maya.py --config $CFG" >/dev/null; then echo "server exited:"; tail -5 $HOME/kestrel-bench/server.out; exit 1; fi
  done; echo "not ready after 600 s"; exit 1;;
stop)
  pkill -TERM -f "[s]erve/server.py"
  for i in $(seq 1 120); do sleep 2
    if ! ss -ltn | grep -q ":8000 " && ! pgrep -f "[k]estrel-bin/kestrel-glm|[s]erve/server.py" >/dev/null; then echo "stopped after $((i*2)) s"; exit 0; fi
  done
  pkill -TERM -f "[s]erve/server.py|[k]estrel-bin/kestrel-glm"; sleep 10; pkill -KILL -f "[s]erve/server.py|[k]estrel-bin/kestrel-glm"; sleep 3; echo "stopped (forced)";;
set|unset|exe)
  python3 - "$@" <<PY
import json, sys
f = "$CFG"; c = json.load(open(f)); op = sys.argv[1]
for kv in sys.argv[2:]:
    if op == "set": k, v = kv.split("=", 1); c["env"][k] = v
    elif op == "unset": c["env"].pop(kv, None)
    elif op == "exe": c["exe"] = kv
json.dump(c, open(f, "w"), indent=2); open(f, "a").write("\n")
print("exe:", c["exe"]); print({k: v for k, v in sorted(c["env"].items()) if k.startswith("MAYA_GLM")})
PY
;;
esac
