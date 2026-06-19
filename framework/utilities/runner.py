"""Run an experiment folder: merge config, dispatch its entrypoint, capture
*scrubbed* output into the experiment's own runs/summary.md.

The entrypoint can be any command in any language. The effective config is
written to <exp>/runs/config.yaml and passed as `--config <path>`; the runner
injects `out_dir` (the runs dir) so the entrypoint knows where to write.
"""
from __future__ import annotations

import datetime as _dt
import re
import shlex
from pathlib import Path

import yaml

from .config import effective_config, read_frontmatter
from .sanitize import DROP_PATTERNS, run_subprocess_tee_sanitize

_DIR_RE = re.compile(r"^(\d{4})-.+$")


def _experiments(experiments_dir: Path) -> list[Path]:
    out = [p for p in experiments_dir.iterdir() if p.is_dir() and _DIR_RE.match(p.name)]
    out.sort(key=lambda p: p.name)
    return out


def find_by_id(experiments_dir: Path, exp_id: int) -> Path:
    prefix = f"{exp_id:04d}-"
    for p in _experiments(experiments_dir):
        if p.name.startswith(prefix):
            return p
    raise FileNotFoundError(f"no experiment with id {exp_id} in {experiments_dir}")


def find_next_pending(experiments_dir: Path) -> Path | None:
    for p in _experiments(experiments_dir):
        readme = p / "README.md"
        if not readme.exists():
            continue
        try:
            fm = read_frontmatter(readme)
        except ValueError:
            continue
        if fm.get("status") == "pending":
            return p
    return None


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_experiment(exp_dir: Path, defaults_path: Path) -> int:
    cfg = effective_config(exp_dir, defaults_path)
    entrypoint = cfg.get("entrypoint")
    if not entrypoint:
        raise ValueError(f"{exp_dir}: effective config missing 'entrypoint'")

    run_dir = exp_dir / "runs"
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
