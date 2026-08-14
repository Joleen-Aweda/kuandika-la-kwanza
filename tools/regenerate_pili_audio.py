#!/usr/bin/env python3
"""Regenerate tracks that must distinguish "pili" from "mbili" and 2."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from pathlib import Path

import edge_tts

from generate_sw_tz_audio import PITCH, RATE, VOICE, spoken_text


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("sw", "sw-TZ")
PILI_PATTERN = re.compile(r"\bpili\b", flags=re.IGNORECASE)
MBILI_PATTERN = re.compile(r"\bmbili\b", flags=re.IGNORECASE)
TWO_PATTERN = re.compile(r"(?<![\w-])2(?![\w-])")


async def main(args: argparse.Namespace) -> None:
    source = ROOT / "content/i18n/sw-TZ"
    texts = json.loads((source / "texts.json").read_text(encoding="utf-8"))
    mappings = json.loads((source / "audios.json").read_text(encoding="utf-8"))
    overrides = json.loads(
        (ROOT / "tools/sw_tz_pronunciation_overrides.json").read_text(encoding="utf-8")
    )
    keys = sorted(
        key
        for key, value in texts.items()
        if PILI_PATTERN.search(str(value))
        or MBILI_PATTERN.search(str(value))
        or TWO_PATTERN.search(str(value))
    )

    for key in keys:
        mappings.setdefault(key, f"{key}.mp3")
    for language in LANGUAGES:
        mapping_path = ROOT / "content/i18n" / language / "audios.json"
        mapping_path.write_text(
            json.dumps(mappings, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    cache = args.cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.workers)

    async def generate(key: str) -> None:
        visible = str(texts[key])
        spoken = spoken_text(key, visible, overrides)
        visible_pili = len(PILI_PATTERN.findall(visible))
        visible_mbili = len(MBILI_PATTERN.findall(visible))
        visible_twos = len(TWO_PATTERN.findall(visible))
        if spoken.lower().count("pi-li") != visible_pili:
            raise RuntimeError(f"pili override mismatch in {key}: {spoken}")
        if spoken.lower().count("mbili") < visible_mbili + visible_twos:
            raise RuntimeError(f"mbili/2 override mismatch in {key}: {spoken}")
        output = cache / mappings[key]
        temporary = output.with_suffix(".tmp")
        async with semaphore:
            await edge_tts.Communicate(
                spoken,
                VOICE,
                rate=RATE,
                pitch=PITCH,
            ).save(str(temporary))
        if temporary.stat().st_size < 300:
            raise RuntimeError(f"invalid audio for {key}")
        temporary.replace(output)

    await asyncio.gather(*(generate(key) for key in keys))

    for language in LANGUAGES:
        target = ROOT / "content/i18n" / language / "audio"
        for key in keys:
            shutil.copyfile(cache / mappings[key], target / mappings[key])

    print(f"Installed {len(keys)} corrected pili/mbili/2 tracks in sw and sw-TZ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/private/tmp/kuandika-pili-rehema"),
    )
    parser.add_argument("--workers", type=int, default=4)
    asyncio.run(main(parser.parse_args()))
