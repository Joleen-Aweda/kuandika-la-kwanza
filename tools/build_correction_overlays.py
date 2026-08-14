#!/usr/bin/env python3
"""Render visible correction overlays with the exact bundled Sassoon font.

The underlying HTML text remains the accessible/read-aloud source. These
transparent overlays only replace the printed pixels that need corrections.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TOP = 110
PAGE_WIDTH = 930
CROPPED_HEIGHT = 1040
FONT_SIZE = 28
LINE_HEIGHT = 27
LINE_NAMES = ("firstLine", "secondLine", "thirdLine", "fourthLine")


def read_js_object(source: str, variable: str, following: str) -> dict:
    pattern = re.compile(
        rf"var {re.escape(variable)} = (\{{.*?\n    \}});\n    var {re.escape(following)}",
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        raise RuntimeError(f"Could not locate {variable} in source-page.js")
    literal = match.group(1)
    literal = re.sub(r"(?m)^(\s*)(\d+):", r'\1"\2":', literal)
    literal = re.sub(
        r"(?m)^(\s*)([A-Za-z_$][A-Za-z0-9_$]*):",
        r'\1"\2":',
        literal,
    )
    literal = re.sub(r",(\s*[}\]])", r"\1", literal)
    return json.loads(literal)


def draw_styled_line(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    value: str,
    font: ImageFont.FreeTypeFont,
    bold_tokens: list[str],
) -> None:
    x, y = position
    if bold_tokens:
        alternatives = "|".join(re.escape(token) for token in sorted(bold_tokens, key=len, reverse=True))
        parts = re.split(rf"(\b(?:{alternatives})\b)", value)
    else:
        parts = [value]
    for part in parts:
        if not part:
            continue
        bold = part in bold_tokens
        draw.text(
            (x, y),
            part,
            font=font,
            fill=(35, 31, 32, 255),
            stroke_width=1 if bold else 0,
            stroke_fill=(35, 31, 32, 255),
        )
        x += round(draw.textlength(part, font=font))


def balance_lines(
    values: list[str],
    font: ImageFont.FreeTypeFont,
) -> list[str]:
    """Reflow a correction into its allotted line count at the book's size."""
    words = " ".join(values).split()
    line_count = len(values)
    word_count = len(words)

    @lru_cache(maxsize=None)
    def solve(start: int, remaining: int) -> tuple[float, tuple[int, ...]]:
        if remaining == 1:
            return font.getlength(" ".join(words[start:])), (word_count,)

        best_width = float("inf")
        best_breaks: tuple[int, ...] = ()
        last_break = word_count - remaining + 1
        for end in range(start + 1, last_break + 1):
            current_width = font.getlength(" ".join(words[start:end]))
            remaining_width, remaining_breaks = solve(end, remaining - 1)
            widest = max(current_width, remaining_width)
            if widest < best_width:
                best_width = widest
                best_breaks = (end,) + remaining_breaks
        return best_width, best_breaks

    _, breaks = solve(0, line_count)
    lines: list[str] = []
    start = 0
    for end in breaks:
        lines.append(" ".join(words[start:end]))
        start = end
    return lines


def main() -> None:
    source = (ROOT / "assets" / "source-page.js").read_text(encoding="utf-8")
    bold_by_page = read_js_object(source, "boldTokensByPage", "positions")
    positions = read_js_object(source, "positions", "pagePositions")
    font = ImageFont.truetype(ROOT / "assets" / "fonts" / "SassoonPrimary-Source.ttf", FONT_SIZE)
    output_dir = ROOT / "images" / "corrections"
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered = 0
    for page_key, raw_positions in positions.items():
        page_positions = raw_positions if isinstance(raw_positions, list) else [raw_positions]
        overlay = Image.new("RGBA", (PAGE_WIDTH, CROPPED_HEIGHT), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        bold_tokens = bold_by_page.get(page_key, [])
        for position in page_positions:
            source_lines = [position[name] for name in LINE_NAMES if position.get(name)]
            lines = balance_lines(source_lines, font)
            rect_top = position["rectY"] - SOURCE_TOP
            rect_height = max(position["height"], (len(lines) * LINE_HEIGHT) + 4)
            draw.rectangle(
                (100, rect_top, 830, rect_top + rect_height),
                fill=(255, 255, 255, 255),
            )
            text_top = position["firstLineY"] - FONT_SIZE - SOURCE_TOP
            for index, line in enumerate(lines):
                draw_styled_line(
                    draw,
                    (110, text_top + (index * LINE_HEIGHT)),
                    line,
                    font,
                    bold_tokens,
                )
        overlay.save(output_dir / f"pg{int(page_key):03d}.png", optimize=True)
        rendered += 1

    print(f"Rendered {rendered} exact-font correction overlays")


if __name__ == "__main__":
    main()
