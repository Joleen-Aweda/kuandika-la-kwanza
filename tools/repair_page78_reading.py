#!/usr/bin/env python3
"""Restore the complete printed sentences to page 78 read-aloud text."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = {
    "pg078_n0004": "Sudi amenunua samaki na sukari.",
    "pg078_n0005": "Sakina amevaa saa.",
    "pg078_n0006": "Salumu amepewa zawadi ya viatu.",
}


def main() -> None:
    page = ROOT / "pg078_sec001.html"
    source = page.read_text(encoding="utf-8")
    for text_id, value in CORRECTIONS.items():
        pattern = re.compile(
            rf'(<[^>]+\bdata-id="{re.escape(text_id)}"[^>]*>).*?(</[^>]+>)',
            re.S,
        )
        source, count = pattern.subn(rf"\g<1>{value}\g<2>", source, count=1)
        if count != 1:
            raise SystemExit(f"Could not update {text_id} in page HTML")
    page.write_text(source, encoding="utf-8")

    for lang in ("sw", "sw-TZ"):
        path = ROOT / "content/i18n" / lang / "texts.json"
        texts = json.loads(path.read_text(encoding="utf-8"))
        texts.update(CORRECTIONS)
        for text_id, value in CORRECTIONS.items():
            easy_id = f"{text_id}_easy_read"
            if easy_id in texts:
                texts[easy_id] = value
        path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Restored {len(CORRECTIONS)} complete page-78 sentences")


if __name__ == "__main__":
    main()
