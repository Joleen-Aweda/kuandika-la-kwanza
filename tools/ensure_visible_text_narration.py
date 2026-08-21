#!/usr/bin/env python3
"""Give every visible semantic text leaf a text/audio ID on its own page."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEAKABLE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]")
LEAF = re.compile(
    r"<(?P<tag>span|p|h[1-6]|label|text|strong|em)"
    r"(?P<attrs>(?:(?!\bdata-id=)[^>])*)>"
    r"(?P<text>[^<>]+)</(?P=tag)>",
    re.IGNORECASE,
)
SECTION = re.compile(
    r"(<section\b[^>]*\bclass=\"[^\"]*source-semantic-copy[^\"]*\"[^>]*>)"
    r"(?P<body>.*?)</section>",
    re.DOTALL,
)


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, str]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    texts = {
        lang: load_json(ROOT / f"content/i18n/{lang}/texts.json")
        for lang in ("sw", "sw-TZ")
    }
    audios = {
        lang: load_json(ROOT / f"content/i18n/{lang}/audios.json")
        for lang in ("sw", "sw-TZ")
    }
    added = 0

    invalid_auto_ids = {
        key for key, value in texts["sw"].items()
        if "_auto_tx" in key and not SPEAKABLE.search(str(value))
    }
    if invalid_auto_ids:
        invalid_pattern = re.compile(
            r'\sdata-id=(["\'])(?:'
            + "|".join(re.escape(key) for key in sorted(invalid_auto_ids))
            + r')\1'
        )
        for path in sorted(ROOT.glob("pg*_sec*.html")):
            source = path.read_text(encoding="utf-8")
            updated = invalid_pattern.sub("", source)
            if updated != source:
                path.write_text(updated, encoding="utf-8")
        for lang in ("sw", "sw-TZ"):
            for key in invalid_auto_ids:
                texts[lang].pop(key, None)
                audios[lang].pop(key, None)

    for path in sorted(ROOT.glob("pg*_sec*.html")):
        page = path.stem[:5]
        source = path.read_text(encoding="utf-8")
        used = set(re.findall(r'data-id=["\']([^"\']+)', source))
        next_number = 1

        def section_replace(section_match: re.Match[str]) -> str:
            nonlocal added, next_number
            body = section_match.group("body")

            def leaf_replace(match: re.Match[str]) -> str:
                nonlocal added, next_number
                value = " ".join(html.unescape(match.group("text")).split())
                if not value or not SPEAKABLE.search(value):
                    return match.group(0)
                while True:
                    text_id = f"{page}_auto_tx{next_number:03d}"
                    next_number += 1
                    if text_id not in used and text_id not in texts["sw"]:
                        break
                used.add(text_id)
                for lang in ("sw", "sw-TZ"):
                    texts[lang][text_id] = value
                    audios[lang][text_id] = f"{text_id}.mp3"
                added += 1
                return (
                    f"<{match.group('tag')}{match.group('attrs')} data-id=\"{text_id}\">"
                    f"{match.group('text')}</{match.group('tag')}>"
                )

            updated_body = LEAF.sub(leaf_replace, body)
            return section_match.group(1) + updated_body + "</section>"

        updated = SECTION.sub(section_replace, source)
        if updated != source:
            path.write_text(updated, encoding="utf-8")

    for lang in ("sw", "sw-TZ"):
        write_json(ROOT / f"content/i18n/{lang}/texts.json", texts[lang])
        write_json(ROOT / f"content/i18n/{lang}/audios.json", audios[lang])
    print(
        f"Added narration IDs for {added} visible text leaves; "
        f"removed {len(invalid_auto_ids)} punctuation-only IDs"
    )


if __name__ == "__main__":
    main()
