# -*- coding: utf-8 -*-
"""Build static seed data for Iran's Electronic Commerce Law and key regulations."""
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

LAW_FILE = CACHE / "ecommerce_law.md"
BYLAW32_FILE = CACHE / "ecommerce_bylaw32.md"
BYLAW3842_FILE = CACHE / "ecommerce_bylaw3842.md"
BYLAW48_FILE = CACHE / "ecommerce_bylaw48.md"

FINE_1399 = {
    68: "دویست و پنجاه میلیون (۲۵۰٬۰۰۰٬۰۰۰) ریال",
    69: "پنجاه میلیون (۵۰٬۰۰۰٬۰۰۰) ریال تا دویست میلیون (۲۰۰٬۰۰۰٬۰۰۰) ریال",
    70: "یکصد میلیون (۱۰۰٬۰۰۰٬۰۰۰) ریال تا دویست و پنجاه میلیون (۲۵۰٬۰۰۰٬۰۰۰) ریال",
    73: "یکصد و پنجاه میلیون (۱۵۰٬۰۰۰٬۰۰۰) ریال",
    74: "یکصد و پنجاه میلیون (۱۵۰٬۰۰۰٬۰۰۰) ریال",
    75: "دویست و پنجاه میلیون (۲۵۰٬۰۰۰٬۰۰۰) ریال",
    76: "یکصد میلیون (۱۰۰٬۰۰۰٬۰۰۰) ریال تا دویست و پنجاه میلیون (۲۵۰٬۰۰۰٬۰۰۰) ریال",
}
FINE_1403 = {
    68: "هشتصد و بیست و پنج میلیون (۸۲۵٬۰۰۰٬۰۰۰) ریال",
    69: "یکصد و شصت و پنج میلیون (۱۶۵٬۰۰۰٬۰۰۰) ریال تا ششصد و شصت میلیون (۶۶۰٬۰۰۰٬۰۰۰) ریال",
    70: "سیصد و سی میلیون (۳۳۰٬۰۰۰٬۰۰۰) ریال تا هشتصد و بیست و پنج میلیون (۸۲۵٬۰۰۰٬۰۰۰) ریال",
    73: "پانصد میلیون (۵۰۰٬۰۰۰٬۰۰۰) ریال",
    74: "پانصد میلیون (۵۰۰٬۰۰۰٬۰۰۰) ریال",
    75: "هشتصد و بیست و پنج میلیون (۸۲۵٬۰۰۰٬۰۰۰) ریال",
    76: "سیصد و سی میلیون (۳۳۰٬۰۰۰٬۰۰۰) ریال تا هشتصد و بیست و پنج میلیون (۸۲۵٬۰۰۰٬۰۰۰) ریال",
}


