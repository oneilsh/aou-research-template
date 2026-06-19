"""Layered experiment configuration.

Resolution order (lowest to highest precedence):
    experiments/_defaults.yaml            # cross-experiment defaults
    experiments/<NNNN-slug>/config.yaml   # this experiment's config

The experiment's README.md frontmatter carries only run *metadata* (status,
created) — not config — and is read separately via read_frontmatter().
"""
from __future__ import annotations

from pathlib import Path

import yaml


def read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter block (expected leading '---')")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter block (no trailing '---')")
    return yaml.safe_load(text[4:end]) or {}


def merge_config(base: dict, override: dict) -> dict:
    out = dict(base)
    out.update(override)
    return out


def load_defaults(defaults_path: Path) -> dict:
    if not defaults_path.exists():
        raise FileNotFoundError(f"missing defaults file: {defaults_path}")
    return yaml.safe_load(defaults_path.read_text()) or {}


def effective_config(exp_dir: Path, defaults_path: Path) -> dict:
    config_path = exp_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"{exp_dir}: missing config.yaml")
    base = load_defaults(defaults_path)
    cfg = yaml.safe_load(config_path.read_text()) or {}
    return merge_config(base, cfg)
