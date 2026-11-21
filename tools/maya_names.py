"""tools/maya_names.py - Maya's settings are MAYA_*; the older STRATA_* names still work as fallbacks: the environment
and a config's "env" take either, the code reads MAYA_* (MAYA_X first, then STRATA_X), on disk and on screen they are MAYA_*.
Kestrel: each setting is also KESTREL_X, its name in Kestrel's docs - read as MAYA_X wherever STRATA_X is, so the
engines, which read MAYA_X, need no change.  Where a setting is under more than one name, MAYA_X counts, then KESTREL_X,
then STRATA_X - the same order in the environment and in a config, whatever order the names come in.  A config is read
under the MAYA_ names (env_in), so a save that rewrites it (the setup's) writes them as MAYA_X.

    alias_env(os.environ)    every STRATA_X that has no MAYA_X also sets MAYA_X (MAYA_X wins), so what a program reads and
                             what it starts (the engines) find the setting under the name they read
    env_in(cfg)              a config as read from disk: its "env" under the names the code reads
    env_out(cfg)             a config about to be written: its "env" under the names users see
"""
from __future__ import annotations

import os

OLD, NEW = "STRATA_", "MAYA_"
KESTREL = "KESTREL_"            # (Kestrel's name for a setting: read as MAYA_X, as OLD is - see the docstring)


def _rank(name: str) -> int:
    """Which of a setting's names counts when it is under several: the lowest (MAYA_ 0, KESTREL_ 1, STRATA_ 2)."""
    return 0 if name.startswith(NEW) else 1 if name.startswith(KESTREL) else 2 if name.startswith(OLD) else 3


def shown(name: str) -> str:
    """A setting's name as users see it."""
    for p in (OLD, KESTREL):
        if name.startswith(p):
            return NEW + name[len(p):]
    return name


def read_as(name: str) -> str:
    """A setting's name as the code reads it (MAYA_*; the older STRATA_* name is the fallback)."""
    return shown(name)


def alias_env(env) -> None:
    """In place (os.environ too): every STRATA_X or KESTREL_X that has no MAYA_X sets MAYA_X (the MAYA_ one counts when
    both are set; KESTREL_X over STRATA_X)."""
    had = {k for k in env.keys() if k.startswith(NEW)}
    for k, v in sorted(list(env.items()), key=lambda kv: -_rank(kv[0])):   # (STRATA_ first: KESTREL_ after it wins)
        if k.startswith((OLD, KESTREL)) and shown(k) not in had:
            env[shown(k)] = v


def both_names(name: str) -> tuple[str, str, str]:
    """(MAYA_X, STRATA_X, KESTREL_X) for a setting under any of its names; a name with none of the prefixes is its own
    three times."""
    m = shown(name)
    if not m.startswith(NEW):
        return m, m, m
    return m, OLD + m[len(NEW):], KESTREL + m[len(NEW):]


def lookup(env, name: str, default=None):
    """A setting from a dict/environment by either of its names (the MAYA_ one first).  A config in memory has its
    settings under the names the code reads (env_in), the shell and the dashboard under the names users see - code
    that reads a setting from either must not care which."""
    for k in both_names(name):
        v = env.get(k)
        if v is not None:
            return v
    return default


def export_env(target, env) -> None:
    """Put a config's "env" into `target` (a child's environment, os.environ) under BOTH names, so the program that
    reads a setting as getenv("MAYA_X") and the one that reads getenv("STRATA_X") each find it (issue #686: env_in
    leaves a config with the STRATA_ name only, and an engine that reads the MAYA_ name alone never saw it)."""
    for k, v in sorted((env or {}).items(), key=lambda kv: -_rank(str(kv[0]))):   # (a MAYA_ key last: it wins, then KESTREL_)
        for name in {str(k), *both_names(str(k))}:
            target[name] = str(v)


def env_in(cfg):
    """A config as read from disk -> its "env" under the names the code reads (in place; returned).  Where a config
    has a setting under several names, the MAYA_ one counts, then KESTREL_, then STRATA_."""
    e = cfg.get("env") if isinstance(cfg, dict) else None
    if isinstance(e, dict):
        out = {}
        for k, v in sorted(e.items(), key=lambda kv: -_rank(str(kv[0]))):   # (the name that counts last)
            out[shown(k)] = v
        cfg["env"] = out
    return cfg


def env_out(cfg):
    """A config about to be written -> a copy with its "env" under the names users see."""
    e = cfg.get("env") if isinstance(cfg, dict) else None
    if not isinstance(e, dict):
        return cfg
    return {**cfg, "env": {shown(k): v for k, v in e.items()}}


alias_env(os.environ)   # (importing this module is enough: an older STRATA_X in the environment also counts as MAYA_X)
