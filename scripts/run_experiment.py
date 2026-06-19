#!/usr/bin/env python
"""Thin CLI over utilities.runner: pick an experiment and run it."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utilities.runner import find_by_id, find_next_pending, run_experiment

REPO = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sel = p.add_mutually_exclusive_group(required=True)
    sel.add_argument("--next", action="store_true", help="run lowest-id pending experiment")
    sel.add_argument("--id", type=int, help="run experiment with this id")
    p.add_argument("--experiments-dir", default=str(REPO / "docs" / "experiments"))
    p.add_argument("--defaults-dir", default=str(REPO / "experiments" / "defaults"))
    p.add_argument("--runs-dir", default=str(REPO / "runs"))
    args = p.parse_args(argv)

    exp_dir = Path(args.experiments_dir)
    if args.next:
        rec = find_next_pending(exp_dir)
        if rec is None:
            print("No pending experiments.", file=sys.stderr)
            return 1
    else:
        rec = find_by_id(exp_dir, args.id)

    print(f"[run] {rec.name}")
    return run_experiment(rec, Path(args.defaults_dir), Path(args.runs_dir))


if __name__ == "__main__":
    sys.exit(main())
