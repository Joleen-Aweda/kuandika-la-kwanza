#!/usr/bin/env python3
"""Add meaningful descriptions to page facsimiles and weak image labels."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEAK_DESCRIPTION_REPLACEMENTS = {
    "pg020_im002": "Picha ya uma wa chuma wenye meno manne na mpini mrefu.",
    "pg022_im003": "Picha ya kaa mwenye miguu mingi na makucha mawili makubwa.",
    "pg028_im001": "Picha ya mvulana anayelia huku machozi yakimtoka.",
    "pg030_im002": "Picha ya tai ya kuvaa shingoni yenye mistari ya rangi mbalimbali.",
    "pg035_im003": "Picha ya jua linalong'aa angani kwa miale mikali.",
    "pg041_im001": "Picha ya yai moja la rangi ya kahawia.",
}
PAGE_DESCRIPTION_OVERRIDES = {
    84: (
        "Picha ya ukurasa wa 84 wa kitabu. Unaonesha zoezi la kuunda sentensi "
        "kwa kutumia jedwali, pamoja na mazoezi ya kufuatisha na kuandika "
        "herufi kubwa Y na Yy."
    ),
}


def write_json(path: Path, value: dict[str, str]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def page_description(source: str, page_number: int, texts: dict[str, str]) -> str:
    if page_number in PAGE_DESCRIPTION_OVERRIDES:
        return PAGE_DESCRIPTION_OVERRIDES[page_number]
    values: list[str] = []
    for text_id in re.findall(r'data-id=["\']([^"\']+)', source):
        if "_im" in text_id or "_page_image" in text_id or "_auto_tx" in text_id:
            continue
        value = " ".join(str(texts.get(text_id, "")).split())
        if len(value) < 4 or value in values:
            continue
        values.append(value)
        if len(values) == 4:
            break
    detail = " ".join(values)
    if detail:
        return f"Picha ya ukurasa wa {page_number} wa kitabu. Unaonesha: {detail}"
    return f"Picha ya ukurasa wa {page_number} wa kitabu cha Kuandika."


def main() -> None:
    texts = {
        lang: json.loads(
            (ROOT / f"content/i18n/{lang}/texts.json").read_text(encoding="utf-8")
        )
        for lang in ("sw", "sw-TZ")
    }
    audios = {
        lang: json.loads(
            (ROOT / f"content/i18n/{lang}/audios.json").read_text(encoding="utf-8")
        )
        for lang in ("sw", "sw-TZ")
    }
    page_count = 0

    for path in sorted(ROOT.glob("*.html")):
        source = path.read_text(encoding="utf-8")
        page_match = re.search(r'images/source-pages/pg(\d{3})\.png', source)
        if not page_match:
            continue
        page_number = int(page_match.group(1))
        text_id = f"pg{page_number:03d}_page_image"
        description = page_description(source, page_number, texts["sw"])
        pattern = re.compile(
            r'<img\b(?=[^>]*\bclass="[^"]*source-facsimile-page[^"]*")[^>]*>'
        )
        match = pattern.search(source)
        if not match:
            continue
        tag = match.group(0)
        tag = re.sub(r'\sdata-id=["\'][^"\']*["\']', "", tag)
        tag = re.sub(r'\saria-hidden=["\']true["\']', "", tag)
        tag = re.sub(
            r'\salt=["\'][^"\']*["\']',
            f' alt="{html.escape(description, quote=True)}"',
            tag,
        )
        tag = tag[:-2] + f' data-id="{text_id}" />' if tag.endswith("/>") else tag[:-1] + f' data-id="{text_id}">'
        source = source[: match.start()] + tag + source[match.end() :]

        for weak_id, replacement in WEAK_DESCRIPTION_REPLACEMENTS.items():
            source = re.sub(
                rf'(<img\b[^>]*\bdata-id="{re.escape(weak_id)}"[^>]*\balt=")[^"]*(")',
                lambda m: m.group(1) + html.escape(replacement, quote=True) + m.group(2),
                source,
            )
        path.write_text(source, encoding="utf-8")
        for lang in ("sw", "sw-TZ"):
            texts[lang][text_id] = description
            audios[lang][text_id] = f"{text_id}.mp3"
        page_count += 1

    for lang in ("sw", "sw-TZ"):
        for text_id, replacement in WEAK_DESCRIPTION_REPLACEMENTS.items():
            texts[lang][text_id] = replacement
            easy_id = f"{text_id}_easy_read"
            if easy_id in texts[lang]:
                texts[lang][easy_id] = replacement
            for versioned_id in (text_id, easy_id):
                if versioned_id not in audios[lang]:
                    continue
                old_name = audios[lang][versioned_id]
                if old_name.endswith("_description.mp3"):
                    continue
                new_name = f"{Path(old_name).stem}_description.mp3"
                audio_dir = ROOT / f"content/i18n/{lang}/audio"
                (audio_dir / new_name).write_bytes((audio_dir / old_name).read_bytes())
                audios[lang][versioned_id] = new_name
        write_json(ROOT / f"content/i18n/{lang}/texts.json", texts[lang])
        write_json(ROOT / f"content/i18n/{lang}/audios.json", audios[lang])
    print(
        f"Added descriptions for {page_count} page images and expanded "
        f"{len(WEAK_DESCRIPTION_REPLACEMENTS)} weak descriptions"
    )


if __name__ == "__main__":
    main()
