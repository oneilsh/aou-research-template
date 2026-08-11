from pathlib import Path
import pytest
from utilities.cli.new import scaffold


def _tmpl(tmp_path):
    t = tmp_path / "_template"; t.mkdir()
    (t / "README.md").write_text(
        "---\nstatus: pending\ncreated: {date}\n---\n\n# Experiment {date} — {slug}\n")
    (t / "config.yaml").write_text(
        "entrypoint: Rscript experiments/{date}-{slug}/analysis.R\n")
    return t


def test_scaffold_writes_date_slug_folder(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    out = scaffold("my-run", exp, _tmpl(tmp_path), today="2026-06-19")
    assert out.name == "2026-06-19-my-run"
    readme = (out / "README.md").read_text()
    assert "Experiment 2026-06-19 — my-run" in readme
    assert "created: 2026-06-19" in readme
    cfg = (out / "config.yaml").read_text()
    assert "experiments/2026-06-19-my-run/analysis.R" in cfg


def test_scaffold_refuses_existing(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    tmpl = _tmpl(tmp_path)
    scaffold("dup", exp, tmpl, today="2026-06-19")
    with pytest.raises(FileExistsError):
        scaffold("dup", exp, tmpl, today="2026-06-19")
