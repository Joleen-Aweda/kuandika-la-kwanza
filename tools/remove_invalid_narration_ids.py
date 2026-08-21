#!/usr/bin/env python3
"""Remove HTML data-id attributes that have no localized text entry.

Decorative SVG labels and practice glyphs must not participate in the
read-aloud sequence. A dangling data-id can make narration advance to the
next valid item, including an item that belongs to the following page.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXTS = json.loads(
    (ROOT / "content/i18n/sw/texts.json").read_text(encoding="utf-8")
)
AUDIOS = json.loads(
    (ROOT / "content/i18n/sw/audios.json").read_text(encoding="utf-8")
)
DATA_ID = re.compile(r"\sdata-id=([\"'])([^\"']+)\1")


def clean(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    removed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal removed
        if match.group(2) in TEXTS and match.group(2) in AUDIOS:
            return match.group(0)
        removed += 1
        return ""

    updated = DATA_ID.sub(replace, source)
    if updated != source:
        path.write_text(updated, encoding="utf-8")
    return removed


def main() -> None:
    removed = sum(clean(path) for path in sorted(ROOT.glob("*.html")))
    print(f"Removed {removed} invalid read-aloud IDs")


if __name__ == "__main__":
    main()
