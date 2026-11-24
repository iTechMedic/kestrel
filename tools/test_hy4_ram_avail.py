"""(Kestrel) maya-hy4's Linux RAM figure (ram_available): MemAvailable plus the GPU drivers' page pool (GPUReclaim),
capped as maya-ds4's ram_avail caps it.

Compiles the engine's own helpers with fixture-backed /proc and /sys reads. No GPU or model is required.

    python -m unittest tools.test_hy4_ram_avail
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <string>
#include <unordered_map>

std::unordered_map<std::string, std::string> files;
std::string read_file(const std::string& path) {
    const auto it = files.find(path);
    return it == files.end() ? std::string() : it->second;
}

HELPERS

constexpr uint64_t GiB = uint64_t{1} << 30;
int checks = 0;
void check(const char* name, uint64_t expected) {
    const uint64_t got = ram_available();
    if (got != expected) {
        std::fprintf(stderr, "%s: got %llu, expected %llu\n", name,
                     (unsigned long long)got, (unsigned long long)expected);
        std::exit(1);
    }
    ++checks;
}
int main() {
    files["/proc/meminfo"] = "MemTotal: 67108864 kB\nMemAvailable: 8388608 kB\n";
    check("no pool: MemAvailable", 8 * GiB);
    files["/proc/meminfo"] = "MemTotal: 67108864 kB\n";
    check("no MemAvailable: unknown (0)", 0);
    files.erase("/proc/meminfo");
    check("no meminfo: unknown (0)", 0);
    files["/proc/meminfo"] = "MemTotal: 67108864 kB\nMemAvailable: 8388608 kB\nAnonPages: 4194304 kB\n"
                             "GPUReclaim: 41943040 kB\n";
    check("GPU pool counted", 48 * GiB);
    files["/proc/meminfo"] += "GPUReclaim: 335544320 kB\n";
    check("GPU pool above the RAM: capped by what is not held", 60 * GiB);
    files["/proc/meminfo"] += "Unevictable: 8388608 kB\nHugePages_Total: 4096\nHugepagesize: 2048 kB\n";
    check("unevictable and reserved huge pages are not free", 44 * GiB);
    files["/sys/class/drm/card1/device/mem_info_gtt_used"] = std::to_string(6 * GiB) + "\n";
    files["/sys/class/drm/card2/device/mem_info_gtt_used"] = std::to_string(2 * GiB) + "\n";
    check("the cards' live GTT is not free", 36 * GiB);
    files["/sys/class/drm/card1/device/mem_info_gtt_used"] = std::to_string(60 * GiB) + "\n";
    check("more live GTT than room: nothing counted", 8 * GiB);
    files.erase("/sys/class/drm/card1/device/mem_info_gtt_used");
    files.erase("/sys/class/drm/card2/device/mem_info_gtt_used");
    // llm2 while Hy4-Flash Maya-L ran (125 GiB; the engine's 58.9 GiB of GTT live): ~9.6 GiB of the pool counted
    files["/proc/meminfo"] = "MemTotal: 131064788 kB\nMemAvailable: 56102016 kB\nAnonPages: 1420072 kB\n"
                             "Shmem: 1103016 kB\nSUnreclaim: 524288 kB\nGPUReclaim: 531573080 kB\n";
    files["/sys/class/drm/card1/device/mem_info_gtt_used"] = "63248089088\n";
    check("llm2 with the engine running", 56102016ull * 1024 +
          (131064788ull - 56102016ull - 1420072ull - 1103016ull - 524288ull) * 1024 - 63248089088ull);
    files.erase("/sys/class/drm/card1/device/mem_info_gtt_used");
    setenv("HY4_GPU_RECLAIM", "0", 1);
    check("HY4_GPU_RECLAIM=0: not counted", 56102016ull * 1024);
    unsetenv("HY4_GPU_RECLAIM");
    setenv("MAYA_HY4_GPU_RECLAIM", "0", 1);
    check("MAYA_HY4_GPU_RECLAIM=0: not counted", 56102016ull * 1024);
    unsetenv("MAYA_HY4_GPU_RECLAIM");
    std::printf("RAM availability: %d fixture checks passed\n", checks);
}
'''


@unittest.skipUnless(sys.platform != "win32" and shutil.which("c++"), "host C++ compiler required")
class Hy4RamAvailableTests(unittest.TestCase):
    def test_gpu_pool_counted_and_capped(self):
        source = (Path(__file__).resolve().parents[1] / "src/hy4/hy4_lane.cpp").read_text()
        helpers = re.findall(r"^(?:static )?uint64_t (?:gpu_pool_free|ram_available)\([^)]*\) \{.*?^\}", source,
                             re.M | re.S)
        self.assertEqual(len(helpers), 2, "expected the engine's pool and RAM helpers")
        # (the Windows branch: GlobalMemoryStatusEx, not compiled here)
        helpers = [re.sub(r"#if defined\(_WIN32\).*?#else\n", "", h, flags=re.S).replace("#endif\n", "")
                   for h in helpers]
        with tempfile.TemporaryDirectory() as d:
            cpp, exe = Path(d) / "ram_available.cpp", Path(d) / "ram_available"
            cpp.write_text(FIXTURE.replace("HELPERS", "\n".join(helpers)))
            build = subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
                                   capture_output=True, text=True, timeout=120)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("11 fixture checks passed", run.stdout)


if __name__ == "__main__":
    unittest.main()
