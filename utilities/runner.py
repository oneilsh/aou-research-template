"""Run an experiment record: merge config, dispatch its declared entrypoint,
and capture *scrubbed* output into an accumulating per-run summary.md.

The entrypoint can be any command in any language. The effective config is
written to <run_dir>/config.yaml and passed to the entrypoint as
`--config <path>`; the runner injects `out_dir` (the run dir) into the config so
the entrypoint knows where to write artifacts.
"""
from __future__ import annotations

import datetime as _dt
import re
import shlex
from pathlib import Path

import yaml

from .config import effective_config
from .sanitize import DROP_PATTERNS, run_subprocess_tee_sanitize

_RECORD_RE = re.compile(r"^(\d{4})-.+\.md$")


def _records(experiments_dir: Path) -> list[Path]:
    out = [p for p in experiments_dir.iterdir() if _RECORD_RE.match(p.name)]
    out.sort(key=lambda p: p.name)
    return out


def find_by_id(experiments_dir: Path, exp_id: int) -> Path:
    """Return the record whose filename starts with the zero-padded id."""
    prefix = f"{exp_id:04d}-"
    for p in _records(experiments_dir):
        if p.name.startswith(prefix):
            return p
    raise FileNotFoundError(f"no experiment record with id {exp_id} in {experiments_dir}")


def find_next_pending(experiments_dir: Path) -> Path | None:
    """Return the lowest-id record with `status: pending`, or None."""
    from .config import read_frontmatter
    for p in _records(experiments_dir):
        try:
            fm = read_frontmatter(p)
        except ValueError:
            continue
        if fm.get("status") == "pending":
            return p
    return None


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_experiment(record_path: Path, defaults_dir: Path, runs_dir: Path) -> int:
    """Dispatch one experiment; return the entrypoint's exit code."""
    cfg = effective_config(record_path, defaults_dir)
    entrypoint = cfg.get("entrypoint")
    if not entrypoint:
        raise ValueError(f"{record_path}: effective config missing 'entrypoint'")

    slug = record_path.stem
    run_dir = runs_dir / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg["out_dir"] = str(run_dir)

    config_path = run_dir / "config.yaml"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=True))

    summary_path = run_dir / "summary.md"
    with summary_path.open("a") as f:
        f.write(f"\n## Run session — {_utc_now()}\n")
        f.write(f"entrypoint: {entrypoint}\n\n")

    cmd = shlex.split(entrypoint) + ["--config", str(config_path)]
    rc = run_subprocess_tee_sanitize(cmd, summary_path, DROP_PATTERNS)

    with summary_path.open("a") as f:
        f.write(f"\n### Session complete (exit {rc})\n")
    return rc
