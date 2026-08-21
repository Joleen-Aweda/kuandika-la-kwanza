#!/usr/bin/env python3
"""Version paired-letter and case-exercise tracks to bypass browser caches."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def is_pair(value: str) -> bool:
    compact = re.sub(r"\s+", "", value)
    match = re.fullmatch(r"([A-Z])([a-z])", compact)
    return bool(match and match.group(1).lower() == match.group(2)) or compact == "Chch"


def main() -> None:
    texts = json.loads((ROOT / "content/i18n/sw-TZ/texts.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "tools/sw_tz_pronunciation_overrides.json").read_text(encoding="utf-8"))
    selected_keys = {
        key for key, value in texts.items()
        if is_pair(value) and "_ans_item-" not in key
    }
    selected_keys.update(
        key for key, speech in overrides.items()
        if "imeandikwa kwa herufi" in speech and key in texts
    )

    for lang in ("sw", "sw-TZ"):
        base = ROOT / "content/i18n" / lang
        path = base / "audios.json"
        mappings = json.loads(path.read_text(encoding="utf-8"))
        selected_files = {mappings[key] for key in selected_keys if key in mappings}
        renamed = {
            old_name: f"{Path(old_name).stem}_pair_case_v2.mp3"
            for old_name in selected_files
        }
        for old_name, new_name in renamed.items():
            shutil.copyfile(base / "audio" / old_name, base / "audio" / new_name)
        for key, old_name in list(mappings.items()):
            if old_name in renamed:
                mappings[key] = renamed[old_name]
        path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{lang}: versioned {len(selected_files)} files for {len(selected_keys)} text IDs")


if __name__ == "__main__":
    main()
