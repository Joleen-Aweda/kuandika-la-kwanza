#!/usr/bin/env python3
"""Validate the source-faithful reader after answer areas are removed."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    pages = [ROOT / "index.html", *sorted(ROOT.glob("pg???_sec001.html"))]
    source_pages = [
        path
        for path in pages
        if "source-facsimile-page" in path.read_text(encoding="utf-8")
    ]
    if len(source_pages) != 120:
        raise AssertionError(f"expected 120 source pages, found {len(source_pages)}")

    forbidden = (
        "guided-practice",
        "page-ink.css",
        "page-ink.js",
        "writing-practice",
        "Sehemu ya jibu",
    )
    required = (
        "source-facsimile.css?v=12",
        "source-page.js?v=34",
        "offline-preloader.js?v=37",
    )
    for path in source_pages:
        source = path.read_text(encoding="utf-8")
        if any(value in source for value in forbidden):
            raise AssertionError(f"{path.name}: answer-area reference remains")
        if any(value not in source for value in required):
            raise AssertionError(f"{path.name}: source-page assets are incomplete")

    source_script = (ROOT / "assets" / "source-page.js").read_text(encoding="utf-8")
    if any(value in source_script for value in ("canvas", "textarea", "localStorage")):
        raise AssertionError("source-page.js still contains answer controls")

    preloader = (ROOT / "assets" / "offline-preloader.js").read_text(encoding="utf-8")
    if "guided-practice-layout" in preloader or "Sehemu ya jibu" in preloader:
        raise AssertionError("offline preloader still embeds answer-area data")

    pages = json.loads((ROOT / "content" / "pages.json").read_text(encoding="utf-8"))
    if len(pages) != 120 or any(item["section_id"].startswith("qz") for item in pages):
        raise AssertionError("dedicated quiz pages remain in the reading order")
    if list(ROOT.glob("qz[0-9][0-9][0-9].html")):
        raise AssertionError("dedicated quiz HTML files remain")
    for language in ("sw", "sw-TZ"):
        base = ROOT / "content" / "i18n" / language
        for name in ("texts.json", "audios.json"):
            data = json.loads((base / name).read_text(encoding="utf-8"))
            if any(key.startswith("qz") for key in data):
                raise AssertionError(f"{language}/{name}: quiz mapping remains")
        if list((base / "audio").glob("qz*.mp3")):
            raise AssertionError(f"{language}: quiz audio files remain")

    print(f"Validated {len(source_pages)} source pages without answer areas")


if __name__ == "__main__":
    main()
