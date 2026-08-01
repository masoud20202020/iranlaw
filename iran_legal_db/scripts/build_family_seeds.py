# -*- coding: utf-8 -*-
"""Build static seeds for family protection and non-contentious matters."""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUT = ROOT / "data" / "seed" / "family_law.py"
FA_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ASCII_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def strip_md(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("__", "").replace("\\-", "-").strip()


def clean(text: str) -> str:
    replacements = {
        "ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "هٔ", "\ufeff": "", "\u00ad": "",
        "\u200e": "‌", "\u200f": "‌", "‎": "‌", "‏": "‌",
        "آئین": "آیین", "هیات": "هیأت", "مسوول": "مسئول", "مسئولیت": "مسئولیت",
        "میباشد": "می‌باشد", "میشود": "می‌شود", "میشوند": "می‌شوند",
        "میگردد": "می‌گردد", "میکند": "می‌کند", "میتواند": "می‌تواند",
        "مینماید": "می‌نماید", "می نماید": "می‌نماید", "می شود": "می‌شود",
        "می گردد": "می‌گردد", "می باشد": "می‌باشد", "نمی باشد": "نمی‌باشد",
        "بموجب": "به موجب", "بعهده": "به عهده", "بدادگاه": "به دادگاه",
        "بنام": "به نام", "بوسیله": "به وسیله", "بموقع": "به موقع",
        "باداره": "به اداره", "بامور": "به امور", "بانجام": "به انجام",
        "بدرخواست": "به درخواست", "بتصدیق": "به تصدیق", "بآگهی": "به آگهی",
        "لازم الاجرا": "لازم‌الاجرا", "ذینفع": "ذی‌نفع", "ذی نفع": "ذی‌نفع",
        "صورتجلسه": "صورت‌جلسه", "صورت مجلس": "صورت‌جلسه", "مجهول المکان": "مجهول‌المکان",
        "حق الزحمه": "حق‌الزحمه", "غیر منقول": "غیرمنقول", "غیر منقوله": "غیرمنقوله",
        "وصیت نامه": "وصیت‌نامه", "انحصار وراثت": "انحصار وراثت",
        "دادکاه": "دادگاه", "تحیر ترکه": "تحریر ترکه", "اسناد سمی": "اسناد رسمی",
        "کانون وکلاء": "کانون وکلای", "بعمل": "به عمل", "بعمل آمده": "به عمل آمده",
        "قبلا": "قبلاً", "عملا": "عملاً", "اصولا": "اصولاً", "راساً": "رأساً",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s*\((?:اصلاحی|الحاقی|منسوخه?)[^)]*\)\s*[ـ–-]?", "", text)
    text = re.sub(r"‌+", "‌", text)
    text = re.sub(r"[ \t]*‌[ \t]*", "‌", text)
    text = re.sub(r"(^|\n)‌", r"\1", text)
    text = re.sub(r"([)\]،؛:.])‌", r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.translate(ASCII_TO_FA)
    return text.strip()


def parse_standard(path: Path, wanted: set[int], first_only=True) -> dict[int, str]:
    articles: dict[int, list[str]] = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = strip_md(raw)
        marker = line.lstrip("‌ #")
        match = re.match(r"^(?:\([^)]*\)\s*)?ماده\s*([۰-۹0-9]+)(?:\s*\([^)]*\))?\s*[ـ–-]\s*(.*)$", marker)
        if match:
            n = int(match.group(1).translate(FA_TO_ASCII))
            if n in wanted and (not first_only or n not in articles):
                current = n
                articles[n] = [match.group(2)] if match.group(2) else []
            else:
                current = None
            continue
        if current is None or not line:
            continue
        if line.startswith("#") or re.match(r"^(فصل|مبحث|باب)\s", line):
            continue
        if line.startswith(("قانون فوق مشتمل", "این قانون که مشتمل", "رئیس مجلس", "رئیس قوه", "محمدکاظم", "* * *")):
            current = None
            continue
        if "https://" in line or "](http" in line:
            continue
        articles[current].append(line)
    missing = sorted(wanted - set(articles))
    if missing:
        raise ValueError(f"missing in {path.name}: {missing}")
    return {n: clean("\n".join(articles[n])) for n in sorted(wanted)}


def parse_all_occurrences(path: Path) -> dict[int, list[str]]:
    occurrences: dict[int, list[list[str]]] = {}
    current = None
    current_parts = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = strip_md(raw)
        marker = line.lstrip("‌ #")
        match = re.match(r"^ماده\s*([۰-۹0-9]+)(?:\s*\([^)]*\))?\s*[ـ–-]\s*(.*)$", marker)
        if match:
            n = int(match.group(1).translate(FA_TO_ASCII))
            if 1 <= n <= 69:
                current = n
                current_parts = [match.group(2)] if match.group(2) else []
                occurrences.setdefault(n, []).append(current_parts)
            else:
                current = None; current_parts = None
            continue
        if current is None or not line:
            continue
        if line.startswith("#") or re.match(r"^(فصل|مبحث)\s", line):
            continue
        if line.startswith(("این آیین نامه مشتمل", "در اجرای ماده ۱۷", "* * *")):
            current = None; current_parts = None
            continue
        if "https://" in line or "](http" in line:
            continue
        current_parts.append(line)
    return {n: [clean("\n".join(parts)) for parts in groups] for n, groups in occurrences.items()}


def update_bylaw(base: dict[int, str], occ: dict[int, list[str]]) -> dict[int, str]:
    current = dict(base)
    current[10] = occ[10][-1].split("\n۲ـ در بند ز", 1)[0].strip()
    current[47] = occ[47][-1]
    current[32] = base[32].replace("هر سه سال یکبار", "هر سال یک بار") + (
        "\nم ـ بررسی مدارک و احراز شرایط متقاضیان اعضای مشاوره خانواده."
        "\nن ـ بررسی اولیه شکایت مطرح‌شده علیه مشاوران خانواده و در صورت اقتضا اعلام تخلفات آنان به دادسرا جهت رسیدگی."
        "\nس ـ مدیریت فرایند ارجاع به مراکز مشاوره از طریق سامانه مشاوره خانواده قوه قضائیه."
        "\nع ـ انتصاب رئیس واحد مشاوره استان جهت پیگیری امور مشاوران و مراکز مشاوره در استان."
    )
    lines = []
    for line in base[33].splitlines():
        if line.startswith(("د ـ", "هـ ـ", "ه‍ ـ", "ز ـ", "ح ـ")):
            continue
        line = line.replace(
            "تحت ریاست و نظارت رئیس کل دادگستری استان یا یکی از معاونین وی به انتخاب رئیس کل دادگستری استان",
            "تحت نظارت رئیس کل دادگستری استان",
        )
        lines.append(line)
    current[33] = "\n".join(lines)
    lines = []
    for line in base[34].splitlines():
        if line.startswith("ب ـ"):
            lines.append("ب ـ تأهل و داشتن حداقل ۳۵ سال سن و ۳ سال سابقه کار مرتبط.")
        elif line.startswith("د ـ"):
            lines.append("د ـ انجام خدمت وظیفه عمومی یا معافیت برای آقایان.")
        else:
            lines.append(line)
    lines.append("تبصره ـ صدور مجوز تأسیس مرکز برای وکلا، سردفتران ازدواج، طلاق و اسناد رسمی، مدیران دفاتر خدمات الکترونیک قضائی و همچنین مدیران مؤسسات داوری و داوران که در حوزه اختلافات خانوادگی فعالیت دارند، ممنوع است.")
    current[34] = "\n".join(lines)
    current[36] = base[36].splitlines()[0] + "\nزمان و مکان برگزاری امتحان از طریق سامانه مرکز امور مشاوران اعلام می‌گردد."
    return current


def main() -> None:
    family = parse_standard(CACHE / "family_protection_law_1391.md", set(range(1, 59)))
    occ = parse_all_occurrences(CACHE / "family_protection_bylaw_current.md")
    if set(range(1,70)) - set(occ):
        raise ValueError("family bylaw coverage")
    bylaw_base = {n: occ[n][0] for n in range(1,70)}
    bylaw_current = update_bylaw(bylaw_base, occ)
    bylaw_amended = (10, 32, 33, 34, 36, 47)
    hasbi = parse_standard(CACHE / "non_contentious_matters_law.md", set(range(1,379)))
    # Normalize the current fee in article 375 and preserve its former amount.
    hasbi_old_375 = hasbi[375].replace("یکصد ریال (۵۰۰ ریال)", "یکصد ریال")
    hasbi[375] = hasbi[375].replace("یکصد ریال (۵۰۰ ریال)", "پانصد ریال")

    values = {
        "FAMILY_PROTECTION_LAW": tuple(sorted(family.items())),
        "FAMILY_BYLAW_BASE": tuple(sorted(bylaw_base.items())),
        "FAMILY_BYLAW_CURRENT": tuple(sorted(bylaw_current.items())),
        "FAMILY_BYLAW_AMENDED": bylaw_amended,
        "FAMILY_BYLAW_REPEALED": (14, 15),
        "HASBI_CURRENT": tuple(sorted(hasbi.items())),
        "HASBI_ART375_OLD": hasbi_old_375,
    }
    header = '''# -*- coding: utf-8 -*-\n"""Generated static texts for family protection and non-contentious matters."""\n# Generated by scripts/build_family_seeds.py from cached sources.\n\n'''
    body = "".join(
        f"{name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n\n"
        for name, value in values.items()
    )
    OUT.write_text(header + body, encoding="utf-8")
    print(f"[OK] Family law={len(family)}; bylaw={len(bylaw_current)} (+{len(bylaw_amended)} histories, 2 repealed)")
    print(f"[OK] Non-contentious matters={len(hasbi)} + article-375 history")
    print(f"[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
