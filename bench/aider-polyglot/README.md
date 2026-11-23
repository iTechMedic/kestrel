# Aider Polyglot: DeepSeek-V4.1-Flash on Kestrel

[Aider's polyglot benchmark](https://aider.chat/docs/leaderboards/) gives a model 225 Exercism exercises in C++, Go,
Java, JavaScript, Python and Rust. For each one, the model edits the code; the exercise's tests run; if they fail, the
model sees the failures and gets one more try. **Pass rate 2** (passed within two tries) is the leaderboard's number.

## Results

**86.0% (43 of 50) at low thinking, 84.0% (42 of 50) at high**: two runs of the same 50-exercise subset on
2026-11-22, with the same settings apart from the thinking level (and the Kestrel version, see below).

| | Kestrel, low | Kestrel, high | DeepSeek-V3.2-Exp Reasoner | DeepSeek R1 0528 | o3 (high) | Gemini 2.5 Pro (32K think) |
|---|--:|--:|--:|--:|--:|--:|
| Pass rate 2 | **86.0** | **84.0** | 74.2 | 71.4 | 81.3 | 83.1 |
| Pass rate 1 | 40.0 | 40.0 | 39.6 | 34.4 | 40.0 | 46.2 |
| Edits well formed | 92.0% | 94.0% | 97.3% | — | — | — |
| Seconds per exercise | 389 | 496 | 291 | 717 | 197 | 200 |
| Tokens out (the 50) | 781K | 1.04M | — | — | — | — |
| Exercises | 50 | 50 | 225 | 225 | 225 | 225 |

The other columns are from aider's leaderboard, which was last updated in October 2025 and has no DeepSeek V4 entry.
We found no other published polyglot score for DeepSeek-V4.1-Flash.

**Read it with these in mind:**
- **50 of 225 exercises.** The full-run score could be about 10 points either way (95% range). "In the low-to-mid
  80s" is fair; the order against the 81-83% models is not settled.
- **A 2.25-bit quant with Turbo.** turboderp's EXL3 quant at 2.25 bits, and Turbo on (`KESTREL_DS4_RESIDENT_TOPK=3`:
  3 of each token's 6 experts while decoding), which changes the answers slightly from the full model.
- **Local speed.** The seconds per exercise are one PC's, mostly thinking time; the others are cloud APIs.

By language (pass rate 2, low / high): Python 7/7 and 7/7, Rust 7/7 and 7/7, JavaScript 9/11 and 10/11,
C++ 6/6 and 5/6, Java 6/10 and 8/10, Go 8/9 and 5/9.

### Low against high

- **The same score, within chance.** 9 of the 50 exercises came out differently: 5 passed only at low, 4 only at high.
  A one-exercise lead says nothing about which level codes better.
- **Low is cheaper:** 22% less time (5.4 against 6.9 hours of exercise time) and 25% fewer tokens out.
- **Low's misses were mostly format slips.** In all 4 exercises only high passed, low's first answer had no
  SEARCH/REPLACE edits (the code, but not as edits aider can apply), and its second try didn't recover. High had the
  same slip once (C++ diamond).
- **DeepSeek V4.1 has three thinking levels:** low, high and max (a "Reasoning Effort" of 50, 75 or 100 of 100 in its
  prompt). Kestrel takes `medium` as high and `xhigh` as max, so a `medium` run is a high run.
- **Two Kestrel versions:** the high run on Kestrel 0.1.2 (the DeepSeek engine at upstream v1.1.71), the low run on
  0.1.3 (v1.1.74). The newer engine passed Kestrel's check against the older one before it shipped.

aider's `--stats` for the high run:

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

and for the low run:

```yaml
  test_cases: 50
  model: openai/deepseek-v4.1-flash
  edit_format: diff
  commit_hash: 5dc9490-dirty
  reasoning_effort: low
  pass_rate_1: 40.0
  pass_rate_2: 86.0
  pass_num_1: 20
  pass_num_2: 43
  percent_cases_well_formed: 92.0
  error_outputs: 4
  num_malformed_responses: 4
  num_with_malformed_responses: 4
  user_asks: 17
  lazy_comments: 0
  syntax_errors: 0
  indentation_errors: 0
  exhausted_context_windows: 0
  prompt_tokens: 399270
  completion_tokens: 781442
  test_timeouts: 0
  date: 2026-11-22
  versions: 0.86.3.dev
  seconds_per_case: 389.0
```

## The setup

- **Server:** Kestrel 0.1.2 for the high run, 0.1.3 for the low run, with the reference PC's tuned config
  ([examples/kestrel-ds4-r9700-8060s.json](../../examples/kestrel-ds4-r9700-8060s.json)): a Radeon AI PRO R9700 with a
  Ryzen AI MAX+ 395's Radeon 8060S as the helper GPU, Linux with ROCm, 262,144-token context.
- **Model:** DeepSeek-V4.1-Flash-1017, EXL3 2.25 bits, Turbo on.
- **Thinking:** aider's `--reasoning-effort high` or `low`, with Kestrel's `thinking_budget` at 32,768 tokens for both.
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

The high run was stopped once to make the timeout change and continued with aider's `--cont`; the 3 exercises
finished before then were kept. affine-cipher (JavaScript) was run again after the Jest change. The low run ran
straight through with all three changes.

## Where it failed

| Exercise | High | Low |
|---|---|---|
| C++ diamond | no SEARCH/REPLACE edits in either try (a format failure) | passed (2nd try) |
| Go connect | wrong win check: counted edge-only boards and diagonals | passed (2nd try) |
| Go error-handling | didn't compile | passed (2nd try) |
| Go food-chain | wrong verses | passed (1st try) |
| Go poker | didn't validate the cards | rejected valid cards (read the suit symbols a byte at a time), then failed again |
| Java change | passed (2nd try) | no SEARCH/REPLACE edits in the first answer; the second try's failed the tests |
| Java hangman | 4 tests failed, then the second try didn't compile | tests failed in both tries |
| Java phone-number | passed (2nd try) | no SEARCH/REPLACE edits in the first answer; the second try's failed the tests |
| Java word-search | called `WordLocation` with the wrong constructor, then wrong coordinates | wrong coordinates in both tries |
| JavaScript bottle-song | passed (1st try) | no SEARCH/REPLACE edits in the first answer; the second try's failed the tests |
| JavaScript food-chain | passed (2nd try) | no SEARCH/REPLACE edits in the first answer; the second try's failed the tests |
| JavaScript grep | treated the pattern as a file name | passed (2nd try) |

Two passing C++ exercises took long because aider's C++ lint reports errors in valid code and the model kept trying to
fix them: parallel-letter-frequency took 7 lint rounds, 121K tokens and 52 minutes at high (43 minutes at low);
queen-attack 18 minutes (14 at low).

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
./run-kestrel.sh high-turbo      # the 50 at high thinking; about 7 hours here
EFFORT=low ./run-kestrel.sh low-turbo   # the 50 at low; about 5.5 hours here
```

Then score it inside the container: `./benchmark/benchmark.py --stats tmp.benchmarks/<the run's folder>`.
Kestrel's `thinking_budget` (in the config, or the dashboard's Settings) caps the thinking; `EFFORT` sets aider's
level (`low`, `high` or `max` for DeepSeek: `medium` is the same as `high`). Results from other PCs and settings are welcome in a [GitHub issue](https://github.com/iTechMedic/kestrel/issues).

## Every exercise

| Language | Exercise | High | Minutes | Tokens out | Low | Minutes | Tokens out |
|---|---|:-:|--:|--:|:-:|--:|--:|
| cpp | bank-account | 1st try | 14.7 | 38,531 | 1st try | 16.1 | 40,707 |
| cpp | clock | 1st try | 29.4 | 77,475 | 2nd try | 19.3 | 49,348 |
| cpp | diamond | **fail** | 3.2 | 6,761 | 2nd try | 24.4 | 57,957 |
| cpp | grade-school | 1st try | 24.6 | 71,803 | 1st try | 24.9 | 63,052 |
| cpp | parallel-letter-frequency | 2nd try | 51.8 | 120,942 | 2nd try | 43.1 | 105,796 |
| cpp | queen-attack | 2nd try | 17.7 | 42,917 | 1st try | 14.4 | 36,236 |
| go | alphametics | 1st try | 6.6 | 17,810 | 1st try | 2.3 | 5,697 |
| go | bowling | 1st try | 4.5 | 10,959 | 2nd try | 7.5 | 22,069 |
| go | connect | **fail** | 15.8 | 46,148 | 2nd try | 7.8 | 21,129 |
| go | error-handling | **fail** | 3.9 | 8,065 | 2nd try | 1.6 | 2,581 |
| go | food-chain | **fail** | 2.9 | 7,193 | 1st try | 1.6 | 2,949 |
| go | pig-latin | 1st try | 2.9 | 6,940 | 1st try | 1.8 | 4,425 |
| go | poker | **fail** | 5.9 | 16,699 | **fail** | 5.1 | 12,638 |
| go | pov | 2nd try | 3.9 | 5,673 | 2nd try | 3.0 | 4,506 |
| go | two-bucket | 1st try | 11.7 | 33,985 | 1st try | 3.8 | 8,899 |
| java | book-store | 2nd try | 21.1 | 60,658 | 2nd try | 2.2 | 3,998 |
| java | change | 2nd try | 2.4 | 5,495 | **fail** | 2.3 | 5,381 |
| java | hangman | **fail** | 22.9 | 54,376 | **fail** | 22.9 | 58,096 |
| java | phone-number | 2nd try | 3.8 | 8,364 | **fail** | 2.6 | 6,955 |
| java | pig-latin | 1st try | 2.8 | 7,304 | 1st try | 2.0 | 3,739 |
| java | pov | 1st try | 2.4 | 4,497 | 1st try | 1.8 | 2,511 |
| java | protein-translation | 2nd try | 2.1 | 2,332 | 2nd try | 2.3 | 2,237 |
| java | transpose | 1st try | 4.5 | 15,314 | 1st try | 5.1 | 16,449 |
| java | word-search | **fail** | 3.7 | 7,979 | **fail** | 8.0 | 19,902 |
| java | zipper | 2nd try | 11.2 | 28,527 | 2nd try | 6.9 | 17,851 |
| javascript | affine-cipher | 2nd try | 4.9 | 12,548 | 2nd try | 2.3 | 3,386 |
| javascript | bottle-song | 1st try | 2.2 | 3,027 | **fail** | 1.4 | 1,470 |
| javascript | food-chain | 2nd try | 10.1 | 16,486 | **fail** | 1.6 | 2,965 |
| javascript | grep | **fail** | 14.6 | 39,136 | 2nd try | 13.1 | 35,450 |
| javascript | house | 2nd try | 2.3 | 4,052 | 2nd try | 2.3 | 4,740 |
| javascript | palindrome-products | 2nd try | 10.7 | 27,984 | 2nd try | 1.9 | 3,449 |
| javascript | phone-number | 2nd try | 2.6 | 5,273 | 2nd try | 2.2 | 5,017 |
| javascript | pig-latin | 1st try | 5.6 | 12,383 | 1st try | 1.9 | 5,096 |
| javascript | resistor-color-trio | 2nd try | 5.3 | 13,858 | 2nd try | 5.5 | 11,236 |
| javascript | say | 2nd try | 2.8 | 3,300 | 2nd try | 1.9 | 2,209 |
| javascript | zebra-puzzle | 2nd try | 9.9 | 27,486 | 1st try | 8.8 | 24,849 |
| python | beer-song | 1st try | 1.2 | 1,380 | 1st try | 1.2 | 1,373 |
| python | connect | 1st try | 6.6 | 15,202 | 1st try | 5.7 | 16,961 |
| python | dominoes | 1st try | 2.8 | 8,548 | 1st try | 3.3 | 8,119 |
| python | hangman | 2nd try | 2.2 | 5,307 | 2nd try | 2.2 | 4,101 |
| python | pov | 2nd try | 7.0 | 11,661 | 2nd try | 3.6 | 5,194 |
| python | transpose | 1st try | 6.1 | 15,496 | 1st try | 6.4 | 18,352 |
| python | zipper | 2nd try | 7.1 | 20,493 | 2nd try | 2.4 | 4,008 |
| rust | bowling | 1st try | 9.2 | 24,865 | 1st try | 4.4 | 11,115 |
| rust | fizzy | 2nd try | 8.6 | 22,520 | 2nd try | 7.5 | 11,848 |
| rust | grade-school | 2nd try | 4.2 | 8,989 | 2nd try | 1.9 | 4,842 |
| rust | poker | 1st try | 3.3 | 10,345 | 1st try | 3.3 | 8,754 |
| rust | say | 1st try | 2.2 | 4,077 | 1st try | 1.1 | 1,861 |
| rust | simple-cipher | 2nd try | 4.0 | 10,538 | 1st try | 3.9 | 9,153 |
| rust | word-count | 1st try | 1.7 | 3,589 | 2nd try | 1.6 | 786 |
