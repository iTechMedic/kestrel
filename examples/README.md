# Example configs

## kestrel-ds4-r9700-8060s.json

This is the tuned config of Kestrel's reference PC:
- **GPUs:** a Radeon AI PRO R9700 and the Radeon 8060S of a Ryzen AI Max+ 395.
- **Model:** DeepSeek-V4.1-Flash in EXL3 at 2.25 bits.
- **Context:** 262,144 tokens.

[docs/KESTREL_LINUX_AMD.md](../docs/KESTREL_LINUX_AMD.md) explains each setting, and the README has its speeds. It
gives the same results as the reference PC's own config. Only its paths differ, and it serves this PC alone until you
change `"host"`.

### Use it as a template

1. **Run the setup first.** It builds the engine, downloads the model and makes the model's pack. This file can't do
   any of that:

   ```sh
   cd ~/kestrel
   ./kestrel.sh --setup --backend hip --model DeepSeek-V4.1-Flash-1017 --ds4-quant exl3-2.25 --gpus 0,1 --context 262144
   ```

   At the end it prints the path of the config it wrote (`maya-<model>.json` in the Kestrel folder). Stop Kestrel
   (Ctrl+C) once it has started.

2. **Copy the example outside the Kestrel folder**, so a later setup or update doesn't touch it:

   ```sh
   mkdir -p ~/kestrel-configs
   cp ~/kestrel/examples/kestrel-ds4-r9700-8060s.json ~/kestrel-configs/kestrel-ds4.json
   ```

3. **Fill in your paths.** Open the setup's config next to your copy, and copy these values from the setup's file
   into yours:

   | Field | What it is |
   |---|---|
   | `"exe"` | the DeepSeek engine (`.../build-hip/maya-ds4`) |
   | the value after `"--pack"` in `"args"` | the model's pack folder |
   | `"tokenizer"` | the pack's `tokenizer` folder |
   | `"cwd"` | the Kestrel folder |
   | `"lib_dirs"` | ROCm's libraries |
   | `"installer"` → `"model_dir"` | the model's folder |

   `"log"` can be any file you like. If you installed into `~/kestrel` and kept the setup's default models folder,
   replacing `YOU` with your user name everywhere is enough. Still take `"lib_dirs"` from the setup's file. The
   example has `/opt/rocm/lib`, but ROCm can also be in `/opt/rocm-<version>/lib`, or under `/usr` from your
   distribution's packages.

4. **Match your GPUs.** `"gpu": [0, 1]` means GPU 0 runs the model's layers and GPU 1 is the helper with the 100 GB
   expert pool. Check the numbers with `rocm-smi`. If your helper GPU has less memory to share, lower
   `KESTREL_DS4_HELPER_GB`. If your PC has less RAM than the reference PC's 128 GB, lower `KESTREL_DS4_WARM_CAP_GB`.

5. **Choose who can connect.** As shipped, only this PC can reach Kestrel (`"host": "127.0.0.1"`). To serve other
   machines on your network:
   - set `"host": "0.0.0.0"`;
   - set `"api_key"` to a long random string, for example from `openssl rand -hex 24`. Clients send it as their API
     key, and the web page asks for it.

   Without a key, anyone on your network can use the model.

6. **Start it by name:**

   ```sh
   cd ~/kestrel && ./kestrel.sh --config ~/kestrel-configs/kestrel-ds4.json
   ```

   Kestrel serves on port 8000 (`"port"`). Check the speed with
   `./kestrel.sh --bench --config ~/kestrel-configs/kestrel-ds4.json`. The first prompt after a start is the slowest
   while the caches fill.

### Exact answers

`KESTREL_DS4_RESIDENT_TOPK=3` computes only the 3 heaviest of each decoded token's 6 experts. Decoding is faster and
the answers differ slightly from the full model's. Remove that line for the model's exact answers. No other setting
changes the answers.

### When you save from the dashboard

When the dashboard or a setup saves this file, it writes the settings back under the engine's own `MAYA_` prefix. They
mean the same thing (see [tools/maya_names.py](../tools/maya_names.py)). The file must stay plain JSON, without
comments.
