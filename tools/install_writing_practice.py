#!/usr/bin/env python3
"""Install versioned book typography and writing-practice assets."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = '    <link href="./assets/writing-practice.css?v=5" rel="stylesheet">\n'
SCRIPT = '    <script src="./assets/writing-practice.js?v=5"></script>\n'


def main() -> None:
    changed = 0
    for page in sorted(ROOT.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        updated = re.sub(
            r'href="\./assets/fonts\.css(?:\?v=\d+)?"',
            'href="./assets/fonts.css?v=2"',
            html,
        )
        if "source-facsimile-page" not in updated:
            if updated != html:
                page.write_text(updated, encoding="utf-8")
                changed += 1
            continue
        updated = re.sub(
            r'<link href="\./assets/writing-practice\.css(?:\?v=\d+)?" rel="stylesheet">',
            STYLE.strip(),
            updated,
        )
        updated = re.sub(
            r'<script src="\./assets/writing-practice\.js(?:\?v=\d+)?"></script>',
            SCRIPT.strip(),
            updated,
        )
        if "assets/writing-practice.css" not in updated:
            marker = '    <link href="./assets/source-facsimile.css?v=4" rel="stylesheet">\n'
            updated = updated.replace(marker, marker + STYLE)
        if "assets/writing-practice.js" not in updated:
            updated = updated.replace("</body>", SCRIPT + "</body>")
        if updated != html:
            page.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Installed writing practice on {changed} pages")


if __name__ == "__main__":
    main()
