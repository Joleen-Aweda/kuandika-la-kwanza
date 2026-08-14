#!/usr/bin/env python3
"""Apply every reviewed instruction expansion without duplicating exercises."""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPANSIONS = {
    "pg008_n0005": (8, "Fuatisha michoro hii /kwa kutumia spa willi fuatisha michoro hii"),
    "pg010_n0005": (10, "Fuatisha michoro hii /kwa kutumia spa willi fuatisha michoro hii"),
    "pg011_n0028": (11, "Andika herufi ya irabu a, Andika doti ya kwanza kwa kurudiarudia na ujaze mstari"),
    "pg012_n0021": (12, "Andika herufi ya irabu e, Andika doti ya kwanza na ya tano kwa nafasi na ujaze mstari"),
    "pg013_n0007": (13, "Andika herufi ya irabu i, Andika doti ya pili na ya nne kwa nafasi na ujaze mstari"),
    "pg013_n0018": (13, "Andika herufi ya irabu o; Andika doti ya kwanza, ya tatu na ya tano kwa nafasi na ujaze mstari"),
    "pg017_n0025": (17, "Andika doti ya kwanza na ya pili kwa nafasi na ujaze mstari"),
    "pg021_n0008": (21, "Andika herufi ya konsonanti k, Andika doti ya kwanza na ya tatu kwa nafasi na ujaze mstari."),
    "pg023_n0002": (23, "Andika herufi d, Andika doti ya kwanza, ya nne na ya tano kwa nafasi na ujaze mstari."),
    "pg024_n0031": (24, "Andika herufi ya konsonanti n, Andika doti ya kwanza, ya tatu, ya nne na ya tano kwa nafasi na ujaze mstari."),
    "pg029_n0011": (29, "andika konsonanti t Andika doti ya pili, ya tatu, ya nne na ya tano kwa nafasi na ujaze mstari."),
    "pg031_n0006": (31, "Andika herufi ya konsonanti p, Andika doti ya kwanza, ya pili, ya tatu na ya nne kwa nafasi na ujaze mstari."),
    "pg033_n0012": (33, "Andika herufi ya konsonanti s, Andika doti ya pili, ya tatu na ya nne kwa nafasi na ujaze mstari."),
    "pg034_n0031": (34, "Andika herufi ya konsonanti j, Andika doti ya pili, ya nne na ya tano kwa nafasi na ujaze mstari."),
    "pg037_n0029": (37, "andika herufi ya konsonanti f Andika doti ya kwanza, ya pili na ya nne kwa nafasi na ujaze mstari"),
    "pg039_n0018": (39, "Andika herufi G, Andika doti ya kwanza, ya pili, ya nne na ya tano kwa nafasi na ujaze mstari."),
    "pg041_n0002": (41, "Andika herufi ya konsonanti y, Andika doti ya kwanza, ya tatu, ya nne, ya tano na ya sita kwa nafasi na ujaze mstari."),
    "pg042_n0020": (42, "Andika herufi ya konsonanti Z, Andika doti ya kwanza, ya tatu ya tano na sita kwa nafasi na ujaze mstari."),
    "pg044_n0011": (44, "andika herufi ya konsonanti h, Andika doti ya kwanza, ya pili na ya tano kwa nafasi na ujaze mstari."),
    "pg047_n0020": (47, "Andika herufi ya konsonanti r; Andika doti ya kwanza, ya pili, ya tatu na ya tano na kwa nafasi na ujaze mstari."),
    "pg049_n0023": (49, "Andika herufi ya konsonanti w, Andika doti ya pili, ya nne, ya tano na ya sita kwa nafasi na ujaze mstari."),
    "pg050_n0019": (50, "Andika herufi ya konsonanti v; Andika doti ya kwanza, ya pili, ya tatu na ya sita kwa nafasi na ujaze mstari."),
    "pg052_n0013": (52, "Andika herufi ya konsonanti ch;Andika doti ya kwanza na ya nne na doti ya kwanza, ya pili na ya tano kwa nafasi na ujaze"),
    "pg055_n0009": (55, "Andika herufi ya irabu A. Andika doti ya sita na ya kwanza kwa nafasi na ujaze mstari. Andika herufi kubwa A ikifuatiwa na herufi ndogo a kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari"),
    "pg057_n0011": (57, "andika herufi ya irabu E, Andika doti ya sita,ya kwanza na ya tano kwa nafasi na ujaze mstari.Andika herufi kubwa E ikifuatiwa na herufi ndogo e kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari"),
    "pg060_n0011": (60, "Andika herufi ya irabu O, Andika doti ya sita,ya kwanza ya tatu na ya tano kwa nafasi na ujaze mstari.Andika herufi kubwa O ikifuatiwa na herufi ndogo o kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari."),
    "pg061_n0031": (61, "Andika herufi ya irabu U, Andika doti ya sita, ya kwanza, ya tatu na ya sita kwa nafasi na ujaze mstari. Andika herufi kubwa U ikifuatiwa na herufi ndogo u kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari."),
    "pg063_n0023": (63, "Andika herufi ya konsonanti B, Andika doti sita, ya kwanza na ya pili kwa nafasi na ujaze mstari. Andika herufi kubwa B ikifuatiwa na herufi ndogo b kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari."),
    "pg065_n0016": (65, "Andika herufi ya konsonanti M, Andika doti ya sita, ya kwanza, ya tatu na ya nne kwa nafasi na ujaze mstari. Andika herufi kubwa M ikifuatiwa na herufi ndogo m kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari."),
    "pg066_n0037": (66, "Andika herufi ya konsonanti K, Andika doti ya sita, ya kwanza na ya tatu kwa nafasi na ujaze mstari. Andika herufi kubwa K ikifuatiwa na herufi ndogo k kwa Pamoja kisha, andika tena herufi hizo kwa nafasi na ujaze mstari."),
}


def replace_data_id_text(source: str, text_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[A-Za-z][A-Za-z0-9]*)\b[^>]*\bdata-id="{re.escape(text_id)}"[^>]*>)(.*?)(</(?P=tag)>)',
        re.DOTALL,
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + html_module.escape(value) + match.group(4),
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Expected one HTML element for {text_id}, found {count}")
    return updated


def update_html() -> None:
    page17 = ROOT / "pg017_sec001.html"
    source = page17.read_text(encoding="utf-8")
    if 'data-id="pg017_n0025"' not in source:
        old = '''      <p class="text-base font-medium text-zinc-800">
        Andika herufi ya konsonanti <strong class="font-bold">b</strong>.
      </p>'''
        new = '''      <p class="text-base font-medium text-zinc-800" data-id="pg017_n0025">
        Andika herufi ya konsonanti b.
      </p>'''
        if old not in source:
            raise RuntimeError("Could not locate the unlabelled lowercase-b instruction")
        page17.write_text(source.replace(old, new, 1), encoding="utf-8")

    for text_id, (page_number, value) in EXPANSIONS.items():
        path = ROOT / f"pg{page_number:03}_sec001.html"
        source = path.read_text(encoding="utf-8")
        path.write_text(replace_data_id_text(source, text_id, value), encoding="utf-8")


def update_texts() -> None:
    for language in ("sw", "sw-TZ"):
        path = ROOT / "content" / "i18n" / language / "texts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for text_id, (_, value) in EXPANSIONS.items():
            data[text_id] = value
            easy_read_id = f"{text_id}_easy_read"
            if easy_read_id in data or text_id == "pg017_n0025":
                data[easy_read_id] = value
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    update_html()
    update_texts()
    print(f"Applied {len(EXPANSIONS)} instruction expansions")


if __name__ == "__main__":
    main()
