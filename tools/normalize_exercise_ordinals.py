#!/usr/bin/env python3
"""Use Kiswahili ordinal words in every numbered exercise heading."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDINALS = {
    "1": "kwanza",
    "2": "pili",
    "3": "tatu",
    "4": "nne",
    "5": "tano",
    "6": "sita",
    "7": "saba",
    "8": "nane",
    "9": "tisa",
    "10": "kumi",
}
PATTERN = re.compile(r"^Zoezi la (10|[1-9])$")


def main() -> None:
    changed = 0
    for language in ("sw", "sw-TZ"):
        path = ROOT / f"content/i18n/{language}/texts.json"
        texts = json.loads(path.read_text(encoding="utf-8"))
        for key, value in texts.items():
            match = PATTERN.fullmatch(str(value).strip())
            if not match:
                continue
            texts[key] = f"Zoezi la {ORDINALS[match.group(1)]}"
            changed += 1
        path.write_text(
            json.dumps(texts, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        audio_map_path = ROOT / f"content/i18n/{language}/audios.json"
        audio_map = json.loads(audio_map_path.read_text(encoding="utf-8"))
        audio_dir = audio_map_path.parent / "audio"
        for key, value in texts.items():
            if not re.fullmatch(
                r"Zoezi la (?:kwanza|pili|tatu|nne|tano|sita|saba|nane|tisa|kumi)",
                str(value).strip(),
                flags=re.IGNORECASE,
            ) or key not in audio_map:
                continue
            old_name = audio_map[key]
            if old_name.endswith("_ordinal.mp3"):
                continue
            new_name = f"{Path(old_name).stem}_ordinal.mp3"
            shutil.copyfile(audio_dir / old_name, audio_dir / new_name)
            audio_map[key] = new_name
        audio_map_path.write_text(
            json.dumps(audio_map, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Normalized {changed} exercise headings across both languages")


if __name__ == "__main__":
    main()
