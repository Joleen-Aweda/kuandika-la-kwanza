#!/usr/bin/env python3
"""Remove the tagged diagonal reading watermark from the source textbook PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject


WATERMARK = re.compile(
    rb"/Artifact\s*<</Subtype\s*/Watermark\s*/Type\s*/Pagination\s*>>BDC"
    rb".*?EMC\s*\Z",
    re.DOTALL,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    reader = PdfReader(args.source)
    writer = PdfWriter()
    removed = 0

    for page_number, page in enumerate(reader.pages, start=1):
        contents = page.get_contents()
        if contents is not None:
            data = contents.get_data()
            cleaned, count = WATERMARK.subn(b"", data)
            if count:
                stream = DecodedStreamObject()
                stream.set_data(cleaned)
                page[NameObject("/Contents")] = stream
                removed += count
        writer.add_page(page)

    if removed == 0:
        raise SystemExit("No tagged watermark objects were found")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as output:
        writer.write(output)

    print(f"Removed {removed} watermark objects from {len(reader.pages)} pages")


if __name__ == "__main__":
    main()
