#!/usr/bin/env python3
"""Version the Sauda explanation tracks so browsers fetch the new narration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYS = ("pg078_n0013", "pg078_n0013_easy_read")


def main() -> None:
    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        path = base / "audios.json"
        mappings = json.loads(path.read_text(encoding="utf-8"))
        for key in KEYS:
            old_name = mappings[key]
            new_name = f"{Path(old_name).stem}_capital_explanation_v2.mp3"
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
            mappings[key] = new_name
        path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Versioned the standard and easy-read Sauda explanation tracks")


if __name__ == "__main__":
    main()
