#!/usr/bin/env python3
"""Regenerate corrected Kuandika tracks with Tanzanian Rehema speech."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from pathlib import Path

import edge_tts

from generate_sw_tz_audio import spoken_text


ROOT = Path(__file__).resolve().parents[1]
VOICE = "sw-TZ-RehemaNeural"
RATE = "-5%"
EXPLICIT_KEYS = {
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
    keys = set(EXPLICIT_KEYS)
    keys.update(
        key for key, value in texts.items()
        if re.fullmatch(r"([A-Za-z])\1{2,}", str(value).strip(), flags=re.IGNORECASE)
    )

    cache = args.cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.workers)

    async def generate(key: str) -> None:
        speech = spoken_text(key, str(texts[key]), overrides)
        output = cache / mappings[key]
        async with semaphore:
            temporary = output.with_suffix(".tmp")
            await edge_tts.Communicate(speech, VOICE, rate=RATE).save(str(temporary))
            if temporary.stat().st_size < 300:
                raise RuntimeError(f"invalid audio for {key}")
            temporary.replace(output)

    await asyncio.gather(*(generate(key) for key in sorted(keys)))
    for language in ("sw", "sw-TZ"):
        target = ROOT / "content/i18n" / language / "audio"
        for key in keys:
            shutil.copyfile(cache / mappings[key], target / mappings[key])
    print(f"Installed {len(keys)} corrected Rehema tracks in sw and sw-TZ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/kuandika-corrected-rehema"))
    parser.add_argument("--workers", type=int, default=4)
    asyncio.run(main(parser.parse_args()))
