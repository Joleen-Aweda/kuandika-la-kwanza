#!/usr/bin/env python3
"""Extract the source book's embedded teaching fonts as web fonts.

The source PDF embeds subset TrueType fonts. Keeping the extraction scripted
makes the visible ADT typography reproducible without depending on fonts that
may or may not be installed on the reader's device.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


FONT_TARGETS = {
    "SassoonPrimary": "SassoonPrimary-Source.ttf",
}


def clean_font_name(value: object) -> str:
    name = str(value or "").lstrip("/")
    return name.split("+", 1)[-1]


def iter_font_descriptors(reader: PdfReader):
    seen: set[tuple[int, int]] = set()
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        for font_ref in (resources.get("/Font") or {}).values():
            font = font_ref.get_object()
            candidates = [font]
            candidates.extend(
                descendant.get_object()
                for descendant in (font.get("/DescendantFonts") or [])
            )
            for candidate in candidates:
                descriptor_ref = candidate.get("/FontDescriptor")
                if not descriptor_ref:
                    continue
                descriptor = descriptor_ref.get_object()
                identity = descriptor.indirect_reference
                marker = (
                    int(identity.idnum) if identity else id(descriptor),
                    int(identity.generation) if identity else 0,
                )
                if marker in seen:
                    continue
                seen.add(marker)
                yield clean_font_name(descriptor.get("/FontName")), descriptor


def extract_fonts(source_pdf: Path, output_dir: Path) -> list[Path]:
    reader = PdfReader(source_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for font_name, descriptor in iter_font_descriptors(reader):
        target_name = FONT_TARGETS.get(font_name)
        font_stream = descriptor.get("/FontFile2")
        if not target_name or not font_stream:
            continue

        target = output_dir / target_name
        target.write_bytes(font_stream.get_object().get_data())
        created.append(target)
        del FONT_TARGETS[font_name]

    if FONT_TARGETS:
        missing = ", ".join(sorted(FONT_TARGETS))
        raise RuntimeError(f"Required embedded fonts were not found: {missing}")
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    for created in extract_fonts(args.source_pdf, args.output_dir):
        print(created)


if __name__ == "__main__":
    main()
