#!/usr/bin/env python
"""Scaffold a dated experiment folder from experiments/_template/."""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path


def scaffold(slug: str, experiments_dir: Path, template_dir: Path, today: str) -> Path:
    out_dir = experiments_dir / f"{today}-{slug}"
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} already exists")
    out_dir.mkdir(parents=True)
    subs = dict(slug=slug, date=today)
    for src in sorted(template_dir.iterdir()):
        if src.is_file():
            (out_dir / src.name).write_text(src.read_text().format(**subs))
    return out_dir


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug", help="short kebab-case slug, e.g. 'sex-condition-count'")
    p.add_argument("--experiments-dir", default="experiments")
    p.add_argument("--template-dir", default="experiments/_template")
    args = p.parse_args(argv)
    today = _dt.date.today().isoformat()
    out = scaffold(args.slug, Path(args.experiments_dir), Path(args.template_dir), today)
    print(f"Wrote {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
