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
    p.add_argument("--experiments-dir", default="experiments")
    p.add_argument("--defaults", default="experiments/_defaults.yaml")
    args = p.parse_args(argv)

    exp_root = Path(args.experiments_dir)
    if args.next:
        exp = find_next_pending(exp_root)
        if exp is None:
            print("No pending experiments.", file=sys.stderr)
            return 1
    else:
        exp = find_by_id(exp_root, args.id)

    print(f"[run] {exp.name}")
    return run_experiment(exp, Path(args.defaults))


if __name__ == "__main__":
    sys.exit(main())
