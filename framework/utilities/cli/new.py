#!/usr/bin/env python
"""Scaffold the next experiment folder from experiments/_template/."""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

_DIR_RE = re.compile(r"^(\d{4})-.+$")


def next_id(experiments_dir: Path) -> int:
    ids = [int(m.group(1)) for p in experiments_dir.iterdir()
           if p.is_dir() and (m := _DIR_RE.match(p.name))]
    return (max(ids) + 1) if ids else 1


def scaffold(slug: str, experiments_dir: Path, template_dir: Path, today: str) -> Path:
    nid = next_id(experiments_dir)
    out_dir = experiments_dir / f"{nid:04d}-{slug}"
    out_dir.mkdir(parents=True)
    subs = dict(id=nid, id_padded=f"{nid:04d}", slug=slug, date=today)
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
