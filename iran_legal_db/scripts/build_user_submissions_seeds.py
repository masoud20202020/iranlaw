#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build seeds for legal texts pasted directly by the user in chat."""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUTPUT = ROOT / "data" / "seed" / "user_submissions.py"
D = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
F = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ARTICLE_RE = re.compile(r"^\s*ماده\s*(?:\(?\s*(واحده|[۰-۹0-9]+)\s*\)?)\s*(.*)$")
BULLET_RE = re.compile(r"^\s*([۰-۹0-9]{1,2})\s*[ـ\-–—:]\s*(.*)$")

DOCS = [
    {
        "ref": "CIR-MM-714-1396",
        "title": "بخشنامه اجرای قانون الحاق یک ماده به قانون مبارزه با مواد مخدر",
        "short": "بخشنامه اجرای ماده الحاقی مواد مخدر",
        "source_file": "user_submission_circular_narcotics_714.md",
        "date": None,
        "authority": "رئیس قوه قضائیه",
        "type_code": "circular",
        "status_code": "in_force",
        "parser": "bulletin",
        "notes": "متن بخشنامه ارسالی کاربر از صفحه ۷۱۴؛ تاریخ صدور بخشنامه در متن ارسالی درج نشده و تاریخ ۱۳۹۶/۰۷/۱۲ مربوط به قانون مادر است.",
        "tags": ("مواد مخدر", "اجرای احکام کیفری", "تخفیف مجازات", "بخشنامه قضایی"),
    },
    {
        "ref": "AICR-768-1396",
        "title": "آیین‌نامه اجرایی حدود اختیارات، شرح وظایف و چگونگی بررسی صحنه جرم",
        "short": "آیین‌نامه بررسی صحنه جرم",
        "source_file": "user_submission_crime_scene_768.md",
        "date": "2017",
        "authority": "رئیس قوه قضائیه",
        "type_code": "regulation",
        "status_code": "in_force",
        "parser": "article",
        "notes": "متن ۱۹ ماده‌ای ارسالی کاربر از صفحه ۷۶۸؛ مصوب ۱۳۹۶/۰۶/۲۹ طبق اطلاعات همراه متن.",
        "tags": ("صحنه جرم", "پزشکی قانونی", "بازپرس", "ضابطان دادگستری"),
    },
    {
        "ref": "AICR-774-1395",
        "title": "آیین‌نامه اجرایی شیوه استقرار و اجرای وظایف معاونت اجرای احکام کیفری یا واحدی از آن در زندان‌ها و مؤسسات کیفری",
        "short": "آیین‌نامه معاونت اجرای احکام کیفری مستقر",
        "source_file": "user_submission_criminal_execution_774.md",
        "date": "2017",
        "authority": "رئیس قوه قضائیه",
        "type_code": "regulation",
        "status_code": "in_force",
        "parser": "article",
        "notes": "متن ۲۵ ماده‌ای ارسالی کاربر از صفحه ۷۷۴؛ مصوب ۱۳۹۵/۱۲/۲۴ طبق اطلاعات همراه متن.",
        "tags": ("اجرای احکام کیفری", "زندان", "قاضی مستقر", "محکوم"),
    },
    {
        "ref": "AIM79-1393",
        "title": "آیین‌نامه اجرایی ماده ۷۹ قانون مجازات اسلامی",
        "short": "آیین‌نامه خدمات عمومی رایگان و مجازات‌های جایگزین",
        "source_file": "user_submission_alternative_punishments_758.md",
        "date": "2014",
        "authority": "رئیس قوه قضائیه",
        "type_code": "regulation",
        "status_code": "in_force",
        "parser": "article",
        "notes": "متن ۱۶ ماده‌ای ارسالی کاربر از صفحه ۷۵۸؛ مصوب ۱۳۹۳/۰۶/۱۲ طبق اطلاعات همراه متن.",
        "tags": ("مجازات جایگزین حبس", "خدمات عمومی رایگان", "اجرای احکام کیفری", "کاهش جمعیت کیفری"),
    },
    {
        "ref": "AIWET-1397-636",
        "title": "آیین‌نامه تبصره ۱ ماده ۱ قانون حفاظت، احیاء و مدیریت تالاب‌های کشور",
        "short": "آیین‌نامه مدیریت تالاب‌ها",
        "source_file": "user_submission_wetlands_636_partial.md",
        "date": "2019",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "in_force",
        "parser": "article",
        "partial": True,
        "notes": "متن ارسالی کاربر از صفحه ۶۳۶ تا پایان ماده ۶ دریافت شده است؛ نسخه فعلی ناقص است و ادامه مواد/پیوست‌ها پس از دریافت بخش بعدی باید تکمیل شود.",
        "tags": ("تالاب", "محیط زیست", "منابع آب", "آلودگی"),
    },
    {
        "ref": "AICOMP-772-1393",
        "title": "آیین‌نامه راجع به نحوه اجرای مجازات‌های تکمیلی موضوع ماده ۲۳ قانون مجازات اسلامی",
        "short": "آیین‌نامه مجازات‌های تکمیلی",
        "source_file": "user_submission_complementary_punishments_772.md",
        "date": "2014", "authority": "رئیس قوه قضائیه", "type_code": "regulation", "status_code": "in_force", "parser": "article",
        "notes": "متن ۲۲ ماده‌ای ارسالی کاربر از صفحه ۷۷۲؛ مصوب ۱۳۹۳/۱۱/۲۶.",
        "tags": ("مجازات تکمیلی", "اجرای احکام کیفری", "اقامت اجباری", "منع اشتغال"),
    },
    {
        "ref": "AIECJ-915-1395",
        "title": "آیین‌نامه شرایط قضات دادسرا و دادگاه در رسیدگی به جرایم مربوط به مفاسد اقتصادی و مالی و دوره‌های آموزشی تخصصی",
        "short": "آیین‌نامه قضات جرایم مفاسد اقتصادی",
        "source_file": "user_submission_economic_corruption_judges_915.md",
        "date": "2017", "authority": "رئیس قوه قضائیه", "type_code": "regulation", "status_code": "in_force", "parser": "article",
        "notes": "متن ۱۹ ماده‌ای ارسالی کاربر از صفحه ۹۱۵؛ متن ماده ۱۹ به تصویب ۱۴۰۳/۰۴/۰۶ نیز اشاره دارد.",
        "tags": ("مفاسد اقتصادی", "قضات تخصصی", "سلامت اداری", "فساد"),
    },
    {
        "ref": "AIPARD-763-1387",
        "title": "آیین‌نامه کمیسیون عفو و تخفیف مجازات محکومین",
        "short": "آیین‌نامه کمیسیون عفو",
        "source_file": "user_submission_pardon_commission_763.md",
        "date": "2008", "authority": "رئیس قوه قضائیه", "type_code": "regulation", "status_code": "amended", "parser": "article",
        "notes": "متن ۳۱ ماده‌ای ارسالی کاربر از صفحه ۷۶۳؛ مصوب ۱۳۸۷/۰۹/۱۲.",
        "tags": ("عفو", "تخفیف مجازات", "کمیسیون عفو", "زندان"),
    },
    {
        "ref": "AIQK-27-1395",
        "title": "آیین‌نامه اجرایی ماده ۲۷ قانون مبارزه با قاچاق کالا و ارز",
        "short": "آیین‌نامه ماده ۲۷ قاچاق",
        "source_file": "user_submission_smuggling_article27_752.md",
        "date": "2017", "authority": "هیئت وزیران", "type_code": "regulation", "status_code": "in_force", "parser": "article",
        "notes": "متن ۷ ماده‌ای ارسالی کاربر از صفحه ۷۵۲؛ مصوب ۱۳۹۵/۰۴/۱۳.",
        "tags": ("قاچاق کالا", "دارو", "وزارت بهداشت", "قاچاق کالاهای ممنوع"),
    },
    {
        "ref": "DIQK-AUCTION-1402",
        "title": "دستورالعمل نحوه فروش کالای قاچاق از طریق حراج عمومی",
        "short": "دستورالعمل حراج عمومی کالای قاچاق",
        "source_file": "user_submission_smuggling_auction_756.md",
        "date": "2023", "authority": "ستاد مرکزی مبارزه با قاچاق کالا و ارز", "type_code": "directive", "status_code": "in_force", "parser": "article",
        "notes": "متن ۱۹ ماده‌ای ارسالی کاربر از صفحه ۷۵۶؛ مصوب ۱۴۰۲/۰۴/۲۸.",
        "tags": ("قاچاق کالا", "حراج عمومی", "اموال تملیکی", "مزایده"),
    },
    {
        "ref": "AIQK-59-1402",
        "title": "مصادیق ماده ۵۹ قانون مبارزه با قاچاق کالا و ارز",
        "short": "مصادیق ماده ۵۹ قاچاق",
        "source_file": "user_submission_smuggling_article59_757.md",
        "date": "2023", "authority": "ستاد مرکزی مبارزه با قاچاق کالا و ارز", "type_code": "regulation", "status_code": "in_force", "parser": "article",
        "notes": "متن ۵ ماده‌ای ارسالی کاربر از صفحه ۷۵۷؛ مصوب ۱۴۰۲/۰۵/۰۴.",
        "tags": ("قاچاق کالا", "مأموران کاشف", "موانع فیزیکی", "سلاح"),
    },
    {
        "ref": "AILEGAL-918-1398",
        "title": "آیین‌نامه نحوه اجرای قرار تعلیق اجرای مجازات، آزادی مشروط، قرار تعویق صدور حکم، نظام نیمه‌آزادی و آزادی تحت نظارت سامانه‌های الکترونیکی و مجازات‌های جایگزین حبس",
        "short": "آیین‌نامه تأسیسات حقوقی و مجازات‌های جایگزین حبس",
        "source_file": "user_submission_alternative_measures_918.md",
        "date": "2019", "authority": "رئیس قوه قضائیه", "type_code": "regulation", "status_code": "in_force", "parser": "article",
        "notes": "متن ۵۶ ماده‌ای ارسالی کاربر از صفحه ۹۱۸؛ مصوب ۱۳۹۸/۰۲/۰۳.",
        "tags": ("آزادی مشروط", "نظام نیمه‌آزادی", "تعلیق مجازات", "مجازات جایگزین حبس", "مراقبت الکترونیکی"),
    },
    {
        "ref": "CIR-POL-730-1399",
        "title": "بخشنامه قوه قضاییه در خصوص نحوه اجرای قانون جرم سیاسی",
        "short": "بخشنامه اجرای قانون جرم سیاسی",
        "source_file": "user_submission_political_crime_730.md",
        "date": "2020", "authority": "رئیس قوه قضائیه", "type_code": "circular", "status_code": "in_force", "parser": "bulletin",
        "notes": "متن ۵ بند ارسالی کاربر از صفحه ۷۳۰؛ مصوب ۱۳۹۹/۰۳/۱۳.",
        "tags": ("جرم سیاسی", "هیات منصفه", "آیین دادرسی کیفری", "حقوق متهم"),
    },
    {
        "ref": "CIR-342-721-1395",
        "title": "بخشنامه تبصره الحاقی به ماده ۳۴۲ قانون آیین دادرسی کیفری",
        "short": "بخشنامه دعوت وزارت دادگستری در دعاوی دیه",
        "source_file": "user_submission_article342_721.md",
        "date": "2016", "authority": "رئیس قوه قضائیه", "type_code": "circular", "status_code": "in_force", "parser": "article",
        "notes": "متن ماده واحده/بخشنامه ارسالی کاربر از صفحه ۷۲۱؛ مصوب ۱۳۹۵/۱۱/۰۳.",
        "tags": ("آیین دادرسی کیفری", "وزارت دادگستری", "دیه", "بیت‌المال"),
    },
    {
        "ref": "DRUG-LIST-1338",
        "title": "تصویب‌نامه راجع به فهرست مواد مخدر",
        "short": "فهرست مواد مخدر ۱۳۳۸",
        "source_file": "user_submission_narcotics_list_52.md",
        "date": "1959", "authority": "هیئت وزیران", "type_code": "regulation", "status_code": "amended", "parser": "article",
        "notes": "متن تاریخی ۶ ماده‌ای ارسالی کاربر از صفحه ۵۲؛ مصوب ۱۳۳۸/۰۵/۰۲ و شامل فهرست مواد مخدر.",
        "tags": ("مواد مخدر", "تریاک", "داروهای مخدر", "فهرست مواد"),
    },
    {
        "ref": "DCC-722-1397",
        "title": "دستورالعمل اجرایی کنترل مجرمان حرفه‌ای و سابقه‌دار",
        "short": "دستورالعمل کنترل مجرمان حرفه‌ای و سابقه‌دار",
        "source_file": "user_submission_professional_criminals_722.md",
        "date": "2018", "authority": "رئیس قوه قضائیه", "type_code": "directive", "status_code": "in_force", "parser": "article",
        "notes": "متن ارسالی کاربر از صفحه ۷۲۲؛ مصوب ۱۳۹۷/۰۴/۲۶. متن منبع دو ماده پایانی را با شماره ۲۱ درج کرده است و این وضعیت در ماده‌های استخراج‌شده حفظ شده است.",
        "tags": ("مجرمان حرفه‌ای", "مجرمان سابقه‌دار", "پایش مجرمان", "بانک اطلاعاتی کیفری"),
    },
]


