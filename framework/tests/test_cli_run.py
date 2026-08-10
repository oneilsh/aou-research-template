import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _mk_exp(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir()
    (exp / "_defaults.yaml").write_text("seed: 1\n")
    d = exp / "2026-06-19-demo"; d.mkdir()
    (d / "README.md").write_text("---\nstatus: pending\n---\n")
    stub = tmp_path / "stub.py"; stub.write_text("print('[demo] ok')\n")
    (d / "config.yaml").write_text(f"entrypoint: {sys.executable} {stub}\n")
    return exp, d


def _run(exp, *args):
    return subprocess.run(
        [sys.executable, "-m", "utilities.cli.run", *args,
         "--experiments-dir", str(exp), "--defaults", str(exp / "_defaults.yaml")],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_run_cli_dispatches_next(tmp_path):
    exp, d = _mk_exp(tmp_path)
    r = _run(exp, "--next")
    assert r.returncode == 0, r.stderr
    assert (d / "runs" / "summary.md").exists()


def test_run_cli_dispatches_slug(tmp_path):
    exp, d = _mk_exp(tmp_path)
    r = _run(exp, "--slug", "demo")
    assert r.returncode == 0, r.stderr
    assert (d / "runs" / "summary.md").exists()
