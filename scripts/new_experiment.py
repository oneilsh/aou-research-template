#!/usr/bin/env python
"""Scaffold the next experiment record from docs/experiments/_template.md."""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

_RECORD_RE = re.compile(r"^(\d{4})-.+\.md$")
REPO = Path(__file__).resolve().parent.parent


def next_id(experiments_dir: Path) -> int:
    ids = [int(m.group(1)) for p in experiments_dir.iterdir()
           if (m := _RECORD_RE.match(p.name))]
    return (max(ids) + 1) if ids else 1


def scaffold(slug: str, experiments_dir: Path, template_path: Path, today: str) -> Path:
    nid = next_id(experiments_dir)
    body = template_path.read_text().format(
        id=nid, id_padded=f"{nid:04d}", slug=slug, date=today,
    )
    out = experiments_dir / f"{nid:04d}-{slug}.md"
    out.write_text(body)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("slug", help="short kebab-case slug, e.g. 'sex-condition-count'")
    p.add_argument("--experiments-dir", default=str(REPO / "docs" / "experiments"))
    p.add_argument("--template", default=str(REPO / "docs" / "experiments" / "_template.md"))
    args = p.parse_args(argv)
    today = _dt.date.today().isoformat()
    out = scaffold(args.slug, Path(args.experiments_dir), Path(args.template), today)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
