#!/usr/bin/env python3
"""Regenerate the Kuandika read-aloud corpus with Tanzanian Swahili speech.

Install the only external dependency with:
    python3 -m pip install edge-tts
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError as exc:  # pragma: no cover - environment setup guard
    raise SystemExit("Install edge-tts before running this tool") from exc


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LANG = "sw-TZ"
TARGET_LANGS = ("sw", "sw-TZ")
VOICE = "sw-TZ-RehemaNeural"
RATE = "-5%"
PITCH = "+0Hz"

NUMBER_WORDS = {
    0: "sifuri", 1: "moja", 2: "mbili", 3: "tatu", 4: "nne",
    5: "tano", 6: "sita", 7: "saba", 8: "nane", 9: "tisa",
    10: "kumi", 11: "kumi na moja", 12: "kumi na mbili",
}
LETTER_NAMES = {
    "b": "be", "m": "me", "k": "ke", "d": "de", "n": "ne",
    "l": "le", "t": "te", "p": "pe", "s": "se", "j": "je",
    "f": "fe", "g": "ge", "y": "ye", "z": "ze", "h": "he",
    "r": "re", "w": "we", "v": "ve", "ch": "che",
}
PUNCTUATION_NAMES = {
    ".": "nukta", ",": "koma", "?": "kiulizo", "!": "mshangao",
    "( . )": "nukta", "( , )": "koma", "( ? )": "kiulizo", "( ! )": "mshangao",
}


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def number_word(value: int) -> str:
    return NUMBER_WORDS.get(value, str(value))


def spoken_text(key: str, visible: str, overrides: dict[str, str]) -> str:
    """Return child-friendly Tanzanian Swahili speech without changing display text."""
    if key in overrides:
        return overrides[key]

    text = visible.strip()
    text = re.sub(r"\bPAH\b", "", text, flags=re.IGNORECASE)
    text = text.replace("2018", "mwaka elfu mbili na kumi na nane")
    text = text.replace("2016", "mwaka elfu mbili na kumi na sita")
    text = re.sub(r"https?://ol\.tie\.go\.tz|\bol\.tie\.go\.tz\b", "maktaba mtandao ya Taasisi ya Elimu Tanzania", text, flags=re.I)
    text = re.sub(r"_{3,}|\.{4,}|…{2,}|\[\[blank[^]]*\]\]", " ", text, flags=re.I)

    compact = re.sub(r"\s+", " ", text).strip()
    if compact in PUNCTUATION_NAMES:
        return PUNCTUATION_NAMES[compact]

    # Long handwriting-practice strings such as "eeeeeeee" are letters,
    # not words or sentences. Six clear repetitions are enough to model the
    # sound without producing an exhausting synthetic drone.
    repeated = re.fullmatch(r"([A-Za-z])\1{2,}", compact, flags=re.IGNORECASE)
    if repeated:
        letter = repeated.group(1).lower()
        pronunciation = LETTER_NAMES.get(letter, letter)
        return ", ".join([pronunciation] * min(len(compact), 6))

    letters_only = re.sub(r"[^A-Za-z]", "", compact).lower()
    if letters_only in {"a", "e", "i", "o", "u"} and len(compact) <= 3:
        return letters_only
    if letters_only in LETTER_NAMES and len(compact) <= 4:
        return LETTER_NAMES[letters_only]

    marker = re.match(r"^\s*(\d{1,2})[.)]\s*(.*)$", compact, re.S)
    if marker:
        number = int(marker.group(1))
        remainder = marker.group(2).strip()
        compact = f"Namba {number_word(number)}. {remainder}".strip()

    # A Tanzanian literacy lesson names isolated consonant graphemes with the
    # implicit vowel e. This remains separate from visible spelling.
    for grapheme in sorted(LETTER_NAMES, key=len, reverse=True):
        compact = re.sub(
            rf"(?<![A-Za-z]){re.escape(grapheme)}(?![A-Za-z])",
            LETTER_NAMES[grapheme],
            compact,
            flags=re.IGNORECASE,
        )

    # Speak symbol-only exercise answers by name instead of silence/noise.
    unique_symbols = set(re.sub(r"[\s()]", "", compact))
    if unique_symbols and unique_symbols <= set(".,?!"):
        names = [PUNCTUATION_NAMES[ch] for ch in re.sub(r"[^.,?!]", "", compact)]
        return ", ".join(names)

    return re.sub(r"\s+", " ", compact).strip(" ,")


async def render_track(text: str, output: Path, retries: int, timeout: int) -> None:
    temporary = output.with_suffix(output.suffix + ".tmp")
    for attempt in range(1, retries + 1):
        try:
            await asyncio.wait_for(
                edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(str(temporary)),
                timeout=timeout,
            )
            if not temporary.exists() or temporary.stat().st_size < 300:
                raise RuntimeError("speech service returned an invalid MP3")
            temporary.replace(output)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == retries:
                raise
            await asyncio.sleep(min(2 ** attempt, 8))


async def run(args: argparse.Namespace) -> None:
    source_root = ROOT / "content" / "i18n" / SOURCE_LANG
    texts = load_json(source_root / "texts.json")
    overrides = load_json(ROOT / "tools" / "sw_tz_pronunciation_overrides.json")
    mappings = load_json(source_root / "audios.json")

    for key, value in texts.items():
        if value.strip():
            mappings.setdefault(key, f"{key}.mp3")

    for lang in TARGET_LANGS:
        target_mapping = ROOT / "content" / "i18n" / lang / "audios.json"
        target_mapping.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jobs = []
    for key, filename in mappings.items():
        visible = texts.get(key, "")
        speech = spoken_text(key, visible, overrides)
        if speech:
            jobs.append((key, speech, filename))

    if args.key:
        selected = set(args.key)
        jobs = [job for job in jobs if job[0] in selected]
        missing_keys = selected - {job[0] for job in jobs}
        if missing_keys:
            raise SystemExit(f"Unknown or empty text IDs: {', '.join(sorted(missing_keys))}")
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"Selected {len(jobs)} Rehema tracks for {', '.join(TARGET_LANGS)}")
    if args.dry_run:
        for key, speech, filename in jobs[:100]:
            print(key, filename, "=>", speech)
        return

    semaphore = asyncio.Semaphore(args.workers)
    failures: list[tuple[str, str]] = []
    completed = 0

    async def guarded(job: tuple[str, str, str]) -> None:
        nonlocal completed
        key, speech, filename = job
        source_output = source_root / "audio" / filename
        try:
            async with semaphore:
                await render_track(speech, source_output, args.retries, args.timeout)
            for lang in TARGET_LANGS:
                if lang == SOURCE_LANG:
                    continue
                target = ROOT / "content" / "i18n" / lang / "audio" / filename
                shutil.copyfile(source_output, target)
            completed += 1
            if completed % 250 == 0:
                print(f"Completed {completed}/{len(jobs)}", flush=True)
        except Exception as exc:
            failures.append((key, str(exc)))

    await asyncio.gather(*(guarded(job) for job in jobs))
    print(f"Generated {completed} tracks; failures={len(failures)}")
    for key, error in failures[:50]:
        print(f"{key}: {error}", file=sys.stderr)
    if failures:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90, help="seconds allowed per synthesis attempt")
    parser.add_argument("--key", action="append", help="generate only this text ID (repeatable)")
    parser.add_argument("--limit", type=int, help="generate only the first N tracks for testing")
    parser.add_argument("--dry-run", action="store_true")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
