"""Layered experiment configuration.

Resolution order (lowest to highest precedence):
    experiments/defaults/_base.yaml
    experiments/defaults/<group>.yaml
    the experiment record's YAML frontmatter

The record's frontmatter names its defaults file via a required `group` key.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def read_frontmatter(path: Path) -> dict:
    """Parse the YAML frontmatter block (delimited by leading/trailing '---')."""
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter block (expected leading '---')")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter block (no trailing '---')")
    return yaml.safe_load(text[4:end]) or {}


def merge_config(base: dict, override: dict) -> dict:
    """Shallow merge; override wins."""
    out = dict(base)
    out.update(override)
    return out


def load_defaults(group: str, defaults_dir: Path) -> dict:
    """Load `_base.yaml` then `<group>.yaml` and merge."""
    base_path = defaults_dir / "_base.yaml"
    group_path = defaults_dir / f"{group}.yaml"
    if not base_path.exists():
        raise FileNotFoundError(f"missing defaults file: {base_path}")
    if not group_path.exists():
        raise FileNotFoundError(f"missing defaults file: {group_path}")
    base = yaml.safe_load(base_path.read_text()) or {}
    group_overrides = yaml.safe_load(group_path.read_text()) or {}
    return merge_config(base, group_overrides)


def effective_config(record_path: Path, defaults_dir: Path) -> dict:
    """Merge _base -> <group>.yaml -> record frontmatter into one config dict."""
    fm = read_frontmatter(record_path)
    group = fm.get("group")
    if not group:
        raise ValueError(f"{record_path}: frontmatter missing required 'group' key")
    return merge_config(load_defaults(group, defaults_dir), fm)
