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

from joleen_review_overlays import BOLD_TOKENS, OVERLAY_POSITIONS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TOP = 110
PAGE_WIDTH = 930
CROPPED_HEIGHT = 1040
EXTENDED_HEIGHT = 1170
FONT_SIZE = 28
LINE_HEIGHT = 27
LETTER_INSTRUCTION_GAP = 30
PARAGRAPH_AFTER_GAP = 16
LINE_NAMES = (
    "firstLine",
    "secondLine",
    "thirdLine",
    "fourthLine",
    "fifthLine",
    "sixthLine",
)

SPLIT_LAYOUTS = {
    "55": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(575, 30), (660, 30), (815, 30)],
        "covers": [(90, 815, 850, 1220)],
        "rows": [
            ((100, 912, 830, 974), (100, 898)),
            ((100, 1001, 830, 1098), (100, 1065)),
        ],
    },
    "57": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(205, 30), (280, 30), (447, 30)],
        "covers": [(90, 447, 850, 1220)],
        "lower_source_y": 750,
        "lower_shift": 70,
        "rows": [
            ((100, 542, 830, 600), (100, 530)),
            ((100, 623, 830, 724), (100, 690)),
        ],
    },
    "60": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(205, 30), (265, 30), (424, 30)],
        "covers": [(90, 424, 850, 1220)],
        "lower_source_y": 730,
        "lower_shift": 70,
        "rows": [
            ((100, 522, 830, 579), (100, 507)),
            ((100, 613, 830, 705), (100, 668)),
        ],
    },
    "61": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(640, 30), (695, 30), (848, 30)],
        "covers": [(90, 848, 850, 1220)],
        "rows": [
            ((100, 939, 830, 998), (100, 931)),
            ((100, 1030, 830, 1125), (100, 1095)),
        ],
    },
    "63": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(570, 30), (655, 30), (829, 30)],
        "covers": [(90, 829, 850, 1220)],
        "rows": [
            ((100, 938, 830, 998), (100, 912)),
            ((100, 1030, 830, 1120), (100, 1077)),
        ],
    },
    "65": {
        "height": 1200,
        "content_offset": 90,
        "top_insertions": [(205, 30), (280, 30), (438, 30)],
        "covers": [(90, 438, 850, 1220)],
        "lower_source_y": 735,
        "lower_shift": 70,
        "rows": [
            ((100, 533, 830, 591), (100, 521)),
            ((100, 623, 830, 715), (100, 683)),
        ],
    },
    "66": {
        "height": 1250,
        "content_offset": 80,
        "top_insertions": [(760, 25, -1), (815, 25, -1), (955, 30, -1)],
        "covers": [
            (90, 955, 850, 1045),
            (0, 1142, PAGE_WIDTH, 1280),
        ],
        "rows": [],
    },
}


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
    target_width: int | None = None,
    max_space_multiplier: float = 3,
) -> None:
    x, y = position
    if target_width is not None:
        words = value.split()
        if len(words) > 1:
            word_widths = [round(draw.textlength(word, font=font)) for word in words]
            natural_space = draw.textlength(" ", font=font)
            available_space = target_width - sum(word_widths)
            justified_space = available_space / (len(words) - 1)
            # Avoid the conspicuously loose spacing produced by justifying a
            # very short line. Such lines are treated like paragraph endings.
            if natural_space <= justified_space <= natural_space * max_space_multiplier:
                for index, word in enumerate(words):
                    token = word.strip(".,;:!?()[]")
                    bold = token in bold_tokens
                    draw.text(
                        (x, y),
                        word,
                        font=font,
                        fill=(35, 31, 32, 255),
                        stroke_width=1 if bold else 0,
                        stroke_fill=(35, 31, 32, 255),
                    )
                    x += word_widths[index]
                    if index < len(words) - 1:
                        x += justified_space
                return
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


def blank_background_band(
    source_page: Image.Image,
    insertion_y: int,
    height: int,
) -> Image.Image:
    """Find a nearby text-free band while preserving the page-edge texture."""
    minimum_y = max(SOURCE_TOP, insertion_y - 80)
    maximum_y = min(1150 - height, insertion_y + 80)
    best: tuple[int, int] | None = None
    best_start = insertion_y
    for candidate_y in range(minimum_y, maximum_y + 1):
        interior = source_page.crop(
            (90, candidate_y, 850, candidate_y + height)
        ).convert("L")
        histogram = interior.histogram()
        dark_pixels = sum(histogram[:235])
        score = (dark_pixels, abs(candidate_y - insertion_y))
        if best is None or score < best:
            best = score
            best_start = candidate_y
    return source_page.crop(
        (0, best_start, PAGE_WIDTH, best_start + height)
    )


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


