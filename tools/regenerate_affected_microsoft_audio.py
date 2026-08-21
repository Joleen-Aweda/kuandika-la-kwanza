#!/usr/bin/env python3
"""Regenerate corrected Kuandika tracks with Tanzanian Rehema speech."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

import edge_tts

from generate_sw_tz_audio import spoken_text
from apply_instruction_expansions import EXPANSIONS


ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
RATE = "-5%"
EXPLICIT_KEYS = {
    "pg016_n0006", "pg016_n0006_easy_read",
    "pg001_n0004", "pg001_n0004_easy_read",
    "pg001_n0011", "pg001_n0011_easy_read",
    "pg001_n0015", "pg001_n0015_easy_read",
    "pg001_n0004", "pg001_n0011", "pg001_n0015",
    "pg003_n0013", "pg003_n0016", "pg003_n0019", "pg003_n0022",
    "pg003_n0025", "pg003_n0028",
    "pg004_n0005", "pg004_n0009", "pg004_n0013", "pg004_n0017",
    "pg004_n0021",
    "pg009_im001_crop_v1", "pg009_im002_crop_v1", "pg009_im006_crop1",
    "pg009_im003_crop1", "pg009_im007_crop_v1", "pg009_im009_crop1",
    "pg011_n0013",
}


async def main(args: argparse.Namespace) -> None:
    source = ROOT / "content/i18n/sw-TZ"
    texts = json.loads((source / "texts.json").read_text(encoding="utf-8"))
    mappings = json.loads((source / "audios.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "tools/sw_tz_pronunciation_overrides.json").read_text(encoding="utf-8"))
    keys = set() if (
        args.exercise_ordinals or args.image_descriptions or args.lesson_ordinals
    ) else set(EXPLICIT_KEYS)
    if args.all_reviewed:
        keys.update(EXPANSIONS)
        keys.update(
            f"{key}_easy_read"
            for key in EXPANSIONS
            if f"{key}_easy_read" in texts
        )
    if args.all_pages:
        page_keys: list[str] = []
        for html_path in sorted(ROOT.glob("pg*_sec*.html")):
            html_source = html_path.read_text(encoding="utf-8")
            page_keys.extend(re.findall(r'data-id=["\']([^"\']+)', html_source))
        keys.update(
            key for key in page_keys
            if key in texts and key in mappings and str(texts[key]).strip()
        )
        keys.update(
            f"{key}_easy_read" for key in page_keys
            if f"{key}_easy_read" in texts
            and f"{key}_easy_read" in mappings
            and str(texts[f"{key}_easy_read"]).strip()
        )
    if args.exercise_ordinals:
        keys.update(
            key for key, value in texts.items()
            if re.fullmatch(
                r"Zoezi la (?:kwanza|pili|tatu|nne|tano|sita|saba|nane|tisa|kumi)",
                str(value).strip(),
                flags=re.IGNORECASE,
            )
            and key in mappings
        )
    if args.image_descriptions:
        weak_image_ids = {
            "pg020_im002", "pg022_im003", "pg028_im001",
            "pg030_im002", "pg035_im003", "pg041_im001",
        }
        keys.update(
            key for key in texts
            if (key.endswith("_page_image") or key in weak_image_ids
                or key.removesuffix("_easy_read") in weak_image_ids)
            and key in mappings
            and str(texts[key]).strip()
        )
    if args.lesson_ordinals:
        keys.update(
            key for key, value in texts.items()
            if (
                re.fullmatch(
                    r"Somo la (?:kwanza|pili|tatu|nne|tano|sita|saba|nane|tisa|kumi)",
                    str(value).strip(),
                    flags=re.IGNORECASE,
                )
                or key in {"pg045_n0009", "pg045_n0009_easy_read"}
            )
            and key in mappings
        )
    if not args.exercise_ordinals and not args.image_descriptions and not args.lesson_ordinals:
        keys.update(
            key for key, value in texts.items()
            if re.fullmatch(r"([A-Za-z])\1{2,}", str(value).strip(), flags=re.IGNORECASE)
        )

    cache = args.cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.workers)

    keys_by_filename: dict[str, list[str]] = defaultdict(list)
    for key in sorted(keys):
        keys_by_filename[mappings[key]].append(key)

    filenames_by_speech: dict[str, list[str]] = defaultdict(list)
    key_by_speech: dict[str, str] = {}
    for filename, filename_keys in sorted(keys_by_filename.items()):
        key = filename_keys[0]
        speech = spoken_text(key, str(texts[key]), overrides)
        filenames_by_speech[speech].append(filename)
        key_by_speech.setdefault(speech, key)

    async def generate(speech: str, filenames: list[str]) -> None:
        key = key_by_speech[speech]
        output = cache / filenames[0]
        if not output.exists() or output.stat().st_size < 300:
          async with semaphore:
            for attempt in range(5):
                temporary = output.with_suffix(".tmp")
                temporary.unlink(missing_ok=True)
                try:
                    await edge_tts.Communicate(
                        speech, VOICE, rate=RATE
                    ).save(str(temporary))
                    if temporary.stat().st_size < 300:
                        raise RuntimeError(f"invalid audio for {key}")
                    temporary.replace(output)
                    break
                except Exception:
                    temporary.unlink(missing_ok=True)
                    if attempt == 4:
                        raise
                    await asyncio.sleep(1.5 * (attempt + 1))
        for alias in filenames[1:]:
            shutil.copyfile(output, cache / alias)

    await asyncio.gather(*(
        generate(speech, filenames)
        for speech, filenames in sorted(filenames_by_speech.items())
    ))
    for language in ("sw", "sw-TZ"):
        target = ROOT / "content/i18n" / language / "audio"
        for filename in keys_by_filename:
            shutil.copyfile(cache / filename, target / filename)
    print(
        f"Installed {len(keys_by_filename)} Rehema audio files for "
        f"{len(keys)} page text IDs from {len(filenames_by_speech)} unique "
        "spoken strings in sw and sw-TZ"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/kuandika-corrected-rehema"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--all-reviewed",
        action="store_true",
        help="Regenerate every reviewed instruction and its easy-read track.",
    )
    parser.add_argument(
        "--all-pages",
        action="store_true",
        help="Regenerate every narrated text ID present on a book page.",
    )
    parser.add_argument(
        "--exercise-ordinals",
        action="store_true",
        help="Regenerate all exercise headings using ordinal wording.",
    )
    parser.add_argument(
        "--image-descriptions",
        action="store_true",
        help="Regenerate page-image and repaired embedded-image descriptions.",
    )
    parser.add_argument(
        "--lesson-ordinals",
        action="store_true",
        help="Regenerate ordinal lesson headings and page 45's word-count phrase.",
    )
    asyncio.run(main(parser.parse_args()))
