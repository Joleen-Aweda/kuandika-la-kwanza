#!/usr/bin/env python3
"""Version page-82 name-case tracks to bypass browser audio caches."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_KEYS = ("pg082_n0019", "pg082_n0021", "pg082_n0022", "pg082_n0023", "pg082_n0024", "pg082_n0025")
KEYS = tuple(key for base in BASE_KEYS for key in (base, f"{base}_easy_read"))


def main() -> None:
    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        path = base / "audios.json"
        mappings = json.loads(path.read_text(encoding="utf-8"))
        for key in KEYS:
            old_name = mappings[key]
            new_name = f"{key}_lowercase_only_v3.mp3" if key != "pg082_n0019" and key != "pg082_n0019_easy_read" else old_name
            if new_name == old_name:
                continue
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
            mappings[key] = new_name
        path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Versioned {len(KEYS)} page-82 name-case tracks in both languages")


if __name__ == "__main__":
    main()