def fill_lines(
    values: list[str],
    font: ImageFont.FreeTypeFont,
    max_width: float,
    min_last_words: int = 1,
) -> list[str]:
    """Wrap like body text: use the line width before continuing below."""
    words = " ".join(values).split()
    line_count = len(values)
    lines: list[str] = []
    start = 0
    for line_index in range(line_count - 1):
        words_needed_below = max(
            line_count - line_index - 1,
            min_last_words if line_index == line_count - 2 else 1,
        )
        end = start + 1
        while end < len(words) - words_needed_below:
            candidate = " ".join(words[start : end + 1])
            if font.getlength(candidate) > max_width:
                break
            end += 1
        lines.append(" ".join(words[start:end]))
        start = end
    lines.append(" ".join(words[start:]))
    return lines


def draw_position_text(
    draw: ImageDraw.ImageDraw,
    position: dict,
    font: ImageFont.FreeTypeFont,
    bold_tokens: list[str],
    y_offset: int = 0,
) -> list[str]:
    position_font = font
    if position.get("fontSize") and position["fontSize"] != FONT_SIZE:
        position_font = ImageFont.truetype(
            ROOT / "assets" / "fonts" / "SassoonPrimary-Source.ttf",
            position["fontSize"],
        )
    source_lines = [position[name] for name in LINE_NAMES if position.get(name)]
    text_x = position.get("textX", 110)
    usable_width = (
        position.get("rectX", 100)
        + position.get("rectWidth", 730)
        - text_x
        - 10
    )
    flow = position.get(
        "flow",
        "balance" if position.get("textAlign") == "center" else "fill",
    )
    lines = (
        fill_lines(
            source_lines,
            position_font,
            usable_width,
            position.get("minLastWords", 3),
        )
        if flow == "fill"
        else balance_lines(source_lines, position_font)
    )
    text_top = position["firstLineY"] + y_offset - position_font.size - SOURCE_TOP
    for index, line in enumerate(lines):
        x = position.get("textX", 110)
        rect_left = position.get("rectX", 100)
        rect_width = position.get("rectWidth", 730)
        alignment = position.get("textAlign", "justify")
        if alignment == "center":
            x = rect_left + round((rect_width - position_font.getlength(line)) / 2)
        target_width = None
        if alignment == "justify" and index < len(lines) - 1:
            target_width = rect_left + rect_width - x - 10
        draw_styled_line(
            draw,
            (x, text_top + (index * LINE_HEIGHT)),
            line,
            position_font,
            bold_tokens,
            target_width,
            position.get("maxSpaceMultiplier", 3),
        )
    return lines


