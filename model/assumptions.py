"""Load and validate assumptions.yaml — the single source of truth for every parameter.

Independent analysis using public information and synthetic data.
Not affiliated with or endorsed by Varaha.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "assumptions.yaml"

VALID_STATUS = {"PUBLIC", "LITERATURE", "ASSUMPTION – VERIFY"}
REQUIRED_FIELDS = ("name", "group", "default", "low", "high", "unit", "source", "status")
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


@dataclass(frozen=True)
class Param:
    name: str
    group: str
    default: float
    low: float
    high: float
    unit: str
    source: str
    status: str
    note: str = ""
    lever: bool = False


@lru_cache(maxsize=4)
def load_raw(path: str | None = None) -> dict[str, Any]:
    with open(path or YAML_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_params(path: str | None = None) -> dict[str, Param]:
    """Return {name: Param}; raises ValueError on any schema violation."""
    raw = load_raw(path)
    out: dict[str, Param] = {}
    for entry in raw["parameters"]:
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        if missing:
            raise ValueError(f"{entry.get('name', '?')}: missing fields {missing}")
        if entry["status"] not in VALID_STATUS:
            raise ValueError(f"{entry['name']}: invalid status {entry['status']!r}")
        lo, d, hi = float(entry["low"]), float(entry["default"]), float(entry["high"])
        if not (lo <= d <= hi):
            raise ValueError(f"{entry['name']}: require low <= default <= high, got {lo}, {d}, {hi}")
        if entry["name"] in out:
            raise ValueError(f"duplicate parameter {entry['name']}")
        out[entry["name"]] = Param(
            name=entry["name"], group=entry["group"], default=d, low=lo, high=hi,
            unit=str(entry["unit"]), source=str(entry["source"]), status=entry["status"],
            note=str(entry.get("note", "")), lever=bool(entry.get("lever", False)),
        )
    return out


def meta(path: str | None = None) -> dict[str, Any]:
    return dict(load_raw(path)["meta"])


def defaults(path: str | None = None) -> dict[str, float]:
    """Flat {name: default} dict — the standard parameter set passed to every model function."""
    return {k: p.default for k, p in load_params(path).items()}


def bounds(path: str | None = None) -> dict[str, tuple[float, float]]:
    return {k: (p.low, p.high) for k, p in load_params(path).items()}


def with_overrides(base: dict[str, float] | None = None, **overrides: float) -> dict[str, float]:
    """Copy of `base` (defaults if None) with overrides; unknown keys are rejected."""
    params = dict(base or defaults())
    for k, v in overrides.items():
        if k not in params:
            raise KeyError(f"unknown parameter {k}")
        params[k] = float(v)
    return params


def monthly_op_days(p: dict[str, float]) -> list[float]:
    return [p[f"op_days_{m}"] for m in MONTHS]


# --------------------------------------------------------------------------- scenarios
def scenarios(path: str | None = None) -> dict[str, dict]:
    return dict(load_raw(path).get("scenarios", {}))


def scenario_params(name: str = "literature", path: str | None = None) -> dict[str, float]:
    """Defaults with the scenario's overrides applied (base scenarios first)."""
    sc = scenarios(path)
    if name not in sc:
        raise KeyError(f"unknown scenario {name}")
    spec = sc[name]
    params = scenario_params(spec["base"], path) if spec.get("base") else defaults(path)
    return with_overrides(params, **(spec.get("overrides") or {}))


def scenario_mc_ranges(name: str, path: str | None = None) -> dict[str, tuple[float, float, float]]:
    """[low, mode, high] Monte Carlo overrides for a scenario, inherited along the base chain."""
    sc = scenarios(path)
    spec = sc[name]
    out = scenario_mc_ranges(spec["base"], path) if spec.get("base") else {}
    for k in (spec.get("overrides") or {}):
        out.pop(k, None)  # a child's own override re-centres that parameter on yaml bounds
    for k, v in (spec.get("mc_ranges") or {}).items():
        out[k] = tuple(float(x) for x in v)
    return out
