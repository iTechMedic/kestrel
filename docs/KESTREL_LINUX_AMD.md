# Kestrel on Linux with AMD: setup and the tuned DeepSeek config

This is how Kestrel's reference PC is set up, and how to get the numbers in the
[README](../README.md#how-fast-is-it) on yours: DeepSeek-V4.1-Flash-1017 at a 262,144-token context, a 250K-token
prompt read at about 1,200 tokens/s and answered at about 51 tokens/s.

Everything here is what runs on that PC today. Some of it is specific to its hardware (an external GPU on OCuLink, a
Kingston NVMe drive): those steps say so. Change one thing at a time and measure (see [Check it](#6-check-it)).

## 1. The reference PC

| Part | What it is |
| --- | --- |
| Main GPU | AMD Radeon AI PRO R9700, 32 GB (`gfx1201`), in an OCuLink dock (PCIe 4.0 x4), stock 300 W |
| Helper GPU and CPU | AMD Ryzen AI MAX+ 395 with its Radeon 8060S (`gfx1151`), 128 GB of unified memory |
| Disk | an NVMe SSD; the model takes 353 GB (the EXL3 files, the Engram tables and the pack) |
| System | Fedora 45 Server, kernel 7.3, ROCm 10.1 |
| Model | DeepSeek-V4.1-Flash-1017, [turboderp's EXL3 quant at 2.25 bits](https://huggingface.co/turboderp/DeepSeek-V4.1-Flash-1017-exl3/tree/2.25bpw) |

The R9700 holds the attention, the shared layers and the most-used experts. The 8060S is a **helper**: about 100 GB
of the next most-used experts sit in its share of the unified memory, and it computes them there instead of copying
them over the PCIe link. The rest are read from the SSD as prompts need them.

Other AMD setups (an RX 7900 XTX, two cards, a Strix Halo alone) work with the same steps; the numbers will differ.
[The AMD guide](AMD_MAYA.md) covers every supported AMD GPU.

## 2. BIOS

- **The OCuLink / PCIe port enabled and fixed at Gen4** (only with an external GPU). Without it the port may not show
  up at all.
- **PSPP (PCIe speed power policy) disabled**, so the link does not slow down to save power.
- Resizable BAR can stay off: amdgpu resizes the card's BAR to its full 32 GB when it loads.

## 3. Linux settings

### Kernel command line

On Fedora, add them with `grubby` and reboot:

```sh
sudo grubby --update-kernel=ALL --args="amdgpu.gttsize=126976 ttm.pages_limit=32505856 ttm.page_pool_size=28835840 \
  amdgpu.lockup_timeout=300000 amdgpu.ppfeaturemask=0xfff7fffb nvme_core.apst_primary_timeout_ms=5000"
```

On Ubuntu and Debian: add them to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then `sudo update-grub` and
reboot. `cat /proc/cmdline` shows what the running kernel got.

| Setting | Why |
| --- | --- |
| `amdgpu.gttsize=126976`, `ttm.pages_limit=32505856` | the 8060S may map up to 124 GiB of system RAM, so the helper's ~100 GB expert pool fits (on a 128 GB Strix Halo) |
| `ttm.page_pool_size=28835840` | keeps up to 110 GiB of those pages pooled between runs, so the next start maps them again quickly. Side effect: after Kestrel stops, `free` shows ~100 GB as used until the kernel needs it back |
| `amdgpu.lockup_timeout=300000` | a long GPU kernel (a big prompt chunk) is not mistaken for a hang |
| `amdgpu.ppfeaturemask=0xfff7fffb` | keeps the PCIe link at full speed (no PCIe power states) and unlocks the power-limit controls |
| `nvme_core.apst_primary_timeout_ms=5000` | our Kingston NVMe sometimes drops to ~2 GB/s reads under heavy load; letting it enter its power states after 5 s idle clears that. Other drives may not need it |

**Only with an external GPU** (OCuLink or Thunderbolt), to keep the link from power-saving or dropping:

```sh
sudo grubby --update-kernel=ALL --args="amdgpu.runpm=0 amdgpu.aspm=0 pcie_port_pm=off thunderbolt.clx=0 iommu=off amd_iommu=off"
```

`iommu=off amd_iommu=off` also removes the IOMMU's DMA protection: use it only on a machine you trust. Our PC also has
`pci=realloc,resource_alignment=35@pci:<the dock bridge's vendor:device>`; it did not change any measured result, so
leave it out unless your dock needs it.

If the external GPU is sometimes missing after a boot, a second reboot brings it back; we use a small boot service
that checks `lspci` for the card and reboots once if it isn't there.

### Memory settings

```sh
echo 'vm.watermark_scale_factor = 200' | sudo tee /etc/sysctl.d/90-kestrel.conf
sudo sysctl --system
```

- `vm.watermark_scale_factor = 200`: the kernel frees memory earlier and in the background. A fresh 20K-token prompt
  went from 38.6-40 s with frequent 44-75 s outliers to a steady ~33.7 s.

**Turn swap off: at this context it is safe and faster.** Even a full 262,144-token conversation fits in RAM on the
reference PC without swap (about 10 GB stays free, see below), and every number in the README was measured with swap
off. Fedora swaps to compressed RAM (zram) by default. With it, the engine's own memory was swapped out and faulted
back in mid-answer; with it off, a day of live coding decoded about 7 tokens/s faster at the same context, and the slow
answers mostly went away. Turn it off for good on Fedora (an empty file overrides the default; delete it to undo),
then reboot:

```sh
sudo touch /etc/systemd/zram-generator.conf
```

`swapon --show` then prints nothing. On other distributions, turn off whatever swap is set up (`swapoff`, and its line
in `/etc/fstab`). Without swap, `vm.swappiness` makes no difference; a lower one (10, or 1) with swap on did not help.

Why it fits: the engine's own memory grows about 13 KB a token of context (about 4 GB at a full 262K conversation),
which on the reference PC (128 GB, the helper's 100 GB pool included) still leaves about 10 GB free. On a PC with less
RAM to spare, or with other big programs running beside Kestrel, keep swap on and expect the slower answers.

### GPU order and power

- **The R9700 must be HIP device 0 and the 8060S device 1** (`rocminfo | grep -E "Marketing Name|gfx"` lists them in
  that order). If yours are the other way round, start Kestrel with `HIP_VISIBLE_DEVICES=1,0`.
- **Power:** the R9700 at its stock 300 W limit, power profile `auto`. The `profile_peak` profile
  (`power_dpm_force_performance_level`) was slower here: a 20K-token prompt took ~3 s longer. Higher power limits were
  not tested.

## 4. Install Kestrel and the model

Install ROCm first ([the AMD guide](AMD_MAYA.md) lists the packages per distribution), then:

```sh
git clone https://github.com/iTechMedic/kestrel.git && cd kestrel
./kestrel.sh --setup --backend hip --model DeepSeek-V4.1-Flash-1017 --ds4-quant exl3-2.25 --gpus 0,1 --context 262144
```

The setup checks the PC, builds the engines for both GPUs (`gfx1201` and `gfx1151`), shows the download (about
160 GB of EXL3 files plus DeepSeek's Engram tables) and asks before it starts, builds the model's pack and writes the
config file it then starts from (its path is printed at the end).

## 5. The tuned config

Stop Kestrel (Ctrl+C), open the config file the setup wrote and set its `"args"` and `"env"` to these. Paths in
`<...>` are yours; keep the rest of the file as the setup wrote it.

The settings are written here under Kestrel's names (`KESTREL_...`). The setup and the dashboard write the same
settings under the engine's own prefix (`MAYA_`, from upstream); either prefix works. Replace the setup's `"env"`
with this one rather than adding to it: where a file has a setting under both prefixes, the `MAYA_` one counts. When
the setup or the dashboard later saves the file, it writes these settings back under `MAYA_`; they mean the same.

```json
"args": ["--pack", "<the pack folder, as the setup wrote it>", "--max-context", "262144", "--tp", "1",
         "--threads", "on", "--mmap-experts", "on", "--reserve-mib", "1024", "--prefill-chunk", "32768",
         "--vision", "on", "--dspark", "on", "--ssd-cache", "auto", "--dspark-conf", "0.4"],
"gpu": [0, 1],
"env": {
  "KESTREL_DS4_HELPER": "1", "KESTREL_DS4_HELPER_GB": "100", "KESTREL_DS4_HELPER_EXL3": "1",
  "KESTREL_DS4_FLOW_HELPER": "1", "KESTREL_DS4_WARM_CAP_GB": "14", "KESTREL_DS4_DSPARK_CUM": "0.2",
  "KESTREL_DS4_PROMPT_PICK": "length:1024", "KESTREL_DS4_ROUTE_FUSE": "2", "KESTREL_DS4_DECODE_TRIM": "12",
  "KESTREL_DS4_LANE_SPIN_US": "200", "KESTREL_DS4_RESIDENT_TOPK": "3", "KESTREL_DS4_AHEAD_EXL3": "1",
  "EXL3_WMMA": "1", "EXL3_WMMA_GFX12": "1",
  "DS4_RING_MB": "auto", "DS4_STREAM_PRIO": "0", "KESTREL_DS4_SLOT_KEEP": "1",
  "DS4_ENGRAM_PREFETCH": "1", "DS4_ENGRAM_CACHE_MB": "4096",
  "KESTREL_DS4_SPEC_STAGED": "1", "KESTREL_DS4_SPEC_STAGED_MIN": "4096",
  "DS4_PROMPT_LIGHT": "64", "DS4_PROMPT_LIGHT_FILES": "64", "DS4_FILE_HOT_GB": "16", "DS4_X3_FAT_ROWS": "256"
}
```

> **One of these changes the answers:** `KESTREL_DS4_RESIDENT_TOPK=3` computes only the 3 heaviest of each decoded
> token's 6 routed experts. It makes decoding faster and the answers slightly different from the full model (like the
> dashboard's Turbo button does). Leave it out for the model's exact answers. Everything else here gives the same
> answers as without it.

What each one does (more in [SETTINGS.md](SETTINGS.md)):

| Setting | What it does |
| --- | --- |
| `KESTREL_DS4_HELPER=1`, `KESTREL_DS4_HELPER_GB=100` | visible GPU 1 (the 8060S) is the helper, with a 100 GB pool of the most-routed experts |
| `KESTREL_DS4_HELPER_EXL3=1` | the helper keeps and computes EXL3 experts itself |
| `KESTREL_DS4_FLOW_HELPER=1` | in a prompt, an expert the helper holds is copied from its pool instead of read from the SSD |
| `KESTREL_DS4_WARM_CAP_GB=14` | 14 GB of experts in host RAM beside the helper's pool |
| `--dspark on`, `--dspark-conf 0.4`, `KESTREL_DS4_DSPARK_CUM=0.2` | DSpark drafting: up to 5 drafted tokens a round (the drafter's own limit), each kept above 0.4 confidence, verified while their combined chance stays above 0.2 (the same tokens as without drafting) |
| `KESTREL_DS4_PROMPT_PICK=length:1024` | prompts of 1,024 tokens or more take the chunked prompt path, shorter ones (most tool outputs) the decode-window path. At 512 the chunked path took ~1K-token tool outputs ~25% faster when their experts were in the page cache, but up to 2x slower when they came from the SSD, and it read ~12 GB from the SSD each time |
| `KESTREL_DS4_ROUTE_FUSE=2`, `KESTREL_DS4_DECODE_TRIM=12` | fewer, fused kernel launches per decoded token (the same results, checked at load) |
| `KESTREL_DS4_LANE_SPIN_US=200` | the CPU lane's threads sleep sooner when idle, leaving the APU more of its shared power for the 8060S |
| `KESTREL_DS4_AHEAD_EXL3=1` | while decoding, the next layer's likely experts are read ahead from the files |
| `EXL3_WMMA=1`, `EXL3_WMMA_GFX12=1` | matrix-core prompt kernels for EXL3, including on RDNA 4 (the R9700) |
| `KESTREL_DS4_SLOT_KEEP=1` | conversations are kept across requests and restarts, so a returning agent session isn't read again |
| `DS4_ENGRAM_PREFETCH=1`, `DS4_ENGRAM_CACHE_MB=4096` | a prompt's Engram rows are read ahead, with a 4 GB cache of them |
| `KESTREL_DS4_SPEC_STAGED=1`, `KESTREL_DS4_SPEC_STAGED_MIN=4096` | in prompt chunks of 4,096 rows or more, a layer's first experts are copied while its attention still runs |
| `DS4_PROMPT_LIGHT=64`, `DS4_PROMPT_LIGHT_FILES=64` | a prompt chunk's lightly used experts (under 64 rows) are computed on the helper instead of copied to the R9700, including ones read from the files |
| `DS4_FILE_HOT_GB=16` | the 16 GB of file experts prompts use most are read through the page cache (and read ahead after loading), the rest unbuffered |
| `DS4_X3_FAT_ROWS=256` | a prompt chunk's busiest experts (256 rows or more) are decoded once to FP16 and multiplied with the GPU library's matrix routines |
| `DS4_RING_MB=auto`, `DS4_STREAM_PRIO=0` | the copy ring sized from the measured link; copies at the default stream priority |
| `--mmap-experts on`, `--ssd-cache auto`, `--reserve-mib 1024`, `--prefill-chunk 32768` | experts read from the files in place, a RAM store of whole experts sized to the free RAM, 1 GB of VRAM kept free, prompts read in chunks of up to 32K tokens |

Then start it again with `./kestrel.sh`. It starts the config used most recently in the Kestrel folder, so with
other models installed too, name this one: `./kestrel.sh --config <the config file>`.

You can also keep the tuned config outside the Kestrel folder, as the reference PC does: copy it anywhere (for
example `~/kestrel-configs/kestrel-ds4.json`) and always start it by name:

```sh
cd ~/kestrel && ./kestrel.sh --config ~/kestrel-configs/kestrel-ds4.json
```

A setup run again then leaves your copy alone. A config can carry its own port and address (`"port": 8000`,
`"host": "0.0.0.0"` with an `"api_key"`), or give them on the command line (`--port`, `--host`, `--api-key`).

## 6. Check it

- **A quick test:** `./kestrel.sh --bench` (a few short prompts; decode and prompt speed). Add
  `--config <the config file>` to test a config kept elsewhere, here and with `--report`.
- **Long prompts:** the first prompt after a start is the slowest while the caches fill; time the second one. Watch
  the dashboard's Monitor for where experts are read from (VRAM, helper, RAM, SSD) and for SSD reads that don't stop.
- **If something is slow or fails:** `./kestrel.sh --report` writes a report of the PC, the config and the engine's
  speed lines and prints where it put it; attach that file to a [GitHub issue](https://github.com/iTechMedic/kestrel/issues).
