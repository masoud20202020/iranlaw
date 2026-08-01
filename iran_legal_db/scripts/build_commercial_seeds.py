# -*- coding: utf-8 -*-
"""Build static commercial-law seed files from archived public legal-text pages.

This script is a maintainer utility; normal database loading only needs the generated
Python modules under data/seed/. If a cached page is missing, it is downloaded.
"""
from __future__ import annotations

import pprint
import re
import ssl
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
SEED = ROOT / "data" / "seed"

SOURCES = {
    "commercial_code_1311_mashruteh.html": (
        "https://mashruteh.org/wiki/index.php?title="
        "%D9%82%D8%A7%D9%86%D9%88%D9%86_%D8%AA%D8%AC%D8%A7%D8%B1%D8%AA_%DB%B1%DB%B3%DB%B1%DB%B1"
        "&printable=yes"
    ),
    "commercial_integrated_vakilsoal.html": (
        "https://vakilsoal.com/%D9%82%D8%A7%D9%86%D9%88%D9%86-%D8%AA%D8%AC%D8%A7%D8%B1%D8%AA/"
    ),
    "commercial_amendment_1347_part1.html": "https://fatemekeshavarz.blogfa.com/post/10",
    "commercial_amendment_1347_part2.html": "https://fatemekeshavarz.blogfa.com/post/11",
}

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ASCII_DIGITS = "0123456789"
TO_ASCII = str.maketrans(PERSIAN_DIGITS, ASCII_DIGITS)

# 1403/03/30 adjustment table (row 50) for the 1347 bill.
PENALTIES_1403 = {
    243: "82/500/000 تا 500/000/000",
    244: "165/000/000 تا 660/000/000",
    246: "100/000/000 تا 200/000/000",
    248: "100/000/000 تا 200/000/000",
    250: "100/000/000 تا 200/000/000",
    251: "82/500/000 تا 500/000/000",
    252: "100/000/000 تا 200/000/000",
    253: "82/500/000 تا 500/000/000",
    254: "100/000/000 تا 200/000/000",
    255: "100/000/000 تا 200/000/000",
    259: "82/500/000 تا 200/000/000",
    260: "82/500/000 تا 500/000/000",
    261: "100/000/000 تا 200/000/000",
    262: "100/000/000 تا 200/000/000",
    263: "330/000/000 تا 1/000/000/000",
    264: "100/000/000 تا 200/000/000",
    265: "100/000/000 تا 200/000/000",
    266: "100/000/000 تا 200/000/000",
    268: "100/000/000 تا 200/000/000",
    297: "100/000/000 تا 200/000/000",
}

# 1403/03/30 adjustment table (row 67) for the 1311 code.
# The original code writes these figures in words, so both old and new forms are kept.
CODE_PENALTIES_1403 = {
    15: ("دویست تا ده هزار ریال", "33/000/000 تا 200/000/000 ریال"),
    16: ("دویست تا دو هزارریال", "33/000/000 تا 200/000/000 ریال"),
    18: ("دویست تا دو هزار ریال", "33/000/000 تا 200/000/000 ریال"),
    201: ("دویست تا سه هزار ریال", "33/000/000 تا 200/000/000 ریال"),
    220: ("دویست تا دو هزار ریال", "33/000/000 تا 200/000/000 ریال"),
    346: ("پانصد تا سه هزار ریال", "82/500/000 تا 200/000/000 ریال"),
}


def ensure_sources() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    context = ssl._create_unverified_context()
    for name, url in SOURCES.items():
        target = CACHE / name
        if target.exists() and target.stat().st_size > 10_000:
            continue
        print(f"Downloading {url}")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            target.write_bytes(response.read())


