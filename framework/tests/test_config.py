from pathlib import Path
import pytest
from utilities.config import read_frontmatter, merge_config, load_defaults, effective_config


def _write(p: Path, text: str) -> Path:
    p.write_text(text); return p


def test_read_frontmatter_ok(tmp_path):
    rec = _write(tmp_path / "README.md", "---\nstatus: pending\n---\n\nbody\n")
    assert read_frontmatter(rec) == {"status": "pending"}


def test_read_frontmatter_missing_raises(tmp_path):
    rec = _write(tmp_path / "README.md", "no frontmatter\n")
    with pytest.raises(ValueError):
        read_frontmatter(rec)


def test_merge_precedence():
    assert merge_config({"a": 1, "b": 2}, {"b": 9}) == {"a": 1, "b": 9}


def test_load_defaults(tmp_path):
    d = _write(tmp_path / "_defaults.yaml", "seed: 42\nk: 1\n")
    assert load_defaults(d) == {"seed": 42, "k": 1}


def test_effective_config_merges(tmp_path):
    d = _write(tmp_path / "_defaults.yaml", "seed: 42\nentrypoint: base\n")
    exp = tmp_path / "0001-demo"; exp.mkdir()
    _write(exp / "config.yaml", "entrypoint: Rscript x.R\nseed: 7\n")
    cfg = effective_config(exp, d)
    assert cfg["entrypoint"] == "Rscript x.R"
    assert cfg["seed"] == 7  # experiment config wins
