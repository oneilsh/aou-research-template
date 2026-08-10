"""Detect experiment slugs reused across different dates (a warning-level check).

A folder name is `YYYY-MM-DD-<slug>`. The filesystem and git already prevent two
folders with the identical name, so this only surfaces the harmless-but-usually-
accidental case of the same slug under two different dates.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

_DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def duplicate_slugs(experiments_dir: Path) -> dict[str, list[str]]:
    by_slug: dict[str, list[str]] = defaultdict(list)
    for p in experiments_dir.iterdir():
        if not p.is_dir():
            continue
        m = _DIR_RE.match(p.name)
        if m:
            by_slug[m.group(2)].append(p.name)
    return {slug: sorted(names) for slug, names in by_slug.items() if len(names) > 1}
