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
    13: "kumi na tatu", 14: "kumi na nne", 15: "kumi na tano",
    16: "kumi na sita", 17: "kumi na saba", 18: "kumi na nane",
    19: "kumi na tisa", 20: "ishirini",
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
SPOKEN_WORD_OVERRIDES = {
    # The voice can blur the unvoiced p into an m-like onset. A syllable
    # boundary keeps "pili" distinct from the number word "mbili" while the
    # visible textbook text remains unchanged.
    "pili": "pi-li",
}
YEAR_SPEECH = {
    "2016": "mwaka elfu mbili na kumi na sita",
    "2018": "mwaka elfu mbili na kumi na nane",
    "2021": "mwaka elfu mbili na ishirini na moja",
    "2023": "mwaka elfu mbili na ishirini na tatu",
}
ABBREVIATION_SPEECH = (
    (r"(?<!\w)Dkt\.(?=\s|$)", "Doctor"),
    (r"(?<!\w)Bw\.(?=\s|$)", "Bwana"),
    (r"(?<!\w)Bi\.(?=\s|$)", "Bibi"),
)
ROMAN_VALUES = {
    "i": 1,
    "v": 5,
    "x": 10,
    "l": 50,
    "c": 100,
    "d": 500,
    "m": 1000,
}


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def number_word(value: int) -> str:
    return NUMBER_WORDS.get(value, str(value))


def roman_value(token: str) -> int:
    total = 0
    previous = 0
    for character in reversed(token.lower()):
        value = ROMAN_VALUES[character]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total


def expand_roman_marker(text: str) -> str:
    """Expand list-style Roman numerals without changing exercise letter i."""
    marker = re.match(r"^(\s*)(\(?)([ivxlcdm]+)([.)])(?=\s|$)", text)
    if marker:
        replacement = f"{marker.group(1)}{number_word(roman_value(marker.group(3)))}"
        return replacement + text[marker.end():]

    exact = re.fullmatch(r"\s*([ivxlcdm]{2,8})\s*", text)
    if exact and exact.group(1) not in {"di", "li", "mi", "vi"}:
        return number_word(roman_value(exact.group(1)))
    return text


def exercise_grapheme(value: str):
    compact = re.sub(r"\s+", "", value).lower()
    if re.fullmatch(r"[a-z]", compact) or compact == "ch":
        return compact
    return None


def is_answer_field(key: str) -> bool:
    return "_ans_item-" in key


