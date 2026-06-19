import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_run_cli_dispatches_next(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    defaults = tmp_path / "defaults"; defaults.mkdir()
    (defaults / "_base.yaml").write_text("seed: 1\n")
    stub = tmp_path / "stub.py"
    stub.write_text("print('[demo] ok')\n")
    (defaults / "demo.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    (exp / "0001-demo.md").write_text("---\nid: 1\ngroup: demo\nstatus: pending\n---\n")
    runs = tmp_path / "runs"
    r = subprocess.run(
        [sys.executable, "-m", "utilities.cli.run", "--next",
         "--experiments-dir", str(exp),
         "--defaults-dir", str(defaults), "--runs-dir", str(runs)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
    assert (runs / "0001-demo" / "summary.md").exists()
