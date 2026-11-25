# GLM-5.3-Flash with EXL3 on the reference PC: what we measured

These notes record a day of GLM tuning on Kestrel's reference PC (2026-11-24): which quant and settings to use, what
each change bought, what did not help and why. The PC and its setup are in [KESTREL_LINUX_AMD.md](KESTREL_LINUX_AMD.md):
an R9700 (32 GB, `gfx1201`) on OCuLink leads, and the Ryzen AI MAX+ 395's Radeon 8060S (`gfx1151`, 128 GB of unified
memory) is the expert helper. All numbers come from the scripts in [bench/kestrel-glm](../bench/kestrel-glm/).

## Recommended setups

| Use | Quant | Turbo | Drafting | Short answers | After a 55K prompt |
| --- | --- | --- | --- | --- | --- |
| Long agent coding sessions | turboderp's **sc_2.60** EXL3 | off (all 8 experts) | DFlash2 | 39.9 tok/s | 28.4 tok/s |
| Short chats, speed first | turboderp's **sc_2.10** EXL3 | off | DFlash2 | 44.7 tok/s | 28.5 tok/s |
| Fastest | sc_2.10 | 4 | DFlash2 | 52.6 tok/s | 36.3 tok/s |
| *Before (0.1.6 default)* | *Maya-S24 (GGUF)* | *4* | *MTP* | *45.6 tok/s* | *33.9 tok/s* |

