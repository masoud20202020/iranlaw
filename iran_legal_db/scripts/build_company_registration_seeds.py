# -*- coding: utf-8 -*-
"""Build static seeds for the company-registration legal package.

The builder reads cached source snapshots and produces a deterministic Python
seed.  It intentionally fails if an expected article is missing; no filler text
is ever generated.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
SEED = ROOT / "data" / "seed" / "company_registration.py"
P2E = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
E2P = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
WORD_NUMBERS = {
    "اول": 1, "دوم": 2, "سوم": 3, "چهارم": 4, "پنجم": 5, "ششم": 6,
    "هفتم": 7, "هشتم": 8, "نهم": 9, "دهم": 10, "یازدهم": 11,
    "دوازدهم": 12,
}


def clean(text: str, *, digits: bool = True) -> str:
    text = (text.replace("\u200f", "").replace("\u200e", "")
            .replace("\u00ad", "").replace("��", "ث")
            .replace("ك", "ک").replace("ي", "ی").replace("ى", "ی"))
    # Some archive transcriptions insert ZWNJ after almost every word.  Keep
    # intra-word joiners but remove those immediately before whitespace/punctuation.
    text = re.sub(r"\u200c(?=\s|[،,:؛.])", "", text)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("_", "")
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*\*\s*\*\s*\*\s*$", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-ـ\n")
    # Correct evident transcription/OCR slips without modernising substantive law.
    fixes = {
        "مدعیالعموم": "مدعی\u200cالعموم",
        "حقالثبت": "حق\u200cالثبت",
        "اسنادرسمی": "اسناد رسمی",
        "تحارتی": "تجارتی",
        "مقاده قبل": "ماده قبل",
        "صواد مصدق": "سواد مصدق",
        "شبعه یا شعب": "شعبه یا شعب",
        "تغئی ر مئی ابد": "تغییر می\u200cیابد",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    if digits:
        text = text.translate(E2P)
    return text


def assert_coverage(rows, expected, label):
    got = [n for n, _ in rows]
    if got != list(expected):
        raise RuntimeError(f"{label}: expected {list(expected)}, got {got}")
    if any(not t.strip() for _, t in rows):
        raise RuntimeError(f"{label}: empty article")


def parse_registration_law():
    raw = (CACHE / "company_registration_law.md").read_text("utf-8")
    start = raw.index("ماده اول ـ")
    end = raw.index("زیرنویس ۱ و ۲", start)
    raw = raw[start:end]
    pat = re.compile(
        r"(?m)^ماده\s+(اول|دوم|سوم|چهارم|پنجم|ششم|هفتم|هشتم|نهم|۱۰|یازدهم|دوازدهم)"
        r"(?:\s*\([^\n]*\))?\s*ـ\s*"
    )
    ms = list(pat.finditer(raw))
    rows = []
    for i, m in enumerate(ms):
        token = m.group(1)
        n = int(token.translate(P2E)) if token[0] in "۰۱۲۳۴۵۶۷۸۹" else WORD_NUMBERS[token]
        body = raw[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(raw)]
        rows.append((n, clean(body)))
    assert_coverage(rows, range(1, 13), "registration law")
    rows = [(n, text.replace("قانون تجارت۱", "قانون تجارت").replace("قانون ثبت۲", "قانون ثبت"))
            for n, text in rows]

    # Restore the enacted 1310 wording of article 10.  The cached consolidated
    # source displays only the amended tariff text.
    original10 = clean(
        "حق‌الثبت شرکت‌ها اعم از ایرانی و خارجی مطابق تعرفه ذیل خواهد بود: "
        "تا دو میلیون تومان سرمایه کل یک در هزار. از دو میلیون و یک تومان تا ده میلیون تومان "
        "نسبت به مازاد ربع واحد در هزار. از ده میلیون تومان تا پنجاه میلیون تومان نسبت به مازاد "
        "یک در بیست هزار و از پنجاه میلیون تومان به بالا نسبت به مازاد یک از پنجاه هزار. "
        "برای تغییراتی که باید به ثبت برسد به استثنای تغییر مربوط به ازدیاد سرمایه که تابع ترتیب "
        "مذکور فوق خواهد بود پنج تومان برای هر تغییر. برای ثبت هر شعبه بیست و پنج تومان."
    )
    current10 = dict(rows)[10]
    original = [(n, original10 if n == 10 else text) for n, text in rows]

    # Current monetary penalties following the 1403/03/30 adjustment.  Only the
    # monetary phrases are replaced; the rest of each enacted provision remains.
    current_1403 = {}
    current_1403[2] = dict(rows)[2].replace(
        "به یک صد الی هزار تومان جزای نقدی",
        "به جزای نقدی از ۱۰۰٬۰۰۰٬۰۰۰ تا ۲۰۰٬۰۰۰٬۰۰۰ ریال",
    )
    current_1403[5] = (dict(rows)[5]
        .replace("پنجاه تومان تا هزار تومان", "۸۲٬۵۰۰٬۰۰۰ تا ۲۰۰٬۰۰۰٬۰۰۰ ریال")
        .replace("پنج الی پنجاه تومان", "۶٬۶۰۰٬۰۰۰ تا ۶۶٬۰۰۰٬۰۰۰ ریال"))
    current_1403[6] = dict(rows)[6].replace(
        "ده الی یکصد تومان", "۱۶٬۵۰۰٬۰۰۰ تا ۲۰۰٬۰۰۰٬۰۰۰ ریال"
    )
    for n in (2, 5, 6):
        if current_1403[n] == dict(rows)[n]:
            raise RuntimeError(f"penalty replacement failed for article {n}")
    return original, current10, current_1403


def parse_numbered(raw: str, start_marker: str, end_marker: str, count: int, label: str):
    start = raw.index(start_marker)
    end = raw.index(end_marker, start)
    part = raw[start:end]
    pat = re.compile(r"(?m)^\s*ماده\s*([۰-۹0-9]+)\s*[-ـ]\s*")
    ms = list(pat.finditer(part))
    rows = []
    for i, m in enumerate(ms):
        n = int(m.group(1).translate(P2E))
        body = part[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(part)]
        rows.append((n, clean(body)))
    assert_coverage(rows, range(1, count + 1), label)
    return rows


def parse_trade_code_bylaw():
    raw = (CACHE / "company_registration_tradecode_bylaw.md").read_text("utf-8")
    start = raw.index("نظر بمواد ۱۹۶")
    end = raw.index("داور-", start)
    part = raw[start:end]
    # Remove the page's inserted table of contents from the body of article 4.
    part = re.sub(r"فهرست مطالب.*?###\s*الف", "### الف", part, flags=re.S)
    pat = re.compile(r"(?m)^ماده\s*([۰-۹]+)\s*[.\-ـ]\s*")
    ms = list(pat.finditer(part))
    rows = []
    for i, m in enumerate(ms):
        n = int(m.group(1).translate(P2E))
        body = part[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(part)]
        rows.append((n, clean(body)))
    assert_coverage(rows, range(1, 11), "trade-code registration bylaw")
    return rows


def parse_executive_regulation():
    current_raw = (CACHE / "company_registration_executive_current.md").read_text("utf-8")
    start = current_raw.index("ماده‌ ۱-")
    end = len(current_raw)
    part = current_raw[start:end]
    pat = re.compile(
        r"(?m)^\s*(?:ماده|مواد)‌?\s*(?:\[)?([۰-۹]+)(?:\])?"
        r"(?:\s+(مکرر))?\s*(?:[-ـ]\s*)?(?:الحاقی\s*‌?\s*)?(?:\[[^\n]*\])?\s*"
    )
    matches = list(pat.finditer(part))
    parsed = {}
    for i, m in enumerate(matches):
        n = int(m.group(1).translate(P2E))
        key = "28bis" if m.group(2) else n
        body = part[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(part)]
        parsed[key] = clean(body)

    # The consolidated source records only the repeal annotations for 31/32.
    # Recover their enacted wording from the historical source snapshot.
    hist_raw = (CACHE / "company_registration_executive.md").read_text("utf-8")
    hp = re.compile(r"(?m)^ماد[هﮤ]\s*([0-9]+)(?:\s*\[([0-9]+)\])?\s*[-ـ]\s*")
    hms = list(hp.finditer(hist_raw))
    historical = {}
    for i, m in enumerate(hms):
        n = int(m.group(2) or m.group(1))
        body = hist_raw[m.end(): hms[i + 1].start() if i + 1 < len(hms) else len(hist_raw)]
        historical[n] = clean(body)
    for n in (31, 32):
        if not historical.get(n):
            raise RuntimeError(f"missing historical executive article {n}")
        parsed[n] = historical[n]

    # Article 29 in one consolidated transcription contains an evident omission;
    # preserve the wording displayed by the historical source (بیمه عمر).
    if historical.get(29):
        parsed[29] = historical[29]
    # Keep the annulled provision itself as the historical text; the ruling
    # annotation belongs in metadata, not inside the provision.
    parsed[36] = clean(
        "تبدیل کلیه شرکت‌های موضوع ماده ۲۰ قانون تجارت مصوب ۱۳۱۱ به یکدیگر مجاز است. "
        "نحوه تبدیل این شرکت‌ها به یکدیگر، به موجب دستورالعملی خواهد بود که ظرف سه ماه، "
        "توسط معاونت حقوقی رئیس‌جمهور با همکاری وزارت امور اقتصادی و دارایی و سازمان ثبت "
        "اسناد و املاک کشور تهیه می‌شود."
    )

    expected = list(range(1, 37)) + ["28bis"]
    missing = [x for x in expected if x not in parsed]
    if missing:
        raise RuntimeError(f"executive regulation missing: {missing}")
    if any(not parsed[x] for x in expected):
        raise RuntimeError("executive regulation has empty substantive text")
    return [(x, parsed[x]) for x in expected]


def parse_foreign_branch_bylaw():
    raw = (CACHE / "foreign_branch_bylaw.md").read_text("utf-8")
    start = raw.index("**ماده 1")
    end = raw.index("معاون اول رییس جمهور", start)
    part = raw[start:end]
    pat = re.compile(r"(?m)^\*\*ماده\s*([0-9]+)\s*(?:-\*\*|\*\*-|\*\*)\s*")
    ms = list(pat.finditer(part))
    rows = []
    for i, m in enumerate(ms):
        n = int(m.group(1))
        body = part[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(part)]
        rows.append((n, clean(body)))
    assert_coverage(rows, range(1, 11), "foreign branch bylaw")
    return rows


def parse_divan_company_conversion():
    raw = (CACHE / "divan_company_conversion_1400.md").read_text("utf-8")
    start = raw.index("اولاً:")
    end = raw.index("حکمتعلی مظفری", start)
    text = clean(raw[start:end])
    if "خارج از صلاحیت" not in text or "ابطال" not in text:
        raise RuntimeError("incomplete Divan ruling source")
    return text


def parse_registry_admin_1386():
    raw = (CACHE / "company_registry_admin_1386.md").read_text("utf-8")
    anchor = raw.index("اصلاحیه طرح اصلاحی آئین‌نامه ثبت شرکت‌ها مصوب ۱۳۴۰", 250)
    start = raw.index("ماده ۱ـ", anchor)
    end = raw.index("این آئین‌نامه مشتمل بر ۱۰ ماده", start)
    part = raw[start:end]
    pat = re.compile(r"(?m)^\s*ماده\s*([۰-۹]+)\s*ـ\s*")
    ms = list(pat.finditer(part))
    rows = []
    for i, m in enumerate(ms):
        n = int(m.group(1).translate(P2E))
        body = part[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(part)]
        rows.append((n, clean(body)))
    assert_coverage(rows, range(1, 11), "registry administration amendment")
    return rows


def main():
    law_original, law_art10, penalties = parse_registration_law()
    executive = parse_executive_regulation()
    trade_bylaw = parse_trade_code_bylaw()
    foreign_bylaw = parse_foreign_branch_bylaw()
    admin = parse_registry_admin_1386()
    divan_ruling = parse_divan_company_conversion()
    foreign_law = clean(
        "شرکت‌های خارجی که در کشور محل ثبت خود شرکت قانونی شناخته می‌شوند، مشروط به عمل متقابل "
        "از سوی کشور متبوع، می‌توانند در زمینه‌هایی که توسط دولت جمهوری اسلامی ایران تعیین می‌شود "
        "در چهارچوب قوانین و مقررات کشور به ثبت شعبه یا نمایندگی خود اقدام کنند. "
        "تبصره ـ آیین‌نامه اجرایی این قانون بنا به پیشنهاد وزارت امور اقتصادی و دارایی با هماهنگی "
        "سایر مراجع ذی‌ربط به تصویب هیئت وزیران خواهد رسید."
    )

    values = [
        ("REGISTRATION_LAW_ORIGINAL", law_original),
        ("REGISTRATION_LAW_ART10_CONSOLIDATED", law_art10),
        ("REGISTRATION_LAW_PENALTIES_1403", penalties),
        ("REGISTRATION_EXECUTIVE_REGULATION", executive),
        ("TRADE_CODE_REGISTRATION_BYLAW", trade_bylaw),
        ("FOREIGN_BRANCH_LAW", foreign_law),
        ("FOREIGN_BRANCH_BYLAW", foreign_bylaw),
        ("REGISTRY_ADMIN_REGULATION_1386", admin),
        ("DIVAN_COMPANY_CONVERSION_RULING", divan_ruling),
    ]
    with SEED.open("w", encoding="utf-8") as f:
        f.write('# -*- coding: utf-8 -*-\n"""بذر ثابت بسته حقوق ثبت شرکت‌ها؛ بدون متن ساختگی."""\n\n')
        for name, value in values:
            f.write(name + " = " + pprint.pformat(value, width=118, sort_dicts=False) + "\n\n")
    print("[OK] law=12 + history; executive=37 keys; trade bylaw=10")
    print("[OK] foreign branch law=1, bylaw=10; registry administration=10; Divan ruling=1")


if __name__ == "__main__":
    main()
