from pathlib import Path

from scripts.new_experiment import scaffold, next_id


def _tmpl(tmp_path):
    t = tmp_path / "_template.md"
    t.write_text("---\nid: {id}\nslug: {slug}\ngroup: demo\nstatus: pending\n"
                 "created: {date}\n---\n\n# Experiment {id_padded} — {slug}\n")
    return t


def test_next_id_increments(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-a.md").write_text("x")
    (exp / "0002-b.md").write_text("x")
    assert next_id(exp) == 3


def test_next_id_empty_is_one(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    assert next_id(exp) == 1


def test_scaffold_writes_record(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "0001-demo.md").write_text("x")
    out = scaffold("my-run", exp, _tmpl(tmp_path), today="2026-06-19")
    assert out.name == "0002-my-run.md"
    text = out.read_text()
    assert "id: 2" in text and "slug: my-run" in text
    assert "created: 2026-06-19" in text
    assert "Experiment 0002 — my-run" in text
