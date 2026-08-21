from pathlib import Path
import pytest
from utilities.cli.newdoc import scaffold_doc


def _tmpl(tmp_path):
    t = tmp_path / "entry.md"
    t.write_text("# {date} — {slug}\n\n**Date:** {date}\n")
    return t


def test_scaffold_doc_writes_dated_file(tmp_path):
    docs = tmp_path / "docs"
    (docs / "decisions").mkdir(parents=True)
    out = scaffold_doc("decisions", "use-duckdb", docs, _tmpl(tmp_path), today="2026-08-11")
    assert out.name == "2026-08-11-use-duckdb.md"
    body = out.read_text()
    assert "# 2026-08-11 — use-duckdb" in body
    assert "**Date:** 2026-08-11" in body


def test_scaffold_doc_refuses_when_not_enabled(tmp_path):
    docs = tmp_path / "docs"; docs.mkdir()  # no decisions/ subdir
    with pytest.raises(FileNotFoundError):
        scaffold_doc("decisions", "x", docs, _tmpl(tmp_path), today="2026-08-11")


def test_scaffold_doc_refuses_existing(tmp_path):
    docs = tmp_path / "docs"
    (docs / "insights").mkdir(parents=True)
    tmpl = _tmpl(tmp_path)
    scaffold_doc("insights", "dup", docs, tmpl, today="2026-08-11")
    with pytest.raises(FileExistsError):
        scaffold_doc("insights", "dup", docs, tmpl, today="2026-08-11")
