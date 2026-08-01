# -*- coding: utf-8 -*-
"""Build static seed modules for the Cheque Issuance Law and Sayad regulations.

Maintainer utility. Normal loading uses data/seed/cheque_law.py directly.
Source snapshots under data/source_cache were fetched through the Jina text proxy
because several Iranian legal sites block direct automated retrieval.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
SEED = ROOT / "data" / "seed"
PERSIAN = "۰۱۲۳۴۵۶۷۸۹"
ASCII = "0123456789"
TO_ASCII = str.maketrans(PERSIAN, ASCII)

CURRENT_FILE = CACHE / "cheque_proxy_2.txt"
HISTORY_FILE = CACHE / "cheque_dadgaran.md"
AMEND_1397_FILE = CACHE / "cheque_ekht1397.md"
AMEND_1400_FILE = CACHE / "cheque_ekht1400.md"
ELECTRONIC_FILE = CACHE / "cheque_electronic.md"
CASE_FILE = CACHE / "cheque_case.md"
BYLAW_FILE = CACHE / "cheque_bylaw5.md"
YJC_1404_FILE = CACHE / "cheque_yjc1404.md"


def clean_markdown(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u200f", "").replace("\u200e", "")
    text = text.replace("��", "یا").replace("�", "ی")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^>+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \n-–")


def canonical_key(article_no: str) -> str:
    normalized = article_no.translate(TO_ASCII).replace(" ", "")
    return normalized.replace("مکرر", "bis")


def parse_current_law() -> list[tuple[str, str]]:
    text = CURRENT_FILE.read_text(encoding="utf-8")
    text = text[text.index("Markdown Content:") + len("Markdown Content:") :]
    marker = re.compile(
        r"(?m)^\*\*ماده\s+([۰-۹0-9]+(?:\s+مکرر)?)(?:-\*\*|\*\*)"
    )
    matches = list(marker.finditer(text))
    expected = [
        "1", "2", "3", "3bis", "4", "5", "5bis", "6", "7", "8", "9", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21",
        "21bis", "22", "23", "24", "25",
    ]
    actual = [canonical_key(match.group(1)) for match in matches]
    if actual != expected:
        raise RuntimeError(f"Unexpected current-law articles: {actual}")

    result: dict[str, str] = {}
    raw_blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        number = match.group(1).strip()
        key = canonical_key(number)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        if "**–**" in block[:600]:
            block = block.split("**–**", 1)[1]
        raw_blocks[key] = block

        if key == "21":
            # Remove two editorial historical paragraphs but retain current tab 1 and tab 2.
            block = re.sub(
                r"\nعبارت حذف شده.*?(?=\n\*\*تبصره ۱)", "\n", block,
                flags=re.DOTALL,
            )
            block = re.sub(
                r"\nمتن سابق تبصره ۱.*?(?=\n\*\*تبصره ۲)", "\n", block,
                flags=re.DOTALL,
            )
        else:
            cut_markers = [
                "\nمتن سابق ماده", "\n**متن سابق ماده", "\nعبارت حذف شده",
                "\n> ### قانون استفساریه", "\n### قانون استفساریه",
                "\n#### مستندات مرتبط", "\n### مستندات مرتبط",
            ]
            positions = [block.find(item) for item in cut_markers if block.find(item) >= 0]
            if positions:
                block = block[: min(positions)]
        if key == "25":
            for ending in ("\n###", "\n##", "\n* * *"):
                if ending in block:
                    block = block.split(ending, 1)[0]
        result[key] = clean_markdown(block)

    # The web consolidation embeds explanatory 1403 notes in article 7. A clean
    # current version is built later from the enacted 1382 version and the official
    # 1403 monetary-adjustment table.
    return [(number, result[canonical_key(number)]) for number, _ in [
        (match.group(1).strip(), None) for match in matches
    ]]


def parse_original_1355() -> list[tuple[int, str]]:
    text = HISTORY_FILE.read_text(encoding="utf-8")
    start = text.index("### متن قانون صدور چک مصوب تیرماه سال ۵۵")
    end = text.index("### اصلاحیه قانون صدور چک مصوب ۱۳۷۲", start)
    section = text[start:end]
    marker = re.compile(r"(?m)^\s*‌?\*\*\s*‌?ماده\s+([۰-۹0-9]+)\s*[–-]\*\*")
    matches = list(marker.finditer(section))
    if [int(m.group(1).translate(TO_ASCII)) for m in matches] != list(range(1, 23)):
        raise RuntimeError("The original 1355 text is not a complete 1-22 sequence")
    rows = []
    for index, match in enumerate(matches):
        end_pos = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = section[match.end() : end_pos]
        if int(match.group(1).translate(TO_ASCII)) == 22:
            block = block.split("قانون فوق مشتمل", 1)[0]
        rows.append((int(match.group(1).translate(TO_ASCII)), clean_markdown(block)))
    return rows


def parse_plain_replacements(section: str) -> dict[str, str]:
    marker = re.compile(
        r"(?m)^\s*‌?ماده\s+([۰-۹0-9]+(?:\s+مکرر)?)\s*[–-]\s*"
    )
    matches = list(marker.finditer(section))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = section[match.end() : end]
        # Outer amendment article begins at a bold marker and must not leak in.
        bold = re.search(r"(?m)^\s*\*\*", block)
        if bold:
            block = block[: bold.start()]
        result[canonical_key(match.group(1))] = clean_markdown(block)
    return result


def section_between(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def parse_outer_amendment_articles(section: str, count: int) -> list[tuple[int, str]]:
    marker = re.compile(r"(?m)^\s*‌?\*\*\s*‌?ماده\s*([۰-۹0-9]+)\s*[–ـ-]?\*\*")
    all_matches = list(marker.finditer(section))
    selected = []
    search_from = 0
    for expected in range(1, count + 1):
        for match in all_matches[search_from:]:
            if int(match.group(1).translate(TO_ASCII)) == expected:
                selected.append(match)
                search_from = all_matches.index(match) + 1
                break
        else:
            raise RuntimeError(f"Missing amendment article {expected}")
    rows = []
    for index, match in enumerate(selected):
        end = selected[index + 1].start() if index + 1 < len(selected) else len(section)
        rows.append((index + 1, clean_markdown(section[match.end() : end])))
    return rows


def parse_numbered_articles(path: Path, start_text: str, stop_text: str | None = None) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    start = text.index(start_text)
    text = text[start:]
    if stop_text and stop_text in text:
        text = text[: text.index(stop_text)]
    marker = re.compile(r"(?m)^\s*(?:\*\*)?ماده\s+([۰-۹0-9]+)\s*(?:\*\*)?\s*[–-](?:\*\*)?\s*")
    matches = list(marker.finditer(text))
    rows = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        # Structural chapter headings belong between articles, not to the prior article.
        chapter = re.search(r"(?m)^\s*#{0,6}\s*فصل\s+", block)
        if chapter:
            block = block[: chapter.start()]
        rows.append((int(match.group(1).translate(TO_ASCII)), clean_markdown(block)))
    return rows


def current_article7(version_1382: str) -> str:
    text = version_1382
    replacements = [
        (
            r"کمتر از ده میلیون\s*\([^)]*\)\s*ریال",
            "کمتر از هفتصد و هشتاد میلیون (۷۸۰٬۰۰۰٬۰۰۰) ریال",
        ),
        (
            r"از ده میلیون\s*\([^)]*\)\s*ریال تا پنجاه[‌ ]*میلیون\s*\([^)]*\)\s*ریال",
            "از هفتصد و هشتاد میلیون (۷۸۰٬۰۰۰٬۰۰۰) ریال تا سه میلیارد و نهصد میلیون (۳٬۹۰۰٬۰۰۰٬۰۰۰) ریال",
        ),
        (
            r"از پنجاه میلیون\s*\([^)]*\)\s*ریال بیشتر",
            "از سه میلیارد و نهصد میلیون (۳٬۹۰۰٬۰۰۰٬۰۰۰) ریال بیشتر",
        ),
    ]
    for pattern, replacement in replacements:
        text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            raise RuntimeError(f"Could not update article 7 amount: {pattern}")
    return text


def write_module(path: Path, assignments: list[tuple[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# -*- coding: utf-8 -*-\n")
        handle.write('"""قانون صدور چک، تاریخچه اصلاحات و مقررات منتخب سامانه صیاد."""\n\n')
        for name, value in assignments:
            handle.write(f"{name} = ")
            handle.write(pprint.pformat(value, width=116, sort_dicts=False))
            handle.write("\n\n")


def main() -> None:
    required = [CURRENT_FILE, HISTORY_FILE, AMEND_1397_FILE, AMEND_1400_FILE,
                ELECTRONIC_FILE, CASE_FILE, BYLAW_FILE, YJC_1404_FILE]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing cached sources: " + ", ".join(missing))

    current_rows = parse_current_law()
    current = {canonical_key(number): text for number, text in current_rows}
    original = parse_original_1355()

    history_text = HISTORY_FILE.read_text(encoding="utf-8")
    sec1372 = section_between(history_text, "### اصلاحیه قانون صدور چک مصوب ۱۳۷۲", "### قانون استفساریه")
    sec1382 = section_between(history_text, "### اصلاحیه قانون صدور چک مصوب سال ۱۳۸۲", "### قانون جدید")
    rep1372 = parse_plain_replacements(sec1372)
    rep1382 = parse_plain_replacements(sec1382)

    # Added article 1 of 1372 is the current article without the 1397 electronic-check note.
    rep1372["1"] = current["1"].split("تبصره", 1)[0].strip()
    # Amendments 1382 that modify only part of an existing provision are represented
    # by their complete consolidated wording.
    for key in ("3", "12", "22"):
        rep1382[key] = current[key]

    amendment1397_text = AMEND_1397_FILE.read_text(encoding="utf-8")
    amendment1397_main = amendment1397_text[amendment1397_text.index("Markdown Content:") :]
    rep1397_plain = parse_plain_replacements(amendment1397_main)

    # Build complete stages for article 21.
    rep1372_article21 = rep1372["21"]
    rep1397_article21 = current["21"]
    current["21"] = rep1397_article21

    # 1397 and 1400 versions of article 6 and article 21 bis.
    rep1397 = {
        "1": current["1"], "4": current["4"], "5": current["5"],
        "5bis": current["5bis"], "6": rep1397_plain["6"],
        "21": rep1397_article21, "21bis": rep1397_plain["21bis"],
        "23": current["23"], "25": current["25"],
    }
    rep1400 = {"6": current["6"], "21bis": current["21bis"], "24": current["24"]}

    # Current article 7 after the 1403 monetary adjustment.
    rep1382["7"] = rep1382["7"]
    current["7"] = current_article7(rep1382["7"])

    # Article 2 and article 14 consolidations from 1376.
    rep1376 = {"2": current["2"], "14": current["14"]}

    # Full amendment instruments.
    amend1372_rows = parse_outer_amendment_articles(sec1372, 8)
    amend1382_rows = parse_outer_amendment_articles(sec1382, 8)
    sec1397_start = amendment1397_main.index("# قانون اصلاح قانون صدور چک") if "# قانون اصلاح قانون صدور چک" in amendment1397_main else 0
    sec1397 = amendment1397_main[sec1397_start:]
    if "قانون فوق مشتمل بر یازده ماده" in sec1397:
        sec1397 = sec1397[:sec1397.index("قانون فوق مشتمل بر یازده ماده")]
    amend1397_rows = parse_outer_amendment_articles(sec1397, 11)

    # 1400 act: three outer articles use unusual split bold tags.
    text1400 = AMEND_1400_FILE.read_text(encoding="utf-8")
    start1400 = text1400.index("**ماده****۱-")
    end1400 = text1400.index("قانون فوق مشتمل بر سه ماده", start1400)
    sec1400 = text1400[start1400:end1400]
    marker1400 = re.compile(r"\*\*ماده\*\*\*\*([۱۲۳123])-\*\*")
    m1400 = list(marker1400.finditer(sec1400))
    amend1400_rows = []
    for index, match in enumerate(m1400):
        end = m1400[index + 1].start() if index + 1 < len(m1400) else len(sec1400)
        amend1400_rows.append((index + 1, clean_markdown(sec1400[match.end():end])))
    if len(amend1400_rows) != 3:
        raise RuntimeError("Could not parse the three-article 1400 amendment")

    # Regulations.
    electronic = parse_numbered_articles(
        ELECTRONIC_FILE, "ماده ۱- در این «دستورالعمل»", "#### بیشتر بخوانید"
    )
    case_rows = parse_numbered_articles(
        CASE_FILE, "ماده ۱- در این دستور العمل", "مقررات ناظر بر اعطای «چک موردی»"
    )
    case_map = dict(case_rows)
    case_map[11] = (
        "چک موردی غیرقابل انتقال به غیر بوده و صرفاً توسط شخصی که چک موردی در وجه او صادر شده است، "
        "قابل تسویه می‌باشد."
    )
    case_rows = [(number, case_map[number]) for number in range(1, 15)]

    bylaw = parse_numbered_articles(
        BYLAW_FILE, "**ماده ۱-**", "**ماده ۵ مکرر قانون صدور چک:**"
    )
    if [n for n, _ in bylaw] != list(range(1, 11)):
        raise RuntimeError(f"Unexpected bylaw articles: {[n for n, _ in bylaw]}")

    sayad_1404_summary = (
        "این دستورالعمل در جلسه سی‌ونهم مورخ ۱۴۰۴/۰۶/۱۸ هیأت عالی بانک مرکزی تصویب و مفاد دستورالعمل "
        "اجرایی ماده (۶) مصوب ۱۳۹۹ را با دستورالعمل حساب جاری تلفیق کرد. محورهای ابلاغ‌شده عبارت‌اند از: "
        "تعریف و تنظیم سامانه صیاد، چک صیادی و سامانه چکاوک؛ حذف الزام ارائه معرف برای افتتاح حساب جاری؛ "
        "تعریف حساب پشتیبان؛ بازنویسی شرایط افتتاح حساب جاری و اعطای دسته‌چک؛ اعتبارسنجی و تعیین سقف اعتبار؛ "
        "تعیین تکلیف مغایرت نسخه کاغذی با اطلاعات صیاد و چک ثبت‌نشده؛ اصلاح راهکارهای رفع سوءاثر؛ افزودن "
        "مقررات فوت و حجر؛ و محدود کردن تعداد دسته‌چک‌های قابل دریافت. متن حاضر خلاصه رسمی ابلاغ است و نه "
        "رونوشت کامل PDF پیوست بخشنامه."
    )

    # Preserve the order used on the face of the current law.
    current_order = [canonical_key(number) for number, _ in current_rows]
    current_rows_clean = [(number, current[canonical_key(number)]) for number, _ in current_rows]

    write_module(
        SEED / "cheque_law.py",
        [
            ("CHEQUE_ORIGINAL_1355", original),
            ("CHEQUE_CURRENT", current_rows_clean),
            ("CHEQUE_CURRENT_ORDER", current_order),
            ("CHEQUE_REPLACEMENTS_1372", rep1372),
            ("CHEQUE_REPLACEMENTS_1376", rep1376),
            ("CHEQUE_REPLACEMENTS_1382", rep1382),
            ("CHEQUE_REPLACEMENTS_1397", rep1397),
            ("CHEQUE_REPLACEMENTS_1400", rep1400),
            ("CHEQUE_AMENDMENT_1372", amend1372_rows),
            ("CHEQUE_AMENDMENT_1382", amend1382_rows),
            ("CHEQUE_AMENDMENT_1397", amend1397_rows),
            ("CHEQUE_AMENDMENT_1400", amend1400_rows),
            ("CHEQUE_ELECTRONIC_INSTRUCTION_1402", electronic),
            ("CHEQUE_CASE_RULES_1400", case_rows),
            ("CHEQUE_ART5BIS_BYLAW_1398", bylaw),
            ("SAYAD_CURRENT_ACCOUNT_1404_SUMMARY", sayad_1404_summary),
        ],
    )

    print(f"[OK] Current Cheque Law: {len(current_rows_clean)} provisions")
    print(f"[OK] Original 1355 law: {len(original)} articles")
    print(f"[OK] Amendment acts: {len(amend1372_rows)} + {len(amend1382_rows)} + {len(amend1397_rows)} + {len(amend1400_rows)}")
    print(f"[OK] Regulations: electronic={len(electronic)}, case={len(case_rows)}, bylaw={len(bylaw)}")


if __name__ == "__main__":
    main()
