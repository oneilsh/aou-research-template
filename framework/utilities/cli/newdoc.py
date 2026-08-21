#!/usr/bin/env python
"""Scaffold a dated meta-process log entry (ADR or insight).

Each entry is `docs/<kind>/YYYY-MM-DD-<slug>.md`, rendered from a template under
framework/meta_process/. The <kind> directory must already exist — that is the
opt-in switch, created by `make enable-<kind>`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

_DEFAULT_TEMPLATE = {
    "decisions": "framework/meta_process/decision_entry.md",
    "insights": "framework/meta_process/insight_entry.md",
}


def scaffold_doc(kind: str, slug: str, docs_dir: Path, template_file: Path, today: str) -> Path:
    kind_dir = docs_dir / kind
    if not kind_dir.is_dir():
        raise FileNotFoundError(
            f"{kind_dir} does not exist — run `make enable-{kind}` first"
        )
    out = kind_dir / f"{today}-{slug}.md"
    if out.exists():
        raise FileExistsError(f"{out} already exists")
    out.write_text(template_file.read_text().format(date=today, slug=slug))
    return out


def _run(kind: str, argv=None) -> int:
    p = argparse.ArgumentParser(description=f"Scaffold a dated {kind} log entry.")
    p.add_argument("slug", help="short kebab-case slug, e.g. 'use-duckdb-locally'")
    p.add_argument("--docs-dir", default="docs")
    p.add_argument("--template", default=_DEFAULT_TEMPLATE[kind])
    args = p.parse_args(argv)
    today = _dt.date.today().isoformat()
    out = scaffold_doc(kind, args.slug, Path(args.docs_dir), Path(args.template), today)
    print(f"Wrote {out}")
    return 0


def main_decision(argv=None) -> int:
    return _run("decisions", argv)


def main_insight(argv=None) -> int:
    return _run("insights", argv)


if __name__ == "__main__":
    sys.exit(main_decision())
