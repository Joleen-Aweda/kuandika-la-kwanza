#!/usr/bin/env python3
"""Merge split ADT sections so each physical page appears exactly once."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content/pages.json"


def section_markup(html: str) -> str:
    match = re.search(r"(?s)(<section\b.*?</section>)", html)
    if not match:
        raise ValueError("section element not found")
    return match.group(1)


def flatten_sections(html: str) -> str:
    """Keep one semantic section while preserving all merged child content."""
    matches = list(re.finditer(r"(?s)<section\b.*?</section>", html))
    if len(matches) < 2:
        return html
    primary = matches[0].group(0)
    additions = []
    for match in matches[1:]:
        section = match.group(0)
        additions.append(section[section.index(">") + 1 : section.rindex("</section>")])
    combined = primary[: primary.rindex("</section>")] + "\n" + "\n".join(additions) + "\n</section>"
    return html[: matches[0].start()] + combined + html[matches[-1].end() :]


def main() -> None:
    pages = json.loads(PAGES_PATH.read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in pages:
        match = re.fullmatch(r"(pg\d{3})_sec\d{3}", entry["section_id"])
        if match:
            groups[match.group(1)].append(entry)

    removed_hrefs: dict[str, str] = {}
    removed_ids: dict[str, str] = {}
    for prefix, entries in groups.items():
        if len(entries) < 2:
            continue
        primary = entries[0]
        primary_path = ROOT / primary["href"]
        html = primary_path.read_text(encoding="utf-8")
        insertion = html.rfind("</div>\n    </main>")
        if insertion < 0:
            raise ValueError(f"content closing marker not found in {primary_path.name}")

        additions = []
        for extra in entries[1:]:
            extra_path = ROOT / extra["href"]
            additions.append(section_markup(extra_path.read_text(encoding="utf-8")))
            removed_hrefs[extra["href"]] = primary["href"]
            removed_ids[extra["section_id"]] = primary["section_id"]
            extra_path.unlink()
        html = html[:insertion] + "\n\n" + "\n\n".join(additions) + "\n" + html[insertion:]
        primary_path.write_text(html, encoding="utf-8")

    pages = [entry for entry in pages if entry["href"] not in removed_hrefs]
    PAGES_PATH.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for index, entry in enumerate(pages, start=1):
        path = ROOT / entry["href"]
        html = flatten_sections(path.read_text(encoding="utf-8"))
        html, count = re.subn(
            r'(<meta name="page-section-id" content=")\d+("\s*/>)',
            rf"\g<1>{index}\2",
            html,
            count=1,
        )
        if count != 1:
            raise ValueError(f"page-section-id not found in {path.name}")
        path.write_text(html, encoding="utf-8")

    for relative in ("content/toc.json", "content/navigation/nav.html"):
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in {**removed_hrefs, **removed_ids}.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    print(f"Merged {len(removed_hrefs)} split sections into {len(groups)} physical page groups")


if __name__ == "__main__":
    main()
