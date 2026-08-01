# -*- coding: utf-8 -*-
"""Build static seeds for the Social Security Law and retirement reforms."""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUT = ROOT / "data" / "seed" / "social_security.py"
FA_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ASCII_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
MISSING_MAIN = (14, 15, 18, 22, 49, 84, 106, 107, 113)


def strip_md(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("__", "").replace("\\-", "-").strip()


def clean(text: str) -> str:
    replacements = {
        "ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "هٔ", "\ufeff": "", "\u00ad": "",
        "\u200e": "‌", "\u200f": "‌", "‎": "‌", "‏": "‌",
        "آئین": "آیین", "هیات": "هیأت", "مسوول": "مسئول", "تامین": "تأمین",
        "میباشد": "می‌باشد", "میشود": "می‌شود", "میشوند": "می‌شوند",
        "میگردد": "می‌گردد", "میکند": "می‌کند", "میتواند": "می‌تواند",
        "میدارند": "می‌دارند", "می نماید": "می‌نماید",
        "می شود": "می‌شود", "می گردد": "می‌گردد", "می باشد": "می‌باشد",
        "نمی باشد": "نمی‌باشد", "بموجب": "به موجب", "بعهده": "به عهده",
        "بسازمان": "به سازمان", "بتصویب": "به تصویب", "بترتیب": "به ترتیب",
        "بمیزان": "به میزان", "بوسیله": "به وسیله", "بعلت": "به علت",
        "بکار": "به کار", "بشرح": "به شرح", "بقوت": "به قوت", "بوجوه": "به وجوه",
        "بدستور": "به دستور", "بحساب": "به حساب", "بحکم": "به حکم", "بسبب": "به سبب",
        "بحبس": "به حبس", "بجای": "به جای", "بجای": "به جای", "بوسیله": "به وسیله",
        "لازم الاجرا": "لازم‌الاجرا", "ذی ربط": "ذی‌ربط", "ذیربط": "ذی‌ربط",
        "غیر نقدی": "غیرنقدی", "از کار افتادگی": "ازکارافتادگی",
        "از کار افتاده": "ازکارافتاده", "از کار افتادگان": "ازکارافتادگان",
        "حقّ": "حق", "راساً": "رأساً", "شواریعالی": "شورای عالی",
        "شورایعالی": "شورای عالی", "موسسات": "مؤسسات", "موسسه": "مؤسسه",
        "دارائی": "دارایی", "منحصرأ": "منحصراً", "هیجده": "هجده",
        "و ظایف": "وظایف", "و زارت": "وزارت", "محل و جوه": "محل وجوه",
        "آیین نامهمدت": "آیین‌نامه\nمدت", "مشمولقانون": "مشمول قانون",
        "بیمه پرداز": "بیمه‌پرداز", "بیمه پردازی": "بیمه‌پردازی",
        "صندوق های": "صندوق‌های", "سازمان ها": "سازمان‌ها", "دستگاه ها": "دستگاه‌ها",
        "هم آهنگ": "هماهنگ", "ذخائر": "ذخایر", "اجراء": "اجرا",
        "بیمه های": "بیمه‌های", "سازمانهای": "سازمان‌های", "کمیسیونهای": "کمیسیون‌های",
        "شرکتهای": "شرکت‌های", "ششماه": "شش ماه", "یکجا": "یکجا", "مادامیکه": "مادامی که",
        "حق  بیمه": "حق بیمه", "بارمالی": "بار مالی", "جزه": "جزء",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove source editorial amendment/repeal labels but retain the legal text.
    text = re.sub(r"\[(?:اصلاحی(?: جزای نقدی)?|الحاقی|منسوخ)[^]]*\]\s*[-–]?\s*", "", text)
    text = re.sub(r"\s*\((?:اصلاحی|الحاقی|منسوخ)[^)]*\)\s*[–-]?", "", text)
    text = re.sub(r"^([0-9۰-۹]+)\.\s+", r"\1- ", text, flags=re.M)
    text = re.sub(r"تبصره\s*([0-9۰-۹]+)\s*[-ـ]?\s*", r"تبصره \1- ", text)
    text = re.sub(r"^ب\s+(?=صاحبان)", "ب- ", text, flags=re.M)
    text = re.sub(r"‌+", "‌", text)
    text = re.sub(r"[ \t]*‌[ \t]*", "‌", text)
    text = re.sub(r"(^|\n)‌", r"\1", text)
    text = re.sub(r"([)\]،؛:.])‌", r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.translate(ASCII_TO_FA)
    text = re.sub(r"(?<=[۰-۹]),(?=[۰-۹])", "٬", text)
    return text.strip()


def parse_main_social_security() -> dict[int, str]:
    articles: dict[int, list[str]] = {}
    current = None
    lines = (CACHE / "social_security_bidbarg.md").read_text(encoding="utf-8").splitlines()
    for raw in lines:
        match = re.match(r"^#### \[ماده ([۰-۹0-9]+) قانون", raw)
        if match:
            current = int(match.group(1).translate(FA_TO_ASCII))
            articles[current] = []
            continue
        if current is None:
            continue
        line = strip_md(raw)
        if not line or line == "* * *":
            continue
        if line.startswith(("قانون فوق مشتمل", "رئیس مجلس شورای ملی", "Image ")):
            current = None
            continue
        if line.startswith("#") or "https://" in line:
            continue
        articles[current].append(line)

    for n in MISSING_MAIN:
        path = CACHE / f"social_security_article_{n}.md"
        parts = []
        active = False
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = strip_md(raw)
            if line.startswith(f"## متن ماده {str(n).translate(ASCII_TO_FA)}"):
                active = True
                continue
            if active and (line.startswith("اشتراک‌گذاری") or line.startswith("[ماده ")):
                break
            if active and line and not line.startswith("#") and "https://" not in line:
                parts.append(line)
        if not parts:
            raise ValueError(f"missing individual article {n}")
        articles[n] = parts

    missing = sorted(set(range(1, 119)) - set(articles))
    if missing:
        raise ValueError(f"Social Security coverage missing: {missing}")
    result = {n: clean("\n".join(articles[n])) for n in range(1, 119)}
    if result[76].startswith("۱- مشمولین این قانون"):
        result[76] = result[76][3:].lstrip()
    return result


def drop_ranges(text: str, start_prefixes: tuple[str, ...], end_prefixes: tuple[str, ...] | None = None) -> str:
    out = []
    dropping = False
    for line in text.splitlines():
        if line.startswith(start_prefixes):
            dropping = True
            if end_prefixes is None:
                continue
        if dropping and end_prefixes and line.startswith(end_prefixes):
            dropping = False
        if not dropping:
            out.append(line)
    return "\n".join(out).strip()


def current_after_1403(base: dict[int, str]) -> dict[int, str]:
    current = dict(base)
    # Article 4: earlier repealed clause b and note 3 are already out; note 4 was repealed in 1403.
    current[4] = "\n".join(
        line for line in base[4].splitlines()
        if not line.startswith(("ب-", "ب -", "ب صاحبان", "تبصره ۳", "تبصره ۴"))
    ).strip()
    current[58] = "\n".join(
        line for line in base[58].splitlines() if not line.startswith(("الف- کمتر", "الف - کمتر"))
    ).strip()
    current[76] = "\n".join(
        line for line in base[76].splitlines() if not line.startswith(("۱- حداقل", "۱ - حداقل"))
    ).strip()
    current[81] = drop_ranges(base[81], ("۱- عیال", "۱ - عیال"), ("۲- فرزندان", "۲ - فرزندان"))
    current[82] = drop_ranges(base[82], ("۲- فرزندان", "۲ - فرزندان"), ("۳- پدر", "۳ - پدر"))
    return current


def pre_1403_partial(base: dict[int, str]) -> dict[int, str]:
    result = {n: base[n] for n in (4, 58, 76, 81, 82)}
    # Clause b and note 3 of article 4 had already been repealed in 1365.
    result[4] = "\n".join(
        line for line in base[4].splitlines() if not line.startswith(("ب-", "ب -", "ب صاحبان", "تبصره ۳"))
    ).strip()
    return result


def parse_invalid_list() -> str:
    lines = (CACHE / "social_security_invalid_1403.md").read_text(encoding="utf-8").splitlines()
    active = False
    parts = []
    for raw in lines:
        line = strip_md(raw)
        if line.startswith("ماده واحده-"):
            active = True
        if active and line.startswith("قانون فوق مشتمل"):
            break
        if active and line and not line.startswith("#") and "https://" not in line:
            parts.append(line)
    text = clean("\n".join(parts))
    if not all(f"{str(n).translate(ASCII_TO_FA)}-" in text for n in (1, 23, 71)):
        raise ValueError("invalid-provisions appendix incomplete")
    return text


def parse_bylaw() -> tuple[tuple[int, str], ...]:
    wanted = set(range(1, 8))
    articles: dict[int, list[str]] = {}
    current = None
    for raw in (CACHE / "retirement_years_bylaw_1403.md").read_text(encoding="utf-8").splitlines():
        line = strip_md(raw)
        match = re.match(r"^ماده\s*([۰-۹0-9]+)\s*[ـ–-]\s*(.*)$", line)
        if match:
            n = int(match.group(1).translate(FA_TO_ASCII))
            current = n if n in wanted else None
            if current:
                articles[current] = [match.group(2)] if match.group(2) else []
            continue
        if current is None or not line:
            continue
        if line.startswith(("#", "معاون اول رئیس جمهور", "محمدرضا عارف")):
            if line.startswith(("معاون اول", "محمدرضا")):
                current = None
            continue
        if "https://" in line:
            continue
        articles[current].append(line)
    if set(articles) != wanted:
        raise ValueError(f"retirement bylaw coverage: {sorted(articles)}")
    return tuple((n, clean("\n".join(articles[n]))) for n in range(1, 8))


def parse_program_article29() -> str:
    lines = (CACHE / "program7_article29_retirement.md").read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("Markdown Content:") + 1
    except ValueError:
        raise ValueError("program article 29 content marker")
    parts = [strip_md(x) for x in lines[start:] if strip_md(x)]
    return clean("\n".join(parts))


def main() -> None:
    base = parse_main_social_security()
    current = current_after_1403(base)
    partial_old = pre_1403_partial(base)
    invalid_text = parse_invalid_list()
    bylaw = parse_bylaw()
    article29 = parse_program_article29()

    values = {
        "SOCIAL_SECURITY_INTEGRATED_PRE1403": tuple(sorted(base.items())),
        "SOCIAL_SECURITY_CURRENT": tuple(sorted(current.items())),
        "SOCIAL_SECURITY_PARTIAL_PRE1403": partial_old,
        "SOCIAL_SECURITY_WHOLE_REPEALED": tuple(sorted({9, 11, *range(12, 28), 46, 86, 92, 98, 99, 100})),
        "SOCIAL_SECURITY_PARTIAL_1403": (4, 58, 76, 81, 82),
        "INVALID_SOCIAL_SECURITY_1403": invalid_text,
        "PROGRAM7_ARTICLE29": article29,
        "RETIREMENT_YEARS_BYLAW": bylaw,
    }
    header = '''# -*- coding: utf-8 -*-\n"""Generated static texts for Social Security and retirement reforms."""\n# Generated by scripts/build_social_security_seeds.py from cached sources.\n\n'''
    body = "".join(
        f"{name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n\n"
        for name, value in values.items()
    )
    OUT.write_text(header + body, encoding="utf-8")
    current_count = 118 - len(values["SOCIAL_SECURITY_WHOLE_REPEALED"])
    print(f"[OK] Social Security coverage=118; current={current_count}; whole repealed={len(values['SOCIAL_SECURITY_WHOLE_REPEALED'])}")
    print("[OK] Partial 1403 histories=5; invalid list=71 rows; program article/bylaw=1/7")
    print(f"[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
