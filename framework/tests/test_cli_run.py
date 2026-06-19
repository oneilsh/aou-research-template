import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_run_cli_dispatches_next(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "_defaults.yaml").write_text("seed: 1\n")
    d = exp / "0001-demo"; d.mkdir()
    (d / "README.md").write_text("---\nstatus: pending\n---\n")
    stub = tmp_path / "stub.py"; stub.write_text("print('[demo] ok')\n")
    (d / "config.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    r = subprocess.run(
        [sys.executable, "-m", "utilities.cli.run", "--next",
         "--experiments-dir", str(exp), "--defaults", str(exp / "_defaults.yaml")],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr
    assert (d / "runs" / "summary.md").exists()
