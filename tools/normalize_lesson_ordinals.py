#!/usr/bin/env python3
"""Normalize Kiswahili lesson ordinals and the page 45 word-count phrase."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDINALS = {
    "1": "kwanza", "2": "pili", "3": "tatu", "4": "nne", "5": "tano",
    "6": "sita", "7": "saba", "8": "nane", "9": "tisa", "10": "kumi",
}


def main() -> None:
    changed = 0
    for language in ("sw", "sw-TZ"):
        path = ROOT / f"content/i18n/{language}/texts.json"
        texts = json.loads(path.read_text(encoding="utf-8"))
        for key, value in texts.items():
            match = re.fullmatch(r"Somo la (10|[1-9])", str(value).strip())
            if match:
                texts[key] = f"Somo la {ORDINALS[match.group(1)]}"
                changed += 1
        texts["pg045_n0009"] = (
            "Andika maneno matano yenye maana kwa kuunganisha herufi "
            "f g y z h na a e i o u."
        )
        texts["pg045_n0009_easy_read"] = (
            "Andika maneno matano yenye maana.\n"
            "Tumia kuunganisha herufi f, g, y, z, h na a, e, i, o, u."
        )
        path.write_text(
            json.dumps(texts, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        audio_map_path = ROOT / f"content/i18n/{language}/audios.json"
        audio_map = json.loads(audio_map_path.read_text(encoding="utf-8"))
        audio_dir = audio_map_path.parent / "audio"
        affected = {
            key for key, value in texts.items()
            if re.fullmatch(
                r"Somo la (?:kwanza|pili|tatu|nne|tano|sita|saba|nane|tisa|kumi)",
                str(value).strip(),
                flags=re.IGNORECASE,
            )
        } | {"pg045_n0009", "pg045_n0009_easy_read"}
        for key in affected:
            if key not in audio_map:
                continue
            old_name = audio_map[key]
            if old_name.endswith("_lesson_ordinal.mp3"):
                continue
            new_name = f"{Path(old_name).stem}_lesson_ordinal.mp3"
            shutil.copyfile(audio_dir / old_name, audio_dir / new_name)
            audio_map[key] = new_name
        audio_map_path.write_text(
            json.dumps(audio_map, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Normalized {changed} numeric lesson headings across both languages")


if __name__ == "__main__":
    main()
