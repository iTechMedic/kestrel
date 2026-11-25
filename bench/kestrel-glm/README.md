# GLM benchmark scripts (Kestrel)

The scripts behind [docs/KESTREL_GLM_EXL3.md](../../docs/KESTREL_GLM_EXL3.md). They talk to a running Kestrel server on
`http://127.0.0.1:8000/v1`, read the API key from the server's config (`--config`, or the `KESTREL_CONFIG`
environment variable; the key is never printed) and append their results to `~/kestrel-bench/` (`KESTREL_BENCH_DIR`
moves it). Python 3, standard library only.

| Script | What it measures |
| --- | --- |
| `glm_bench.py LABEL --config CFG` | answer speed on three short prompts, then a 13.7K-token prompt (read speed and the answer after it); each prompt twice (`--runs`), the long one with a fresh first line each time so nothing is reused |
| `long_bench.py LABEL --config CFG` | one ~55K-token prompt (`--reps 4` copies of the 13.7K document): read speed and the answer after it |
| `glm_quality.py LABEL --config CFG` | 12 short questions with one right answer - a check that a quant is not broken, too easy to rank quants |
| `coding_eval.py LABEL --config CFG` | 20 Python tasks, each answer run against hidden edge-case tests (a subprocess, 20 s, in a temporary folder); `reasoning_effort` low, temperature 0 |
| `coding_rescore.py coding_<label>.json ...` | scores saved answers again with one rule for every model: the last fenced code block that parses and defines the task's name |
| `coding_selfcheck.py` | every task's tests against `coding_ref.py`'s reference solutions - run it after changing a task |
| `answer_reuse_test.py CFG` | two tool-loop turns and a user turn: does each turn continue the last answer's state? (`grep "glm reuse"` in the engine log) |
| `agent_turns_test.py CFG` | a longer agent session (three files written through a tool), the wait before each turn's first token |
| `image_session_test.py --state FILE` | a long conversation with a picture; `--state` saves it, so a run after a restart sends the same conversation back |
| `bench_summary.py [prefix ...]` | each label's medians from `results.jsonl` |
| `CFG=<config> srv.sh start / stop / set K=V / unset K / exe PATH` | starts and stops a test server from a config (Linux; `KESTREL_DIR` is the checkout, default this repository; `LOG` the engine log, default the config's), and edits that config's env and engine |

Models answer differently from run to run in the last bits (drafting, Turbo, the arithmetic order), so compare
settings on several runs; a one-task difference in the coding test is noise.
