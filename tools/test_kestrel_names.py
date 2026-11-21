"""tools/test_kestrel_names.py - Kestrel's names for the settings: KESTREL_X works wherever MAYA_X does (maya_names), and
every KESTREL_ name Kestrel's own docs give is a setting the code really reads.

    python -m unittest tools.test_kestrel_names -v
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
import maya  # noqa: E402
import maya_names as N  # noqa: E402

DOCS = (ROOT / "README.md", ROOT / "docs" / "KESTREL_LINUX_AMD.md")


def docs_kestrel_names() -> list:
    found = {n for p in DOCS for n in re.findall(r"\bKESTREL_[A-Z0-9_]*[A-Z0-9]\b(?!\.md)", p.read_text(encoding="utf-8"))}
    return sorted(found - {"KESTREL_VERSION"})               # (a file: Kestrel's release, not a setting)


def guide_env() -> dict:
    """The env block of the tuned config in docs/KESTREL_LINUX_AMD.md, as a dict."""
    text = (ROOT / "docs" / "KESTREL_LINUX_AMD.md").read_text(encoding="utf-8")
    return dict(re.findall(r'"((?:KESTREL|DS4|EXL3|HSA|HIP|GPU)_[A-Z0-9_]+)":\s*"([^"]*)"', text))


class KestrelNames(unittest.TestCase):
    def test_environment(self):
        env = {"KESTREL_DS4_HELPER": "1", "KESTREL_DS4_SLOT_KEEP": "1", "MAYA_DS4_SLOT_KEEP": "0", "PATH": "/bin"}
        N.alias_env(env)
        self.assertEqual(env["MAYA_DS4_HELPER"], "1")          # Kestrel's name alone counts as the name the code reads
        self.assertEqual(env["MAYA_DS4_SLOT_KEEP"], "0")       # both set: the MAYA_ one counts, as with STRATA_
        self.assertEqual(env["PATH"], "/bin")

    def test_names(self):
        self.assertEqual(N.shown("KESTREL_DS4_PROMPT_PICK"), "MAYA_DS4_PROMPT_PICK")
        self.assertEqual(N.read_as("KESTREL_DS4_PROMPT_PICK"), "MAYA_DS4_PROMPT_PICK")
        self.assertEqual(N.shown("DS4_RING_MB"), "DS4_RING_MB")
        self.assertFalse("KESTREL_DS4_HELPER".startswith(N.OLD))   # (a config in Kestrel's names is not rewritten as old)

    def test_lookup_finds_either_name(self):
        self.assertEqual(N.lookup({"KESTREL_PAR_MAX": "4"}, "MAYA_PAR_MAX"), "4")
        self.assertEqual(N.lookup({"MAYA_PAR_MAX": "4"}, "KESTREL_PAR_MAX"), "4")
        self.assertEqual(N.lookup({"MAYA_PAR_MAX": "4", "KESTREL_PAR_MAX": "2"}, "KESTREL_PAR_MAX"), "4")
        self.assertIsNone(N.lookup({"KESTREL_PAR_MAX": "4"}, "PATH"))

    def test_config_env_in(self):
        cfg = N.env_in({"env": {"KESTREL_DS4_HELPER_GB": "100", "KESTREL_DS4_DECODE_TRIM": "12",
                                "MAYA_DS4_DECODE_TRIM": "8", "DS4_RING_MB": "auto"}})
        self.assertEqual(cfg["env"], {"MAYA_DS4_HELPER_GB": "100", "MAYA_DS4_DECODE_TRIM": "8", "DS4_RING_MB": "auto"})

    def test_env_on_the_command_line(self):
        self.assertEqual(maya.parse_env(["KESTREL_DS4_WARM_CAP_GB=14"]), {"MAYA_DS4_WARM_CAP_GB": "14"})

    def test_export_env_of_a_raw_config(self):
        out = {}
        N.export_env(out, {"KESTREL_DS4_ROUTE_FUSE": "2"})
        self.assertEqual(out["MAYA_DS4_ROUTE_FUSE"], "2")
        self.assertEqual(out["STRATA_DS4_ROUTE_FUSE"], "2")

    def test_the_guides_config_reaches_the_engine(self):
        """The Linux guide's env block in a config on disk, as the setup reads it and the server starts the engine:
        each KESTREL_ setting arrives as the MAYA_ name the engine's getenv reads, the others as they are."""
        from serve.server import child_env
        env = guide_env()
        self.assertGreater(len([k for k in env if k.startswith("KESTREL_")]), 10)
        self.assertNotIn("MAYA_", json.dumps(env))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "kestrel-ds4.json"
            p.write_text(json.dumps({"exe": sys.executable, "backend": "hip", "gpu": [0], "env": env}))
            cfg = maya.read_json(p)
            child = child_env(cfg)
            for k, v in env.items():
                self.assertEqual(child.get(N.shown(k)), v, k)
            out = subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('MAYA_DS4_PROMPT_PICK'))"],
                                 env=child, capture_output=True, text=True, timeout=60).stdout.strip()
        self.assertEqual(out, env["KESTREL_DS4_PROMPT_PICK"])


class DocsNameRealSettings(unittest.TestCase):
    def test_every_kestrel_name_in_the_docs_is_read_by_the_code(self):
        """A KESTREL_ name in README.md or docs/KESTREL_LINUX_AMD.md must be a MAYA_ setting some source reads (a typo,
        or a setting upstream removed, fails here)."""
        names = docs_kestrel_names()
        self.assertIn("KESTREL_DS4_PROMPT_PICK", names)
        src = []
        for top in ("src", "include", "serve", "tools"):
            src += [f for f in (ROOT / top).rglob("*") if f.suffix in (".cpp", ".cu", ".cuh", ".h", ".hpp", ".mm", ".py")]
        src.append(ROOT / "maya.py")
        text = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in src)
        for n in names:
            m = N.shown(n)                  # (the DeepSeek engine's ds4_env("DS4_X") reads MAYA_DS4_X, then DS4_X)
            read = '"' + m + '"' in text or re.search(r'ds4_env\(\s*"' + re.escape(m[len(N.NEW):]) + '"', text)
            self.assertTrue(read, f"{n}: no source reads {m}")


if __name__ == "__main__":
    unittest.main()