def norm(line: str) -> str:
    return line.replace("\ufeff", "").replace("\r", "").replace("\u00ad", "").replace("\u200c", "‌").strip()


def clean_text(lines: list[str]) -> str:
    out = []
    for line in lines:
        line = norm(line)
        if line.startswith("#") or line.startswith("-") and ("منبع:" in line or "تاریخ" in line or "نوع:" in line or "وضعیت" in line):
            continue
        if line.startswith("https://"):
            continue
        if line in {"", "======================================================================"}:
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out).strip()


def parse_articles(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    heads = []
    for i, line in enumerate(lines):
        m = ARTICLE_RE.match(norm(line))
        if m:
            heads.append((i, m))
    rows = []
    for pos, (start, match) in enumerate(heads):
        end = heads[pos + 1][0] if pos + 1 < len(heads) else len(lines)
        raw_no = match.group(1).translate(D)
        article_no = "ماده واحده" if raw_no == "واحده" else f"ماده {raw_no.translate(F)}"
        body = ([match.group(2).strip()] if match.group(2).strip() else []) + lines[start + 1:end]
        text = clean_text(body)
        if text:
            rows.append({"article_no": article_no, "article_key_suffix": f"a{pos + 1:03d}", "text": text})
    if not rows:
        text = clean_text(lines)
        if text:
            rows.append({"article_no": "متن", "article_key_suffix": "text", "text": text})
    return rows


def parse_bulletin(path: Path) -> list[dict]:
    lines = [norm(x) for x in path.read_text(encoding="utf-8").splitlines()]
    starts = []
    expected = 1
    for i, line in enumerate(lines):
        m = BULLET_RE.match(line)
        if m and int(m.group(1).translate(D)) == expected:
            starts.append((i, expected))
            expected += 1
    rows = []
    for pos, (start, number) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        text = clean_text(lines[start:end])
        # Remove the leading number/separator from the stored legal text.
        m = BULLET_RE.match(lines[start])
        if m:
            first = m.group(2).strip()
            rest = lines[start + 1:end]
            text = clean_text([first] + rest)
        if text:
            rows.append({"article_no": f"بند {str(number).translate(F)}", "article_key_suffix": f"b{number:02d}", "text": text})
    return rows


def main() -> None:
    documents = []
    for doc in DOCS:
        path = CACHE / doc["source_file"]
        rows = parse_bulletin(path) if doc["parser"] == "bulletin" else parse_articles(path)
        if not rows:
            raise SystemExit(f"empty submission: {path}")
        item = dict(doc)
        item.pop("parser")
        item["source_url"] = next((line.split("منبع:", 1)[1].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- منبع:")), "")
        item["source_path"] = str(path.relative_to(ROOT)).replace("\\", "/")
        item["article_count"] = len(rows)
        item["rows"] = rows
        documents.append(item)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "# -*- coding: utf-8 -*-\n\n" +
        "# Generated by scripts/build_user_submissions_seeds.py.\n" +
        "DOCUMENTS = " + pprint.pformat(documents, width=120, sort_dicts=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] built {len(documents)} user-submitted documents / {sum(d['article_count'] for d in documents)} articles")
    for d in documents:
        print(f"  {d['ref']}: {d['article_count']} articles — {d['title']}{' [partial]' if d.get('partial') else ''}")


if __name__ == "__main__":
    main()
