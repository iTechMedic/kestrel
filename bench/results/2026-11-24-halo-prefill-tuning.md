# R9700 + 8060S: prefill/decode tuning sweep — 2026-11-24

Reference PC: R9700 (gfx1201) over OCuLink lead + Ryzen AI Max 8060S (gfx1151) helper, 128 GB.
Engine `kestrel-glm-answer-da0a2eb`, EXL3 sc_2.10, DFlash2, Turbo off (the PC's usual setup).
All runs: `glm_bench.py` / `long_bench.py`, greedy, thinking off; API through a copy of that config, the
original untouched. Raw runs kept in the bench results log (`results.jsonl`).

## Numbers

| label | env change | short decode | 13.7K read | 55K read |
| --- | --- | ---: | ---: | ---: |
| halo-base1 | — | 44.8 | 632 | 684 |
| halo-base2 | — (repeat) | 44.6 | 628 | — |
| kda1 / kda2 | `MAYA_GLM_KDA_GRAPH=1` | 44.6 / 45.4 | 638 / 631 | — |
| hovl1 / hovl2 | `MAYA_GLM_HELPER_OVERLAP=1` | 44.6 / 44.5 | 627 / 631 | — |
| pfmb12 | `MAYA_GLM_PREFILL_MB=12288` | — | — | 666 (worse, see below) |
| link-ps2 | `MAYA_GLM_EXPERT_HELPER=link` + prompt lane | 44.6 | **369** | 364 |

Run-to-run noise on short decode is ~±1 %; none of the on/off variants is a win.

## Where the prefill time goes (trace on the current config, 13.7K single chunk, 20.5 s)

Per MoE layer (`MAYA_GLM_PREFILL_TRACE`): `start->plan` (mixer + router) **160-180 ms** for the recurrent (KDA)
layers and **~510 ms** for every 4th (DSA) layer; the expert side is only ~95 ms (copies land at plan+195,
compute 94 ms). Over a chunk that is ~11.7 s of mixer vs ~4.4 s of experts, i.e. **prefill here is 60-65 %
attention on the lead GPU**. At 55K the last (tail) chunk is nearly pure attention: `lead 8768` ms of 11.4 s.

## Findings

- **The linked helper's prefill lane loses on this pairing.** With `MAYA_GLM_EXPERT_HELPER=link` (the
  `maya-glm-helper` program built from the engine's own tree, prompt exchange 1.01 GB, EXL3 x3 lane on),
  13.7K reads fall 632 -> 369 tok/s: the 8060S does EXL3 prompt rows at ~260 tok/s equivalent, ~2.4x slower
  than the R9700. The staggered half-chunk pipeline (`MAYA_GLM_PF_PIPE=1`) additionally requires *consecutive*
  helper-owned MoE layers - with the default `MAYA_GLM_LINK_PF_STREAM=2` (every other layer streamed) there are
  none, so `pipe_n` is 0 and the pipe silently stays off. Even forced all-helper (`LINK_PF_STREAM=0`), perfect
  overlap could at best match the lead's own rate. **Conclusion: helper prefill offload is a dead end on this
  machine; keep the in-process helper (`EXPERT_HELPER=1`), whose value is decode experts.**
  The fused RDNA4 kernel path was never active here (`pf_fused_here` needs RDNA4 + `n_embd==4096 && n_ff==2048`
  + `MAYA_HIP_PREFILL_FUSED`; the helper log shows the generic x3 lane, no "prompt experts through the fused
  kernel" line) - and making it fit would only reach parity at best.
- **`MAYA_GLM_KDA_GRAPH=1` on HIP: within noise** (44.6/45.4 vs 44.8) - matches the SETTINGS.md note that a
  Ryzen AI Max-class one-GPU decode shows no change; the off-by-default for AMD costs nothing here.
- **`MAYA_GLM_HELPER_OVERLAP=1`: flat** — on this box the helper and CPU lane rarely share a route.
- **`MAYA_GLM_PREFILL_MB=12288`: slightly worse** (666 vs 684 at 55K) — the chunk cap stays 16384 and the bigger
  buffer eats the resident expert pool (resident 2774 -> 2364). Keep 6144.
- **`EXL3_WMMA_ROWS=32` needs no setting**: `wmma_rows()` (src/kernels/cuda/exl3.cu:3453) already defaults to
  32 on gfx12 - the measured win is in the code as a default.
- **`vm.watermark_scale_factor=200` and `vm.swappiness=10` are already persistent** on the reference PC
  (`/etc/sysctl.d/90-maya-reclaim.conf`, `99-swappiness.conf`); zram swap is off.
- Not applicable here: `MAYA_GLM_SPEC_CANCEL` / `_SAMPLE` and the batched draft windows require a GPU *split*
  (this box is one lead + integrated helper); the single-GPU DFlash policy is documented as measured within 1 %
  of the best cut/product rule, and its acceptance is 87-94 %.
- hipBLASLt tables: the trunk GEMM shapes are identical between the GGUF and EXL3 packs (same model), the tuned
  tables are already loaded, and an earlier sweep measured no change from them - nothing to retune.

## What the numbers say about the remaining headroom

On this pairing the scheduling is at its ceiling: prefill waits on the lead's attention kernels (DSA index pass
~3.2x a KDA layer, both far above the expert work beside them), and decode at 44-45 tok/s runs on the tuned
DFlash2 path. The only levers above ~10 % left are kernel-level on gfx1201 (the DSA/KDA prefill attention
themselves - kernel work), or the quality-trade knobs already tuned (Turbo: measured +21 % decode after a 13.7K
read and +27 % after 55K, sc_2.10 with DFlash2, at some quality cost).
