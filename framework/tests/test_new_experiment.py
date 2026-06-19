from pathlib import Path
from utilities.cli.new import scaffold, next_id


def _tmpl(tmp_path):
    t = tmp_path / "_template"; t.mkdir()
    (t / "README.md").write_text("---\nstatus: pending\ncreated: {date}\n---\n\n# Experiment {id_padded} — {slug}\n")
    (t / "config.yaml").write_text("entrypoint: Rscript experiments/{id_padded}-{slug}/analysis.R\n")
    return t


def test_next_id_increments(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-a").mkdir(); (exp / "0002-b").mkdir()
    assert next_id(exp) == 3


def test_next_id_empty_is_one(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    assert next_id(exp) == 1


def test_scaffold_writes_folder(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-demo").mkdir()
    out = scaffold("my-run", exp, _tmpl(tmp_path), today="2026-06-19")
    assert out.name == "0002-my-run"
    readme = (out / "README.md").read_text()
    assert "Experiment 0002 — my-run" in readme and "created: 2026-06-19" in readme
    cfg = (out / "config.yaml").read_text()
    assert "experiments/0002-my-run/analysis.R" in cfg
