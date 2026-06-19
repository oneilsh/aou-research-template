"""Scrub subprocess output so committed run records carry no patient-level rows.

The air-gap workflow has a human copy results out of the secure environment by
hand. This module makes that safe by construction: when an analysis runs through
the runner, its stdout is streamed live to the terminal but only a *sanitized*
copy is written to the committed summary.md. Any line that looks like row-level
patient output is dropped; aggregates, estimates, and summary statistics pass
through.

Extend PATIENT_PATTERNS for the output shapes your analysis produces.
"""
from __future__ import annotations

import re
import signal
import subprocess
import sys
from pathlib import Path

# Lines that look like per-subject / row-level output. Dropped from the record.
PATIENT_PATTERNS: list[re.Pattern] = [
    # Catches bare column-header dumps (print(df)/df.show()) as well as key=value forms.
    re.compile(r"\bperson_id\b", re.IGNORECASE),
    re.compile(r"\bperson_hash\b", re.IGNORECASE),
    re.compile(r"\bhash:[0-9a-f]{6,}", re.IGNORECASE),
    re.compile(r"\brow\s+\d+\s*[:|]", re.IGNORECASE),
]

# Environment log noise with no value in the committed record. Still teed live.
NOISE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} (INFO|WARN|DEBUG) "),
    re.compile(r"\[CONTEXT ratelimit_period="),
]

DROP_PATTERNS: list[re.Pattern] = PATIENT_PATTERNS + NOISE_PATTERNS


def sanitize_line(line: str, patterns: list[re.Pattern]) -> str | None:
    """Return the line unchanged if safe to commit, or None to drop it."""
    for pat in patterns:
        if pat.search(line):
            return None
    return line


class _SignalReceived(Exception):
    def __init__(self, signum: int):
        super().__init__(f"signal {signum}")
        self.signum = signum


def run_subprocess_tee_sanitize(
    cmd: list[str], summary_path: Path, patterns: list[re.Pattern] | None = None,
) -> int:
    """Run `cmd`; stream stdout live; append only sanitized lines to summary_path.

    Every line is echoed to this process's stdout (live debugging). Lines that
    survive `sanitize_line` are also appended to `summary_path`. On SIGTERM/SIGINT
    a `### Killed (signal: N)` marker is written and 130 is returned; otherwise
    the child's exit code is returned.
    """
    if patterns is None:
        patterns = DROP_PATTERNS

    def _handler(signum, frame):  # noqa: ARG001 — frame unused
        raise _SignalReceived(signum)

    prev_term = signal.signal(signal.SIGTERM, _handler)
    prev_int = signal.signal(signal.SIGINT, _handler)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True,
    )
    if proc.stdout is None:
        raise RuntimeError("subprocess stdout not captured")
    try:
        with summary_path.open("a") as fout:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                clean = sanitize_line(line, patterns)
                if clean is not None:
                    fout.write(clean)
                    fout.flush()
        return proc.wait()
    except _SignalReceived as sig:
        with summary_path.open("a") as fout:
            fout.write(f"\n### Killed (signal: {sig.signum})\n")
            fout.flush()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return 130
    finally:
        signal.signal(signal.SIGTERM, prev_term)
        signal.signal(signal.SIGINT, prev_int)
