#!/usr/bin/env python3
"""Synchronize converted page numbers and section indices."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    pages_path = ROOT / "content/pages.json"
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    pages = [item for item in pages if item.get("section_id") != "pg002_sec001"]
    pages.insert(1, {
        "section_id": "pg002_sec001",
        "href": "pg002_sec001.html",
        "page_number": 2,
    })

    for item in pages:
        match = re.fullmatch(r"pg(\d{3})_sec001", item.get("section_id", ""))
        if match:
            item["page_number"] = int(match.group(1))
        else:
            item.pop("page_number", None)
    write_json(pages_path, pages)

    toc_path = ROOT / "content/toc.json"
    toc = json.loads(toc_path.read_text(encoding="utf-8"))
    toc = [item for item in toc if item.get("section_id") != "pg002_sec001"]
    toc.insert(1, {
        "section_id": "pg002_sec001",
        "href": "pg002_sec001.html",
        "title": "Taarifa za uchapishaji",
        "chapter_id": "pg002_n0001",
        "level": 1,
    })
    write_json(toc_path, toc)

    for index, item in enumerate(pages, start=1):
        page = ROOT / item["href"]
        html = page.read_text(encoding="utf-8")
        updated, count = re.subn(
            r'(<meta name="page-section-id" content=")\d+("\s*/>)',
            rf"\g<1>{index}\2",
            html,
            count=1,
        )
        if count != 1:
            raise RuntimeError(f"Could not update page-section-id in {page.name}")
        if updated != html:
            page.write_text(updated, encoding="utf-8")

    print(f"Synchronized {len(pages)} reading-order entries")


if __name__ == "__main__":
    main()
