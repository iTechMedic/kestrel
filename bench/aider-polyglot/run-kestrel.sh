#!/bin/bash
# Aider's polyglot benchmark against a running Kestrel server. Run it from your aider clone (see README.md).
#   ./run-kestrel.sh RUN-NAME            the 50 exercises in kestrel-50.txt
#   ./run-kestrel.sh RUN-NAME all        all 225
#   ./run-kestrel.sh RUN-NAME check      2 exercises, to check the setup
#   RESUME=1 ./run-kestrel.sh RUN-NAME   continue that run: finished exercises are kept, the rest run
#   EFFORT=medium ./run-kestrel.sh ...   thinking level (default high)
# Needs OPENAI_API_BASE (Kestrel's address, e.g. http://192.168.1.20:8000/v1) and OPENAI_API_KEY (Kestrel's api_key,
# or any text if it has none). The thinking cap is Kestrel's own "thinking_budget".
# Results: tmp.benchmarks/<date>--RUN-NAME. Score: ./benchmark/benchmark.py --stats <that folder> (in the container).
set -euo pipefail
cd "$(dirname "$0")"
: "${OPENAI_API_BASE:?set OPENAI_API_BASE to the Kestrel server, e.g. http://127.0.0.1:8000/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-none}" EFFORT="${EFFORT:-high}"
newcont=--new; [ -n "${RESUME:-}" ] && newcont=--cont
name="${1:?give the run a name, e.g. high-turbo}"
case "${2:-50}" in
  50)    sel=(--keywords "$(cat kestrel-50.txt)") ;;
  all)   sel=() ;;
  check) sel=(--keywords "python/exercises/practice/grep,go/exercises/practice/bowling") ;;
  *)     echo "second argument: 50, all or check"; exit 1 ;;
esac
docker run --rm --memory=12g --memory-swap=12g \
  -v "$PWD":/aider -v "$PWD/tmp.benchmarks/.":/benchmarks \
  -e OPENAI_API_KEY -e OPENAI_API_BASE -e EFFORT -e AIDER_DOCKER=1 -e AIDER_BENCHMARK_DIR=/benchmarks \
  aider-benchmark:jest29 bash -c '
    pip install -q -e .[dev] >/tmp/pip.log 2>&1 || { tail -20 /tmp/pip.log; exit 1; }
    ./benchmark/benchmark.py "$0" --model openai/deepseek-v4.1-flash --edit-format diff \
      --read-model-settings kestrel-model-settings.yml --reasoning-effort "$EFFORT" --threads 1 \
      --exercises-dir polyglot-benchmark "$@"
  ' "$name" "$newcont" "${sel[@]}"
