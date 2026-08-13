#!/usr/bin/env python3
"""Install exact source-page presentation and direct page inking."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_STYLE = '    <link href="./assets/source-facsimile.css?v=5" rel="stylesheet">\n'
INK_STYLE = '    <link href="./assets/page-ink.css?v=1" rel="stylesheet">\n'
INK_SCRIPT = '    <script src="./assets/page-ink.js?v=1"></script>\n'


def page_path(number: int) -> Path:
    return ROOT / ("index.html" if number == 1 else f"pg{number:03d}_sec001.html")


def ensure_class(tag: str, class_name: str) -> str:
    match = re.search(r'class="([^"]*)"', tag)
    if match:
        classes = match.group(1).split()
        if class_name not in classes:
            classes.append(class_name)
        return tag[: match.start(1)] + " ".join(classes) + tag[match.end(1) :]
    return tag[:-1] + f' class="{class_name}">'


def install_page(number: int) -> bool:
    path = page_path(number)
    html = path.read_text(encoding="utf-8")
    updated = html

    updated = re.sub(
        r'\s*<link href="\./assets/writing-practice\.css(?:\?v=\d+)?" rel="stylesheet">',
        "",
        updated,
    )
    updated = re.sub(
        r'\s*<script src="\./assets/writing-practice\.js(?:\?v=\d+)?"></script>',
        "",
        updated,
    )
    updated = re.sub(
        r'<link href="\./assets/source-facsimile\.css(?:\?v=\d+)?" rel="stylesheet">',
        SOURCE_STYLE.strip(),
        updated,
    )
    if "assets/source-facsimile.css" not in updated:
        marker = re.search(r'\s*</head>', updated)
        if not marker:
            raise RuntimeError(f"Missing </head> in {path.name}")
        updated = updated[: marker.start()] + "\n" + SOURCE_STYLE + updated[marker.start() :]

    updated = re.sub(
        r'<link href="\./assets/page-ink\.css(?:\?v=\d+)?" rel="stylesheet">',
        INK_STYLE.strip(),
        updated,
    )
    if "assets/page-ink.css" not in updated:
        source_link = re.search(r'\s*<link href="\./assets/source-facsimile\.css\?v=5" rel="stylesheet">', updated)
        if not source_link:
            raise RuntimeError(f"Missing source style in {path.name}")
        updated = updated[: source_link.end()] + "\n" + INK_STYLE.rstrip() + updated[source_link.end() :]

    image = f'<img class="source-facsimile-page" src="images/source-pages/pg{number:03d}.png" alt="" aria-hidden="true" />'
    if "source-facsimile-page" not in updated:
        content = re.search(r'<div\s+id="content"[^>]*>', updated)
        if not content:
            raise RuntimeError(f"Missing #content in {path.name}")
        updated = updated[: content.end()] + "\n  " + image + updated[content.end() :]

    section = re.search(r'<section\b[^>]*data-section-id="pg\d{3}_sec001"[^>]*>', updated)
    if not section:
        raise RuntimeError(f"Missing semantic section in {path.name}")
    updated = updated[: section.start()] + ensure_class(section.group(0), "source-semantic-copy") + updated[section.end() :]

    updated = re.sub(
        r'<script src="\./assets/page-ink\.js(?:\?v=\d+)?"></script>',
        INK_SCRIPT.strip(),
        updated,
    )
    if "assets/page-ink.js" not in updated:
        updated = updated.replace("</body>", INK_SCRIPT + "</body>")

    if updated != html:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = sum(install_page(number) for number in range(1, 121))
    print(f"Installed exact facsimiles on {changed} pages")


if __name__ == "__main__":
    main()