Both EXL3 quants are by-hand downloads (`--model EXL3-sc_2.60bpw` or `EXL3-sc_2.10bpw`). In long conversations the two
run at the same speed (see [Why the smaller quant only helps short answers](#why-the-smaller-quant-only-helps-short-answers)),
so sc_2.60's better accuracy is nearly free where it matters most.

The engine settings these setups share (on top of what the setup writes for two AMD GPUs):

```
"args":  ... "--dflash", "<models>/GLM-5.3-Flash-DFlash2/GLM-5.3-Flash-DFlash2-Q4_K_M.gguf"
"env":   "MAYA_GLM_EXPERT_HELPER": "1", "MAYA_GLM_SPLIT": "0", "MAYA_GLM_HELPER_EXL3": "1",
         "MAYA_GLM_PREFILL_SUB": "4096", "MAYA_GLM_PREFILL_MB": "6144", "MAYA_GLM_SLOT_KEEP": "1"
         (Turbo 4: "MAYA_GLM_RESIDENT_TOPK": "4")
"gpu":   [<R9700>, <8060S>]   - the faster card first
```

**The DFlash2 drafter's license is CC BY-NC-ND 4.0: non-commercial use only.** Without it, drop `--dflash` and set
`MAYA_GLM_MTP_DECODE=1` and `MAYA_GLM_MTP_ADAPT=1` (the MTP rows below).

## Every measurement

Speeds in tokens per second. "13.7K" and "55K" are prompts read from scratch, then a 256-token answer. The coding test
is 20 Python tasks with hidden edge-case tests (`coding_eval.py`, reasoning effort low, temperature 0).

| Quant | Turbo | Drafting | Short | 13.7K: read / answer | 55K: read / answer | Coding | Tokens / time for all 20 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Maya-S24 | 4 | MTP | 45.6 | 700 / 32.2 | 726 / 33.9 | 16/20 | 22,740 / 554 s |
| Maya-S24 | off | MTP | 41.0 | 709 / 30.9 | 699 / 27.4 | 18/20 | 7,582 / 215 s |
| sc_2.10 | 4 | MTP | 44.0 | 582 / 31.3 | 697 / 34.2 | 18/20 | 7,386 / 190 s |
| sc_2.10 | off | MTP | 38.6 | 584 / 26.9 | 698 / 30.4 | 18/20 | 6,091 / 181 s |
| sc_2.10 | 4 | DFlash2 | **52.6** | 640 / **35.0** | 694 / **36.3** | 19/20 | 8,908 / 202 s |
| sc_2.10 | off | DFlash2 | 44.7 | 636 / 29.0 | 675 / 28.5 | 19/20 | 8,485 / 231 s |
| sc_2.60 | off | MTP | 35.3 | 593 / 25.8 | 741 / 27.2 | 17/20 | 6,137 / 220 s |
| sc_2.60 | off | DFlash2 | 39.9 | 566 / 29.1 | 631 / 28.4 | 18/20 | 5,227 / **160 s** |
| sc_2.60 | 4 | DFlash2 | 47.6 | 646 / 33.1 | 673 / 30.8 | 18/20 | 7,903 / 202 s |

Prompt-read speeds vary by about ±5% from run to run (the 55K rows especially); Turbo and drafting do not change them.

### Reading the coding scores

**17-19 out of 20 is one result at this test's resolution.** Twelve tasks pass everywhere and one (`edit_distance`)
fails almost everywhere; the other few flip between runs of the *same* model when only the drafter changes (the
drafter does not change what the model wants to write, only the last bits of its arithmetic, and a near-tie early on
sends the answer down another path). It cannot tell sc_2.10 from sc_2.60. turboderp's KL divergence against the full
model can: **sc_2.60 0.093, sc_2.10 0.157** (lower is closer to the full model).

What the test does show: **Maya-S24 with Turbo 4 is the outlier** - the lowest score, two answers that did not compile,
and three times the tokens of every other setup, as it revised its answers again and again. sc_2.10 with Turbo 4 stays
as concise as with Turbo off.

## What changed in Kestrel

- **The answer's state is kept** (engine, `src/program/generate.cpp`, `answer_snapshot`). GLM saved its conversation
  state just before each answer, so an agent's next turn read the whole last answer again - 32,485 tokens (47 s) in one
  live turn, 19,880 (27 s) in another. GLM's template sends a tool loop's answers back as they were written (reasoning
  included), so the engine now moves its snapshot to the end of a finished answer, after keeping the prompt's state as
  a fallback (a checkpoint; for a prompt with pictures, a slot). The log says either `glm reuse: the last answer's
  state goes on` or the exact token where a prompt left the answer. Measured: a turn after a tool call reads 11-17 new
  tokens (0.7-0.8 s); a 27K-token conversation with a screenshot, 13-16 (0.7-0.8 s). `MAYA_GLM_ANSWER_SNAP=0` turns
  it off.
- **Conversations survive restarts** with `MAYA_GLM_SLOT_KEEP=1` (an existing engine feature, off by default): the
  engine saves the conversation in the model when it ends and takes it back from disk at the next start. The first
  turn after a restart (27K tokens, a screenshot): 3.4 s instead of ~37 s. Slots use up to `MAYA_GLM_SLOT_GB` (16) GB
  in `<pack>/slots`.
- **EXL3 prompts in sub-batches of 4,096** (the setup, `maya.py`): an EXL3 quant on an APU system with 96 GB or more
  now gets `MAYA_GLM_PREFILL_SUB=4096`. The trunk's EXL3 matrices are decoded once a sub-batch. A 55K prompt on
  sc_2.60: 648 -> 736-741 tok/s. GGUF quants keep 1,024: Maya-S24 is slower at 4,096 (726 -> 686).
- **sc_2.60 and sc_2.10 in the setup's model list** (by hand, pinned revisions, every file's sha256).

## What did not help, and why

- **A bigger prompt budget** (`MAYA_GLM_PREFILL_MB=12288`): no faster (630 against 648 tok/s). The engine keeps a
  checkpoint every `MAYA_GLM_CKPT_EVERY` (16,384) tokens, which ends a chunk, so chunks stay at 16K whatever the budget;
  the bigger loan only shrank the expert pool.
- **Sub-batches of 8,192**: 729 tok/s, no better than 4,096. The mixer got cheaper again, but the larger loan left the
  expert pool so small that each chunk copied 28-43 GB over OCuLink instead of 6-23 GB.
- **The helper's knobs**: `MAYA_GLM_HELPER_OVERLAP` only matters where the CPU lane computes experts (0.2 a token
  here); `MAYA_GLM_HELPER_SPIN` is documented as no faster.
