#!/usr/bin/env python3
"""Remove dedicated quiz pages and their reader assets from the ADT bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUIZ_ID = re.compile(r"^qz\d{3}")
LANGUAGES = ("sw", "sw-TZ")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def is_quiz(value: object) -> bool:
    return isinstance(value, str) and QUIZ_ID.match(value) is not None


def remove_manifest_entries() -> tuple[list[dict], set[str]]:
    path = ROOT / "content" / "pages.json"
    pages = read_json(path)
    quiz_ids = {
        entry["section_id"]
        for entry in pages
        if is_quiz(entry.get("section_id"))
    }
    pages = [
        entry
        for entry in pages
        if not is_quiz(entry.get("section_id"))
        and not is_quiz(Path(entry.get("href", "")).stem)
    ]
    write_json(path, pages)

    toc_path = ROOT / "content" / "toc.json"
    toc = read_json(toc_path)
    if isinstance(toc, list):
        toc = [
            entry
            for entry in toc
            if not is_quiz(entry.get("section_id"))
            and not is_quiz(Path(entry.get("href", "")).stem)
        ]
        write_json(toc_path, toc)

    return pages, quiz_ids


def renumber_pages(pages: list[dict]) -> None:
    for index, entry in enumerate(pages, start=1):
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        updated, count = re.subn(
            r'(<meta name="page-section-id" content=")\d+("\s*/>)',
            rf"\g<1>{index}\2",
            source,
            count=1,
        )
        if count != 1:
            raise RuntimeError(f"Could not update page-section-id in {path.name}")
        if updated != source:
            path.write_text(updated, encoding="utf-8")


def remove_language_assets(language: str) -> tuple[int, int]:
    base = ROOT / "content" / "i18n" / language
    audios_path = base / "audios.json"
    audios = read_json(audios_path)
    quiz_audio_files = {
        filename
        for text_id, filename in audios.items()
        if is_quiz(text_id) and isinstance(filename, str)
    }
    audios = {key: value for key, value in audios.items() if not is_quiz(key)}
    write_json(audios_path, audios)

    removed_texts = 0
    for relative in (
        "texts.json",
        "images.json",
        "videos.json",
        "timecode/timecode_output.json",
    ):
        path = base / relative
        if not path.exists():
            continue
        value = read_json(path)
        if not isinstance(value, dict):
            continue
        before = len(value)
        value = {key: item for key, item in value.items() if not is_quiz(key)}
        removed_texts += before - len(value)
        write_json(path, value)

    removed_audio = 0
    audio_dir = base / "audio"
    for filename in sorted(quiz_audio_files):
        if not QUIZ_ID.match(Path(filename).stem):
            continue
        path = audio_dir / filename
        if path.exists():
            path.unlink()
            removed_audio += 1
    return removed_texts, removed_audio


def remove_quiz_html() -> int:
    removed = 0
    for path in sorted(ROOT.glob("qz[0-9][0-9][0-9].html")):
        path.unlink()
        removed += 1
    return removed


def main() -> None:
    pages, quiz_ids = remove_manifest_entries()
    renumber_pages(pages)
    removed_texts = 0
    removed_audio = 0
    for language in LANGUAGES:
        text_count, audio_count = remove_language_assets(language)
        removed_texts += text_count
        removed_audio += audio_count
    removed_html = remove_quiz_html()
    print(
        f"Removed {len(quiz_ids)} quiz entries, {removed_html} quiz pages, "
        f"{removed_texts} localized quiz strings, and {removed_audio} quiz audio files"
    )


if __name__ == "__main__":
    main()
