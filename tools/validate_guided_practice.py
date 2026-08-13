#!/usr/bin/env python3
"""Validate the PDF-aligned guided-practice installation across the book."""

from __future__ import annotations

import json
import re
from pathlib import Path

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / "content" / "guided-practice-layout.json"
INSTRUCTION_RE = re.compile(
    r"\b(?:Chora|Fuatisha|Andika|Nakili|Jaza|Tunga|Panga|Unganisha|"
    r"Kamilisha|Oanisha|Taja)\b",
    re.IGNORECASE,
)


def clean(value: str) -> str:
    return " ".join(value.split())


def semantic_prompts(path: Path) -> list[str]:
    tree = html.fromstring(path.read_text(encoding="utf-8"))
    prompts: list[str] = []
    for element in tree.xpath('//*[@data-id and not(self::img)]'):
        text = clean("".join(element.itertext()))
        if 2 < len(text) <= 480 and INSTRUCTION_RE.search(text):
            prompts.append(text)
    return prompts


def validate() -> tuple[int, int]:
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
    expected_pages = {f"pg{number:03}_sec001" for number in range(7, 121)}
    if set(layout) != expected_pages:
        missing = sorted(expected_pages - set(layout))
        unexpected = sorted(set(layout) - expected_pages)
        raise AssertionError(f"layout pages differ: missing={missing}, unexpected={unexpected}")

    entry_count = 0
    for page_id, page_layout in layout.items():
        page_path = ROOT / f"{page_id}.html"
        prompts = semantic_prompts(page_path)
        entries = page_layout["entries"]
        footer_start = int(page_layout["footerStart"])
        seen_dom_indices: set[int] = set()
        previous_top = -1

        if not entries:
            raise AssertionError(f"{page_id}: no guided-practice entries")

        for entry in entries:
            start = int(entry["start"])
            top = int(entry["top"])
            end = int(entry["end"])
            if not (0 <= start <= top < end <= footer_start <= 1280):
                raise AssertionError(
                    f"{page_id}: invalid source band {start=}, {top=}, {end=}, {footer_start=}"
                )
            if top < previous_top:
                raise AssertionError(f"{page_id}: entries are not in source-page order")
            previous_top = top

            dom_index = entry["domIndex"]
            if dom_index is None:
                continue
            dom_index = int(dom_index)
            if dom_index in seen_dom_indices:
                raise AssertionError(f"{page_id}: duplicate domIndex {dom_index}")
            if not 0 <= dom_index < len(prompts):
                raise AssertionError(f"{page_id}: invalid domIndex {dom_index}")
            if clean(entry["text"]) != prompts[dom_index]:
                raise AssertionError(
                    f"{page_id}: prompt mismatch at domIndex {dom_index}: "
                    f"{entry['text']!r} != {prompts[dom_index]!r}"
                )
            seen_dom_indices.add(dom_index)

        expected_dom_indices = set(range(len(prompts)))
        if seen_dom_indices != expected_dom_indices:
            missing = sorted(expected_dom_indices - seen_dom_indices)
            raise AssertionError(f"{page_id}: semantic prompts missing from layout: {missing}")
        for current, following in zip(entries, entries[1:]):
            if int(following["start"]) < int(current["end"]):
                raise AssertionError(
                    f"{page_id}: source exercise blocks overlap between "
                    f"{current['text']!r} and {following['text']!r}"
                )
        entry_count += len(entries)

    source_pages = [ROOT / "index.html", *sorted(ROOT.glob("pg???_sec001.html"))]
    source_pages = [path for path in source_pages if "source-facsimile-page" in path.read_text(encoding="utf-8")]
    if len(source_pages) != 120:
        raise AssertionError(f"expected 120 source-facsimile pages, found {len(source_pages)}")
    for path in source_pages:
        source = path.read_text(encoding="utf-8")
        required_assets = (
            'source-facsimile.css?v=7',
            'page-ink.js?v=3',
            'guided-practice.css?v=13',
            'guided-practice.js?v=13',
        )
        if any(asset not in source for asset in required_assets):
            raise AssertionError(f"{path.name}: cropped-page assets are missing")

    preloader = (ROOT / "assets" / "offline-preloader.js").read_text(encoding="utf-8")
    for required in (
        "./assets/guided-practice.css",
        "./assets/guided-practice.js",
        "./content/guided-practice-layout.json",
    ):
        if required not in preloader:
            raise AssertionError(f"offline preloader is missing {required}")

    return len(layout), entry_count


if __name__ == "__main__":
    page_count, prompt_count = validate()
    print(f"Validated {prompt_count} guided prompts across {page_count} source pages")
