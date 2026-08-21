#!/usr/bin/env python3
"""Expand every ADT image description and keep HTML/i18n fallbacks aligned."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_RE = re.compile(r"<img\b[^>]*?data-id=\"([^\"]+)\"[^>]*?>", re.S)
ALT_RE = re.compile(r'\balt="[^"]*"')


def clean(text: str) -> str:
    text = re.sub(r"\[\[blank:[^]]+\]\]", "nafasi ya kujaza", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(". ") + "."


def page_detail(page: int, base: str) -> str:
    lower = base.lower()
    if "sura ya" in lower:
        layout = (
            "Kichwa cha sura na somo kimewekwa kwa herufi kubwa juu ya ukurasa, "
            "kisha shughuli ya kujifunza inaendelea chini yake."
        )
    elif "fwatisha" in lower or "fuatisha" in lower or "andika herufi" in lower:
        layout = (
            "Maelekezo yako juu, yakifuatiwa na mfano wa herufi wenye mishale au namba za hatua, "
            "pamoja na mistari ya mazoezi ya kufuatisha na kuandika."
        )
    elif "andika majina ya picha" in lower or "picha hizi" in lower:
        layout = (
            "Kichwa cha zoezi kiko juu; picha za vitu zimepangwa kwa nafasi zilizo wazi "
            "ili mwanafunzi atambue kila picha na aandike jina lake."
        )
    elif "jedwali" in lower or "chati" in lower:
        layout = (
            "Maelekezo yako juu na jedwali au chati imepangwa katika safu na nguzo, "
            "ikiwa na mifano na nafasi za mwanafunzi kuandika majibu."
        )
    elif "andika sentensi" in lower or "andika maneno" in lower or "andika silabi" in lower:
        layout = (
            "Maelekezo yako juu na maneno au sentensi za mfano zimepangwa kwa mistari, "
            "pamoja na nafasi za mwanafunzi kufanya zoezi la kuandika."
        )
    elif "zoezi" in lower:
        layout = (
            "Kichwa cha zoezi kinaonekana wazi juu, na maelekezo, mifano na nafasi za kujibu "
            "zimepangwa kwa mpangilio wa kusomeka kutoka juu kwenda chini."
        )
    else:
        layout = (
            "Maandishi na vipengele vya kuona vimepangwa kutoka juu kwenda chini kwa nafasi wazi, "
            "ili mwanafunzi afuate maudhui kwa urahisi."
        )
    purpose = (
        "Picha hii ni nakala ya ukurasa mzima na humsaidia msomaji kuelewa mpangilio, "
        "maandishi, mifano na sehemu za kufanyia zoezi kwa pamoja."
    )
    return f"{clean(base)} {layout} {purpose}"


def embedded_detail(base: str) -> str:
    base = clean(base)
    lower = base.lower()
    if any(word in lower for word in ("hatua", "mwongozo", "mishale", "herufi", "mstari", "nukta", "kufuatisha")):
        extra = (
            "Maumbo, mistari, mishale na namba vinaonesha sehemu ya kuanzia, mwelekeo wa kalamu "
            "na mpangilio wa hatua. Picha hii humsaidia mwanafunzi kufuatisha na kuandika kwa umbo sahihi."
        )
    elif any(word in lower for word in ("familia", "wasichana", "mvulana", "sungura", "babu", "bibi")):
        extra = (
            "Wahusika, mavazi, mkao na kitendo kinachofanyika vinaonekana kwa uwazi. "
            "Picha hii humsaidia mwanafunzi kutambua wahusika, kueleza tendo na kuhusisha picha na maneno."
        )
    elif any(word in lower for word in ("jedwali", "zoezi la", "kisanduku", "safu", "silabi")):
        extra = (
            "Vipengele vya zoezi vimepangwa katika safu na sehemu tofauti, zikiwa na mfano na nafasi za kujaza. "
            "Picha hii humwongoza mwanafunzi kuelewa mpangilio wa kazi kabla ya kuandika jibu."
        )
    elif lower.startswith("picha ya") or len(base.split()) > 8:
        extra = (
            "Kitu kikuu kimetengwa wazi dhidi ya mandharinyuma ili umbo na sehemu zake muhimu zitambulike. "
            "Picha hii hutumika kuunganisha maelezo yanayosomwa na kitu kinachoonekana."
        )
    else:
        label = base.rstrip(".")
        extra = (
            f"Mchoro unaonesha {label.lower()} kwa uwazi, ukiwa umetengwa dhidi ya mandharinyuma ili umbo lake litambulike. "
            "Picha hii humsaidia mwanafunzi kutambua kitu, kutamka jina lake na kuliandika katika zoezi."
        )
    return f"{base} {extra}"


def main() -> None:
    text_paths = [ROOT / "content/i18n/sw/texts.json", ROOT / "content/i18n/sw-TZ/texts.json"]
    texts = json.loads(text_paths[0].read_text(encoding="utf-8"))
    html_paths = sorted(ROOT.glob("pg*_sec*.html")) + [ROOT / "index.html"]
    descriptions: dict[str, str] = {}

    for path in html_paths:
        source = path.read_text(encoding="utf-8")
        for match in IMAGE_RE.finditer(source):
            image_id = match.group(1)
            if image_id.endswith("_page_image") or "source-facsimile-page" in match.group(0):
                continue
            base = texts.get(image_id, "").strip()
            if not base:
                raise SystemExit(f"Missing description for {image_id} in {path.name}")
            page_match = re.match(r"pg(\d{3})", image_id)
            page = int(page_match.group(1)) if page_match else 0
            descriptions[image_id] = embedded_detail(base)

    for path in html_paths:
        source = path.read_text(encoding="utf-8")

        def replace_image(match: re.Match[str]) -> str:
            tag, image_id = match.group(0), match.group(1)
            description = html.escape(descriptions[image_id], quote=True)
            if ALT_RE.search(tag):
                return ALT_RE.sub(f'alt="{description}"', tag, count=1)
            return tag[:-1] + f' alt="{description}">'

        updated = IMAGE_RE.sub(replace_image, source)
        path.write_text(updated, encoding="utf-8")

    for text_path in text_paths:
        language_texts = json.loads(text_path.read_text(encoding="utf-8"))
        language_texts.update(descriptions)
        text_path.write_text(json.dumps(language_texts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Expanded {len(descriptions)} unique image descriptions across {len(html_paths)} pages")
    print("\n".join(sorted(descriptions)))


if __name__ == "__main__":
    main()
