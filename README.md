<p align="center"><img src="serve/web/icon.svg" width="128" alt="Kestrel logo"></p>

<h1 align="center">Kestrel</h1>

<p align="center"><b>DeepSeek-V4.1-Flash-1017 (748 B), GLM-5.3 (744 B), GLM-5.3-Flash (321 B), MiniMax-M3.1-Flash (428 B),
Hy4-Flash (220 B) and Inkling-2-Mini (26 B) on your own GPUs</b><br>
private and fast · NVIDIA and AMD · Linux and Windows · chat, pictures, OpenAI- and Anthropic-compatible API ·
several requests at once</p>

Models this size usually need a datacenter. Kestrel runs them on the hardware you already have. Each model has an
engine built for it: it keeps the experts your conversation uses most on the GPU, the next ones in RAM and the rest on
your NVMe SSD, and moves them as you chat. It measures your GPUs, CPU, RAM and SSD and tunes itself to them. Nothing
leaves your machine.

Kestrel is a fork of [Project Maya](https://github.com/mw00/project-maya) by Peasant Smith
([credits](#credits-and-license)). It follows Project Maya's releases and adds its own look, its own releases and
updater, and engine work for AMD GPUs - DeepSeek-V4.1-Flash on a Radeon card with a Ryzen AI Max's Radeon 8060S as a
helper GPU, at contexts up to 256K. What each release changes: [releases](https://github.com/iTechMedic/kestrel/releases).

- **Fast at long contexts:** a 250K-token prompt read at 1,477 tokens/s and answered at about 50 tokens/s on a Radeon AI PRO
  R9700 with a Radeon 8060S helper ([how it was measured](#how-fast-is-it)).
- **Plugs into your tools:** OpenAI- and Anthropic-compatible API with tool calls, ready for coding agents.
- **Several requests at once:** up to 8 answered together with GLM-5.3-Flash, DeepSeek-V4.1-Flash and
  MiniMax-M3.1-Flash - for agents that run several sessions, or several people on one PC.
- **Everything in the box:** a chat and a live monitor in the browser, pictures on the models that read them, thinking
  levels, a Models page that downloads, loads and deletes models, a Turbo button, a one-command setup, and Kestrel's
  own color schemes.

## Quick start

```sh
git clone https://github.com/iTechMedic/kestrel.git && cd kestrel
./kestrel.sh
```

The first run asks which model you want, downloads it, builds everything once and **starts the model**. Then open
`http://127.0.0.1:8080`. Windows: `START-KESTREL.bat` instead of `./kestrel.sh`. More in [Install](#install).

More documentation: [docs/README.md](docs/README.md), Project Maya's own docs, which apply to Kestrel too. Where they
name Project Maya's start, run `./kestrel.sh` (Windows: `START-KESTREL.bat`), and a setting they spell with the `MAYA_`
prefix also works as `KESTREL_...`.

## <a name="the-models"></a><a name="deepseek-v41-flash-1017-new"></a><a name="minimax-m31-flash-new"></a>Pick your model

Most of the quants Kestrel downloads are Peasant Smith's, made for Project Maya and published on
[Hugging Face](https://huggingface.co/peasantsmith) under their own names (Maya-XS, -S, -M, -L: the tier is how many
bits the experts keep). The setup recommends one for your PC; to pick one yourself, give its setup id:
`./kestrel.sh --setup --model glm-maya-s24`.

| Model | Quant · setup id | Size | Made for |
| --- | --- | ---: | --- |
| **[GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash)**<br><sub>zai-org · MIT · 321 B, 18 B active · up to 1M context</sub> | **Maya-S** (default) · `glm-maya-s` | 96.5 GB | PCs with a smaller memory pool (RAM and VRAM together) |
| | Maya-S24 · `glm-maya-s24` | 94.7 GB | cards of 24 GB or less: ~1.5 GB more of the card for experts, decode +14% |
| | Maya-XS · `glm-maya-xs` | 73.4 GB | PCs with 64 GB of RAM and a 24 GB card, at 128K context |
| | Maya-M · `glm-maya-m` | 116 GB | a bigger memory pool; calibrated toward tool calls and front-end code |
| | Maya-M-Derisked · `glm-maya-m-derisked` | 116 GB | Maya-M with a weight edit by [Blackfrost_AI](https://x.com/Blackfrost_AI) that reduces blanket refusals; experimental |
| | Maya-L · `glm-maya-l` | 156.3 GB | the biggest memory pools; the closest to the original |
| **[GLM-5.3](https://huggingface.co/zai-org/GLM-5.3)**<br><sub>zai-org · [its own license](https://huggingface.co/zai-org/GLM-5.3) · 744 B, 40 B active · up to 1M context · text only</sub> | **Maya-XS** · `glm-5.3-maya-xs` | 170.0 GB | the whole model in a 192 GB memory pool (VRAM and RAM together); NVIDIA from the V100 on and AMD ([details](docs/GLM53.md)) |
| | UD-IQ2_M (unsloth) · `GLM-5.3-UD-IQ2_M` | 238.6 GB | the biggest memory pools; closer to the original |
| **[DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017)**<br><sub>DeepSeek · MIT · 748 B</sub> | **Maya-S** (default) · `deepseek-maya-s` | 340 GB | any amount of memory: what VRAM and RAM don't hold is read from the SSD |
| | Maya-XS (v2) · `deepseek-maya-xs` | 277 GB | the whole model in a 128 GB PC's memory (the Engram tables stay on the SSD); v2 is about 12% closer to the original and about 20% faster at writing than v1 - running the setup again offers the update |
| **[MiniMax-M3.1-Flash](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash)**<br><sub>MiniMax · [MiniMax Community License](LICENSE.minimax-m31) · 428 B, 23 B active · up to 1M context</sub> | Maya-XS · `minimax-maya-xs` | 93 GB | the whole model in a 128 GB PC's memory |
| | Maya-S · `minimax-maya-s` | 122 GB | closer to the original |
| **[Hy4-Flash](https://huggingface.co/tencent/Hy4-flash)**<br><sub>Tencent · [Tencent Hy License](LICENSE.hy4-flash) · 220 B · up to 1M context · reads pictures · NVIDIA, AMD on Linux</sub> | Maya-XS · `hy4-flash-maya-xs`<br>Maya-S · `hy4-flash-maya-s`<br>Maya-M · `hy4-flash-maya-m`<br>Maya-L · `hy4-flash-maya-l` | 44.8 GB<br>53.0 GB<br>68.4 GB<br>89.5 GB<br>each + one 63.4 GB n-gram table | PCs with about 56-64 GB (Maya-XS; cards from 8 GB), 68-80 GB (Maya-S), 80-96 GB (Maya-M) or 104-128 GB (Maya-L) of RAM + VRAM; Maya-S, Maya-M and Maya-L on cards from 12 GB; the n-gram table stays on the SSD |
| **[Inkling-2-Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)** (new)<br><sub>thinkingmachines · Apache 2.0 · 26 B, 8 of 128 experts a token · up to 1M context · reads pictures · experimental preview</sub> | UD-Q4_K_XL (unsloth) · `inkling-2-mini` | 17.6 GB | AMD on Linux: one RDNA 3 / 4 card from 12 GB (the experts that don't fit stay in RAM; 24 GB or more holds the whole model), or a Ryzen AI Max ([speed on an R9700](#inkling-2-mini-on-a-radeon-ai-pro-r9700)). NVIDIA from the V100 / RTX 20 on, from 8 GB (the experts that don't fit stay in RAM), Linux and Windows, one or two GPUs |

**Which model fits your PC?** See [docs/MEMORY.md](docs/MEMORY.md) for each model's recommended memory (VRAM + RAM together).

All of them run on NVIDIA from the V100 / RTX 20 on, and on AMD and Windows (see
[What you need](#what-you-need)); Hy4-Flash runs on NVIDIA (Linux and Windows) and on AMD on Linux (Strix Halo / Gorgon Halo, Radeon cards) and reads pictures on every card that runs it (8 GB cards included). Inkling-2-Mini runs on AMD on Linux only, on one GPU. DeepSeek's sizes include its Engram tables. The setup also offers unsloth's GGUF and
turboderp's and LibertAIDAI's EXL3 quants of DeepSeek, orcarouter's abliterated DeepSeek, Mia-AiLab's EXL3 quant of MiniMax,
turboderp's EXL3 quants of GLM, Qwen-3.8-Flash-Next (CYBER-FROST) as its Q5_K_M GGUF and Qwen-3.8-Flash-Next
itself as unsloth's UD-IQ2_XS GGUF, both with pictures
([its settings](docs/SETTINGS.md#qwen-38-flash-next-cyber-frost)), and Tencent's own Q4_K_M of Hy4-flash (AngelSlim's GGUF)
with MTP drafting (run on NVIDIA RTX 30 / A100 and newer, Linux; with pictures: `./kestrel.sh --setup --model hy4-flash-q4_k_m`;
[its settings](docs/SETTINGS.md#hy4-flash)). **Each model's files, drafters, pictures and options:
[docs/MODELS.md](docs/MODELS.md).**

**turboderp's self-calibrated EXL3 weights of GLM-5.3-Flash** (`sc_2.60bpw`, `sc_2.10bpw`) are supported but not
in the setup's menu: name one and the setup downloads it (`./kestrel.sh --setup --model EXL3-sc_2.60bpw`). Best
for long agent sessions on a discrete card + Ryzen AI Max layout: after a long prompt both answer at the same
speed, and sc_2.60 is the closer one to the full model. [What they are, how to get them and the settings we
measured](docs/KESTREL_GLM_EXL3.md#use-turboderps-exl3-weights).

## Quality

The quants Kestrel downloads are other people's work, measured by their makers against the original models:

- **GLM-5.3-Flash · Maya quants** (Peasant Smith) keep 97.7-99.2% of the FP8 model's zero-shot accuracy and pick its
  next token 83-90% of the time (Maya-L: 99.2%, 90%). How they're made and measured: [MAYA-S](bench/results/MAYA-S.md),
  [MAYA-S24](bench/results/MAYA-S24.md), [MAYA-M](bench/results/MAYA-M.md), [MAYA-L](bench/results/MAYA-L.md).
- **DeepSeek V4.1 · Maya-S** picks the same next token as the original 92.6% of the time.
- **MiniMax M3.1 · Maya-S** picks it 87.6% of the time (the average over its categories).
- **Hy4-Flash · Maya quants** pick it 88.5% (Maya-XS) to 96.6% (Maya-L) of the time, with a KL divergence of 0.16
  down to 0.012 - charts against Tencent's own GGUFs on the [model card](https://huggingface.co/peasantsmith/Hy4-Flash-Maya-GGUF).

**Coding, measured with Kestrel:** DeepSeek-V4.1-Flash scored **86%** at low thinking and **84%** at high on
[aider's polyglot benchmark](https://aider.chat/docs/leaderboards/) (43 and 42 of a fixed 50-exercise subset, passed
within two tries), with the 2.25-bit EXL3 quant and Turbo on, on the PC in [How fast is it?](#how-fast-is-it). The two
levels scored the same within chance; low took about a fifth less time. DeepSeek's best on aider's leaderboard is
V3.2-Exp at 74.2%. The setup, what failed and how to run it yourself:
[bench/aider-polyglot](bench/aider-polyglot/README.md).

More on each model's card on [Hugging Face](https://huggingface.co/peasantsmith). Each of Kestrel's own engine changes
is checked against the engine before it - the same prompts, compared token by token - before it ships.

## How fast is it?

Kestrel's own measurements. Measured 2026-11-25 (Project Maya v1.1.81's code) on one PC: a Radeon AI PRO R9700
(32 GB, over OCuLink) with a Ryzen AI MAX+ 395's Radeon 8060S as the helper GPU (128 GB of unified memory), Linux with
ROCm. Model: DeepSeek-V4.1-Flash-1017, turboderp's EXL3 quant at 2.25 bits (`--ds4-quant exl3-2.25`), 262,144-token
context, DSpark drafting on, swap off (at this context it fits in RAM, and it is faster).

| Prompt length | Prompt read (tokens/s) | Decode (tokens/s) | Without `DS4_INDEX_TC_GFX12`: read / decode |
|---:|---:|---:|---:|
| 8K | 783 | 61.2 | 824 / 61.7 |
| 16K | 1,113 | 61.8 | 1,152 / 61.8 |
| 32K | 1,431 | 48.1 | 1,365 / 59.0 |
| 64K | 1,538 | 66.2 | 1,443 / 48.2 |
| 128K | 1,505 | 37.6 | 1,412 / 53.9 |
| 192K | 1,524 | 50.1 | 1,313 / 45.8 |
| **250K** | **1,477** | **47.2** | **1,217 / 52.5** |

A 250,282-token prompt is read in under 3 minutes (170 s, against 206 s without the switch), and the answer then comes
at about 50 tokens/s.

**The indexer on the matrix cores:** `DS4_INDEX_TC_GFX12=1`, in the tuned config since 2026-11-25, runs the sparse
attention's indexer (it scores every earlier token of the context for each new one) on the R9700's matrix cores. Its
work grows with the square of the prompt's length, so it pays off on long prompts: at 250K the indexer took 30 s
instead of 66 s. From 32K up prompts are read 5-21% faster; 8K and 16K are read 3-5% slower (about 0.5 s on an 8K
prompt). It multiplies the same values as the default kernel and only adds them up in another order, so the last
bits differ and a long greedy answer can part from the default kernel's after a while, but the quality is the same
(upstream's measurement of the RDNA 3 version, on by default there: KL to the full-precision model 0.1649 against
0.1661, the same top token 91.08% against 91.07%). Leave it out of the config for the default kernel.

How: fresh prompts with a fact to recall placed 10% in (recalled at every length, with and without the switch),
256-token answers, greedy, thinking off; the second of two passes on one start; 8K and 16K are the medians of six warm
runs each. The column on the right is the same sweep earlier the same day without the switch. Decode is the same on
average (51.8 against 53.5 tokens/s from 16K up): the time per decoding round was the same, and a single answer's
speed moves by 10 tokens/s or more with how many drafts it keeps. The config was tuned by hand for this PC: a fresh `./kestrel.sh` setup chooses its own
settings, and your numbers will depend on your GPUs, RAM and SSD. **To set up the same way** - the Linux settings, the
install and the tuned config, step by step: [docs/KESTREL_LINUX_AMD.md](docs/KESTREL_LINUX_AMD.md).

The first short prompt after a long pause, or right after a very long prompt, is slower once while the caches fill
again: an 8K prompt then took 17-26 s instead of about 10 s.

Measured yours? `./kestrel.sh --bench`, then `./kestrel.sh --report`, and share both in a
[GitHub issue](https://github.com/iTechMedic/kestrel/issues).

A token is about ¾ of a word. The first answers after a start are the slowest while the caches fill with what you use.

### Inkling-2-Mini on a Radeon AI PRO R9700

Measured 2026-11-23 on the same PC, on the R9700 alone: the whole model and its FP8 cache fit in its 32 GB, so the
8060S is not used. Model: unsloth's UD-Q4_K_XL, 262,144-token context, drafting on (`--drafting auto` chose the
drafter together with the earlier text of the chat). Fresh prompts, 800-token answers, greedy, thinking off.

| Prompt length | Prompt read (tokens/s) | Decode (tokens/s) |
|---:|---:|---:|
| 2.7K | 1,138 | 101.7 |
| 9.9K | 1,126 | 86.9 |
| 37.6K | 890 | 72.3 |
| 117K | 550 | 58.5 |

Since 0.1.4 the drafter is a 0.4 GB GGUF that the setup downloads, and drafting keeps the answers the same as without
it. On this PC it is faster on short and mid-length prompts and about even on long ones. In a live coding session,
short answers came at 67-154 tokens/s and long ones at about 70. Text, thinking, tool calls and pictures were
checked. It is a far smaller model than the ones above: much faster on one card, not as strong on hard tasks.

To set it up on one GPU of a PC with several, name the card (`./kestrel.sh --check` shows the numbers):

```sh
./kestrel.sh --setup --backend hip --model inkling-2-mini --gpu 0
```

### Reading the speed numbers

The prompt speed in the log and on the dashboard's Monitor counts **only the tokens read new**. The part of a
conversation Kestrel already holds from an earlier turn is reused and not counted. That is the same rule llama.cpp
uses (its `prompt_n` leaves out `cache_n`), so the numbers compare with other engines' - but in everyday use they
can look slow while the answers come quickly:

- **Most of a conversation is reused.** Coding agents send the whole conversation every turn. In a live session on
  the PC above, a turn with a 36,315-token conversation had 124 new tokens: the answer started after 1.1 s, and the
  log showed that read as about 110 tokens/s. What you wait for is the 1.1 s.
- **Short reads are slower per token.** Each pass over a prompt has a cost that hardly depends on its length:
  every layer's experts have to reach the GPUs (most of this model does not fit in VRAM; the rest comes from RAM and
  the SSD). Spread over more tokens, it costs less a token: the table above reads 8K tokens at 783 tokens/s and 64K
  at 1,538. A tool output of a few hundred tokens takes a second or two, however low its tokens/s.
- **Cold starts are slower.** The first prompts after a start read experts from the SSD until the caches fill.
- **Kept conversations aren't read again.** With `KESTREL_DS4_SLOT_KEEP=1` (in the tuned config) a conversation
  is kept across requests and restarts, so an agent session that comes back is not read again at all.

Where it is slow for real: a large new prompt, such as a pasted document, is read at the table's rates - a
100K-token one takes about 70 s on the PC above, longer on a smaller one.

**Comparing with other engines:** compare the same model, prompt length, context and hardware. Headline numbers
are often a short prompt from an empty context with the whole model in VRAM (llama.cpp's `llama-bench` default
test is a 512-token prompt), or many requests at once added together. The table above is one request at a time,
long prompts at full depth, with most of the model read from RAM and the SSD.

## Using it

- **In the browser:** chat (kept in your browser, with search, pins and folders, per-chat instructions and thinking
  level, edit and regenerate, HTML previews), a live **Monitor** of the model and your hardware (down to what fills
  each GPU's memory), a context size and port you can change in Settings, and **Models**: every model set up on this
  machine, switching to another (Kestrel starts again with it) and each one's engine settings (context, GPUs, drafting,
  images, memory), saved into its config file.
- **Models page:** the catalog lists every model Kestrel can set up, with its size. Download one with a progress bar, load it, unload
  the running one or delete one - no command line needed.
- **Turbo:** one button beside the model's parameters sets the fastest settings for the model (greedy sampling, no
  thinking, expert skipping, the fastest drafting). It trades some quality for speed; switching it off restores your
  settings exactly.
- **Saved:** the sidebar's Saved line adds up what the model's own API (DeepSeek's, Z.ai's or MiniMax's) would have
  charged for the same tokens - the prompt Kestrel reuses from its cache at the API's cached price, DeepSeek's peak hours
  at its peak price - kept per model in `token-savings.json`; its prices can be changed in **Settings › Savings**.
- **Your apps and coding agents:** an OpenAI-compatible API at `http://127.0.0.1:8080/v1`, and Anthropic's at
  `http://127.0.0.1:8080/v1/messages` (Claude Code: `ANTHROPIC_BASE_URL=http://127.0.0.1:8080`). Tool calls are
  streamed as the model writes them, and a long prompt's reading progress too when a request asks for it
  (`"return_progress": true`). A web page served from another address can call it too once you allow its address
  (`"cors_origins"`, [docs/SETUP.md](docs/SETUP.md#web-pages-on-another-address)).
- **Responses API:** `/v1/responses` supports text/image conversations, streaming, function tool calls,
  schema-validated output, background tasks with cancellation/replay, and optional shared in-memory history
  (`store:true`, `previous_response_id`). Responses are not stored by default. Options and limits:
  [docs/RESPONSES.md](docs/RESPONSES.md).
- **Model API:** `/api/tags`, `/api/ps`, `/api/show`, `/api/chat`, `/api/generate`, `/api/pull` and `/api/delete` list,
  load, download and delete models from any app or script. A request for a model that is not loaded swaps to it, and
  `keep_alive` unloads it when idle. `/models/load`, `/models/unload` and `/models/sse` are on by default too
  (`"model_management": false` turns them off).
- **Thinking:** Off, Low, High (the default) or Max, in Settings or per request, and a **thinking budget** field that
  sets how many tokens the model may think before it answers.
- **Loop guard:** on by default - an agent that repeats the same tool call with the same result is steered off it.
- **Pictures:** attach one in the chat, or send image parts through either API. Every model reads them except
  GLM-5.3, which is text only - and Hy4-Flash on 8 GB cards (setup details per model: [docs/MODELS.md](docs/MODELS.md)). Videos too,
  for the models that read them.
- **Files:** attach any file in the chat. Text and code go in as they are; **PDFs** as their text, or a scanned one's
  first pages as pictures; Word, Excel, PowerPoint, OpenDocument, EPUB and RTF files as their text. Anything Kestrel can't
  read says why. The same works through the APIs: OpenAI `file` / `input_file` parts and Anthropic `document` blocks
  (sent inline). poppler, when installed (`sudo apt install poppler-utils`), reads PDFs a little better; it is optional.
- **MCP tools:** list MCP servers in the config (`"mcp_servers"`; Claude Desktop's `mcpServers` block works as it is)
  and the web chat's model can call their tools. A switch in the chat's **+** menu turns them on and off. What it
  does: [serve/mcp.py](serve/mcp.py).
- **From another device:** `./kestrel.sh --setup --host 0.0.0.0 --api-key <secret>`. Always set a key.
- **Tuning:** `./kestrel.sh --calibrate` tunes the engine to your hardware in 10-15 minutes. Every setting:
  [docs/SETTINGS.md](docs/SETTINGS.md).
- <a name="deepseek-engram-prompt-read-ahead"></a><a name="deepseek-conversations-kept"></a><a name="deepseek-loading-the-experts"></a>**Each model's own options** - GLM-5.3-Flash's several requests at once (`--parallel`), long contexts and DFlash2
  drafter; DeepSeek's kept conversations, expert loading and Engram read-ahead; MiniMax's thinking levels:
  [docs/MODELS.md](docs/MODELS.md).

## What you need

| | |
| --- | --- |
| **GPU** | NVIDIA, compute capability 7.0 or newer (V100, RTX 20 and newer): one, or up to 16 that share the model. More VRAM is faster. Pascal (Tesla P40 / P100, GTX 10) is experimental, not validated yet. **AMD:** RX 7900 XT / XTX, Radeon AI PRO R9700 / RX 9070, Strix Halo and Gorgon Halo (Radeon 8060S / 8065S); RX 6800 / 6900 and Radeon PRO V620 / W6800 not validated yet; GLM-5.3-Flash and DeepSeek-V4.1-Flash-1017 read pictures there too - [the AMD guide](docs/AMD_MAYA.md) |
| **RAM** | 32 GB runs it. More RAM keeps more experts close and is faster |
| **Disk** | **A fast NVMe SSD** with room for the model (~75 GB for GLM-5.3-Flash · Maya-XS, ~100 GB for GLM-5.3-Flash · Maya-S, ~160 GB for GLM-5.3-Flash · Maya-L, ~350 GB for DeepSeek V4.1 · Maya-S, ~470 GB for unsloth's Q8 GGUF of it, ~95 GB for MiniMax M3.1 · Maya-XS, ~110 GB for Hy4-Flash · Maya-XS, ~200 GB for MiniMax-M3.1-Flash's EXL3 quant, ~20 GB for Inkling-2-Mini) and its picture encoder (1.1 GB). Not a hard disk |
| **System** | Linux (x86-64; a CPU with AVX2 is best), the NVIDIA driver, CUDA 12.x (CUDA 13 works for RTX 20 and newer, not for the V100 or Pascal), g++, Python 3.10+. Windows 10/11: [docs/WINDOWS.md](docs/WINDOWS.md). Not WSL2. AMD: ROCm 7 |

The setup checks all of this, prints the exact command for anything missing, and installs nothing system-wide.

## Install

Run the two commands in [Quick start](#quick-start) and answer a few questions (Enter takes the recommended choice).
The setup shows every download before it starts it, builds everything once (20-40 minutes plus the download) and
**starts the model**. Then open `http://127.0.0.1:8080`. Ctrl+C stops it, and `./kestrel.sh` starts it again right
away.

**Which model starts:** each setup writes a config file (`maya-<model>.json`) in the Kestrel folder, and
`./kestrel.sh` starts the one used most recently. With several models installed, or a config you keep somewhere
else (a tuned copy, for example), name the one to start:

```sh
./kestrel.sh --config /path/to/your-config.json
./kestrel.sh --config /path/to/your-config.json --port 8000    # another port than the default 8080
```

`--bench` and `--report` take `--config` the same way. The dashboard's Models page switches between the installed
models too.

**A complete example config:** the reference PC's tuned DeepSeek config is in
[examples/kestrel-ds4-r9700-8060s.json](examples/kestrel-ds4-r9700-8060s.json).
[examples/README.md](examples/README.md) shows how to use it as a template for your own PC.

- **Windows:** `START-KESTREL.bat` instead of `./kestrel.sh` - see [docs/WINDOWS.md](docs/WINDOWS.md).
- **AMD:** [the AMD guide](docs/AMD_MAYA.md). Kestrel's tuned Linux setup for a Radeon card with a Radeon 8060S
  helper: [docs/KESTREL_LINUX_AMD.md](docs/KESTREL_LINUX_AMD.md).
- **Mac with Apple Silicon (experimental, GLM-5.3-Flash only):** `./kestrel.sh --backend metal` (on a Mac,
  `./kestrel.sh` picks Metal by itself) - see [docs/METAL.md](docs/METAL.md). Not tested with the real model yet: if
  you run it, please say how it went in an issue.
- **Intel Arc:** not supported by Kestrel's engine.
- **Updating:** the page's **Settings › About and updates** (Kestrel's releases), or `git pull` then `./kestrel.sh`.
  The model isn't downloaded again.
- **Model files downloaded another way** (a download manager, another PC, a Hugging Face cache):
  `./kestrel.sh --import-model FOLDER` finds the model's files in FOLDER by size and checksum, whatever they are called,
  and moves them into place (`--copy` when FOLDER is on another drive; the originals stay). Files that do not match are
  left alone.
- **Every option** (GPUs, context, a model folder you already have, remote access, ...): [docs/SETUP.md](docs/SETUP.md).

> **The start takes a few minutes:** the engine pins most of the free RAM (all but about 6 GB) for its expert tier,
> so other programs get little RAM while Kestrel runs.

## Something went wrong?

Run **`./kestrel.sh --report`** (Windows: `START-KESTREL.bat --report`) right after a slow answer or an error, and
attach the report file it writes (it prints where) to a [GitHub issue](https://github.com/iTechMedic/kestrel/issues).
It holds your hardware, your setup and the engine's speed lines; nothing is sent anywhere by itself. The engine's own
log is the `.log` file beside the model's config file in the Kestrel folder. Found a security problem? Report it
privately: [SECURITY.md](SECURITY.md).

- **The build stops** ("nvcc ... cannot build for these GPUs", "unsupported GNU version", or `cuda_profiler_api.h` /
  `nvtx3/nvToolsExt.h` missing): [docs/SETUP.md](docs/SETUP.md#if-the-build-fails) has the fix for each.
- **Slow, with the SSD busy all the time:** not enough free RAM for the experts. Close programs or add RAM.
- **Windows: answers suddenly several times slower:** the card is too full and Windows moves GPU memory to RAM. Leave
  more of it free: `START-KESTREL.bat --setup --vram-reserve-mib 2048`
  ([the expert pool's size](docs/SETTINGS.md#the-expert-pools-size)).
- **Windows on a Strix Halo / Gorgon Halo: other programs run out of memory, or the setup warns about the page
  file:** set the page file to the size the setup prints ([the AMD guide](docs/AMD_MAYA.md)).
- **The download stopped:** run `./kestrel.sh` again; it continues where it stopped.
- **Port 8080 is in use:** Kestrel is already running, or `--port 8081` starts another one. Settings > Port moves
  Kestrel to another port for good (it starts again there).

Bug reports, speed reports and pull requests are welcome.

## Credits and license

- **Project Maya:** Kestrel is a fork of [Project Maya](https://github.com/mw00/project-maya), created and led by
  Peasant Smith ([@mw00](https://github.com/mw00)), who owns that project, its name and the Maya models; Kestrel is not
  affiliated with it. Nearly all of Kestrel's engines, setup and dashboard are Project Maya's work.
  [@needmorevram](https://github.com/needmorevram) co-maintains Project Maya and contributed DFlash2 drafting, EXL3
  support, KV streaming, conversation checkpoints, the layer-split search, the expert profile, the CPU expert kernels,
  and for the DeepSeek engine the 3.5-bit EXL3 option, tensor parallel over 4 / 8 GPUs and the threaded expert-cache
  swaps. Thanks also to everyone who sent Project Maya code and speed reports
  ([contributors](https://github.com/mw00/project-maya/graphs/contributors)). To support Project Maya's work:
  [GitHub Sponsors](https://github.com/sponsors/mw00).
- **Kestrel's own changes** (its look, releases and AMD engine work) are by iTechMedic, with community changes from
  @nicholas631 and Josef Gattermayer that are not in Project Maya yet.
- **Built on [ggml / llama.cpp](https://github.com/ggml-org/llama.cpp)** (MIT License, Copyright (c) 2023-2026 The ggml
  authors): the quantization formats, the CPU dot products and the prompt path's MMQ kernels, built from a pinned
  commit (`third_party/ggml/LICENSE`).
- **EXL3 support** follows [exllamav3](https://github.com/turboderp-org/exllamav3)'s format, codebooks, CPU expert
  kernel and tensor-core decoding of a tile (MIT License, Copyright (c) 2025 Turboderp; `third_party/exllamav3/LICENSE`). **The DFlash2 drafter's
  forward** follows [beellama.cpp](https://github.com/Anbeeld/beellama.cpp)'s (MIT License, Copyright (c) 2023-2026
  The ggml authors, Anbeeld; `third_party/beellama.cpp/LICENSE`).
- The models: [GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) by zai-org (MIT); Peasant Smith's quants and the
  image encoder file are made from zai-org's released weights and keep its license.
  [GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) by zai-org (its own license); its GGUF is
  [unsloth's](https://huggingface.co/unsloth/GLM-5.3-GGUF).
  [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) by DeepSeek (MIT); Peasant Smith's
  quant, its Engram tables and the drafter are made from DeepSeek's released weights and keep its license; the vision
  tower comes from DeepSeek's checkpoint, the GGUF option from
  [unsloth's GGUFs](https://huggingface.co/unsloth/DeepSeek-V4.1-Flash-1017-GGUF), the EXL3 options are
  turboderp's ([2.25 bpw](https://huggingface.co/turboderp/DeepSeek-V4.1-Flash-1017-exl3/tree/2.25bpw)) and
  LibertAIDAI's ([2.9](https://huggingface.co/LibertAIDAI/DeepSeek-V4.1-Flash-1017-EXL3-2.9bpw) and
  [3.5 bpw](https://huggingface.co/LibertAIDAI/DeepSeek-V4.1-Flash-1017-EXL3-3.5bpw)). The optional DFlash2 drafter
  ([GLM-5.3-Flash-DFlash2-GGUF](https://huggingface.co/Anbeeld/GLM-5.3-Flash-DFlash2-GGUF) by Anbeeld) is CC BY-NC-ND
  4.0, non-commercial use only, and is downloaded only when you choose it.
- The dashboard's font: Outfit (SIL Open Font License 1.1, `serve/web/fonts/OFL.txt`); its icons:
  [Lucide](https://lucide.dev) (ISC License, `serve/web/LICENSE.lucide.txt`); its UI library:
  [Preact](https://preactjs.com) (MIT License) with [htm](https://github.com/developit/htm) (Apache License 2.0),
  bundled in `serve/web/preact.js` with their notices.
- Kestrel is open source under the [MIT License](LICENSE), like Project Maya; the notices in [LICENSE](LICENSE) and
  `third_party/` stay with every copy.
