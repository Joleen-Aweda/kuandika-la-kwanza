#!/usr/bin/env python3
"""Keep full-page facsimiles visual-only and remove them from read-aloud."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAG_RE = re.compile(
    r'<img\b(?=[^>]*\bclass="[^"]*source-facsimile-page[^"]*")[^>]*>',
    re.S,
)


def presentation_tag(tag: str) -> str:
    tag = re.sub(r'\s(?:alt|data-id|aria-hidden|role)="[^"]*"', "", tag)
    closing = " />" if tag.rstrip().endswith("/>") else ">"
    body = tag.rstrip()[:-2] if closing == " />" else tag.rstrip()[:-1]
    return body.rstrip() + ' alt="" aria-hidden="true" role="presentation"' + closing


def main() -> None:
    pages = [ROOT / "index.html", *sorted(ROOT.glob("pg???_sec001.html"))]
    updated_pages = 0
    for path in pages:
        source = path.read_text(encoding="utf-8")
        updated, count = TAG_RE.subn(lambda match: presentation_tag(match.group(0)), source)
        if count:
            path.write_text(updated, encoding="utf-8")
            updated_pages += 1

    removed_keys = set()
    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        for name in ("texts.json", "audios.json"):
            path = base / name
            data = json.loads(path.read_text(encoding="utf-8"))
            keys = [key for key in data if key.endswith("_page_image")]
            removed_keys.update(keys)
            for key in keys:
                del data[key]
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for audio in (base / "audio").glob("pg???_page_image.mp3"):
            audio.unlink()

    print(f"Marked {updated_pages} page facsimiles as presentation-only; removed {len(removed_keys)} narration IDs")


if __name__ == "__main__":
    main()