- **EXL3 kernel choices**: `MAYA_GLM_EXL3_DECODE` exists only in NVIDIA builds; the RDNA4 scalar prompt tiles
  (`MAYA_EXL3_HIP_SCALAR_ROWS`) cover 3- and 4-bit experts, and these quants' are 2 and 2.5 bits.
- **Turbo 6** (`MAYA_GLM_RESIDENT_TOPK=6`, sc_2.60, MTP): 39.0 against 35.3 tok/s short (+10%), 12/12 on the quick
  check. A middle ground, not used.

### Where the time goes

**Writing is memory-bound on both GPUs.** Per token, each layer's experts the R9700 does not hold go to the 8060S in
one call: 5.2 experts a call, 0.24 ms of GPU time (gate/up 0.153, down 0.088) - about 42 MB in 0.24 ms, ~175 GB/s of
the 8060S's ~256. Over 43 layers that is ~12 ms of a ~30 ms token. The R9700 spends ~10 ms reading the trunk: turboderp's
quants keep the attention projections in BF16, 6.27 GB a token against Maya-S24's 5.24 GB (Q4_K attention), which also
leaves fewer VRAM expert slots (3,025 against 3,572).

**Reading prompts is bound by the trunk on the R9700**, not by OCuLink: in each 16K chunk the mixer (attention and the
other non-expert layers) takes 12-20 s; the expert copies overlap it. The 8060S does not take part in reading prompts
("prefill unchanged" in the log) - it computes in decode only, at about 36% busy.

### Why the smaller quant only helps short answers

With Turbo off and DFlash2, sc_2.10 is 12% faster than sc_2.60 on short answers (44.7 against 39.9), but after a
13.7K or 55K prompt both answer at 28.4-29.1 tok/s: attention over the long context dominates, and it does not depend
on the quant. Agent sessions run at 20-90K tokens.

## Why DeepSeek answers faster on the same PC

DeepSeek-V4.1-Flash's tuned EXL3 config answers at ~60 tok/s short and 47-60 after a long prompt, though it reads
prompts slower (440-530 tok/s) and even streams some experts from the SSD. Memory is not the difference:

| | DeepSeek-V4.1-Flash | GLM-5.3-Flash |
| --- | --- | --- |
| Expert weights a token | 3 of 6 experts (Turbo 3), ~4.2 B | 4 of 8 (Turbo 4) ~4.3 B; all 8 ~8.7 B |
| Drafting | DSpark (7.5 GB drafter) + 3 MTP layers: several tokens a round | 1 MTP layer: 1.7-2.0 tokens a round, the adaptive length settles on 1 |
| Attention: earlier tokens read a token | 512 | 2,048 |

The drafting was the biggest part: verifying a window costs nearly the same for one accepted draft or five. GLM's
DFlash2 drafter (8-token blocks, 87-94% of drafts accepted on longer answers) closed much of it: +16-20% short. The
attention difference stays, which is why GLM still slows more after long prompts.

## Things that cost us time

- **The GPU order changes when a card moves to another port.** After the R9700 moved to OCuLink it became HIP device 0;
  a config with the 8060S first read prompts at 156 tok/s against 540-700. Check each model's GPU list.
- **`--expert-profile` must name a file that exists**: the engine will not start otherwise. GLM's shipped profile
  (`data/expert-profile-glm.bin`) is the model's routing, not the quant's - use it for any GLM quant.
- **A server started in the background ignores SIGINT**; stop it with SIGTERM (the engine still ends cleanly and saves
  its conversation with `MAYA_GLM_SLOT_KEEP=1`). When stopping with `pkill -f`, bracket a letter of the pattern
  (`[s]erve/server.py`) so the pattern cannot match the shell running it.
- **The live coding test without a thinking level** ran past 6,000 tokens of reasoning and never wrote code; agents
  usually send `reasoning_effort` (`low` here).
- **The first turn after any restart reads the whole conversation** without `MAYA_GLM_SLOT_KEEP=1` - 94,627 tokens,
  2 min 22 s in one live session.
- **The 12-question quick check** (`glm_quality.py`) only shows that a quant is not broken: every setup scored 11-12.
