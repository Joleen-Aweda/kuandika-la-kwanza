#!/usr/bin/env python3
"""Version page-86 Zz tracks to bypass browser audio caches."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYS = ("pg086_n0017", "pg086_n0019", "pg086_n0021", "pg086_n0023", "pg086_n0025")


def main() -> None:
    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        path = base / "audios.json"
        mappings = json.loads(path.read_text(encoding="utf-8"))
        for key in KEYS:
            old_name = mappings[key]
            new_name = f"{key}_z_kubwa_z_ndogo_v2.mp3"
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
            mappings[key] = new_name
        path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Versioned five page-86 Zz tracks in both languages")


if __name__ == "__main__":
    main()