def clean_markdown(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u200f", "").replace("\u200e", "")
    text = text.replace("��", "د").replace("�", "ی")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^>+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \n-–ـ")


def strip_structure(block: str) -> str:
    heading = re.search(r"(?m)^\s*#{1,6}\s+", block)
    return block[: heading.start()] if heading else block


def parse_law() -> tuple[list[tuple[int, str]], list[tuple[int, str]], dict[int, str]]:
    text = LAW_FILE.read_text(encoding="utf-8").replace("��", "د").replace("�", "ی")
    text = text[text.index("Markdown Content:") + len("Markdown Content:") :]
    marker = re.compile(r"(?m)^\*\*ماده\s*([۰-۹0-9]+)\s*(?:[-ـ]\*\*|\*\*)")
    matches = list(marker.finditer(text))
    numbers = [int(m.group(1).translate(TO_ASCII)) for m in matches]
    if numbers != list(range(1, 82)):
        raise RuntimeError(f"Electronic Commerce Law sequence error: {numbers}")

    raw: dict[int, str] = {}
    for index, match in enumerate(matches):
        number = numbers[index]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = strip_structure(text[match.end() : end])
        # Remove editorial fine-adjustment lines; legal text is transformed below.
        block = re.sub(r"(?m)^\s*جزای نقدی مندرج در این ماده.*$", "", block)
        raw[number] = block

    original: dict[int, str] = {}
    current: dict[int, str] = {}
    for number in range(1, 82):
        block = raw[number]
        if number in (67, 68):
            base = block.split("**تبصره", 1)[0]
            former = re.search(r"متن سابق تبصره\s*[-ـ]?\s*(.*)", block, flags=re.DOTALL)
            original_text = clean_markdown(base)
            if former:
                original_text += " تبصره- " + clean_markdown(former.group(1))
            original[number] = original_text
            current[number] = clean_markdown(base)
        else:
            # Drop any purely editorial historical paragraph but retain operative tabs.
            block = re.sub(r"(?m)^\s*متن سابق.*$", "", block)
            original[number] = clean_markdown(block)
            current[number] = original[number]

    # Ministry merger amendments of 1390.
    current[32] = current[32].replace("وزارتخانه‌های بازرگانی", "وزارتخانه‌های صنعت، معدن و تجارت")
    current[48] = current[48].replace("وزارت بازرگانی", "وزارت صنعت، معدن و تجارت")
    original[32] = current[32].replace("وزارتخانه‌های صنعت، معدن و تجارت", "وزارتخانه‌های بازرگانی")
    original[48] = current[48].replace("وزارت صنعت، معدن و تجارت", "وزارت بازرگانی")

    fine_1399: dict[int, str] = {}
    for number in FINE_1399:
        base = current[number]
        fine_1399[number] = replace_fine(number, base, FINE_1399[number])
        current[number] = replace_fine(number, base, FINE_1403[number])

    return (
        [(n, original[n]) for n in range(1, 82)],
        [(n, current[n]) for n in range(1, 82)],
        fine_1399,
    )


def replace_fine(number: int, text: str, replacement: str) -> str:
    patterns = {
        68: r"پنجاه میلیون\s*\(۵۰\.۰۰۰\.۰۰۰\)\s*ریال",
        69: r"ده میلیون\s*\(۱۰\.۰۰۰\.۰۰۰\)\s*ریال تا پنجاه میلیون\s*\(۵۰\.۰۰۰\.۰۰۰\)\s*ریال",
        70: r"بیست میلیون\s*\(۲۰\.۰۰۰\.۰۰۰\)\s*ریال تا یکصد میلیون\s*\(۱۰۰\.۰۰۰\.۰۰۰\)\s*ریال",
        73: r"پنجاه میلیون\s*\(۵۰\.۰۰۰\.۰۰۰\)\s*ریال",
        74: r"پنجاه میلیون\s*\(۵۰\.۰۰۰\.۰۰۰\)\s*ریال",
        75: r"پنجاه میلیون\s*\(۵۰\.۰۰۰\.۰۰۰\)\s*ریال",
        76: r"بیست میلیون\s*\(۲۰\.۰۰۰\.۰۰۰\)\s*ریال تا یکصد میلیون\s*\(۱۰۰\.۰۰۰\.۰۰۰\)\s*ریال",
    }
    updated, count = re.subn(patterns[number], replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Fine phrase not found in article {number}")
    return updated


def parse_bylaw32() -> tuple[list[tuple[int, str]], list[tuple[int, str]], dict[int, str]]:
    text = BYLAW32_FILE.read_text(encoding="utf-8")
    text = text[text.index("Markdown Content:") + len("Markdown Content:") :]
    starts = [
        "در این آیین‌نامه، اصطلاحات زیر",
        "به منظور حفظ یکپارچگی و سیاستگذاری",
        "وظایف شورا به شرح زیر",
        "سطوح دفاتر خدمات صدور گواهی",
        "وظایف و مسئولیتهای مرکز ریشه",
        "مرکز ریشه به محض قطع عملیات",
        "مراکز میانی حسب مورد توسط",
        "مراکز میانی در حین فعالیت",
        "مجوز مراکز میانی به طور ادواری",
        "مجوز مراکز میانی صرفا",
        "کلیه موسسات اعم از دولتی",
        "دفاتر ثبت‌نام می‌توانند بنا به مورد",
        "وظایف دفاتر ثبت‌نام به شرح زیر",
        "مجوز دفاتر ثبت‌نام حداکثر",
        "دفاتر ثبت‌نام موظفند هنگام ثبت‌نام",
        "حق‌الثبت دفاتر ثبت‌نام",
        "به منظور حفظ محرمانه بودن",
        "اعتبار و پذیرش گواهی الکترونیکی",
        "در موارد زیر با حفظ سوابق موجود",
        "تمامی دستگاههای اجرایی مکلفند",
    ]
    positions = []
    cursor = 0
    for phrase in starts:
        pos = text.find(phrase, cursor)
        if pos < 0:
            raise RuntimeError(f"Bylaw article start not found: {phrase}")
        positions.append(pos)
        cursor = pos + len(phrase)
    original = []
    for index, pos in enumerate(positions):
        end = positions[index + 1] if index + 1 < len(positions) else len(text)
        original.append((index + 1, clean_markdown(text[pos:end])))

    current_map = dict(original)
    versions: dict[int, str] = {}
    # 1393: Foreign Affairs representative added.
    art2_1393 = current_map[2] + " ش- معاون ذی‌ربط وزیر امور خارجه."
    versions[1393] = art2_1393
    # 1394: Interior representative added.
    art2_1394 = art2_1393 + " ص- معاون ذی‌ربط وزیر کشور."
    versions[1394] = art2_1394
    # 1400: Chamber title updated.
    art2_1400 = art2_1394.replace(
        "رییس اتاق بازرگانی و صنایع و معادن ایران",
        "رییس اتاق بازرگانی، صنایع، معادن و کشاورزی ایران (اتاق ایران)",
    )
    current_map[2] = art2_1400
    return original, [(n, current_map[n]) for n in range(1, 21)], versions


def parse_simple_articles(path: Path, start_marker: str, count: int) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    text = text[text.index(start_marker) :]
    marker = re.compile(r"(?m)^(?:\*\*)?ماده\s*([۰-۹0-9]+)\s*‌*[ـ-]‌*(?:\*\*)?\s*")
    matches = list(marker.finditer(text))
    selected = [m for m in matches if 1 <= int(m.group(1).translate(TO_ASCII)) <= count]
    # Stop after first complete sequence.
    sequence = []
    expected = 1
    for match in selected:
        n = int(match.group(1).translate(TO_ASCII))
        if n == expected:
            sequence.append(match)
            expected += 1
            if expected == count + 1:
                break
    if len(sequence) != count:
        raise RuntimeError(f"Could not parse {count} articles from {path.name}")
    rows = []
    for index, match in enumerate(sequence):
        end = sequence[index + 1].start() if index + 1 < len(sequence) else len(text)
        block = strip_structure(text[match.end() : end])
        rows.append((index + 1, clean_markdown(block)))
    return rows


def write_module(path: Path, assignments: list[tuple[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# -*- coding: utf-8 -*-\n")
        handle.write('"""قانون تجارت الکترونیکی و آیین‌نامه‌های اصلی آن."""\n\n')
        for name, value in assignments:
            handle.write(f"{name} = ")
            handle.write(pprint.pformat(value, width=116, sort_dicts=False))
            handle.write("\n\n")


def main() -> None:
    original, current, fines1399 = parse_law()
    bylaw32_original, bylaw32_current, bylaw32_versions = parse_bylaw32()
    bylaw3842_original = parse_simple_articles(BYLAW3842_FILE, "**ماده1-**", 2)
    bylaw3842_current = dict(bylaw3842_original)
    bylaw3842_current[1] = bylaw3842_current[1].replace(
        "هـ ـ نوارهای صوتی و تصویری و نرم افزارهای رایانه ای بسته بندی شده که به وسیله مصرف کننده باز شده باشند.",
        "هـ ـ نوارهای صوتی و تصویری و نرم‌افزارهای رایانه‌ای بسته‌بندی‌شده که به وسیله مصرف‌کننده باز شده باشند و کارت‌های اشتراک رمزدار اینترنتی که بسته‌بندی و رمز آن باز شده باشند.",
    ).replace(
        "از طریق شبکه جامع اطلاع رسانی بازرگانی کشور و پایگاه اطلاع رسانی سازمان یادشده به آگاهی عموم برساند.",
        "از طریق شبکه جامع اطلاع‌رسانی بازرگانی کشور، پایگاه اطلاع‌رسانی سازمان یادشده و روزنامه رسمی جمهوری اسلامی ایران به آگاهی عموم برساند.",
    )
    bylaw48 = parse_simple_articles(BYLAW48_FILE, "ماده ۱ ـ", 5)

    write_module(
        SEED / "ecommerce_law.py",
        [
            ("ECOMMERCE_ORIGINAL_1382", original),
            ("ECOMMERCE_CURRENT", current),
            ("ECOMMERCE_FINE_TEXTS_1399", fines1399),
            ("ECOMMERCE_FINE_ARTICLES", sorted(FINE_1399)),
            ("ECOMMERCE_BYLAW32_ORIGINAL", bylaw32_original),
            ("ECOMMERCE_BYLAW32_CURRENT", bylaw32_current),
            ("ECOMMERCE_BYLAW32_ART2_INTERMEDIATE", bylaw32_versions),
            ("ECOMMERCE_BYLAW3842_ORIGINAL", bylaw3842_original),
            ("ECOMMERCE_BYLAW3842_CURRENT", [(n, bylaw3842_current[n]) for n in (1, 2)]),
            ("ECOMMERCE_BYLAW48", bylaw48),
        ],
    )
    print("[OK] Electronic Commerce Law: 81/81")
    print("[OK] Fine histories: 7 articles (1382/1399/1403); attempt provisions updated 1399")
    print("[OK] Regulations: article 32 bylaw=20, articles 38/42 bylaw=2, article 48 bylaw=5")


if __name__ == "__main__":
    main()
