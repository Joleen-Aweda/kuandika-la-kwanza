#!/usr/bin/env python3
"""Version every letter-case track so browsers fetch kubwa/ndogo narration."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPHEMES = (
    "ch", "a", "e", "i", "o", "u", "b", "m", "k", "d", "n", "l",
    "t", "p", "s", "j", "f", "g", "y", "z", "h", "r", "w", "v",
)
PATTERN = re.compile(
    rf"(?<![A-Za-z])(?:{'|'.join(sorted(GRAPHEMES, key=len, reverse=True))})(?![A-Za-z])",
    re.IGNORECASE,
)


def main() -> None:
    source_texts = json.loads(
        (ROOT / "content/i18n/sw-TZ/texts.json").read_text(encoding="utf-8")
    )
    selected_keys = {
        key for key, value in source_texts.items()
        if PATTERN.search(value) and value.strip() and "_ans_item-" not in key
    }

    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        path = base / "audios.json"
        mappings = json.loads(path.read_text(encoding="utf-8"))
        selected_files = {mappings[key] for key in selected_keys if key in mappings}
        renamed = {
            old_name: f"{Path(old_name).stem}_letter_case_v2.mp3"
            for old_name in selected_files
        }
        for old_name, new_name in renamed.items():
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
        for key, old_name in list(mappings.items()):
            if old_name in renamed:
                mappings[key] = renamed[old_name]
        path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{lang}: versioned {len(renamed)} files for {len(selected_keys)} case-aware text IDs")


if __name__ == "__main__":
    main()