def render_split_layout(
    overlay: Image.Image,
    page_key: str,
    positions: list[dict],
    font: ImageFont.FreeTypeFont,
    bold_tokens: list[str],
) -> None:
    """Place each instruction beside the practice row it describes."""
    layout = SPLIT_LAYOUTS[page_key]
    content_offset = layout.get("content_offset", 0)
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, overlay.width, overlay.height), fill=(255, 255, 255, 255))

    source_page = Image.open(
        ROOT / f"images/source-pages/pg{int(page_key):03d}.png"
    ).convert("RGBA")
    insertions = layout.get("top_insertions", [])
    if insertions:
        source_cursor = SOURCE_TOP
        destination_y = 0
        inserted_height = 0
        for insertion in insertions:
            insertion_y, gap_height = insertion[:2]
            sample_y = insertion[2] if len(insertion) == 3 else None
            segment = source_page.crop((0, source_cursor, PAGE_WIDTH, insertion_y))
            overlay.alpha_composite(segment, dest=(0, destination_y))
            destination_y += segment.height

            if sample_y == -1:
                background_band = Image.new(
                    "RGBA",
                    (PAGE_WIDTH, gap_height),
                    (255, 255, 255, 255),
                )
            elif sample_y is not None:
                background_band = source_page.crop(
                    (0, sample_y, PAGE_WIDTH, sample_y + gap_height)
                )
            else:
                background_band = blank_background_band(
                    source_page,
                    insertion_y,
                    gap_height,
                )
            overlay.alpha_composite(background_band, dest=(0, destination_y))
            destination_y += gap_height
            inserted_height += gap_height
            source_cursor = insertion_y

        remaining = source_page.crop((0, source_cursor, PAGE_WIDTH, 1150))
        overlay.alpha_composite(remaining, dest=(0, destination_y))
        if inserted_height != content_offset:
            raise RuntimeError(
                f"Page {page_key} inserts {inserted_height}px but offsets {content_offset}px"
            )
    else:
        source_base = source_page.crop((0, SOURCE_TOP, PAGE_WIDTH, 1150))
        overlay.alpha_composite(source_base, dest=(0, 0))

    draw = ImageDraw.Draw(overlay)
    for left, top, right, bottom in layout["covers"]:
        draw.rectangle(
            (
                left,
                top + content_offset - SOURCE_TOP,
                right,
                bottom + content_offset - SOURCE_TOP,
            ),
            fill=(255, 255, 255, 255),
        )

    lower_source_y = layout.get("lower_source_y")
    if lower_source_y is not None:
        lower_content = source_page.crop((0, lower_source_y, PAGE_WIDTH, 1150))
        overlay.alpha_composite(
            lower_content,
            dest=(
                0,
                lower_source_y
                + layout["lower_shift"]
                + content_offset
                - SOURCE_TOP,
            ),
        )

    for crop_box, destination in layout["rows"]:
        row = source_page.crop(crop_box)
        overlay.alpha_composite(
            row,
            dest=(
                destination[0],
                destination[1] + content_offset - SOURCE_TOP,
            ),
        )

    draw = ImageDraw.Draw(overlay)
    for position in positions:
        y_offset = position.get("layoutOffset", content_offset)
        lines = [position[name] for name in LINE_NAMES if position.get(name)]
        rect_top = position["rectY"] + y_offset - SOURCE_TOP
        rect_height = max(position["height"], (len(lines) * LINE_HEIGHT) + 4)
        rect_left = position.get("rectX", 100)
        rect_right = rect_left + position.get("rectWidth", 730)
        draw.rectangle(
            (rect_left, rect_top, rect_right, rect_top + rect_height),
            fill=tuple(position.get("fill", (255, 255, 255, 255))),
        )
        draw_position_text(draw, position, font, bold_tokens, y_offset)


def shifted_position(position: dict, y_offset: int) -> dict:
    shifted = dict(position)
    for key in ("rectY", "firstLineY", "secondLineY", "thirdLineY", "fourthLineY"):
        if key in shifted:
            shifted[key] += y_offset
    return shifted


def render_gapped_instruction_layout(
    overlay: Image.Image,
    page_key: str,
    positions: list[dict],
    font: ImageFont.FreeTypeFont,
    bold_tokens: list[str],
) -> None:
    """Replace one printed instruction with a taller corrected block."""
    source_page = Image.open(
        ROOT / f"images/source-pages/pg{int(page_key):03d}.png"
    ).convert("RGBA")
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, overlay.width, overlay.height), fill=(255, 255, 255, 255))

    source_cursor = SOURCE_TOP
    destination_y = 0
    rendered_positions: list[
        tuple[dict, int, list[str], ImageFont.FreeTypeFont]
    ] = []
    for position in positions:
        position_font = font
        if position.get("fontSize") and position["fontSize"] != FONT_SIZE:
            position_font = ImageFont.truetype(
                ROOT / "assets" / "fonts" / "SassoonPrimary-Source.ttf",
                position["fontSize"],
            )
        old_top = position["rectY"] - 10
        old_bottom = position["rectY"] + 50
        segment = source_page.crop((0, source_cursor, PAGE_WIDTH, old_top))
        overlay.alpha_composite(segment, dest=(0, destination_y))
        destination_y += segment.height
        source_lines = [position[name] for name in LINE_NAMES if position.get(name)]
        usable_width = (
            position.get("rectX", 100)
            + position.get("rectWidth", 730)
            - position.get("textX", 110)
            - 10
        )
        flow = position.get(
            "flow",
            "balance" if position.get("textAlign") == "center" else "fill",
        )
        lines = (
            fill_lines(
                source_lines,
                position_font,
                usable_width,
                position.get("minLastWords", 3),
            )
            if flow == "fill"
            else balance_lines(source_lines, position_font)
        )
        block_height = (
            max(position["height"], (len(lines) * LINE_HEIGHT) + 4)
            + 12
            + PARAGRAPH_AFTER_GAP
        )
        background_band = blank_background_band(source_page, old_top, block_height)
        overlay.alpha_composite(background_band, dest=(0, destination_y))
        rendered_positions.append((position, destination_y, lines, position_font))
        destination_y += block_height
        source_cursor = old_bottom

    remaining = source_page.crop((0, source_cursor, PAGE_WIDTH, 1150))
    overlay.alpha_composite(remaining, dest=(0, destination_y))

    draw = ImageDraw.Draw(overlay)
    for position, rect_top, lines, position_font in rendered_positions:
        rect_height = (
            max(position["height"], (len(lines) * LINE_HEIGHT) + 4)
            + 12
            + PARAGRAPH_AFTER_GAP
        )
        rect_left = position.get("rectX", 100)
        rect_right = rect_left + position.get("rectWidth", 730)
        draw.rectangle(
            (rect_left, rect_top, rect_right, rect_top + rect_height),
            fill=tuple(position.get("fill", (255, 255, 255, 255))),
        )
        for index, line in enumerate(lines):
            x = position.get("textX", 110)
            rect_left = position.get("rectX", 100)
            rect_width = position.get("rectWidth", 730)
            target_width = None
            if position.get("textAlign", "justify") == "justify" and index < len(lines) - 1:
                target_width = rect_left + rect_width - x - 10
            draw_styled_line(
                draw,
                (x, rect_top + 5 + (index * LINE_HEIGHT)),
                line,
                position_font,
                bold_tokens,
                target_width,
                position.get("maxSpaceMultiplier", 3),
            )


