import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "framework" / "scripts" / "check_no_data_files.sh"


def test_rejects_data_file_outside_tests():
    r = subprocess.run([str(SCRIPT), "experiments/leak.csv"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "outside allowed paths" in r.stdout


def test_allows_data_file_in_tests_data():
    r = subprocess.run([str(SCRIPT), "tests/data/fixture.csv"], capture_output=True, text=True)
    assert r.returncode == 0
