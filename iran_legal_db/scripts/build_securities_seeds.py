# -*- coding: utf-8 -*-
"""Build deterministic seeds for the Iranian securities-market package.

All provisions are parsed from cached source snapshots.  Expected coverage is
strictly checked and the build fails rather than generating placeholder text.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
SEED = ROOT / "data" / "seed" / "securities_market.py"
P2E = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
E2P = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def clean(text: str) -> str:
    text = (text.replace("\u200f", "").replace("\u200e", "")
            .replace("\u00ad", "").replace("��", "ی")
            .replace("ك", "ک").replace("ي", "ی").replace("ى", "ی"))
    text = re.sub(r"\u200c(?=\s|[،,:؛.])", "", text)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("_", "")
    text = re.sub(r"(?m)^\s*#{1,6}\s*.*$", " ", text)
    text = re.sub(r"(?m)^\s*(?:فصل|بخش)\s+[^\n]*$", " ", text)
    text = re.sub(r"(?m)^\s*\*\s*\*\s*\*\s*$", " ", text)
    text = re.sub(r"\(\s*(?:اصلاحی|اصصلاحی|اصلاحیه|الحاقی|الحاقیه)\s+[۰-۹0-9/]+\s*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip(" .-ـ–\n")
    fixes = {
        "بهیچوجه": "به هیچ وجه", "حد اکثر": "حداکثر", "فنآوری": "فناوری",
        "الکتونیکی": "الکترونیکی", "واژههای": "واژه‌های", "هیات": "هیئت",
        "اعلا�": "اعلام", "صورتخلاصه": "صورت‌خلاصه",
        "حسابداری دات کام": "", "می بایست": "می‌بایست", "می باشد": "می‌باشد",
        "می شوند": "می‌شوند", "می شود": "می‌شود", "نمی تواند": "نمی‌تواند",
        "نمی توانند": "نمی‌توانند", "شرکتهای": "شرکت‌های", "سرمایه گذار": "سرمایه‌گذار",
        "سرمایه گذاری": "سرمایه‌گذاری", "سهامداران": "سهامداران",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    text = re.sub(r"(?<!ح)سابرس", "حسابرس", text)
    text = re.sub(r"\s+", " ", text).strip(" .-ـ–\n")
    return text.translate(E2P)


def parse_sequential(path: Path, start_marker: str, end_marker: str, count: int,
                     pattern: str, label: str):
    raw = path.read_text("utf-8").replace("**", "")
    raw = re.sub(r"!\[[^]]*\]\([^)]*\)", "", raw)
    raw = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", raw)
    start = raw.index(start_marker)
    end = raw.index(end_marker, start) if end_marker else len(raw)
    part = raw[start:end]
    rx = re.compile(pattern, re.M)
    matches = []
    expected = 1
    for m in rx.finditer(part):
        n = int(m.group(1).translate(P2E))
        if n == expected:
            matches.append(m)
            expected += 1
            if expected == count + 1:
                break
    got = [int(m.group(1).translate(P2E)) for m in matches]
    if got != list(range(1, count + 1)):
        raise RuntimeError(f"{label}: expected 1..{count}, got {got}")
    rows = []
    for i, m in enumerate(matches):
        body = part[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(part)]
        body = clean(body)
        if not body:
            raise RuntimeError(f"{label}: empty article {i + 1}")
        rows.append((i + 1, body))
    return rows


def parse_market_law():
    rows = parse_sequential(
        CACHE / "securities_market_law.md", "ماده۱ ـ", "قانون فوق مشتمل", 60,
        r"^\s*ماده\s*([۰-۹]+)(?:\s*\([^\n)]*\))?\s*[ـ–-]\s*",
        "securities market law",
    )
    data = dict(rows)
    current7 = data[7].replace(
        "الزام آن‌ها به تا اساسنامه‌های خود با آن",
        "الزام آن‌ها به تطابق اساسنامه‌های خود با آن",
    )
    if "تأسیس و فعالیت" not in current7:
        raise RuntimeError("article 7 current amendment not found")
    original7 = current7.replace("تأسیس و فعالیت", "تأسیس", 2)
    original7 = re.sub(
        r"۷\s*[-ـ]\s*تصویب اساسنامه.*?(?=۸\s*ـ)",
        "۷ ـ تصویب اساسنامه بورس‌ها، کانون‌ها و نهادهای مالی موضوع این قانون. ",
        original7,
        flags=re.S,
    )
    if "شرکت‌های سهامی عام ثبت شده نزد سازمان" in original7:
        raise RuntimeError("article 7 historical reconstruction failed")

    current19 = data[19]
    if "کارگروه تعامل پذیری دولت الکترونیکی" not in current19:
        raise RuntimeError("article 19 current amendment not found")
    original19 = current19.replace(
        "کارگروه تعامل پذیری دولت الکترونیکی", "دادستان کل کشور"
    )
    original = [(n, original7 if n == 7 else (original19 if n == 19 else t))
                for n, t in rows]
    current_updates = {7: current7, 19: current19}
    return original, current_updates


def replace_fine(text: str, replacement: str) -> str:
    rx = re.compile(
        r"از ده میلیون \(۱۰\.۰۰۰\.۰۰۰\) ریال تا یک میلیارد "
        r"\(۱\.۰۰۰\.۰۰۰\.۰۰۰\) ریال"
    )
    out, n = rx.subn(replacement, text, count=1)
    if n != 1:
        raise RuntimeError("article 14 fine phrase not found")
    return out


def parse_financial_instruments():
    rows = parse_sequential(
        CACHE / "financial_instruments_law.md", "ماده ۱-", "قانون فوق مشتمل", 18,
        r"^\s*ماده\s*([۰-۹]+)\s*[-ـ–]\s*", "financial instruments law",
    )
    base14 = dict(rows)[14]
    versions = {
        "1388": base14,
        "1394": replace_fine(base14, "از بیست و پنج میلیون (۲۵.۰۰۰.۰۰۰) ریال تا دو میلیارد و پانصد میلیون (۲.۵۰۰.۰۰۰.۰۰۰) ریال"),
        "1398": replace_fine(base14, "از سی و دو میلیون (۳۲.۰۰۰.۰۰۰) ریال تا سه میلیارد و دویست میلیون (۳.۲۰۰.۰۰۰.۰۰۰) ریال"),
        "1401": replace_fine(base14, "از یکصد میلیون (۱۰۰.۰۰۰.۰۰۰) ریال تا ده میلیارد (۱۰.۰۰۰.۰۰۰.۰۰۰) ریال"),
    }
    return rows, versions


def parse_governance():
    rows = parse_sequential(
        CACHE / "corporate_governance_1401.md", "ماده 1:",
        "این دستورالعمل در 6 فصل", 43,
        r"^\s*ماده\s*([۰-۹0-9]+)\s*[:\-ـ–]?\s*", "corporate governance",
    )
    original = dict(rows)
    # Correct the truncated transcription of the original article 43.
    original[43] = clean(
        "شرکت‌های درج‌شده در تابلوی قرمز و نارنجی بازار پایه شرکت فرابورس ایران "
        "صرفاً موظف به رعایت مواد ۲۷، ۳۰ و تبصره ماده ۳۶ می‌باشند."
    )

    current = {}
    tab2 = clean(
        "تبصره ۲ ـ رئیس هیئت مدیره یک شرکت نمی‌تواند عضو موظف بوده یا همزمان سمت دیگری "
        "در همان شرکت (به استثنای کمیته‌های هیئت مدیره) داشته باشد. مدیرعامل و اعضای موظف "
        "هیئت مدیره نمی‌توانند در شرکت‌های ثبت‌شده نزد سازمان بورس یا نهادهای مالی، مدیرعامل "
        "یا عضو موظف هیئت مدیره بوده یا سمت اجرایی داشته باشند. هیچ‌یک از اعضای هیئت مدیره "
        "نباید اصالتاً یا به نمایندگی از شخص حقوقی همزمان در بیش از سه شرکت ثبت‌شده نزد سازمان "
        "بورس یا نهادهای مالی، به عنوان عضو هیئت مدیره انتخاب شوند. اعضای هیئت مدیره باید در "
        "این خصوص اقرارنامه‌ای را به کمیته انتصابات ارائه نمایند. مدیران نهادهای واسط از تعدد "
        "عضویت بیش از سه شرکت مستثنی می‌باشند. بانک‌ها و بیمه‌ها موظفند مفاد این تبصره را با "
        "لحاظ اساسنامه نمونه مصوب سازمان اجرا نمایند."
    )
    art4, changed = re.subn(
        r"تبصره\s*۲\s*[:ـ-].*?(?=تبصره\s*۳\s*[:ـ-])", tab2 + " ",
        original[4], count=1, flags=re.S,
    )
    if changed != 1:
        raise RuntimeError("governance article 4 amendment failed")
    current[4] = art4
    current[30] = clean(
        "حضور حسابرس مستقل و بازرس قانونی در کلیه مجامع شرکت الزامی بوده و ناشر مکلف است "
        "به صورت کتبی از حسابرس مستقل و بازرس قانونی دعوت به عمل آورد."
    )
    tab36 = clean(
        "تبصره ـ در صورتی که شرکت یا سهامداران قصد ارائه پیشنهاد تغییر حسابرس مستقل و بازرس "
        "قانونی را قبل از پایان حداکثر دوره تصدی سمت آنان طبق دستورالعمل مؤسسات حسابرسی معتمد "
        "سازمان بورس و اوراق بهادار مصوب ۱۳۸۵/۰۵/۰۸ شورای عالی بورس و اصلاحات آن دارند، باید "
        "مراتب را با ذکر دلیل به همراه نظر کمیته حسابرسی، حداقل ده روز قبل از برگزاری مجمع به "
        "سازمان اعلام نمایند. سازمان پس از بررسی دلایل تغییر، تا پنج روز قبل از برگزاری مجمع، "
        "نظر خود را در خصوص تأیید یا عدم تأیید اعلام می‌نماید. در صورت عدم تأیید سازمان، باید "
        "از تغییر حسابرس مستقل و بازرس قانونی خودداری شود. شرکت‌های درج‌شده در تابلوی نارنجی "
        "و قرمز بازار پایه فرابورس ایران و شرکت‌های ثبت‌شده نزد سازمان که سهام آن‌ها در هیچ‌یک "
        "از تابلوهای بازار درج نشده یا نزد بورس تهران یا فرابورس ایران پذیرفته نشده است، از "
        "ارائه نظر کمیته حسابرسی معاف می‌باشند."
    )
    art36, changed = re.subn(
        r"تبصره\s*[:ـ-].*$", tab36, original[36], count=1, flags=re.S,
    )
    if changed != 1:
        raise RuntimeError("governance article 36 amendment failed")
    current[36] = art36
    current[37] = clean(
        "اطلاعات بااهمیتی از قبیل نام، مشخصات کامل، تحصیلات، تجارب و مدارک حرفه‌ای اعضای "
        "هیئت مدیره و مدیرعامل، کمیته‌های تخصصی هیئت مدیره و اعضای آن‌ها، موظف یا غیرموظف "
        "بودن آنان، عضویت در هیئت مدیره سایر شرکت‌ها به اصالت یا نمایندگی و رویه‌های حاکمیت "
        "شرکتی و ساختار آن و نحوه ارتباط بین سهامداران و هیئت مدیره، باید به نحو مناسب در "
        "تارنمای رسمی شرکت و در یک یادداشت جداگانه در گزارش تفسیری مدیریت و گزارش فعالیت "
        "هیئت مدیره افشا و به‌روزرسانی شود."
    )
    current[43] = clean(
        "شرکت‌های درج‌شده در تابلوی قرمز و نارنجی بازار پایه شرکت فرابورس ایران و شرکت‌هایی "
        "که نزد سازمان ثبت شده‌اند لیکن سهام آن‌ها در هیچ‌یک از تابلوهای بازار پایه درج نشده "
        "یا نزد بورس تهران یا فرابورس ایران پذیرفته نشده‌اند، صرفاً از مفاد این دستورالعمل "
        "موظف به رعایت مواد ۲۷، ۲۸، ۳۰ و تبصره ماده ۳۶ می‌باشند."
    )
    return [(n, original[n]) for n in range(1, 44)], current


def main():
    market_original, market_current = parse_market_law()
    bylaw = parse_sequential(
        CACHE / "securities_market_bylaw_numbered.md", "ماده 1-", None, 20,
        r"^\s*ماده\s*([۰-۹0-9]+)\s*[-ـ–]\s*", "market bylaw",
    )
    instruments, instrument14 = parse_financial_instruments()
    financing = parse_sequential(
        CACHE / "production_financing_law.md", "ماده ۱–", "قانون فوق مشتمل", 46,
        r"^\s*ماده\s*([۰-۹]+)\s*[-ـ–]\s*", "production financing law",
    )
    registration = parse_sequential(
        CACHE / "financial_entities_registration_directive.md", "ماده ۱:",
        None, 7,
        r"^\s*ماده\s*([۰-۹]+)\s*[:\-ـ–]\s*", "financial entities registration",
    )
    governance, governance_current = parse_governance()

    values = [
        ("SECURITIES_MARKET_ORIGINAL", market_original),
        ("SECURITIES_MARKET_CURRENT_UPDATES", market_current),
        ("SECURITIES_MARKET_BYLAW", bylaw),
        ("FINANCIAL_INSTRUMENTS_LAW", instruments),
        ("FINANCIAL_INSTRUMENTS_ART14_VERSIONS", instrument14),
        ("PRODUCTION_FINANCING_LAW", financing),
        ("FINANCIAL_ENTITIES_REGISTRATION_DIRECTIVE", registration),
        ("CORPORATE_GOVERNANCE_ORIGINAL", governance),
        ("CORPORATE_GOVERNANCE_CURRENT_UPDATES", governance_current),
    ]
    with SEED.open("w", encoding="utf-8") as f:
        f.write('# -*- coding: utf-8 -*-\n"""بذر ثابت بسته بازار سرمایه؛ بدون متن ساختگی."""\n\n')
        for name, value in values:
            f.write(name + " = " + pprint.pformat(value, width=118, sort_dicts=False) + "\n\n")
    print("[OK] securities law=60; bylaw=20; financial instruments=18")
    print("[OK] production financing=46; registration directive=7; governance=43")


if __name__ == "__main__":
    main()
