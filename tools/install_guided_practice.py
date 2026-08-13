#!/usr/bin/env python3
"""Install source-faithful guided answer areas on every textbook source page."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = '    <link href="./assets/guided-practice.css?v=13" rel="stylesheet">\n'
SCRIPT = '    <script src="./assets/guided-practice.js?v=13"></script>\n'


def main() -> None:
    changed = 0
    for path in sorted([ROOT / "index.html", *ROOT.glob("pg???_sec001.html")]):
        html = path.read_text(encoding="utf-8")
        if "source-facsimile-page" not in html:
            continue

        updated = re.sub(
            r'\s*<link href="\./assets/guided-practice\.css(?:\?v=\d+)?" rel="stylesheet">',
            "\n" + STYLE.rstrip(),
            html,
        )
        updated = re.sub(
            r'\s*<script src="\./assets/guided-practice\.js(?:\?v=\d+)?"></script>',
            "\n" + SCRIPT.rstrip(),
            updated,
        )

        if "assets/guided-practice.css" not in updated:
            marker = re.search(r'^\s*<link href="\./assets/page-ink\.css\?v=\d+" rel="stylesheet">\s*$', updated, re.M)
            if not marker:
                raise RuntimeError(f"Page-ink stylesheet marker missing in {path.name}")
            updated = updated[: marker.end()] + "\n" + STYLE.rstrip() + updated[marker.end() :]

        if "assets/guided-practice.js" not in updated:
            marker = re.search(r'^\s*<script src="\./assets/page-ink\.js\?v=\d+"></script>\s*$', updated, re.M)
            if not marker:
                raise RuntimeError(f"Page-ink script marker missing in {path.name}")
            updated = updated[: marker.end()] + "\n" + SCRIPT.rstrip() + updated[marker.end() :]

        updated = updated.replace("offline-preloader.js?v=7", "offline-preloader.js?v=10")
        updated = updated.replace("offline-preloader.js?v=8", "offline-preloader.js?v=10")
        updated = updated.replace("offline-preloader.js?v=9", "offline-preloader.js?v=10")
        updated = updated.replace("source-facsimile.css?v=5", "source-facsimile.css?v=7")
        updated = updated.replace("source-facsimile.css?v=6", "source-facsimile.css?v=7")
        updated = updated.replace("page-ink.js?v=1", "page-ink.js?v=3")
        updated = updated.replace("page-ink.js?v=2", "page-ink.js?v=3")
        if updated != html:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Installed guided practice on {changed} source pages")


if __name__ == "__main__":
    main()