def main() -> None:
    bold_by_page = BOLD_TOKENS
    positions = OVERLAY_POSITIONS
    font = ImageFont.truetype(ROOT / "assets" / "fonts" / "SassoonPrimary-Source.ttf", FONT_SIZE)
    output_dir = ROOT / "images" / "corrections"
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered = 0
    for page_key, raw_positions in positions.items():
        page_positions = raw_positions if isinstance(raw_positions, list) else [raw_positions]
        layout = SPLIT_LAYOUTS.get(page_key)
        gapped_instruction_page = layout is None and any(
            position.get("gap", 0) > 0 for position in page_positions
        )
        overlay_height = (
            layout.get("height", CROPPED_HEIGHT)
            if layout
            else max(
                CROPPED_HEIGHT,
                CROPPED_HEIGHT + (
                    sum(
                        max(
                            position["height"],
                            len([name for name in LINE_NAMES if position.get(name)]) * LINE_HEIGHT + 4,
                        )
                        + 12
                        + PARAGRAPH_AFTER_GAP
                        - 60
                        for position in page_positions
                    )
                    if gapped_instruction_page
                    else 0
                ),
            )
        )
        overlay = Image.new("RGBA", (PAGE_WIDTH, overlay_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        bold_tokens = bold_by_page.get(page_key, [])
        if layout:
            render_split_layout(overlay, page_key, page_positions, font, bold_tokens)
            overlay.save(output_dir / f"pg{int(page_key):03d}.png", optimize=True)
            rendered += 1
            continue
        if gapped_instruction_page:
            render_gapped_instruction_layout(
                overlay,
                page_key,
                page_positions,
                font,
                bold_tokens,
            )
            overlay.save(output_dir / f"pg{int(page_key):03d}.png", optimize=True)
            rendered += 1
            continue
        for position in page_positions:
            source_lines = [position[name] for name in LINE_NAMES if position.get(name)]
            lines = balance_lines(source_lines, font)
            rect_top = position["rectY"] - SOURCE_TOP
            rect_height = max(position["height"], (len(lines) * LINE_HEIGHT) + 4)
            rect_left = position.get("rectX", 100)
            rect_right = rect_left + position.get("rectWidth", 730)
            rectangle_fill = tuple(position.get("fill", (255, 255, 255, 255)))
            draw.rectangle(
                (rect_left, rect_top, rect_right, rect_top + rect_height),
                fill=rectangle_fill,
            )
            draw_position_text(draw, position, font, bold_tokens)
        overlay.save(output_dir / f"pg{int(page_key):03d}.png", optimize=True)
        rendered += 1

    print(f"Rendered {rendered} exact-font correction overlays")


if __name__ == "__main__":
    main()
