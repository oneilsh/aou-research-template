import re
import sys
from pathlib import Path

from utilities.sanitize import (
    DROP_PATTERNS,
    sanitize_line,
    run_subprocess_tee_sanitize,
)


def test_drops_row_level_lines():
    assert sanitize_line("person_id = 12345", DROP_PATTERNS) is None
    assert sanitize_line("person_hash deadbeef", DROP_PATTERNS) is None
    assert sanitize_line("token hash:deadbeef12", DROP_PATTERNS) is None


def test_drops_log_noise():
    assert sanitize_line("24/01/02 10:11:12 INFO Foo: hi", DROP_PATTERNS) is None


def test_passes_aggregates():
    line = "[demo] mean(n_conditions) by group: 3.1 / 4.2"
    assert sanitize_line(line, DROP_PATTERNS) == line


def test_drops_bare_person_id_header():
    assert sanitize_line("person_id  grp  n_conditions", DROP_PATTERNS) is None


def test_tee_sanitize_writes_only_clean_lines(tmp_path):
    out = tmp_path / "summary.md"
    code = (
        "print('person_id = 999'); "
        "print('[demo] mean = 4.2')"
    )
    rc = run_subprocess_tee_sanitize([sys.executable, "-c", code], out)
    assert rc == 0
    text = out.read_text()
    assert "mean = 4.2" in text
    assert "person_id" not in text
