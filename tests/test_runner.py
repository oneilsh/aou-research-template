from pathlib import Path

from utilities.runner import find_by_id, find_next_pending, run_experiment


def _setup(tmp_path):
    exp = tmp_path / "experiments"
    exp.mkdir()
    defaults = tmp_path / "defaults"
    defaults.mkdir()
    (defaults / "_base.yaml").write_text("seed: 1\n")
    (defaults / "demo.yaml").write_text("entrypoint: STUB\n")
    return exp, defaults


def test_find_by_id_and_next(tmp_path):
    exp, _ = _setup(tmp_path)
    (exp / "0001-a.md").write_text("---\nid: 1\ngroup: demo\nstatus: done\n---\n")
    (exp / "0002-b.md").write_text("---\nid: 2\ngroup: demo\nstatus: pending\n---\n")
    assert find_by_id(exp, 1).name == "0001-a.md"
    assert find_next_pending(exp).name == "0002-b.md"


def test_run_experiment_scrubs_and_records(tmp_path):
    exp, defaults = _setup(tmp_path)
    # A stub entrypoint that prints one row-level line and one aggregate line,
    # and proves it received --config.
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import sys\n"
        "assert '--config' in sys.argv\n"
        "print('person_id = 7')\n"
        "print('[demo] mean = 3.14')\n"
    )
    import sys as _sys
    (defaults / "demo.yaml").write_text(f"entrypoint: {_sys.executable} {stub}\n")
    rec = exp / "0001-demo.md"
    rec.write_text("---\nid: 1\ngroup: demo\nstatus: pending\n---\n")
    runs = tmp_path / "runs"
    rc = run_experiment(rec, defaults, runs)
    assert rc == 0
    summary = (runs / "0001-demo" / "summary.md").read_text()
    assert "mean = 3.14" in summary
    assert "person_id" not in summary
    assert "Session complete (exit 0)" in summary
    assert (runs / "0001-demo" / "config.yaml").exists()