def spoken_text(key: str, visible: str, overrides: dict[str, str]) -> str:
    """Return child-friendly Tanzanian Swahili speech without changing display text."""
    if key in overrides:
        visible = overrides[key]
    # Easy-read variants must teach the same pronunciation as their standard
    # tracks, even when their simplified visible text omits the final letter.
    elif key.endswith("_easy_read"):
        standard_key = key.removesuffix("_easy_read")
        # Read the simplified text itself when it contains numerals so 1/2
        # remain moja/mbili instead of inheriting kwanza/pili wording from
        # the standard track.
        has_visible_number = re.search(r"(?<![\w-])\d+(?![\w-])", visible)
        if standard_key in overrides and not has_visible_number:
            visible = overrides[standard_key]

    text = visible.strip()
    text = re.sub(r"\bPAH\b", "", text, flags=re.IGNORECASE)

    # ISBN hyphens are visual separators, not spoken subtraction signs. Read
    # the identifier digit by digit so the voice never inserts "ondoa".
    isbn = re.search(r"\bISBN\s*:\s*([0-9-]+)", text, flags=re.IGNORECASE)
    if isbn:
        digits = re.sub(r"\D", "", isbn.group(1))
        spoken_digits = ", ".join(number_word(int(digit)) for digit in digits)
        return f"I, S, B, N. {spoken_digits}"

    for pattern, expansion in ABBREVIATION_SPEECH:
        text = re.sub(pattern, expansion, text)
    text = expand_roman_marker(text)

    for year, spoken_year in YEAR_SPEECH.items():
        text = re.sub(rf"\bmwaka\s+{year}\b", spoken_year, text, flags=re.IGNORECASE)
        text = re.sub(rf"\b{year}\b", spoken_year, text)
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

    grapheme = exercise_grapheme(compact)
    if grapheme:
        pronunciation = LETTER_NAMES.get(grapheme, grapheme)
        return f"Herufi {pronunciation}"

    standalone_number = re.fullmatch(r"\d{1,2}", compact)
    if standalone_number:
        return number_word(int(standalone_number.group(0)))

    marker = re.match(r"^\s*(\d{1,2})[.)]\s*(.*)$", compact, re.S)
    if marker:
        number = int(marker.group(1))
        remainder = marker.group(2).strip()
        compact = f"Namba {number_word(number)}. {remainder}".strip()

    # Convert standalone numerals inside ordinary text without touching years,
    # identifiers such as item-2, or digits that form part of a larger number.
    compact = re.sub(
        r"(?<![\w-])(\d{1,2})(?![\w-])",
        lambda match: number_word(int(match.group(1))),
        compact,
    )

    for written, spoken in SPOKEN_WORD_OVERRIDES.items():
        compact = re.sub(
            rf"\b{re.escape(written)}\b",
            spoken,
            compact,
            flags=re.IGNORECASE,
        )

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

    removed_answer_mappings = 0
    for key in list(mappings):
        visible = texts.get(key)
        if visible is not None and (not visible.strip() or is_answer_field(key)):
            del mappings[key]
            removed_answer_mappings += 1

    for key, value in texts.items():
        if value.strip() and not is_answer_field(key):
            mappings.setdefault(key, f"{key}.mp3")

    exercise_letter_keys: set[str] = set()
    if args.exercise_letters:
        for key, value in texts.items():
            grapheme = exercise_grapheme(value)
            if grapheme and not is_answer_field(key):
                mappings[key] = f"exercise-letter-{grapheme}.mp3"
                exercise_letter_keys.add(key)

    for lang in TARGET_LANGS:
        target_mapping = ROOT / "content" / "i18n" / lang / "audios.json"
        target_mapping.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jobs = []
    for key, filename in mappings.items():
        visible = texts.get(key, "")
        speech = spoken_text(key, visible, overrides)
        if speech:
            jobs.append((key, speech, filename))

    selected = set(args.key or [])
    if args.abbreviations:
        selected.update(
            key
            for key, value in texts.items()
            if any(re.search(pattern, value) for pattern, _ in ABBREVIATION_SPEECH)
        )
    if args.exercise_letters:
        selected.update(exercise_letter_keys)
    if args.letter_titles:
        title_keys = {
            key
            for key, speech in overrides.items()
            if speech.startswith("Ninaandika herufi")
        }
        selected.update(title_keys)
        selected.update(
            f"{key}_easy_read"
            for key in title_keys
            if f"{key}_easy_read" in texts
        )
    if args.review_corrections:
        from apply_instruction_expansions import EXPANSIONS

        selected.update(EXPANSIONS)
        selected.update(
            f"{key}_easy_read"
            for key in EXPANSIONS
            if f"{key}_easy_read" in texts
        )
        # Page 111 previously reused page 108 IDs.  Its repaired, unique IDs
        # all need their own read-aloud files and mappings.
        selected.update(
            key
            for key, value in texts.items()
            if key.startswith("pg111_") and value.strip() and not is_answer_field(key)
        )
    if selected:
        jobs = [job for job in jobs if job[0] in selected]
        missing_keys = selected - {job[0] for job in jobs}
        if missing_keys:
            raise SystemExit(f"Unknown or empty text IDs: {', '.join(sorted(missing_keys))}")
    if args.limit:
        jobs = jobs[: args.limit]
    selected_text_ids = len(jobs)
    unique_jobs: dict[str, tuple[str, str, str]] = {}
    for job in jobs:
        key, speech, filename = job
        existing = unique_jobs.get(filename)
        if existing and existing[1] != speech:
            raise SystemExit(f"Conflicting speech for shared audio file {filename}")
        unique_jobs.setdefault(filename, job)
    jobs = list(unique_jobs.values())
    print(
        f"Selected {len(jobs)} Rehema tracks for {selected_text_ids} text IDs "
        f"in {', '.join(TARGET_LANGS)}; removed {removed_answer_mappings} answer/blank mappings"
    )
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
    parser.add_argument(
        "--letter-titles",
        action="store_true",
        help="generate every Ninaandika-herufi title and its easy-read track",
    )
    parser.add_argument(
        "--abbreviations",
        action="store_true",
        help="generate tracks containing Dkt., Bw., or Bi. with spoken expansions",
    )
    parser.add_argument(
        "--exercise-letters",
        action="store_true",
        help="generate shared Herufi-a, Herufi-be, and related exercise tracks",
    )
    parser.add_argument(
        "--review-corrections",
        action="store_true",
        help="generate every Joleen review correction and repaired page 111 track",
    )
    parser.add_argument("--limit", type=int, help="generate only the first N tracks for testing")
    parser.add_argument("--dry-run", action="store_true")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
