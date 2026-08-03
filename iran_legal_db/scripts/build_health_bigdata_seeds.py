#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build normalized seeds from the raw health/medicine dataset in the bigdata commit.

The commit contains one ``مشاهده_متن_قانون.txt`` and one HTML copy per source page under
``data/بهداشت_و_درمان``.  This builder deliberately uses the text copy, removes the
website chrome, extracts article boundaries, normalizes article numbers to Persian
 digits, and writes a reproducible Python seed consumed by ``load_health_bigdata.py``.

Seven raw pages are already represented by stable documents in the operational database;
they are recorded in the manifest and skipped rather than duplicated.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "بهداشت_و_درمان"
OUTPUT = ROOT / "data" / "seed" / "health_bigdata.py"

ASCII_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# A few source pages have a typo in the heading ("ماه62" instead of "ماده 62").
# It is fixed only for boundary detection; the article text remains otherwise intact.
ARTICLE_RE = re.compile(
    r"^\s*(?:ماده|مادّه|ماه)\s*"
    r"(?:\(?\s*(?P<number>واحده|[۰-۹0-9]+(?:\s*(?:مکرر|الحاقی)(?:\s*[۰-۹0-9]+)?)?)\s*\)?)"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)

# These are the raw directory names in the commit.  The metadata is intentionally
# explicit: the filename alone is not a reliable legal title or document type.
RAW_DOCUMENTS = {
    "آیین_نامه_ساخت_و_ورود_دارو": {
        "ref": "AIRDI-1368",
        "title": "آیین‌نامه ساخت و ورود دارو و فرآورده‌های بیولوژیک",
        "short": "آیین‌نامه ساخت و ورود دارو",
        "date": "1989-08-26",
        "authority": "وزارت بهداشت، درمان و آموزش پزشکی",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("دارو", "فرآورده‌های بیولوژیک", "سازمان غذا و دارو", "حقوق سلامت"),
        "expected_count": 62,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۶۸/۰۶/۰۴ و همراه با اصلاحات و الحاقات اخیر در منبع. مقابله با متن رسمی توصیه می‌شود.",
    },
    "آيين_نامه_مالی_و_معاملاتی_دانشگاه_های_علوم_پزشکی_و_خدمات_بهداشتی_درمانی_کشور": {
        "ref": "AIFU-1390",
        "title": "آیین‌نامه مالی و معاملاتی دانشگاه‌ها و دانشکده‌های علوم پزشکی و خدمات بهداشتی درمانی کشور",
        "short": "آیین‌نامه مالی و معاملاتی دانشگاه‌های علوم پزشکی",
        "date": "2011",
        "authority": "وزارت بهداشت، درمان و آموزش پزشکی",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("دانشگاه علوم پزشکی", "امور مالی", "معاملات دولتی", "حقوق سلامت"),
        "expected_count": 106,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب سال ۱۳۹۰ و همراه با اصلاحات و الحاقات اخیر در منبع. برخی جداول و پیوست‌های اجرایی ممکن است در متن صفحه ناقص باشند.",
    },
    "آیین_نامه_اداری_استخدامی_اعضای_هیئت_علمی_دانشگاه_های_علوم_پزشکی_کشور": {
        "ref": "AIFAC-1390",
        "title": "آیین‌نامه اداری استخدامی اعضای هیئت علمی دانشگاه‌های علوم پزشکی کشور",
        "short": "آیین‌نامه استخدامی اعضای هیئت علمی علوم پزشکی",
        "date": "2012-02-19",
        "authority": "وزارت بهداشت، درمان و آموزش پزشکی",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("اعضای هیئت علمی", "استخدام دانشگاهی", "دانشگاه علوم پزشکی", "حقوق اداری"),
        "expected_count": 129,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۰/۱۱/۳۰ و همراه با اصلاحات و الحاقات اخیر در منبع. در متن خام، عنوان ماده ۶۲ به‌صورت «ماه۶۲» آمده و در builder به‌عنوان ماده ۶۲ شناسایی شده است.",
    },
    "آیین_نامه_قانون_ارتقاء_بهره_وری_کارکنان_بالینی_نظام_سلامت": {
        "ref": "AICPN-1388",
        "title": "آیین‌نامه اجرایی قانون ارتقاء بهره‌وری کارکنان بالینی نظام سلامت",
        "short": "آیین‌نامه بهره‌وری کارکنان بالینی",
        "date": "2010-02-01",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "in_force",
        "tags": ("کارکنان بالینی", "نظام سلامت", "بهره‌وری", "حقوق کار"),
        "expected_count": 9,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۸۸/۱۱/۱۲ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "آیین_نامه_معاینه_و_معافیت_پزشکی_مشمولان_خدمت_وظیفه_عمومی": {
        "ref": "AIMED-1393",
        "title": "آیین‌نامه معاینه و معافیت پزشکی مشمولان خدمت وظیفه عمومی",
        "short": "آیین‌نامه معاینه و معافیت پزشکی مشمولان",
        "date": "2014-05-11",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("معافیت پزشکی", "خدمت وظیفه عمومی", "پزشکی نظامی", "سلامت"),
        "expected_count": 28,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۳/۰۲/۲۱ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "آیین_نامه_نصب_و_ثبت_اجباری_علائم_صنعتی_بر_روی_بعضی_از_اجناس_داروئی_و_خوراکی_و_آرایشی": {
        "ref": "AIBRAND-1328",
        "title": "آیین‌نامه نصب و ثبت اجباری علائم صنعتی بر روی بعضی از اجناس دارویی و خوراکی و آرایشی",
        "short": "آیین‌نامه علائم صنعتی کالاهای دارویی و خوراکی",
        "date": "1949-04-23",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("دارو", "مواد خوردنی", "علائم صنعتی", "بهداشت عمومی"),
        "expected_count": 8,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۲۸/۰۲/۰۳ و همراه با اصلاحات و الحاقات اخیر در منبع. وضعیت اعتبار عملی مواد باید با مقررات ثبت علائم و قوانین سلامت تطبیق شود.",
    },
    "آیین‌_نامه_اجرایی_نحوه_نگهداری_و_درمان_مجانین": {
        "ref": "AIMH-1398",
        "title": "آیین‌نامه اجرایی نحوه نگهداری و درمان مجانین",
        "short": "آیین‌نامه نگهداری و درمان مجانین",
        "date": "2019-04-15",
        "authority": "رئیس قوه قضائیه",
        "type_code": "regulation",
        "status_code": "in_force",
        "tags": ("مجانین", "نگهداری و درمان", "پزشکی قانونی", "اجرای احکام کیفری"),
        "expected_count": 12,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۸/۰۱/۲۶ رئیس قوه قضائیه و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "آیین‏_نامه_ثبت_دارو_در_سازمان_غذا_و_دارو": {
        "ref": "AIDR-1393",
        "title": "آیین‌نامه ثبت دارو در سازمان غذا و دارو",
        "short": "آیین‌نامه ثبت دارو",
        "date": "2015-01-07",
        "authority": "وزارت بهداشت، درمان و آموزش پزشکی",
        "type_code": "regulation",
        "status_code": "amended",
        "tags": ("ثبت دارو", "سازمان غذا و دارو", "فرآورده‌های سلامت", "دارو"),
        "expected_count": 23,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۳/۱۰/۱۷ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "اساسنامه_بیمارستان_دادگستری": {
        "ref": "BJC-1400",
        "title": "اساسنامه بیمارستان دادگستری",
        "short": "اساسنامه بیمارستان دادگستری",
        "date": "2021-05-13",
        "authority": "رئیس قوه قضائیه",
        "type_code": "bylaw",
        "status_code": "in_force",
        "tags": ("بیمارستان", "قوه قضائیه", "خدمات درمانی", "حقوق سلامت"),
        "expected_count": 26,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۴۰۰/۰۲/۲۳ رئیس قوه قضائیه و جایگزین آیین‌نامه بیمارستان قوه قضائیه مصوب ۱۳۸۰/۰۶/۳۰ طبق ماده ۲۶.",
    },
    "اساسنامه_سازمان_فوریت‌های_پیش_بیمارستانی_اورژانس_کشور": {
        "ref": "AIEPO-1396-11-04",
        "title": "اساسنامه سازمان فوریت‌های پیش‌بیمارستانی اورژانس کشور (نسخه ۱۳۹۶/۱۱/۰۴)",
        "short": "اساسنامه اورژانس کشور ـ نسخه اول",
        "date": "2018-01-24",
        "authority": "هیئت وزیران",
        "type_code": "bylaw",
        "status_code": "amended",
        "tags": ("اورژانس پیش‌بیمارستانی", "وزارت بهداشت", "خدمات فوریت پزشکی", "بیمارستان"),
        "expected_count": 9,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع با تاریخ تصویب ۱۳۹۶/۱۱/۰۴؛ برای حفظ دو نسخه متفاوت موجود در داده خام، جدا از نسخه ۱۳۹۶/۱۱/۲۸ ثبت شده است.",
    },
    "اساسنامه_سازمان_فوریت‌های_پیش_‌بیمارستانی_اورژانس_کشور": {
        "ref": "AIEPO-1396-11-28",
        "title": "اساسنامه سازمان فوریت‌های پیش‌بیمارستانی اورژانس کشور (نسخه ۱۳۹۶/۱۱/۲۸)",
        "short": "اساسنامه اورژانس کشور ـ نسخه دوم",
        "date": "2018-02-17",
        "authority": "هیئت وزیران",
        "type_code": "bylaw",
        "status_code": "in_force",
        "tags": ("اورژانس پیش‌بیمارستانی", "وزارت بهداشت", "خدمات فوریت پزشکی", "بیمارستان"),
        "expected_count": 9,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع با تاریخ ۱۳۹۶/۱۱/۲۸؛ چون متن و قالب آن با نسخه ۱۳۹۶/۱۱/۰۴ تفاوت دارد، به‌عنوان سند جدا و نسخه متأخر نگهداری شده است.",
    },
    "ضوابط_و_روش_های_مدیریت_اجرایی_پسماندهای_پزشکی_و_پسماندهای_وابسته": {
        "ref": "DMEW-1386",
        "title": "ضوابط و روش‌های مدیریت اجرایی پسماندهای پزشکی و پسماندهای وابسته",
        "short": "ضوابط مدیریت پسماندهای پزشکی",
        "date": "2008-03-09",
        "authority": "هیئت وزیران",
        "type_code": "directive",
        "status_code": "in_force",
        "tags": ("پسماند پزشکی", "بهداشت محیط", "بیمارستان", "محیط زیست"),
        "expected_count": 73,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۸۶/۱۲/۱۹ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "قانون_ارتقاء_بهره_وری_کارکنان_بالینی_نظام_سلامت": {
        "ref": "QCP-1388",
        "title": "قانون ارتقاء بهره‌وری کارکنان بالینی نظام سلامت",
        "short": "قانون بهره‌وری کارکنان بالینی",
        "date": "2009-04-19",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "amended",
        "tags": ("کارکنان بالینی", "نظام سلامت", "بهره‌وری", "حقوق کار"),
        "expected_count": 1,
        "notes": "متن ماده‌واحده بازنشرشده از صفحه منبع؛ مصوب ۱۳۸۸/۰۱/۳۰ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "قانون_ارتقاء_سلامت_نظام_اداری_و_مقابله_با_فساد": {
        "ref": "QASAF-1390",
        "title": "قانون ارتقاء سلامت نظام اداری و مقابله با فساد",
        "short": "ارتقاء سلامت نظام اداری و مقابله با فساد",
        "date": "2011-05-19",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "amended",
        "tags": ("مقابله با فساد", "سلامت اداری", "شفافیت", "حقوق اداری"),
        "expected_count": 35,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۰/۰۲/۲۹ همراه با اصلاحات و الحاقات سال ۱۳۹۹ در منبع.",
    },
    "قانون_الزام_تخلیه_ساختمان_های_وزارتخانه_های_فرهنگ_و_آموزش_عالی_و_بهداشت،_درمان_و_آموزش_پزشکی_و": {
        "ref": "QEVB-1368",
        "title": "قانون الزام تخلیه ساختمان‌های وزارتخانه‌های فرهنگ و آموزش عالی و بهداشت، درمان و آموزش پزشکی و انتقال به پردیس‌های دانشگاهی",
        "short": "الزام تخلیه ساختمان‌های وزارتخانه‌های آموزش عالی و بهداشت",
        "date": "1990-02-18",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "tags": ("وزارت بهداشت", "دانشگاه علوم پزشکی", "اموال دولتی", "حقوق اداری"),
        "expected_count": 1,
        "notes": "متن ماده‌واحده بازنشرشده از صفحه منبع؛ مصوب ۱۳۶۸/۱۱/۲۹.",
    },
    "قانون_سازمان_دامپزشکی_کشور": {
        "ref": "QVET-1350",
        "title": "قانون سازمان دامپزشکی کشور",
        "short": "قانون سازمان دامپزشکی کشور",
        "date": "1971-06-14",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "type_code": "law",
        "status_code": "amended",
        "tags": ("دامپزشکی", "بهداشت دام", "فرآورده‌های خام دامی", "کشاورزی"),
        "expected_count": 21,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۵۰/۰۳/۲۴ و همراه با اصلاحات و الحاقات اخیر در منبع.",
    },
    "قانون_محل_مطب_پزشکان": {
        "ref": "QLOP-1366",
        "title": "قانون محل مطب پزشکان",
        "short": "قانون محل مطب پزشکان",
        "date": "1988-01-10",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "tags": ("مطب", "پزشکان", "کاربری ساختمان", "حقوق سلامت"),
        "expected_count": 1,
        "notes": "متن ماده‌واحده بازنشرشده از صفحه منبع؛ مصوب ۱۳۶۶/۱۰/۲۰ و تأییدشده توسط شورای نگهبان طبق متن پایانی منبع.",
    },
    "قانون_ممنوعیت_تبلیغات_و_معرفی_محصولات_و_خدمات_غیرمجاز_و_آسیب‌رسان_به_سلامت_در_رسانه‌های_ارتباط_جمعی": {
        "ref": "QHAP-1397",
        "title": "قانون ممنوعیت تبلیغات و معرفی محصولات و خدمات غیرمجاز و آسیب‌رسان به سلامت در رسانه‌های ارتباط جمعی",
        "short": "ممنوعیت تبلیغات آسیب‌رسان به سلامت",
        "date": "2018-06-12",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "tags": ("تبلیغات سلامت", "سازمان غذا و دارو", "محصولات غیرمجاز", "بهداشت عمومی"),
        "expected_count": 5,
        "notes": "متن ماده‌به‌ماده بازنشرشده از صفحه منبع؛ مصوب ۱۳۹۷/۰۳/۲۲. ماده ۵ قانون، نسخ ماده ۵ قانون مقررات امور پزشکی و دارویی را اعلام می‌کند.",
    },
    "لايحه_قانونی_تشديد_مجازات_مرتکبين_جرايم_مواد_مخدر_و_اقدامات_تامينی_و_درمانی_به_منظور_مداوا_و_اشتغال": {
        "ref": "QDRA-1359",
        "title": "لایحه قانونی تشدید مجازات مرتکبین جرایم مواد مخدر و اقدامات تأمینی و درمانی به منظور مداوا و اشتغال",
        "short": "لایحه تشدید مجازات جرایم مواد مخدر ۱۳۵۹",
        "date": "1980-06-09",
        "authority": "شورای انقلاب جمهوری اسلامی ایران",
        "type_code": "law",
        "status_code": "abrogated",
        "tags": ("مواد مخدر", "مجازات", "اقدامات تأمینی", "درمان اعتیاد"),
        "expected_count": 25,
        "historical_only": True,
        "expiry_date": "1988-05-24",
        "notes": "متن تاریخی ۲۵ ماده‌ای بازنشرشده از صفحه منبع؛ مصوب ۱۳۵۹/۰۳/۱۹ و به موجب ماده ۲۵ از تاریخ اجرای قانون بعدی مواد مخدر منسوخ شده است. همه مواد این سند به‌صورت تاریخی ثبت می‌شوند.",
    },
    "مصوبه_افزايش_ظرفيت_پزشکی_در_مقطع_عمومی": {
        "ref": "DMCAP-1400",
        "title": "مصوبه افزایش ظرفیت پزشکی در مقطع عمومی",
        "short": "مصوبه افزایش ظرفیت پزشکی عمومی",
        "date": "2021-12-14",
        "authority": "شورای عالی انقلاب فرهنگی",
        "type_code": "directive",
        "status_code": "in_force",
        "tags": ("ظرفیت پزشکی", "آموزش پزشکی", "دانشگاه علوم پزشکی", "مناطق محروم"),
        "expected_count": 1,
        "notes": "متن ماده‌واحده و تبصره‌های بازنشرشده از صفحه منبع؛ مصوبه جلسات ۸۵۱ و ۸۵۲ شورای عالی انقلاب فرهنگی در ۱۴۰۰/۰۹/۲۳ و ۱۴۰۰/۱۰/۰۷. جدول ظرفیت در متن صفحه به‌صورت کامل درج نشده است.",
    },
}

# Raw pages already represented by stable documents in the database.  We still
# validate that they exist in the commit so a future re-run cannot silently lose
# part of the input dataset.
EXISTING_DOCUMENTS = {
    "قانون_آموزش_مداوم_جامعه_پزشکی_کشور": {"ref": "QCME-1375", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون_تشکیل_سازمان_پزشکی_قانونی_کشور": {"ref": "QLMO-1372", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون_تشکیلات_و_وظایف_وزارت_بهداشت،_درمان_و_آموزش_پزشکی": {"ref": "QMBH-1364", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون_تعزیرات_حکومتی_امور_بهداشتی_و_درمانی": {"ref": "QTAHD-1367", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون_مربوط_به_مقررات_امور_پزشکی_و_دارویی_و_مواد_خوردنی_و_آشامیدنی": {"ref": "QMDA-1334", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون_مواد_خوردنی_و_آشامیدنی_و_آرایشی_و_بهداشتی": {"ref": "QMKAB-1346", "reason": "قبلاً در بسته health_law وارد شده است."},
    "قانون‌_سازمان‌_نظام‌_پزشکی‌_جمهوری‌_اسلامی‌_ايران‌": {"ref": "QSNM-1383", "reason": "قبلاً در بسته health_law وارد شده است."},
}


def normalize_line(line: str) -> str:
    line = line.replace("\ufeff", "").replace("\r", "")
    line = line.replace("\u00a0", " ").replace("\u00ad", "")
    line = line.replace("ي", "ی").replace("ك", "ک")
    return line.rstrip()


def article_match(line: str):
    # The raw txt has no Markdown, but accepting a small amount of decoration
    # keeps the parser stable if a future export includes it.
    candidate = normalize_line(line).strip().lstrip("*#").strip()
    return ARTICLE_RE.match(candidate)


def source_url(lines: list[str]) -> str:
    for line in lines[:30]:
        if "لینک:" in line:
            return line.split("لینک:", 1)[1].strip()
    raise ValueError("source URL not found in raw text")


def clean_body(lines: list[str], match) -> str:
    first = normalize_line(lines[0]).strip().lstrip("*#").strip()
    rest = match.group("rest")
    # Remove only the separator after the article number; notes such as
    # «(اصلاحی ۱۳۹۹)» are legal metadata and must remain in the text.
    rest = re.sub(r"^\s*[\-ـ–—:：]\s*", "", rest).strip()
    body_lines = ([rest] if rest.strip() else []) + [normalize_line(x).strip() for x in lines[1:]]

    cleaned: list[str] = []
    for line in body_lines:
        line = line.replace("\u200c", "‌")
        # Site/footer markers are outside the legal text in the raw export.
        if re.match(r"^\s*(?:تازه\s*های\s*قوانین|تازه‌های\s*قوانین|مطالب مرتبط|ارسال دیدگاه|ثبت دیدگاه|نظرات کاربران)\b", line):
            break
        if line.strip() in {"* * *", "***", "—", "___"}:
            continue
        line = line.replace("\r", "").strip()
        line = re.sub(r"[ \t]+", " ", line)
        cleaned.append(line)

    # Trim blank paragraphs but preserve paragraph boundaries inside an article.
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    out: list[str] = []
    previous_blank = False
    for line in cleaned:
        blank = not line
        if blank and previous_blank:
            continue
        out.append(line)
        previous_blank = blank
    return "\n".join(out).strip()


def canonical_article_no(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    if raw == "واحده":
        return "ماده واحده", "single"
    normalized = raw.translate(ASCII_DIGITS)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    key_no = normalized.replace(" ", "-")
    return normalized.translate(PERSIAN_DIGITS), key_no


def parse_document(raw_dir: str, meta: dict) -> dict:
    path = RAW_ROOT / raw_dir / "مشاهده_متن_قانون.txt"
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    url = source_url(lines)
    heads: list[tuple[int, object]] = []
    for index, line in enumerate(lines):
        match = article_match(line)
        if match:
            heads.append((index, match))
    if len(heads) != meta["expected_count"]:
        raise ValueError(f"{raw_dir}: extracted {len(heads)} articles, expected {meta['expected_count']}")

    rows = []
    seen = set()
    for position, (start, match) in enumerate(heads):
        end = heads[position + 1][0] if position + 1 < len(heads) else len(lines)
        article_no, key_no = canonical_article_no(match.group("number"))
        if article_no in seen:
            raise ValueError(f"{raw_dir}: duplicate article number {article_no}")
        seen.add(article_no)
        text = clean_body(lines[start:end], match)
        if not text:
            raise ValueError(f"{raw_dir}: empty text for {article_no}")
        rows.append({"article_no": article_no, "article_key_suffix": key_no, "text": text})

    out = dict(meta)
    out["raw_dir"] = raw_dir
    out["source_url"] = url
    out["source_url_decoded"] = unquote(url)
    out["rows"] = rows
    out["article_count"] = len(rows)
    return out


def main() -> None:
    raw_dirs = {p.name for p in RAW_ROOT.iterdir() if p.is_dir()}
    configured = set(RAW_DOCUMENTS) | set(EXISTING_DOCUMENTS)
    missing = sorted(configured - raw_dirs)
    unexpected = sorted(raw_dirs - configured)
    if missing or unexpected:
        raise SystemExit(f"raw manifest mismatch; missing={missing}, unexpected={unexpected}")

    documents = [parse_document(raw_dir, RAW_DOCUMENTS[raw_dir]) for raw_dir in sorted(RAW_DOCUMENTS)]
    manifest = []
    for raw_dir in sorted(EXISTING_DOCUMENTS):
        meta = EXISTING_DOCUMENTS[raw_dir]
        path = RAW_ROOT / raw_dir / "مشاهده_متن_قانون.txt"
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        manifest.append({"raw_dir": raw_dir, "ref": meta["ref"], "source_url": source_url(lines), "reason": meta["reason"]})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    content = "# -*- coding: utf-8 -*-\n\n"
    content += "# Generated by scripts/build_health_bigdata_seeds.py; do not edit rows manually.\n"
    content += "DOCUMENTS = " + pprint.pformat(documents, width=120, sort_dicts=False, compact=False) + "\n\n"
    content += "SKIPPED_EXISTING = " + pprint.pformat(manifest, width=120, sort_dicts=False, compact=False) + "\n"
    OUTPUT.write_text(content, encoding="utf-8")

    total_rows = sum(doc["article_count"] for doc in documents)
    print(f"[OK] built {len(documents)} new documents / {total_rows} articles -> {OUTPUT}")
    print(f"[OK] skipped {len(manifest)} raw pages already represented in the database")
    for doc in documents:
        print(f"  {doc['ref']}: {doc['article_count']} articles — {doc['title']}")


if __name__ == "__main__":
    main()
