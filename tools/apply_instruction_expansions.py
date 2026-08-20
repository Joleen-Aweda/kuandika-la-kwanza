#!/usr/bin/env python3
"""Apply the Joleen review instructions without duplicating exercises.

The cleaned PDF artwork remains the visual base.  This script keeps the
semantic HTML and both Swahili text catalogues in lockstep with every reviewed
instruction, including exercises that continue onto the following PDF page.
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOT_ORDINALS = {
    1: "kwanza",
    2: "pili",
    3: "tatu",
    4: "nne",
    5: "tano",
    6: "sita",
}


def dot_list(*numbers: int) -> str:
    values = [f"doti ya {DOT_ORDINALS[number]}" for number in numbers]
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " na " + values[-1]


def trace_instruction(kind: str, letter: str, *dots: int) -> str:
    return (
        f"Andika herufi {kind} {letter} kwa {dot_list(*dots)} kwa nafasi "
        "na ujaze mstari."
    )


def write_instruction(kind: str, letter: str, *dots: int) -> str:
    return (
        f"Andika herufi {kind} {letter}. Andika kwa {dot_list(*dots)} "
        "kwa nafasi na ujaze mstari."
    )


def blend_trace(letter: str, *dots: int) -> str:
    return (
        f"Andika herufi mwambatano {letter} kwa {dot_list(*dots)} kwa nafasi "
        "na ujaze mstari."
    )


def blend_write(letter: str, *dots: int) -> str:
    return (
        f"Andika herufi mwambatano {letter}. Andika kwa {dot_list(*dots)} "
        "kwa nafasi na ujaze mstari."
    )


SPAR_WHEEL = (
    "Chora mchoro huu/Chora mchoro huu kwa kutumia Kifaa cha kuchorea "
    "(Spar wheel)."
)

VIDEO_IRABU = (
    "Tazama video zinavyoonesha jinsi ya kuandika herufi ndogo za irabu. "
    "Kisha andika herufi hizo kwa kufuata hatua zake / doti zake."
)
VIDEO_SMALL_CONSONANTS = (
    "Tazama video zinavyoonesha jinsi ya kuandika herufi ndogo za konsonanti. "
    "Kisha andika herufi hizo kwa kufuata hatua zake / doti zake."
)
VIDEO_CAPITAL_CONSONANTS = (
    "Tazama video zinavyoonesha jinsi ya kuandika herufi kubwa za konsonanti. "
    "Kisha andika herufi hizo kwa kufuata hatua zake / doti zake."
)


# text_id: (PDF/HTML page number, approved visible and accessible wording)
EXPANSIONS: dict[str, tuple[int, str]] = {
    # Front matter and pre-writing exercises.
    "pg006_n0016": (6, "4. Kumudu kuandika kwa kutumia vifaa vya brelli."),
    "pg007_n0008": (
        7,
        "Chora michoro hii/Chora michoro hii  kwa kutumia vifaa vya brielli.",
    ),
    "pg008_n0005": (
        8,
        "Fuatisha michoro hii / kwa kutumia kifaa cha kuchorea (Spar wheel), "
        "fuatisha michoro hii.",
    ),
    "pg009_n0002": (
        9,
        "Chora picha hizi kwa kutumia kifaa cha brelli. Chora picha hizi.",
    ),
    "pg010_n0005": (
        10,
        "Fuatisha michoro hii / kwa kutumia kifaa cha kuchorea (Spar wheel), "
        "fuatisha michoro hii.",
    ),
    "pg010_n0006": (
        10,
        "Chora michoro hii/Chora michoro hii  kwa kutumia vifaa vya brielli.",
    ),

    # Lowercase vowels and consonants.
    "pg011_n0014": (11, SPAR_WHEEL),
    "pg011_n0016": (
        11,
        "Fuatisha herufi ya irabu a kwa kuandika doti ya kwanza kwa kurudia "
        "na ujaze mstari.",
    ),
    "pg011_n0028": (
        11,
        "Andika herufi ya irabu a. Andika doti ya kwanza kwa kurudiarudia "
        "na ujaze mstari.",
    ),
    "pg012_n0005": (12, SPAR_WHEEL),
    "pg012_n0034": (12, SPAR_WHEEL),
    "pg012_n0009": (
        12,
        "Fuatisha herufi ya irabu e kwa kuandika doti ya kwanza na doti ya tano "
        "kwa nafasi na ujaze mstari.",
    ),
    "pg012_n0021": (
        12,
        "Andika herufi ya irabu e. Andika doti ya kwanza na doti ya tano kwa "
        "nafasi na ujaze mstari.",
    ),
    "pg013_n0007": (
        13,
        "Andika herufi ya irabu i. Andika doti ya pili na doti ya nne kwa "
        "nafasi na ujaze mstari.",
    ),
    "pg013_n0018": (
        13,
        "Andika herufi ya irabu o. Andika doti ya kwanza, doti ya tatu na "
        "doti ya tano kwa nafasi na ujaze mstari.",
    ),
    "pg013_n0028": (13, SPAR_WHEEL),
    "pg014_n0006": (14, SPAR_WHEEL),
    "pg016_n0006": (16, VIDEO_IRABU),
    "pg017_n0013": (17, SPAR_WHEEL),
    "pg017_n0014": (17, trace_instruction("ya konsonanti", "b", 1, 2)),
    "pg017_n0025": (
        17,
        "Andika herufi ya konsonanti b. Andika doti ya kwanza na doti ya pili "
        "kwa nafasi na ujaze mstari.",
    ),
    "pg019_n0008": (19, SPAR_WHEEL),
    "pg019_n0010": (19, trace_instruction("ya konsonanti", "m", 1, 3, 4)),
    "pg020_n0030": (20, SPAR_WHEEL),
    "pg021_n0002": (21, trace_instruction("ya konsonanti", "k", 1, 3)),
    "pg021_n0008": (21, write_instruction("ya konsonanti", "k", 1, 3)),
    "pg022_n0019": (22, SPAR_WHEEL),
    "pg022_n0021": (22, trace_instruction("ya konsonanti", "d", 1, 4, 5)),
    "pg023_n0002": (23, write_instruction("ya konsonanti", "d", 1, 4, 5)),
    "pg024_n0015": (24, SPAR_WHEEL),
    "pg024_n0018": (24, trace_instruction("ya konsonanti", "n", 1, 3, 4, 5)),
    "pg024_n0031": (24, write_instruction("ya konsonanti", "n", 1, 3, 4, 5)),
    "pg027_n0008": (27, SPAR_WHEEL),
    "pg027_n0009": (27, trace_instruction("ya konsonanti", "l", 1, 2, 3)),
    "pg027_n0018": (27, write_instruction("ya konsonanti", "l", 1, 2, 3)),
    "pg029_n0006": (29, trace_instruction("ya konsonanti", "t", 2, 3, 4, 5)),
    "pg029_n0011": (29, write_instruction("ya konsonanti", "t", 2, 3, 4, 5)),
    "pg030_n0026": (30, SPAR_WHEEL),
    "pg031_n0002": (31, trace_instruction("ya konsonanti", "p", 1, 2, 3, 4)),
    "pg031_n0006": (31, write_instruction("ya konsonanti", "p", 1, 2, 3, 4)),
    "pg032_n0025": (32, SPAR_WHEEL),
    "pg033_n0002": (33, trace_instruction("ya konsonanti", "s", 2, 3, 4)),
    "pg033_n0012": (33, write_instruction("ya konsonanti", "s", 2, 3, 4)),
    "pg034_n0020": (34, trace_instruction("ya konsonanti", "j", 2, 4, 5)),
    "pg034_n0031": (34, write_instruction("ya konsonanti", "j", 2, 4, 5)),
    "pg037_n0018": (37, trace_instruction("ya konsonanti", "f", 1, 2, 4)),
    "pg037_n0029": (37, write_instruction("ya konsonanti", "f", 1, 2, 4)),
    "pg039_n0005": (39, trace_instruction("ya konsonanti", "g", 1, 2, 4, 5)),
    "pg039_n0018": (39, write_instruction("ya konsonanti", "g", 1, 2, 4, 5)),
    "pg040_n0032": (40, trace_instruction("ya konsonanti", "y", 1, 3, 4, 5, 6)),
    "pg041_n0002": (41, write_instruction("ya konsonanti", "y", 1, 3, 4, 5, 6)),
    "pg042_n0015": (42, trace_instruction("ya konsonanti", "z", 1, 3, 5, 6)),
    "pg042_n0020": (42, write_instruction("ya konsonanti", "z", 1, 3, 5, 6)),
    "pg044_n0005": (44, trace_instruction("ya konsonanti", "h", 1, 2, 5)),
    "pg044_n0011": (44, write_instruction("ya konsonanti", "h", 1, 2, 5)),
    "pg047_n0013": (47, trace_instruction("ya konsonanti", "r", 1, 2, 3, 5)),
    "pg047_n0020": (47, write_instruction("ya konsonanti", "r", 1, 2, 3, 5)),
    "pg049_n0006": (49, SPAR_WHEEL),
    "pg049_n0009": (49, trace_instruction("ya konsonanti", "w", 2, 4, 5, 6)),
    "pg049_n0023": (49, write_instruction("ya konsonanti", "w", 2, 4, 5, 6)),
    "pg050_n0014": (50, trace_instruction("ya konsonanti", "v", 1, 2, 3, 6)),
    "pg050_n0019": (50, write_instruction("ya konsonanti", "v", 1, 2, 3, 6)),
    "pg052_n0005": (52, trace_instruction("ya konsonanti", "ch", 1, 4, 1, 2, 5)),
    "pg052_n0013": (52, write_instruction("ya konsonanti", "ch", 1, 4, 1, 2, 5)),
    "pg054_n0005": (54, VIDEO_SMALL_CONSONANTS),
    "pg054_im002_crop1": (
        54,
        "Sungura akielekeza: " + VIDEO_SMALL_CONSONANTS,
    ),

    # Uppercase vowels and consonants.
    "pg055_n0007": (55, trace_instruction("ya irabu", "A", 6, 1)),
    "pg055_n0009": (
        55,
        write_instruction("ya irabu", "A", 6, 1)
        + " Andika herufi kubwa A ikifuatiwa na herufi ndogo a kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg057_n0005": (57, trace_instruction("ya irabu", "E", 6, 1, 5)),
    "pg057_n0011": (
        57,
        write_instruction("ya irabu", "E", 6, 1, 5)
        + " Andika herufi kubwa E ikifuatiwa na herufi ndogo e kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg058_n0018": (58, trace_instruction("ya irabu", "I", 6, 2, 4)),
    "pg060_n0004": (60, trace_instruction("ya irabu", "O", 6, 1, 3, 5)),
    "pg060_n0011": (
        60,
        write_instruction("ya irabu", "O", 6, 1, 3, 5)
        + " Andika herufi kubwa O ikifuatiwa na herufi ndogo o kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg061_n0023": (61, trace_instruction("ya irabu", "U", 6, 1, 3, 6)),
    "pg061_n0031": (
        61,
        write_instruction("ya irabu", "U", 6, 1, 3, 6)
        + " Andika herufi kubwa U ikifuatiwa na herufi ndogo u kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg063_n0013": (63, trace_instruction("ya konsonanti", "B", 6, 1, 2)),
    "pg063_n0023": (
        63,
        write_instruction("ya konsonanti", "B", 6, 1, 2)
        + " Andika herufi kubwa B ikifuatiwa na herufi ndogo b kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg065_n0005": (65, trace_instruction("ya konsonanti", "M", 6, 1, 3, 4)),
    "pg065_n0016": (
        65,
        write_instruction("ya konsonanti", "M", 6, 1, 3, 4)
        + " Andika herufi kubwa M ikifuatiwa na herufi ndogo m kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg066_n0032": (66, trace_instruction("ya konsonanti", "K", 6, 1, 3)),
    "pg066_n0037": (
        66,
        write_instruction("ya konsonanti", "K", 6, 1, 3)
        + " Andika herufi kubwa K ikifuatiwa na herufi ndogo k kwa pamoja "
        "kisha, andika tena herufi hizo kwa nafasi na ujaze mstari.",
    ),
    "pg068_n0005": (68, trace_instruction("ya konsonanti", "D", 6, 1, 4, 5)),
    "pg069_n0019": (69, trace_instruction("ya konsonanti", "N", 6, 1, 4, 5)),
    "pg070_n0002": (70, write_instruction("ya konsonanti", "N", 6, 1, 4, 5)),
    "pg072_n0015": (72, trace_instruction("ya konsonanti", "L", 6, 1, 2, 3)),
    "pg074_n0005": (74, trace_instruction("ya konsonanti", "T", 6, 2, 3, 4, 5)),
    "pg075_n0023": (75, trace_instruction("ya konsonanti", "P", 6, 1, 2, 3, 4)),
    "pg076_n0002": (76, write_instruction("ya konsonanti", "P", 6, 1, 2, 3, 4)),
    "pg077_n0013": (77, trace_instruction("ya konsonanti", "S", 6, 2, 3, 4)),
    "pg077_n0017": (77, write_instruction("ya konsonanti", "S", 6, 2, 3, 4)),
    "pg079_n0005": (79, trace_instruction("ya konsonanti", "J", 6, 2, 4, 5)),
    "pg079_n0010": (79, write_instruction("ya konsonanti", "J", 6, 2, 4, 5)),
    "pg081_n0013": (81, trace_instruction("ya konsonanti", "F", 6, 1, 2, 4)),
    "pg081_n0023": (81, write_instruction("ya konsonanti", "F", 6, 1, 2, 4)),
    "pg082_n0029": (82, trace_instruction("ya konsonanti", "G", 6, 1, 2, 4, 5)),
    "pg083_n0002": (83, write_instruction("ya konsonanti", "G", 6, 1, 2, 4, 5)),
    "pg084_n0022": (84, trace_instruction("ya konsonanti", "Y", 6, 1, 3, 4, 5, 6)),
    "pg084_n0027": (84, write_instruction("ya konsonanti", "Y", 6, 1, 3, 4, 5, 6)),
    "pg086_n0006": (86, trace_instruction("ya konsonanti", "Z", 6, 1, 3, 5, 6)),
    "pg086_n0011": (86, write_instruction("ya konsonanti", "Z", 6, 1, 3, 5, 6)),
    "pg087_n0016": (87, trace_instruction("ya konsonanti", "H", 6, 1, 2, 5)),
    "pg088_n0002": (88, write_instruction("ya konsonanti", "H", 6, 1, 2, 5)),
    "pg090_n0012": (90, trace_instruction("ya konsonanti", "R", 6, 1, 2, 3, 5)),
    "pg090_n0022": (90, write_instruction("ya konsonanti", "R", 6, 1, 2, 3, 5)),
    "pg092_n0004": (92, trace_instruction("ya konsonanti", "W", 6, 2, 4, 5, 6)),
    "pg092_n0011": (92, write_instruction("ya konsonanti", "W", 6, 2, 4, 5, 6)),
    "pg093_n0027": (93, trace_instruction("ya konsonanti", "V", 6, 1, 2, 3, 6)),
    "pg094_n0002": (94, write_instruction("ya konsonanti", "V", 6, 1, 2, 3, 6)),
    "pg095_n0021": (95, trace_instruction("ya konsonanti", "CH", 6, 6, 1, 4, 1, 2, 5)),
    "pg095_n0031": (95, write_instruction("ya konsonanti", "CH", 6, 6, 1, 4, 1, 2, 5)),
    "pg097_n0016": (97, VIDEO_CAPITAL_CONSONANTS),

    # Joined letters.  Obvious review-document slips are resolved by the
    # heading: ny keeps n's dots, and nd never changes to mb.
    "pg098_n0016": (98, blend_trace("sh", 2, 3, 4, 1, 2, 5)),
    "pg098_n0018": (98, blend_write("sh", 2, 3, 4, 1, 2, 5)),
    "pg100_n0022": (100, blend_trace("th", 2, 3, 4, 5, 1, 2, 5)),
    "pg101_n0002": (101, blend_write("th", 2, 3, 4, 5, 1, 2, 5)),
    "pg102_n0013": (102, blend_trace("mb", 1, 3, 4, 1, 2)),
    "pg102_n0015": (102, blend_write("mb", 1, 3, 4, 1, 2)),
    "pg104_n0028": (104, blend_trace("ny", 1, 3, 4, 5, 1, 3, 4, 5, 6)),
    "pg104_n0035": (104, blend_write("ny", 1, 3, 4, 5, 1, 3, 4, 5, 6)),
    "pg106_n0031": (106, blend_trace("ng", 1, 3, 4, 5, 1, 2, 4, 5)),
    "pg107_n0002": (107, blend_write("ng", 1, 3, 4, 5, 1, 2, 4, 5)),
    "pg109_n0005": (109, blend_trace("nd", 1, 3, 4, 5, 1, 4, 5)),
    "pg109_n0011": (109, blend_write("nd", 1, 3, 4, 5, 1, 4, 5)),
    "pg111_n0003": (111, blend_trace("kw", 1, 3, 2, 4, 5, 6)),
    "pg111_n0010": (111, blend_write("kw", 1, 3, 2, 4, 5, 6)),
    "pg113_n0005": (113, blend_trace("mw", 1, 3, 4, 2, 4, 5, 6)),
    "pg113_n0011": (113, blend_write("mw", 1, 3, 4, 2, 4, 5, 6)),
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


def replace_image_alt(source: str, text_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<img\b[^>]*\bdata-id="{re.escape(text_id)}"[^>]*\balt=")[^"]*(")'
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + html_module.escape(value, quote=True) + match.group(2),
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Expected one image for {text_id}, found {count}")
    return updated


def add_braille_objective() -> None:
    path = ROOT / "pg006_sec001.html"
    source = path.read_text(encoding="utf-8")
    if 'data-id="pg006_n0016"' in source:
        return
    marker = '<div class="block"><span data-id="pg006_n0015">3. Kutumia kanuni za uandishi.</span></div>'
    insertion = marker + '\n          <div class="block"><span data-id="pg006_n0016">4. Kumudu kuandika kwa kutumia vifaa vya brelli.</span></div>'
    if marker not in source:
        raise RuntimeError("Could not locate the introduction objective list")
    path.write_text(source.replace(marker, insertion, 1), encoding="utf-8")


def repair_page111_ids() -> None:
    """Give the kw lesson its own IDs instead of reusing page 108's IDs."""
    path = ROOT / "pg111_sec001.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace('data-section-id="pg108_sec001"', 'data-section-id="pg111_sec001"')
    source = source.replace('data-id="pg108_', 'data-id="pg111_')
    path.write_text(source, encoding="utf-8")


