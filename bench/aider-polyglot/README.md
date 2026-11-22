# Aider Polyglot: DeepSeek-V4.1-Flash on Kestrel

[Aider's polyglot benchmark](https://aider.chat/docs/leaderboards/) gives a model 225 Exercism exercises in C++, Go,
Java, JavaScript, Python and Rust. For each one, the model edits the code; the exercise's tests run; if they fail, the
model sees the failures and gets one more try. **Pass rate 2** (passed within two tries) is the leaderboard's number.

## Result

**84.0% (42 of 50)**, run 2026-11-22 on a 50-exercise subset.

| | Kestrel run | DeepSeek-V3.2-Exp Reasoner | DeepSeek R1 0528 | o3 (high) | Gemini 2.5 Pro (32K think) |
|---|--:|--:|--:|--:|--:|
| Pass rate 2 | **84.0** | 74.2 | 71.4 | 81.3 | 83.1 |
| Pass rate 1 | 40.0 | 39.6 | 34.4 | 40.0 | 46.2 |
| Edits well formed | 94.0% | 97.3% | — | — | — |
| Seconds per exercise | 496 | 291 | 717 | 197 | 200 |
| Exercises | 50 | 225 | 225 | 225 | 225 |

The other columns are from aider's leaderboard, which was last updated in October 2025 and has no DeepSeek V4 entry.
We found no other published polyglot score for DeepSeek-V4.1-Flash.

**Read it with these in mind:**
- **50 of 225 exercises.** The full-run score could be about 10 points either way (95% range). "In the low-to-mid
  80s" is fair; the order against the 81-83% models is not settled.
- **A 2.25-bit quant with Turbo.** turboderp's EXL3 quant at 2.25 bits, and Turbo on (`KESTREL_DS4_RESIDENT_TOPK=3`:
  3 of each token's 6 experts while decoding), which changes the answers slightly from the full model.
- **Local speed.** The seconds per exercise are one PC's, mostly thinking time; the others are cloud APIs.

By language (pass rate 2): Python 7/7, Rust 7/7, JavaScript 10/11, C++ 5/6, Java 8/10, Go 5/9.

aider's `--stats` for the run:

```yaml
  test_cases: 50
  model: openai/deepseek-v4.1-flash
  edit_format: diff
  commit_hash: 5dc9490-dirty
  reasoning_effort: high
  pass_rate_1: 40.0
  pass_rate_2: 84.0
  pass_num_1: 20
  pass_num_2: 42
  percent_cases_well_formed: 94.0
  error_outputs: 3
  num_malformed_responses: 3
  num_with_malformed_responses: 3
  user_asks: 15
  lazy_comments: 0
  syntax_errors: 0
  indentation_errors: 0
  exhausted_context_windows: 0
  prompt_tokens: 419710
  completion_tokens: 1035290
  test_timeouts: 0
  date: 2026-11-22
  versions: 0.86.3.dev
  seconds_per_case: 496.1
```

## The setup

- **Server:** Kestrel 0.1.2 (DeepSeek engine at upstream v1.1.71), the reference PC's tuned config
  ([examples/kestrel-ds4-r9700-8060s.json](../../examples/kestrel-ds4-r9700-8060s.json)): a Radeon AI PRO R9700 with a
  Ryzen AI MAX+ 395's Radeon 8060S as the helper GPU, Linux with ROCm, 262,144-token context.
- **Model:** DeepSeek-V4.1-Flash-1017, EXL3 2.25 bits, Turbo on.
- **Thinking:** aider's `--reasoning-effort high`, with Kestrel's `thinking_budget` at 32,768 tokens.
- **Sampling:** the model's own (temperature 1.0); [kestrel-model-settings.yml](kestrel-model-settings.yml) stops aider
  forcing temperature 0.
- **aider:** commit 5dc9490 with [three small changes](aider-kestrel.patch), the diff (SEARCH/REPLACE) edit format, one
  exercise at a time, polyglot-benchmark at 7e0611e, run from a Mac in aider's benchmark container.
- **The 50 exercises:** [kestrel-50.txt](kestrel-50.txt), drawn per language in proportion to the full set (6 C++,
  9 Go, 10 Java, 11 JavaScript, 7 Python, 7 Rust) with a fixed seed (20261121), so every run gets the same 50.

**The changes to aider** ([aider-kestrel.patch](aider-kestrel.patch)):
- **Jest pinned to 29.7.0** in the benchmark container. The current Jest (30) removed `toThrowError`, which some of the
  JavaScript exercises' tests use, so those can't pass with any answer.
- **Request timeout 600 → 3600 s.** aider's benchmark doesn't stream; a 32K-token think takes about 10 minutes at
  this speed, so at 600 s aider cancelled answers that were nearly done and asked again.
- **`OPENAI_API_BASE` passed into the container**, to reach a server on another machine.

The run was stopped once to make the timeout change and continued with aider's `--cont`; the 3 exercises finished
before then were kept. affine-cipher (JavaScript) was run again after the Jest change.

## Where it failed

| Exercise | Why |
|---|---|
| C++ diamond | no SEARCH/REPLACE edits in either try (a format failure) |
| Go connect | wrong win check: counted edge-only boards and diagonals |
| Go error-handling | didn't compile |
| Go food-chain | wrong verses |
| Go poker | didn't validate the cards |
| Java hangman | 4 tests failed, then the second try didn't compile |
| Java word-search | called `WordLocation` with the wrong constructor, then wrong coordinates |
| JavaScript grep | treated the pattern as a file name |

Two passing C++ exercises took long because aider's C++ lint reports errors in valid code and the model kept trying to
fix them: parallel-letter-frequency took 7 lint rounds, 121K tokens and 52 minutes; queen-attack 18 minutes.

## Run it yourself

You need Docker, an aider clone and a Kestrel server serving DeepSeek-V4.1-Flash.

```sh
git clone https://github.com/Aider-AI/aider.git && cd aider
git apply ~/kestrel/bench/aider-polyglot/aider-kestrel.patch
cp ~/kestrel/bench/aider-polyglot/{kestrel-50.txt,kestrel-model-settings.yml,run-kestrel.sh} .
git clone https://github.com/Aider-AI/polyglot-benchmark tmp.benchmarks/polyglot-benchmark
docker build --file benchmark/Dockerfile -t aider-benchmark:jest29 .

export OPENAI_API_BASE=http://<kestrel's address>:8000/v1 OPENAI_API_KEY=<kestrel's api_key>
./run-kestrel.sh setup check     # 2 exercises, a few minutes
./run-kestrel.sh high-turbo      # the 50; about 7 hours here
```

Then score it inside the container: `./benchmark/benchmark.py --stats tmp.benchmarks/<the run's folder>`.
Kestrel's `thinking_budget` (in the config, or the dashboard's Settings) caps the thinking; `EFFORT=medium` sets aider's
level. Results from other PCs and settings are welcome in a [GitHub issue](https://github.com/iTechMedic/kestrel/issues).

## Every exercise

| Language | Exercise | Try 1 | Try 2 | Minutes | Tokens out |
|---|---|:-:|:-:|--:|--:|
| cpp | bank-account | pass | — | 14.7 | 38,531 |
| cpp | clock | pass | — | 29.4 | 77,475 |
| cpp | diamond | fail | fail | 3.2 | 6,761 |
| cpp | grade-school | pass | — | 24.6 | 71,803 |
| cpp | parallel-letter-frequency | fail | pass | 51.8 | 120,942 |
| cpp | queen-attack | fail | pass | 17.7 | 42,917 |
| go | alphametics | pass | — | 6.6 | 17,810 |
| go | bowling | pass | — | 4.5 | 10,959 |
| go | connect | fail | fail | 15.8 | 46,148 |
| go | error-handling | fail | fail | 3.9 | 8,065 |
| go | food-chain | fail | fail | 2.9 | 7,193 |
| go | pig-latin | pass | — | 2.9 | 6,940 |
| go | poker | fail | fail | 5.9 | 16,699 |
| go | pov | fail | pass | 3.9 | 5,673 |
| go | two-bucket | pass | — | 11.7 | 33,985 |
| java | book-store | fail | pass | 21.1 | 60,658 |
| java | change | fail | pass | 2.4 | 5,495 |
| java | hangman | fail | fail | 22.9 | 54,376 |
| java | phone-number | fail | pass | 3.8 | 8,364 |
| java | pig-latin | pass | — | 2.8 | 7,304 |
| java | pov | pass | — | 2.4 | 4,497 |
| java | protein-translation | fail | pass | 2.1 | 2,332 |
| java | transpose | pass | — | 4.5 | 15,314 |
| java | word-search | fail | fail | 3.7 | 7,979 |
| java | zipper | fail | pass | 11.2 | 28,527 |
| javascript | affine-cipher | fail | pass | 4.9 | 12,548 |
| javascript | bottle-song | pass | — | 2.2 | 3,027 |
| javascript | food-chain | fail | pass | 10.1 | 16,486 |
| javascript | grep | fail | fail | 14.6 | 39,136 |
| javascript | house | fail | pass | 2.3 | 4,052 |
| javascript | palindrome-products | fail | pass | 10.7 | 27,984 |
| javascript | phone-number | fail | pass | 2.6 | 5,273 |
| javascript | pig-latin | pass | — | 5.6 | 12,383 |
| javascript | resistor-color-trio | fail | pass | 5.3 | 13,858 |
| javascript | say | fail | pass | 2.8 | 3,300 |
| javascript | zebra-puzzle | fail | pass | 9.9 | 27,486 |
| python | beer-song | pass | — | 1.2 | 1,380 |
| python | connect | pass | — | 6.6 | 15,202 |
| python | dominoes | pass | — | 2.8 | 8,548 |
| python | hangman | fail | pass | 2.2 | 5,307 |
| python | pov | fail | pass | 7.0 | 11,661 |
| python | transpose | pass | — | 6.1 | 15,496 |
| python | zipper | fail | pass | 7.1 | 20,493 |
| rust | bowling | pass | — | 9.2 | 24,865 |
| rust | fizzy | fail | pass | 8.6 | 22,520 |
| rust | grade-school | fail | pass | 4.2 | 8,989 |
| rust | poker | pass | — | 3.3 | 10,345 |
| rust | say | pass | — | 2.2 | 4,077 |
| rust | simple-cipher | fail | pass | 4.0 | 10,538 |
| rust | word-count | pass | — | 1.7 | 3,589 |
