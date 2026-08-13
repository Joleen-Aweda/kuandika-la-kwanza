#!/usr/bin/env python3
"""Build source-page prompt positions for interleaved guided practice.

The visible textbook uses exact 930 x 1280 renders of the source PDF.  This
manifest aligns the semantic exercise prompts with their vertical positions in
the PDF so an answer card can replace the printed answer area immediately
below each prompt without rebuilding the rest of the page.
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import pdfplumber
from lxml import html


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = Path(
    "/Users/joleen/Desktop/KUANDIKA STD 1 PB/Kuandika Std 1 Final.pdf"
)
OUTPUT = ROOT / "content" / "guided-practice-layout.json"
IMAGE_HEIGHT = 1280
INSTRUCTION_RE = re.compile(
    r"\b(?:Chora|Fuatisha|Andika|Nakili|Jaza|Tunga|Panga|Unganisha|"
    r"Kamilisha|Oanisha|Taja)\b",
    re.IGNORECASE,
)


def clean(value: str) -> str:
    return " ".join(value.split())


def comparable(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, comparable(left), comparable(right)).ratio()


def semantic_prompts(page_number: int) -> list[str]:
    path = ROOT / f"pg{page_number:03}_sec001.html"
    tree = html.fromstring(path.read_text(encoding="utf-8"))
    prompts: list[str] = []
    for element in tree.xpath('//*[@data-id and not(self::img)]'):
        text = clean("".join(element.itertext()))
        if 2 < len(text) <= 480 and INSTRUCTION_RE.search(text):
            prompts.append(text)
    return prompts


def pdf_lines(page) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        placed = False
        for row in rows:
            if abs(float(row["top"]) - float(word["top"])) <= 2.2:
                row["words"].append(word)
                placed = True
                break
        if not placed:
            rows.append({"top": word["top"], "bottom": word["bottom"], "words": [word]})

    lines: list[dict[str, object]] = []
    for row in sorted(rows, key=lambda item: float(item["top"])):
        line_words = sorted(row["words"], key=lambda item: item["x0"])
        lines.append(
            {
                "top": float(row["top"]),
                "bottom": max(float(word["bottom"]) for word in line_words),
                "text": clean(" ".join(str(word["text"]) for word in line_words)),
            }
        )
    return lines


def source_prompts(lines: list[dict[str, object]], page_height: float) -> list[dict[str, object]]:
    prompts: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        text = str(line["text"])
        top = float(line["top"])
        if top >= page_height * 0.94 or not INSTRUCTION_RE.search(text):
            continue

        bottom = float(line["bottom"])
        combined = text
        # A prompt that does not end in punctuation commonly continues on the
        # following source line.  Include that line in the retained page band.
        if not re.search(r"[.:!?]$", text) and index + 1 < len(lines):
            following = lines[index + 1]
            gap = float(following["top"]) - bottom
            if 0 <= gap <= 12 and float(following["top"]) < page_height * 0.94:
                combined = clean(combined + " " + str(following["text"]))
                bottom = float(following["bottom"])

        prompts.append({"top": top, "bottom": bottom, "text": combined})
    return prompts


def match_prompts(dom: list[str], source: list[dict[str, object]]) -> dict[int, int]:
    """Greedily align semantic prompts to source prompts while preserving order."""

    matches: dict[int, int] = {}
    next_source = 0
    for dom_index, prompt in enumerate(dom):
        best_index = -1
        best_score = 0.0
        for source_index in range(next_source, len(source)):
            score = similarity(prompt, str(source[source_index]["text"]))
            if score > best_score:
                best_score = score
                best_index = source_index
        if best_index >= 0 and best_score >= 0.56:
            matches[dom_index] = best_index
            next_source = best_index + 1
    return matches


def footer_top(lines: list[dict[str, object]], page_height: float) -> float:
    candidates = [
        float(line["top"])
        for line in lines
        if "Final.indd" in str(line["text"]) or float(line["top"]) >= page_height * 0.965
    ]
    return min(candidates) if candidates else page_height * 0.965


def interpolate_unmatched(
    dom_count: int,
    source: list[dict[str, object]],
    matches: dict[int, int],
    footer: float,
) -> list[float]:
    assigned: list[float | None] = [None] * dom_count
    for dom_index, source_index in matches.items():
        assigned[dom_index] = float(source[source_index]["top"])

    matched_indices = sorted(matches)
    for dom_index in range(dom_count):
        if assigned[dom_index] is not None:
            continue
        previous = max((index for index in matched_indices if index < dom_index), default=None)
        following = min((index for index in matched_indices if index > dom_index), default=None)
        if previous is None and following is None:
            assigned[dom_index] = footer * (dom_index + 1) / (dom_count + 1)
        elif previous is None:
            high = float(assigned[following])
            assigned[dom_index] = high * (dom_index + 1) / (following + 1)
        elif following is None:
            low = float(assigned[previous])
            assigned[dom_index] = low + (footer - low) * (dom_index - previous) / (dom_count - previous)
        else:
            low = float(assigned[previous])
            high = float(assigned[following])
            assigned[dom_index] = low + (high - low) * (dom_index - previous) / (following - previous)

    return [float(value) for value in assigned]


def build_page(page_number: int, page) -> dict[str, object]:
    lines = pdf_lines(page)
    dom = semantic_prompts(page_number)
    source = source_prompts(lines, float(page.height))
    matches = match_prompts(dom, source)
    footer = footer_top(lines, float(page.height))
    dom_tops = interpolate_unmatched(len(dom), source, matches, footer)
    scale = IMAGE_HEIGHT / float(page.height)

    entries: list[dict[str, object]] = []
    matched_source = set(matches.values())
    for dom_index, text in enumerate(dom):
        source_index = matches.get(dom_index)
        top = dom_tops[dom_index]
        if source_index is not None:
            bottom = float(source[source_index]["bottom"])
        else:
            bottom = top + 22
        entries.append(
            {
                "domIndex": dom_index,
                "text": text,
                "top": round(top * scale),
                "end": round((bottom + 2) * scale),
            }
        )

    # Preserve source prompts omitted by the semantic conversion.  The reader
    # can still create a correctly labelled letter-writing card from the text.
    for source_index, prompt in enumerate(source):
        if source_index in matched_source:
            continue
        entries.append(
            {
                "domIndex": None,
                "text": str(prompt["text"]),
                "top": round(float(prompt["top"]) * scale),
                "end": round((float(prompt["bottom"]) + 2) * scale),
            }
        )

    entries.sort(key=lambda item: (int(item["top"]), item["domIndex"] is None))
    heading_re = re.compile(r"^(?:Somo|Zoezi|Ninaandika|Ninachora|Sura)\b", re.IGNORECASE)
    previous_end_points = 0.0
    for index, entry in enumerate(entries):
        top_points = float(entry["top"]) / scale
        if index == 0:
            start_points = 0.0
        else:
            nearby_headings = [
                float(line["top"])
                for line in lines
                if previous_end_points <= float(line["top"]) < top_points
                and top_points - float(line["top"]) <= 105
                and heading_re.search(str(line["text"]))
            ]
            start_points = (
                max(previous_end_points, min(nearby_headings) - 18)
                if nearby_headings
                else max(previous_end_points, top_points - 7)
            )
        entry["start"] = max(0, round(start_points * scale))
        previous_end_points = float(entry["end"]) / scale

    return {
        "footerStart": min(1270, max(0, round((footer - 8) * scale))),
        "entries": entries,
    }


def main() -> None:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(SOURCE_PDF)

    layout: dict[str, object] = {}
    with pdfplumber.open(SOURCE_PDF) as pdf:
        for page_number in range(7, 121):
            page_layout = build_page(page_number, pdf.pages[page_number - 1])
            if page_layout["entries"]:
                layout[f"pg{page_number:03}_sec001"] = page_layout

    OUTPUT.write_text(
        json.dumps(layout, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    entry_count = sum(len(page["entries"]) for page in layout.values())
    print(f"Wrote {entry_count} positioned prompts across {len(layout)} pages to {OUTPUT}")


if __name__ == "__main__":
    main()
