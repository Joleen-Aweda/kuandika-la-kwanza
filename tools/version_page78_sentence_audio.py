#!/usr/bin/env python3
"""Give corrected page-78 sentence audio fresh filenames to bypass browser cache."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYS = (
    "pg078_n0004",
    "pg078_n0005",
    "pg078_n0006",
    "pg078_n0004_easy_read",
    "pg078_n0005_easy_read",
    "pg078_n0006_easy_read",
)


def main() -> None:
    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        mapping_path = base / "audios.json"
        mappings = json.loads(mapping_path.read_text(encoding="utf-8"))
        for key in KEYS:
            old_name = mappings[key]
            new_name = f"{Path(old_name).stem}_complete_v2.mp3"
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
            mappings[key] = new_name
        mapping_path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Versioned {len(KEYS)} corrected sentence tracks in both languages")


if __name__ == "__main__":
    main()
