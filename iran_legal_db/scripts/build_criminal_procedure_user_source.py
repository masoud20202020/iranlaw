#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the source-backed article payload for materials 1–317 of the Criminal Procedure Code.

The user supplied the section pages from NovinLaw in chat.  The section files in
``data/source_cache`` are kept as the auditable raw layer; this builder only
removes the page headers and splits the text at article headings.  It deliberately
fails closed when a section is missing or when the contiguous article range is
not complete.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUTPUT = ROOT / "data" / "seed" / "criminal_procedure_user_source.py"

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
PERSIAN = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ARTICLE_RE = re.compile(r"^\s*ماده\s+\(?\s*([۰-۹0-9]+)\s*\)?\s*$")
SOURCE_RE = re.compile(r"^-\s*منبع:\s*(\S+)")

# Files are ordered by article range.  Keeping the source URLs in each file
# makes the generated article-level provenance explicit.
FILES = [
    "criminal_procedure_user_380_382.md",
    "criminal_procedure_user_383.md",
    "criminal_procedure_user_384.md",
    "criminal_procedure_user_385.md",
    "criminal_procedure_user_386.md",
    "criminal_procedure_user_387.md",
    "criminal_procedure_user_388.md",
    "criminal_procedure_user_389.md",
    "criminal_procedure_user_390.md",
    "criminal_procedure_user_391_392.md",
    "criminal_procedure_user_393.md",
]

BASE_URL = "https://www.novinlaw.ir/rules/legals/%D9%82%D9%88%D8%A7%D9%86%DB%8C%D9%86-%D9%88-%D9%85%D9%82%D8%B1%D8%B1%D8%A7%D8%AA/childs/show/"
URL_BY_FILE_RANGE = {
    "criminal_procedure_user_380_382.md": (
        (1, 7, BASE_URL + "380"),
        (8, 21, BASE_URL + "381"),
        (22, 27, BASE_URL + "382"),
    ),
    "criminal_procedure_user_391_392.md": (
        (285, 287, BASE_URL + "391"),
        (288, 293, BASE_URL + "392"),
    ),
}


def clean_line(value: str) -> str:
    return (
        value.replace("\ufeff", "")
        .replace("\r", "")
        .replace("\u00ad", "")
        .replace("\\_", "_")
        .strip()
    )


def normalize_body(lines: list[str]) -> str:
    out: list[str] = []
    for raw in lines:
        line = raw.replace("\r", "").replace("\ufeff", "").strip()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        # Raw source metadata and Markdown headings are provenance, not legal text.
        if line.startswith("#") or line.startswith("-") and (
            line.startswith("- منبع:") or line.startswith("- عنوان منبع:")
        ):
            continue
        if line.startswith("================================================================"):
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def parse_file(path: Path) -> tuple[list[tuple[int, str]], dict[int, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    source_url = ""
    for line in lines:
        match = SOURCE_RE.match(line.strip())
        if match:
            source_url = match.group(1)
            break
    if not source_url:
        raise SystemExit(f"missing source URL: {path}")

    heads: list[tuple[int, int]] = []
    for index, raw in enumerate(lines):
        match = ARTICLE_RE.match(clean_line(raw))
        if match:
            heads.append((index, int(match.group(1).translate(DIGITS))))
    if not heads:
        raise SystemExit(f"no article headings: {path}")

    rows: list[tuple[int, str]] = []
    notes: dict[int, str] = {}
    for position, (start, number) in enumerate(heads):
        end = heads[position + 1][0] if position + 1 < len(heads) else len(lines)
        body = normalize_body(lines[start + 1 : end])
        if not body:
            raise SystemExit(f"empty article {number}: {path}")
        rows.append((number, body))
        url = source_url
        for low, high, candidate in URL_BY_FILE_RANGE.get(path.name, ()):
            if low <= number <= high:
                url = candidate
                break
        notes[number] = (
            f"منبع برخط نوین‌لاو، صفحه بخش مواد {number}؛ {url}. "
            "متن از منبع ارسالی کاربر پاک‌سازی حداقلی شده است؛ برای استناد رسمی با روزنامه رسمی مقابله شود."
        )
    return rows, notes


def main() -> None:
    all_rows: dict[int, str] = {}
    source_notes: dict[int, str] = {}
    for name in FILES:
        rows, notes = parse_file(CACHE / name)
        for number, text in rows:
            if number in all_rows:
                raise SystemExit(f"duplicate article heading: {number}")
            all_rows[number] = text
            source_notes[number] = notes[number]

    expected = set(range(1, 318))
    actual = set(all_rows)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise SystemExit(f"article range mismatch; missing={missing}, extra={extra}")

    rows = [(number, all_rows[number]) for number in sorted(all_rows)]
    OUTPUT.write_text(
        "# -*- coding: utf-8 -*-\n"
        "\"\"\"Generated by build_criminal_procedure_user_source.py.\"\"\"\n\n"
        "ARTICLES_1_317 = " + pprint.pformat(rows, width=120, sort_dicts=False) + "\n\n"
        "SOURCE_NOTE_BY_ARTICLE = " + pprint.pformat(source_notes, width=120, sort_dicts=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] built source payload: {len(rows)} articles (1–317)")
    print(f"[OK] output: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
