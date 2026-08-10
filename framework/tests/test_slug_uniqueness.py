import warnings
from pathlib import Path
from utilities.slugcheck import duplicate_slugs

ROOT = Path(__file__).resolve().parent.parent.parent


def test_detects_slug_reused_across_dates(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "2026-06-19-a").mkdir()
    (exp / "2026-07-01-a").mkdir()
    (exp / "2026-06-19-b").mkdir()
    (exp / "_template").mkdir()  # non-dated dirs are ignored
    dups = duplicate_slugs(exp)
    assert set(dups) == {"a"}
    assert dups["a"] == ["2026-06-19-a", "2026-07-01-a"]


def test_unique_slugs_return_empty(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "2026-06-19-a").mkdir()
    (exp / "2026-06-20-b").mkdir()
    assert duplicate_slugs(exp) == {}


def test_repo_experiments_slugs_unique():
    # Non-failing guard: warns (does not fail) if the committed tree reuses a
    # slug across dates, surfacing accidental twins without blocking re-runs.
    dups = duplicate_slugs(ROOT / "experiments")
    if dups:
        warnings.warn(f"experiment slugs reused across dates: {dups}", stacklevel=2)
