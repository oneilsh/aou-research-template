from pathlib import Path

import pytest

from utilities.config import (
    read_frontmatter,
    merge_config,
    load_defaults,
    effective_config,
)


def _write(p: Path, text: str) -> Path:
    p.write_text(text)
    return p


def test_read_frontmatter_ok(tmp_path):
    rec = _write(tmp_path / "r.md", "---\nid: 1\ngroup: demo\n---\n\nbody\n")
    assert read_frontmatter(rec) == {"id": 1, "group": "demo"}


def test_read_frontmatter_missing_raises(tmp_path):
    rec = _write(tmp_path / "r.md", "no frontmatter here\n")
    with pytest.raises(ValueError):
        read_frontmatter(rec)


def test_merge_precedence():
    assert merge_config({"a": 1, "b": 2}, {"b": 9}) == {"a": 1, "b": 9}


def test_load_defaults_layers(tmp_path):
    _write(tmp_path / "_base.yaml", "seed: 42\nk: 1\n")
    _write(tmp_path / "demo.yaml", "k: 7\n")
    assert load_defaults("demo", tmp_path) == {"seed": 42, "k": 7}


def test_effective_config_full_stack(tmp_path):
    _write(tmp_path / "_base.yaml", "seed: 42\nentrypoint: base\n")
    _write(tmp_path / "demo.yaml", "entrypoint: Rscript x.R\n")
    rec = _write(tmp_path / "0001-demo.md", "---\nid: 1\ngroup: demo\nseed: 7\n---\n\nbody\n")
    cfg = effective_config(rec, tmp_path)
    assert cfg["entrypoint"] == "Rscript x.R"
    assert cfg["seed"] == 7  # record frontmatter wins
