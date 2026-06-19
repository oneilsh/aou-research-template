#!/usr/bin/env python
"""Pick an experiment and run it."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from utilities.runner import find_by_id, find_next_pending, run_experiment


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sel = p.add_mutually_exclusive_group(required=True)
    sel.add_argument("--next", action="store_true", help="run lowest-id pending experiment")
    sel.add_argument("--id", type=int, help="run experiment with this id")
    p.add_argument("--experiments-dir", default="docs/experiments")
    p.add_argument("--defaults-dir", default="experiments/defaults")
    p.add_argument("--runs-dir", default="runs")
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
