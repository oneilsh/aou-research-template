import sys
from pathlib import Path
from utilities.runner import find_by_id, find_next_pending, run_experiment


def _mk(exp_root, name, status):
    d = exp_root / name; d.mkdir()
    (d / "README.md").write_text(f"---\nstatus: {status}\n---\n")
    return d


def test_find_by_id_and_next(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    _mk(exp, "0001-a", "done"); _mk(exp, "0002-b", "pending")
    assert find_by_id(exp, 1).name == "0001-a"
    assert find_next_pending(exp).name == "0002-b"


def test_run_experiment_scrubs_and_records(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    d = _mk(exp, "0001-demo", "pending")
    defaults = tmp_path / "_defaults.yaml"; defaults.write_text("seed: 1\n")
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import sys\n"
        "assert '--config' in sys.argv\n"
        "print('person_id = 7')\n"
        "print('[demo] mean = 3.14')\n"
    )
    (d / "config.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    rc = run_experiment(d, defaults)
    assert rc == 0
    summary = (d / "runs" / "summary.md").read_text()
    assert "mean = 3.14" in summary
    assert "person_id" not in summary
    assert "Session complete (exit 0)" in summary
    assert (d / "runs" / "config.yaml").exists()
