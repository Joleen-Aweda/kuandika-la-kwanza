#!/usr/bin/env python3
"""Install the integrated writing-practice assets on converted semantic pages."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = '    <link href="./assets/writing-practice.css?v=4" rel="stylesheet">\n'
SCRIPT = '    <script src="./assets/writing-practice.js?v=4"></script>\n'


def main() -> None:
    changed = 0
    for page in sorted(ROOT.glob("pg*_sec*.html")):
        html = page.read_text(encoding="utf-8")
        if "source-facsimile-page" not in html:
            continue
        updated = html
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