def inline_texts(path: Path, prefix: str) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf'<(?P<tag>[A-Za-z][A-Za-z0-9]*)\b[^>]*\bdata-id="(?P<id>{re.escape(prefix)}[^"]+)"[^>]*>(?P<value>.*?)</(?P=tag)>',
        re.DOTALL,
    )
    values: dict[str, str] = {}
    for match in pattern.finditer(source):
        value = re.sub(r"<[^>]+>", "", match.group("value"))
        value = html_module.unescape(re.sub(r"\s+", " ", value).strip())
        values[match.group("id")] = value
    return values


def update_html() -> None:
    add_braille_objective()
    repair_page111_ids()
    for text_id, (page_number, value) in EXPANSIONS.items():
        path = ROOT / f"pg{page_number:03d}_sec001.html"
        source = path.read_text(encoding="utf-8")
        updated = (
            replace_image_alt(source, text_id, value)
            if "_im" in text_id
            else replace_data_id_text(source, text_id, value)
        )
        path.write_text(updated, encoding="utf-8")


def update_texts() -> None:
    repaired_pages = {}
    repaired_pages.update(inline_texts(ROOT / "pg108_sec001.html", "pg108_"))
    repaired_pages.update(inline_texts(ROOT / "pg111_sec001.html", "pg111_"))

    for language in ("sw", "sw-TZ"):
        path = ROOT / "content" / "i18n" / language / "texts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for text_id, (_, value) in EXPANSIONS.items():
            data[text_id] = value
            easy_read_id = f"{text_id}_easy_read"
            if easy_read_id in data or text_id.startswith("pg111_"):
                data[easy_read_id] = value
        for text_id, value in repaired_pages.items():
            data[text_id] = value
            data[f"{text_id}_easy_read"] = value
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    update_html()
    update_texts()
    print(f"Applied {len(EXPANSIONS)} reviewed text corrections and repaired page 111 IDs")


if __name__ == "__main__":
    main()