def clean(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u200f", "").replace("\u200e", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_heading(text: str) -> bool:
    text = clean(text)
    if re.match(r"^(باب|فصل|مبحث|بخش|قسمت|عنوان)\b", text):
        return True
    if len(text) < 100 and re.match(r"^[۰-۹0-9]+\s*[-–—ـ]\s*[^.)]", text):
        return True
    return text in {
        "در اقسام مختلفه شرکتها و قواعد راجعه به آنها",
        "در قواعد راجعه به بروات",
        "در قبول و نکول",
        "در نکول",
        "در ضمانت برات",
        "در حق‌العمل‌کار و آمر",
        "ورشکستگی به تقصیر",
        "ورشکستگی به تقلب",
    }


def strip_trailing_structure_heading(text: str) -> str:
    # Several headings share a source <p> with the preceding article.
    heading = (
        r"\.\s+(?=(?:باب|فصل|مبحث|بخش)\s+"
        r"(?:اول|دوم|سوم|چهارم|پنجم|ششم|هفتم|هشتم|نهم|دهم|یازدهم|"
        r"دوازدهم|سیزدهم|چهاردهم|پانزدهم|شانزدهم)\b)"
    )
    match = re.search(heading, text)
    if match:
        text = text[: match.start() + 1]
    return text.strip()


def parse_code_1311() -> list[tuple[int, str]]:
    source = CACHE / "commercial_code_1311_mashruteh.html"
    soup = BeautifulSoup(source.read_bytes(), "lxml")
    root = soup.select_one("#mw-content-text .mw-parser-output") or soup.select_one("#mw-content-text")
    marker = re.compile(r"ماده\s+([۰-۹0-9]+)\s*[-–—ـ]\s*")
    articles: dict[int, list[str]] = {}
    current = None

    for element in root.find_all(recursive=False):
        if element.name != "p":
            continue
        text = clean(element.get_text("\n", strip=True))
        if not text:
            continue
        # A source paragraph can contain several consecutive articles. A reference
        # such as «مفاد ماده ۴۱۳ - ۴۱۴» must not be mistaken for a new article;
        # genuine subsequent article headers in this source follow a full stop.
        raw_matches = list(marker.finditer(text))
        matches = []
        for raw_index, match in enumerate(raw_matches):
            prefix = text[:match.start()].rstrip()
            number = int(match.group(1).translate(TO_ASCII))
            follows_embedded_heading = (
                raw_index == 0 and current is not None and number == current + 1
            )
            if match.start() == 0 or prefix.endswith(".") or follows_embedded_heading:
                matches.append(match)
        if not matches:
            if current and not is_heading(text):
                articles[current].append(text)
            continue
        for index, match in enumerate(matches):
            number = int(match.group(1).translate(TO_ASCII))
            if not 1 <= number <= 600:
                continue
            current = number
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            articles[number] = [text[match.end() : end].strip()]

    if sorted(articles) != list(range(1, 601)):
        missing = [number for number in range(1, 601) if number not in articles]
        raise RuntimeError(f"Incomplete 1311 code; missing: {missing}")

    result = []
    for number in range(1, 601):
        text = strip_trailing_structure_heading(clean(" ".join(articles[number])))
        if number == 600:
            text = re.split(r"\s+چون به موجب قانون ۳۰ فروردین ۱۳۱۰", text, maxsplit=1)[0].strip()
        result.append((number, text))
    return result


def parse_integrated_1347() -> list[tuple[int, str, str | None]]:
    source = CACHE / "commercial_integrated_vakilsoal.html"
    soup = BeautifulSoup(source.read_bytes(), "lxml")
    heading = next(
        h for h in soup.find_all("h2")
        if clean(h.get_text(" ", strip=True)) == "لایحه قانونی اصلاح قسمتی از قانون تجارت"
    )
    elements = [child for child in heading.parent.children if getattr(child, "name", None)]
    start = elements.index(heading) + 1
    marker = re.compile(r"^ماده\s+([۰-۹0-9]+)(?:\s*\(([^)]*)\))?\s*[-–—ـ]\s*")
    articles: dict[int, list[str]] = {}
    labels: dict[int, str | None] = {}
    current = None
    expected = 1

    for element in elements[start:]:
        text = clean(element.get_text(" ", strip=True))
        if not text:
            continue
        match = marker.match(text)
        if match:
            number = int(match.group(1).translate(TO_ASCII))
            # The web page resumes article 94 of the 1311 code after article 300.
            if expected == 301:
                break
            if number != expected:
                if not articles:
                    continue
                raise RuntimeError(f"Expected article {expected}, found {number}")
            current = number
            expected += 1
            articles[number] = [text[match.end() :].strip()]
            labels[number] = match.group(2)
        elif current and element.name == "p":
            articles[current].append(text)

    if expected != 301:
        raise RuntimeError(f"Integrated text stops at article {expected - 1}")
    return [(n, clean(" ".join(articles[n])), labels[n]) for n in range(1, 301)]


def parse_original_1347(
    integrated: list[tuple[int, str, str | None]],
) -> list[tuple[int, str]]:
    marker = re.compile(r"ماده\s+([۰-۹0-9]+)\s*[-–—ـ]\s*")
    articles: dict[int, str] = {}
    for filename in ("commercial_amendment_1347_part1.html", "commercial_amendment_1347_part2.html"):
        soup = BeautifulSoup((CACHE / filename).read_bytes(), "lxml")
        root = soup.select_one(".postcontent") or soup
        text = clean(root.get_text(" ", strip=True))
        matches = []
        for match in marker.finditer(text):
            number = int(match.group(1).translate(TO_ASCII))
            if 1 <= number <= 300:
                matches.append((number, match))
        for index, (number, match) in enumerate(matches):
            end = matches[index + 1][1].start() if index + 1 < len(matches) else len(text)
            body = clean(text[match.end() : end])
            if number == 300:
                body = re.split(r"\s*لایحه قانونی فوق مشتمل", body, maxsplit=1)[0].strip()
            articles[number] = body

    # Article 101 is omitted from the two-part transcription. It was never amended,
    # so the integrated wording is also the original wording.
    articles[101] = {n: text for n, text, _ in integrated}[101]
    if sorted(articles) != list(range(1, 301)):
        missing = [number for number in range(1, 301) if number not in articles]
        raise RuntimeError(f"Incomplete original 1347 text; missing: {missing}")
    return [(number, articles[number]) for number in range(1, 301)]


def replace_penalty_range(text: str, replacement: str) -> str:
    pattern = re.compile(
        r"(جزای[\u200c ]*نقدی\s+از[\u200c ]*)"
        r"[۰-۹0-9][۰-۹0-9/.,٬]*\s+تا\s+[۰-۹0-9][۰-۹0-9/.,٬]*"
        r"(?=\s+ریال)"
    )
    updated, count = pattern.subn(lambda match: match.group(1) + replacement, text)
    if count == 0:
        raise RuntimeError(f"No penalty range found in: {text[:120]}")
    return updated


def write_module(path: Path, docstring: str, assignments: list[tuple[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# -*- coding: utf-8 -*-\n")
        handle.write(f'"""{docstring}"""\n\n')
        for name, value in assignments:
            handle.write(f"{name} = ")
            handle.write(pprint.pformat(value, width=118, sort_dicts=False))
            handle.write("\n\n")


def main() -> None:
    ensure_sources()
    code_original = parse_code_1311()
    code_current = dict(code_original)
    for number, (old_amount, new_amount) in CODE_PENALTIES_1403.items():
        if old_amount not in code_current[number]:
            raise RuntimeError(f"Original penalty phrase not found in code article {number}")
        code_current[number] = code_current[number].replace(old_amount, new_amount, 1)

    integrated = parse_integrated_1347()
    original = parse_original_1347(integrated)
    original_map = dict(original)
    text_1399 = {number: text for number, text, label in integrated if label and "1399" in label}

    current_map = {number: text for number, text, _ in integrated}
    labels = {number: label for number, _, label in integrated}
    # The official national-law tree does not list the purported 1396 change to article 39.
    # Keep the enacted text and record the source discrepancy in docs/sources.md.
    current_map[39] = original_map[39]
    labels[39] = None
    # The 1348 entries are an official corrigendum. Keep the complete enacted wording;
    # this avoids omissions in the integrated transcription (notably article 20's note).
    for number, label in list(labels.items()):
        if label and "1348" in label:
            current_map[number] = original_map[number]
    # Apply the latest official 1403 monetary adjustment.
    for number, amount in PENALTIES_1403.items():
        current_map[number] = replace_penalty_range(current_map[number], amount)
        labels[number] = "اصلاحی جزای نقدی 1403/03/30"

    code_current_list = [(n, code_current[n]) for n in range(1, 601)]
    amendment_current = [(n, current_map[n], labels[n]) for n in range(1, 301)]
    amendment_1399 = [(n, text_1399[n]) for n in sorted(text_1399)]

    SEED.mkdir(parents=True, exist_ok=True)
    write_module(
        SEED / "commercial_code_1311.py",
        "قانون تجارت مصوب ۱۳۱۱: متن کامل ۶۰۰ ماده و متن جاری مواد دارای تعدیل جزای نقدی ۱۴۰۳.",
        [
            ("COMMERCIAL_CODE_1311_ORIGINAL", code_original),
            ("COMMERCIAL_CODE_1311_CURRENT", code_current_list),
            ("COMMERCIAL_CODE_PENALTY_ARTICLES_1403", sorted(CODE_PENALTIES_1403)),
        ],
    )
    write_module(
        SEED / "commercial_amendment_1347.py",
        "لایحه قانونی اصلاح قسمتی از قانون تجارت مصوب ۱۳۴۷: متن ۳۰۰ ماده و نسخه‌های اصلاحی.",
        [
            ("COMMERCIAL_AMENDMENT_1347_ORIGINAL", original),
            ("COMMERCIAL_AMENDMENT_1399_PENALTY_TEXTS", amendment_1399),
            ("COMMERCIAL_AMENDMENT_CURRENT", amendment_current),
            ("COMMERCIAL_AMENDMENT_PENALTY_ARTICLES_1403", sorted(PENALTIES_1403)),
        ],
    )

    print(f"[OK] 1311 code: {len(code_original)} articles")
    print(f"[OK] 1347 amendment bill: {len(amendment_current)} articles")
    print(f"[OK] 1399/1403 penalty histories: {len(amendment_1399)} articles")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise
