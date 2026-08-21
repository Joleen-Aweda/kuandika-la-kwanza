#!/usr/bin/env python3
"""Restore every printed word to page 78's read-aloud sequence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAMES = "Saidi, Salima, Soweto, Selina, Sakina, Somalia, Sudi, Suzana."
SENTENCES = {
    "pg078_n0004": "Sudi amenunua samaki na sukari.",
    "pg078_n0005": "Sakina amevaa saa.",
    "pg078_n0006": "Salumu amepewa zawadi ya viatu.",
}


def write_json(path: Path, value: dict[str, str]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    page = ROOT / "pg078_sec001.html"
    source = page.read_text(encoding="utf-8")
    marker = '<section data-section-type="activity_fill_in_the_blank" data-section-id="pg078_sec001" class="source-semantic-copy mx-auto max-w-4xl text-left">'
    names_span = f'<span class="sr-only" data-id="pg078_n0001">{NAMES}</span>'
    if names_span not in source:
        if marker not in source:
            raise SystemExit("Could not locate page 78 section")
        source = source.replace(marker, marker + names_span, 1)
    page.write_text(source, encoding="utf-8")

    for lang in ("sw", "sw-TZ"):
        texts_path = ROOT / "content/i18n" / lang / "texts.json"
        texts = json.loads(texts_path.read_text(encoding="utf-8"))
        texts["pg078_n0001"] = NAMES
        texts["pg078_n0001_easy_read"] = NAMES
        write_json(texts_path, texts)

    overrides_path = ROOT / "tools/sw_tz_pronunciation_overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
    for key, sentence in SENTENCES.items():
        overrides[key] = sentence
        overrides[f"{key}_easy_read"] = sentence
    write_json(overrides_path, overrides)
    print("Restored eight names and three omitted sentence words on page 78")


if __name__ == "__main__":
    main()
