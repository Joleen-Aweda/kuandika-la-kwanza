#!/usr/bin/env python3
"""Validate every correction row from -KUANDIKA STD ONE- JOLEEEN.docx."""

from __future__ import annotations

import html
import hashlib
import json
import re
from pathlib import Path

from apply_instruction_expansions import EXPANSIONS
from joleen_review_overlays import OVERLAY_POSITIONS


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("sw", "sw-TZ")

# The document contains 65 data rows.  Converted-page offsets are represented
# by the real IDs used in this bundle rather than the printed PDF page alone.
REVIEW_ROWS: dict[int, tuple[str, ...]] = {
    1: ("pg001_n0014", "pg002_n0004"),
    2: ("pg005_n0006", "pg005_n0007", "pg005_n0010"),
    3: ("pg006_n0016",),
    4: ("pg008_n0005",),
    5: ("pg009_n0002",),
    6: ("pg010_n0005", "pg010_n0006"),
    7: ("pg011_n0016",),
    8: ("pg012_n0005", "pg012_n0009"),
    9: ("pg016_n0006",),
    10: ("pg017_n0013", "pg017_n0014"),
    11: ("pg019_n0008", "pg019_n0010"),
    12: ("pg020_n0030",),
    13: ("pg021_n0002",),
    14: ("pg022_n0019", "pg022_n0021"),
    15: ("pg024_n0015", "pg024_n0018"),
    16: ("pg027_n0008", "pg027_n0009", "pg027_n0018"),
    17: ("pg029_n0006",),
    18: ("pg030_n0026", "pg031_n0002"),
    19: ("pg032_n0025",),
    20: ("pg033_n0002",),
    21: ("pg034_n0020",),
    22: ("pg037_n0018",),
    23: ("pg039_n0005",),
    24: ("pg040_n0032",),
    25: ("pg042_n0015",),
    26: ("pg044_n0005",),
    27: ("pg047_n0013",),
    28: ("pg049_n0006", "pg049_n0009"),
    29: ("pg050_n0014",),
    30: ("pg052_n0005",),
    31: ("pg054_n0005", "pg054_im002_crop1"),
    32: ("pg055_n0007",),
    33: ("pg057_n0005",),
    34: ("pg058_n0018",),
    35: ("pg060_n0004",),
    36: ("pg061_n0023",),
    37: ("pg063_n0013",),
    38: ("pg065_n0005",),
    39: ("pg066_n0032",),
    40: ("pg068_n0005",),
    41: ("pg069_n0019",),
    42: ("pg070_n0002",),
    43: ("pg072_n0015",),
    44: ("pg074_n0005",),
    45: ("pg075_n0023", "pg076_n0002"),
    46: ("pg077_n0013", "pg077_n0017"),
    47: ("pg079_n0005", "pg079_n0010"),
    48: ("pg081_n0013", "pg081_n0023"),
    49: ("pg082_n0029", "pg083_n0002"),
    50: ("pg084_n0022", "pg084_n0027"),
    51: ("pg086_n0006", "pg086_n0011"),
    52: ("pg087_n0016", "pg088_n0002"),
    53: ("pg090_n0012", "pg090_n0022"),
    54: ("pg092_n0004", "pg092_n0011"),
    55: ("pg093_n0027", "pg094_n0002"),
    56: ("pg095_n0021", "pg095_n0031"),
    57: ("pg097_n0016",),
    58: ("pg098_n0016", "pg098_n0018"),
    59: ("pg100_n0022", "pg101_n0002"),
    60: ("pg102_n0013", "pg102_n0015"),
    61: ("pg104_n0028", "pg104_n0035"),
    62: ("pg106_n0031", "pg107_n0002"),
    63: ("pg109_n0005", "pg109_n0011"),
    64: ("pg111_n0003", "pg111_n0010"),
    65: ("pg113_n0005", "pg113_n0011"),
}


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def main() -> None:
    errors: list[str] = []
    if sorted(REVIEW_ROWS) != list(range(1, 66)):
        errors.append("Review checklist must contain rows 1 through 65")

    checked_ids = {text_id for ids in REVIEW_ROWS.values() for text_id in ids}
    missing_semantic_ids = checked_ids - set(EXPANSIONS) - {
        "pg001_n0014", "pg002_n0004", "pg005_n0006", "pg005_n0007", "pg005_n0010"
    }
    if missing_semantic_ids:
        errors.append("Checklist IDs missing from corrections: " + ", ".join(sorted(missing_semantic_ids)))

    texts_by_language = {
        lang: load_json(ROOT / "content" / "i18n" / lang / "texts.json")
        for lang in LANGUAGES
    }
    audio_by_language = {
        lang: load_json(ROOT / "content" / "i18n" / lang / "audios.json")
        for lang in LANGUAGES
    }

    for text_id, (page_number, expected) in EXPANSIONS.items():
        page = ROOT / f"pg{page_number:03d}_sec001.html"
        source = page.read_text(encoding="utf-8")
        if f'data-id="{text_id}"' not in source:
            errors.append(f"{page.name}: missing {text_id}")
        if normalized(expected) not in normalized(source):
            errors.append(f"{page.name}: inline text differs for {text_id}")
        for lang in LANGUAGES:
            if texts_by_language[lang].get(text_id) != expected:
                errors.append(f"{lang}/texts.json differs for {text_id}")

    for row, ids in REVIEW_ROWS.items():
        for text_id in ids:
            for lang in LANGUAGES:
                visible = texts_by_language[lang].get(text_id, "").strip()
                if not visible:
                    errors.append(f"Review row {row}: missing {lang} text {text_id}")
                    continue
                filename = audio_by_language[lang].get(text_id)
                if not filename:
                    errors.append(f"Review row {row}: missing {lang} audio mapping {text_id}")
                    continue
                audio = ROOT / "content" / "i18n" / lang / "audio" / filename
                if not audio.exists() or audio.stat().st_size < 300:
                    errors.append(f"Review row {row}: missing/invalid {lang} audio {filename}")

    corrected_audio_ids = set(EXPANSIONS)
    corrected_audio_ids.update(
        f"{text_id}_easy_read"
        for text_id in EXPANSIONS
        if f"{text_id}_easy_read" in texts_by_language["sw-TZ"]
    )
    corrected_audio_ids.update(
        text_id
        for text_id, value in texts_by_language["sw-TZ"].items()
        if text_id.startswith("pg111_")
        and value.strip()
        and "_ans_item-" not in text_id
    )
    for text_id in corrected_audio_ids:
        files: list[Path] = []
        for lang in LANGUAGES:
            filename = audio_by_language[lang].get(text_id)
            if not filename:
                errors.append(f"Missing corrected audio mapping: {lang}/{text_id}")
                continue
            audio = ROOT / "content" / "i18n" / lang / "audio" / filename
            if not audio.exists() or audio.stat().st_size < 300:
                errors.append(f"Missing/invalid corrected audio: {lang}/{filename}")
                continue
            files.append(audio)
        if len(files) == 2:
            hashes = [hashlib.sha256(path.read_bytes()).digest() for path in files]
            if hashes[0] != hashes[1]:
                errors.append(f"sw and sw-TZ audio differ for {text_id}")

    for page in OVERLAY_POSITIONS:
        overlay = ROOT / "images" / "corrections" / f"pg{int(page):03d}.png"
        if not overlay.exists() or overlay.stat().st_size < 1000:
            errors.append(f"Missing correction overlay {overlay.name}")

    page111 = (ROOT / "pg111_sec001.html").read_text(encoding="utf-8")
    if 'data-section-id="pg111_sec001"' not in page111 or 'data-id="pg108_' in page111:
        errors.append("Page 111 still reuses page 108 identifiers")

    if errors:
        print("\n".join(errors))
        raise SystemExit(f"Validation failed with {len(errors)} problem(s)")
    print(
        f"Validated all {len(REVIEW_ROWS)} review rows, {len(EXPANSIONS)} corrected text IDs, "
        f"{len(OVERLAY_POSITIONS)} visible correction pages, and "
        f"{len(corrected_audio_ids)} corrected audio IDs."
    )


if __name__ == "__main__":
    main()
