# -*- coding: utf-8 -*-
"""Load energy, oil, gas, electricity and renewables legal package."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "data" / "seed")]

from energy import ENERGY, OIL  # noqa: E402
from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic  # noqa: E402
from schema import get_connection  # noqa: E402

D = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
F = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

SOURCE_URLS = {
    "QN-1366": "https://www.ekhtebar.ir/قانون-نفت-مصوب-1366/",
    "QAEM-1389": "https://www.ekhtebar.ir/قانون-اصلاح-الگوی-مصرف-انرژی-مصوب-۱۳۸۹/",
    "QOBI-1346": "https://www.ekhtebar.ir/قانون-سازمان-برق-ایران-مصوب-۱۳۴۶/",
    "QMEP-1401": "https://www.ekhtebar.com/قانون-مانعزدایی-از-توسعه-صنعت-برق/",
    "QSATBA-1395": "https://www.ekhtebar.ir/قانون-اساسنامه-سازمان-انرژی‌های-تجدی/",
    "AIPC-1395": "https://www.ekhtebar.ir/شرایط-عمومی،-ساختار-و-الگوی-قراردادها/",
    "QVMN-1391": "https://shenasname.ir/naft/2750-قانون-وظایف-و-اختیارات-وزارت-نفت",
    "QHSE-1394": "https://www.ekhtebar.ir/قانون-حمایت-از-صنعت-برق-کشور-مصوب-۱۳۹۴/",
    "QTMN-1353": "https://fa.wikisource.org/wiki/قانون_تاسیس_وزارت_نیرو",
    "QUG-1396": "https://shenasname.ir/laws/4023-mojazat_ab",
    "AHEPL-1394": "https://www.ekhtebar.ir/حریم-خطوط-هوایی-انتقال-و-توزیع-نیروی-بر/",
    "ANGC-1356": "https://fa.wikisource.org/wiki/اساسنامه_شرکت_ملی_گاز_ایران",
    "QWTE-1399": "https://www.ekhtebar.ir/قانون-کمک-به-ساماندهی-پسماندهای-عادی-ب/",
    "AIEO-1403": "https://www.ekhtebar.ir/آیین-نامه-اجرایی-بند-الف-ماده-46-قانون-بر/",
    "DMBE-1403": "https://davoudabadi.ir/page/80541738",
    "AIREP-1394": "https://www.solh.ir/regulation/7/6538",
    "DTEP-1404": "https://www.mizanonline.ir/fa/news/4832859/ابلاغ-تعرفه‌های-برق-و-شرایط-عمومی-جهت-اجرا-از-ابتدای-خرداد-۱۴۰۴",
    "AIKBRE-1401": "https://tolosanat.com/articles/ماده-۱۶-قانون-جهش-تولید-دانش-بنیان-مصوب/",
    "DAD-POWER-UNAUTH-1403": "https://davoudabadi.ir/page/0491832",
    "DAD-POWERPLANT-ZARGAN-1381": "https://davoudabadi.ir/page/0374298",
    "DAD-ELECTRIC-DIGGING-1401": "https://davoudabadi.ir/page/2039541",
    "DAD-OIL-GAS-RETIRE-1400": "https://davoudabadi.ir/page/6753081",
}

SEED_DOCS = [
    {
        "ref": "QN-1366",
        "title": "قانون نفت",
        "short": "قانون نفت",
        "date": "1987-09-06",
        "rows": OIL,
        "notes": "متن ۱۶ ماده‌ای منبع‌دار قانون نفت، با اصلاحات منعکس در منبع.",
        "tags": ("نفت", "گاز", "قرارداد نفتی", "وزارت نفت"),
    },
    {
        "ref": "QAEM-1389",
        "title": "قانون اصلاح الگوی مصرف انرژی",
        "short": "اصلاح الگوی مصرف انرژی",
        "date": "2011-02-23",
        "rows": ENERGY,
        "notes": "متن کامل ۷۵ ماده قانون اصلاح الگوی مصرف انرژی.",
        "tags": ("مصرف انرژی", "بهره‌وری انرژی", "استاندارد انرژی", "محیط زیست"),
    },
]

PARSED_DOCS = [
    {
        "ref": "QOBI-1346",
        "title": "قانون سازمان برق ایران",
        "short": "سازمان برق ایران",
        "date": "1967-07-10",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "type_code": "law",
        "status_code": "amended",
        "source_file": "electricity_org_1346.md",
        "count": 23,
        "notes": "متن کامل ۲۳ ماده قانون سازمان برق ایران؛ شامل تعدیل جزای نقدی ماده ۱۰ در سال ۱۴۰۳ طبق منبع.",
        "tags": ("برق", "وزارت نیرو", "شرکت برق منطقه‌ای", "تعرفه برق"),
    },
    {
        "ref": "QMEP-1401",
        "title": "قانون مانع‌زدایی از توسعه صنعت برق",
        "short": "مانع‌زدایی از توسعه صنعت برق",
        "date": "2022-11-06",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "electricity_development_1401.md",
        "count": 19,
        "notes": "متن کامل ۱۹ ماده و ۷ تبصره قانون مانع‌زدایی از توسعه صنعت برق.",
        "tags": ("صنعت برق", "نیروگاه", "تجدیدپذیر", "تعرفه برق", "بورس انرژی"),
    },
    {
        "ref": "QSATBA-1395",
        "title": "قانون اساسنامه سازمان انرژی‌های تجدیدپذیر و بهره‌وری انرژی برق (ساتبا)",
        "short": "اساسنامه ساتبا",
        "date": "2016-12-14",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "satba_statute_1395.md",
        "count": 13,
        "notes": "متن کامل ۱۳ ماده و ۶ تبصره قانون اساسنامه سازمان انرژی‌های تجدیدپذیر و بهره‌وری انرژی برق (ساتبا).",
        "tags": ("ساتبا", "انرژی تجدیدپذیر", "برق تجدیدپذیر", "بهره‌وری انرژی برق"),
    },
    {
        "ref": "AIPC-1395",
        "title": "شرایط عمومی، ساختار و الگوی قراردادهای بالادستی نفت و گاز",
        "short": "الگوی قراردادهای بالادستی نفت و گاز",
        "date": "2016-08-03",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "amended",
        "source_file": "ipc_upstream_contracts_1395.md",
        "count": 16,
        "notes": "متن کامل مواد ۱۶گانه تصویب‌نامه شرایط عمومی، ساختار و الگوی قراردادهای بالادستی نفت و گاز از بازنشر اختبار؛ مقابله رسمی‌تر توصیه می‌شود.",
        "tags": ("قرارداد نفتی", "بالادستی نفت و گاز", "IPC", "شرکت ملی نفت"),
    },
    {
        "ref": "QVMN-1391",
        "title": "قانون وظایف و اختیارات وزارت نفت",
        "short": "وظایف و اختیارات وزارت نفت",
        "date": "2012-05-08",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "oil_ministry_powers_1391.md",
        "count": 15,
        "notes": "متن کامل ۱۵ ماده قانون وظایف و اختیارات وزارت نفت.",
        "tags": ("وزارت نفت", "حاکمیت نفت و گاز", "قرارداد نفتی", "صنعت نفت"),
    },
    {
        "ref": "QHSE-1394",
        "title": "قانون حمایت از صنعت برق کشور",
        "short": "حمایت از صنعت برق",
        "date": "2015-11-01",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "electricity_support_1394.md",
        "count": 6,
        "notes": "متن کامل ۶ ماده و یک تبصره قانون حمایت از صنعت برق کشور.",
        "tags": ("صنعت برق", "توانیر", "انشعاب برق", "عوارض برق"),
    },
    {
        "ref": "QTMN-1353",
        "title": "قانون تأسیس وزارت نیرو",
        "short": "تأسیس وزارت نیرو",
        "date": "1974-12-22",
        "authority": "مجلس شورای ملی",
        "type_code": "law",
        "status_code": "amended",
        "source_file": "energy_ministry_1353.md",
        "count": 11,
        "notes": "متن کامل ۱۱ ماده قانون تأسیس وزارت نیرو؛ بازنشر از ویکی‌نبشته، مقابله رسمی‌تر توصیه می‌شود.",
        "tags": ("وزارت نیرو", "آب و برق", "انرژی", "سیاست انرژی"),
    },
    {
        "ref": "QUG-1396",
        "title": "قانون مجازات استفاده‌کنندگان غیرمجاز از آب، برق، تلفن، فاضلاب و گاز",
        "short": "استفاده غیرمجاز از آب، برق، تلفن، فاضلاب و گاز",
        "date": "2017-05-31",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "utility_unauthorized_use_1396.md",
        "count": 7,
        "notes": "متن کامل ۷ ماده و ۴ تبصره قانون مجازات استفاده‌کنندگان غیرمجاز از آب، برق، تلفن، فاضلاب و گاز.",
        "tags": ("استفاده غیرمجاز", "انشعاب برق", "انشعاب گاز", "خدمات عمومی"),
    },
    {
        "ref": "AHEPL-1394",
        "title": "تصویب‌نامه حریم خطوط هوایی انتقال و توزیع نیروی برق",
        "short": "حریم خطوط انتقال و توزیع برق",
        "date": "2015-04-19",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "in_force",
        "source_file": "power_line_right_of_way_1394.md",
        "count": 13,
        "notes": "متن کامل ۱۳ ماده تصویب‌نامه حریم خطوط هوایی انتقال و توزیع نیروی برق.",
        "tags": ("حریم خطوط برق", "انتقال برق", "توزیع برق", "وزارت نیرو"),
    },
    {
        "ref": "ANGC-1356",
        "title": "اساسنامه شرکت ملی گاز ایران",
        "short": "اساسنامه شرکت ملی گاز ایران",
        "date": "1977-11-03",
        "authority": "مجلس شورای ملی",
        "type_code": "bylaw",
        "status_code": "amended",
        "source_file": "national_gas_company_statute_1356.md",
        "count": 49,
        "notes": "متن کامل ۴۹ ماده و ۱۳ تبصره اساسنامه شرکت ملی گاز ایران از بازنشر ویکی‌نبشته؛ مقابله رسمی‌تر توصیه می‌شود.",
        "tags": ("شرکت ملی گاز", "گاز طبیعی", "صنعت گاز", "شرکت ملی نفت"),
    },
    {
        "ref": "QWTE-1399",
        "title": "قانون کمک به ساماندهی پسماندهای عادی با مشارکت بخش غیردولتی",
        "short": "تبدیل پسماند عادی به انرژی",
        "date": "2020-04-08",
        "authority": "مجلس شورای اسلامی",
        "type_code": "law",
        "status_code": "in_force",
        "source_file": "waste_to_energy_1399.md",
        "count": 6,
        "notes": "متن کامل ۶ ماده قانون کمک به ساماندهی پسماندهای عادی با مشارکت بخش غیردولتی؛ پیونددهنده مدیریت پسماند با تولید برق و انرژی.",
        "tags": ("پسماند به انرژی", "برق تجدیدپذیر", "پسماند", "خرید تضمینی برق"),
    },
    {
        "ref": "AIREP-1394",
        "title": "آیین‌نامه اجرایی ماده (۶۱) قانون اصلاح الگوی مصرف انرژی",
        "short": "آیین‌نامه خرید تضمینی برق تجدیدپذیر ماده ۶۱",
        "date": "2016-02-03",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "in_force",
        "source_file": "renewable_purchase_article61_1394.md",
        "count": 7,
        "notes": "متن کامل ۷ ماده آیین‌نامه اجرایی ماده ۶۱ قانون اصلاح الگوی مصرف انرژی درباره نرخ پایه و قرارداد خرید تضمینی برق تجدیدپذیر؛ مقابله رسمی‌تر توصیه می‌شود.",
        "tags": ("خرید تضمینی برق", "برق تجدیدپذیر", "ماده ۶۱", "ساتبا", "تعرفه تجدیدپذیر"),
    },
    {
        "ref": "DTEP-1404",
        "title": "بخشنامه ابلاغ تعرفه‌های برق و شرایط عمومی آنها از ابتدای خرداد ۱۴۰۴",
        "short": "تعرفه‌های برق و شرایط عمومی ۱۴۰۴",
        "date": "2025-04-20",
        "authority": "وزارت نیرو",
        "type_code": "directive",
        "status_code": "in_force",
        "source_file": "electricity_tariffs_1404.md",
        "count": 10,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از بخشنامه تعرفه‌های برق و شرایط عمومی آنها در سال ۱۴۰۴؛ جداول تصویری نرخ‌ها و پیوست کامل عددی، رونوشت لفظ‌به‌لفظ کامل نشده‌اند.",
        "tags": ("تعرفه برق", "شرایط عمومی برق", "هزینه تأمین برق", "مدیریت مصرف", "پاسخگویی بار"),
    },
    {
        "ref": "AIKBRE-1401",
        "title": "آیین‌نامه اجرایی ماده (۱۶) قانون جهش تولید دانش‌بنیان درباره تأمین برق تجدیدپذیر صنایع",
        "short": "آیین‌نامه ماده ۱۶ جهش تولید دانش‌بنیان و برق تجدیدپذیر صنایع",
        "date": "2022-08-17",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "amended",
        "source_file": "knowledge_based_article16_renewable_bylaw_1401.md",
        "count": 6,
        "notes": "بازنشر ماده‌ای منبع‌دار و غیررسمی از آیین‌نامه اجرایی ماده ۱۶ قانون جهش تولید دانش‌بنیان با اصلاح ماده ۵ در ۱۴۰۱/۰۸/۱۵؛ مقابله رسمی‌تر توصیه می‌شود.",
        "tags": ("جهش تولید دانش‌بنیان", "برق تجدیدپذیر صنایع", "بورس انرژی", "تعرفه تجدیدپذیر", "ساتبا"),
    },
    {
        "ref": "DAD-POWER-UNAUTH-1403",
        "title": "دادنامه هیأت تخصصی دیوان عدالت اداری درباره دستورالعمل برخورد با استفاده غیرمجاز از برق",
        "short": "دادنامه استفاده غیرمجاز از برق",
        "date": "2024-07-10",
        "authority": "هیأت تخصصی صنایع و بازرگانی دیوان عدالت اداری",
        "type_code": "divan_ruling",
        "status_code": "in_force",
        "source_file": "energy_divan_unauthorized_electricity_1403.md",
        "count": 1,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از دادنامه شماره ۱۴۰۳۳۱۳۹۰۰۰۰۹۱۷۸۰۹ هیأت تخصصی صنایع و بازرگانی درباره دستورالعمل توانیر در برخورد با استفاده غیرمجاز از برق؛ رونوشت کامل نیست.",
        "tags": ("دیوان عدالت اداری", "استفاده غیرمجاز از برق", "توانیر", "انشعاب برق"),
    },
    {
        "ref": "DAD-POWERPLANT-ZARGAN-1381",
        "title": "دادنامه هیأت عمومی دیوان عدالت اداری درباره واگذاری بهره‌برداری نیروگاه‌های رامین و زرگان",
        "short": "دادنامه بهره‌برداری نیروگاه زرگان",
        "date": "2003-01-19",
        "authority": "هیأت عمومی دیوان عدالت اداری",
        "type_code": "divan_ruling",
        "status_code": "in_force",
        "source_file": "energy_divan_zargan_powerplant_1381.md",
        "count": 1,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از دادنامه شماره ۳۸۱ هیأت عمومی درباره بند ۵ دستورالعمل وزارت نیرو و بهره‌برداری نیروگاه‌های رامین و زرگان؛ رونوشت کامل نیست.",
        "tags": ("دیوان عدالت اداری", "نیروگاه", "توانیر", "خصوصی‌سازی برق"),
    },
    {
        "ref": "DAD-ELECTRIC-DIGGING-1401",
        "title": "دادنامه هیأت عمومی دیوان عدالت اداری درباره بهای خدمات حفاری و جابه‌جایی تأسیسات شبکه برق",
        "short": "دادنامه بهای خدمات حفاری و شبکه برق",
        "date": "2022-06-07",
        "authority": "هیأت عمومی دیوان عدالت اداری",
        "type_code": "divan_ruling",
        "status_code": "in_force",
        "source_file": "energy_divan_electric_network_digging_1401.md",
        "count": 1,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از دادنامه شماره ۱۴۰۱۰۹۹۷۰۹۰۵۸۱۰۴۷۲ درباره ابطال بهای خدمات حفاری و کنده‌کاری معابر و تبصره مربوط به تیر برق؛ رونوشت کامل نیست.",
        "tags": ("دیوان عدالت اداری", "شبکه برق", "تیر برق", "حفاری معابر", "شهرداری"),
    },
    {
        "ref": "DAD-OIL-GAS-RETIRE-1400",
        "title": "دادنامه هیأت عمومی دیوان عدالت اداری درباره مقررات بازنشستگی کارکنان صنعت نفت و گاز",
        "short": "دادنامه بازنشستگی کارکنان صنعت نفت و گاز",
        "date": "2021-10-26",
        "authority": "هیأت عمومی دیوان عدالت اداری",
        "type_code": "divan_ruling",
        "status_code": "in_force",
        "source_file": "energy_divan_oil_gas_retirement_1400.md",
        "count": 1,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از دادنامه شماره ۲۳۱۵ هیأت عمومی درباره مقررات بازنشستگی کارکنان صنعت نفت، از جمله کارکنان شرکت انتقال گاز/شرکت ملی گاز؛ رونوشت کامل نیست.",
        "tags": ("دیوان عدالت اداری", "وزارت نفت", "شرکت ملی گاز", "استخدام صنعت نفت", "بازنشستگی"),
    },
    {
        "ref": "AIEO-1403",
        "title": "آیین‌نامه اجرایی بند (الف) ماده (۴۶) قانون برنامه پنجساله هفتم پیشرفت جمهوری اسلامی ایران",
        "short": "آیین‌نامه حساب بهینه‌سازی مصرف انرژی برنامه هفتم",
        "date": "2024-11-20",
        "authority": "هیئت وزیران",
        "type_code": "regulation",
        "status_code": "in_force",
        "source_file": "energy_optimization_account_1403.md",
        "count": 10,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از آیین‌نامه اجرایی بند الف ماده ۴۶ برنامه هفتم درباره حساب بهینه‌سازی مصرف انرژی، گواهی صرفه‌جویی و بازار بهینه‌سازی؛ رونوشت لفظ‌به‌لفظ کامل نیست.",
        "tags": ("حساب بهینه‌سازی", "گواهی صرفه‌جویی", "بازار بهینه‌سازی", "برنامه هفتم"),
    },
    {
        "ref": "DMBE-1403",
        "title": "دستورالعمل وزارت نیرو در خصوص توسعه مبادلات برق در بورس انرژی",
        "short": "دستورالعمل توسعه مبادلات برق در بورس انرژی",
        "date": "2024-09-22",
        "authority": "وزارت نیرو",
        "type_code": "directive",
        "status_code": "in_force",
        "source_file": "electricity_exchange_bourse_1403.md",
        "count": 10,
        "notes": "خلاصه/گزیده ساختاری منبع‌دار از دستورالعمل توسعه مبادلات برق در بورس انرژی؛ رونوشت لفظ‌به‌لفظ کامل نیست.",
        "tags": ("بورس انرژی", "تابلو برق سبز", "بازار برق", "خرده‌فروشی برق"),
    },
]


def one(conn, query: str, value: str):
    row = conn.execute(query, (value,)).fetchone()
    return row["id"] if row else None


def ensure_authority(conn, name: str, authority_type: str = "legislative") -> int:
    row = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO authorities(name_fa, authority_type) VALUES(?,?)", (name, authority_type))
    return cur.lastrowid


def parse_articles(source_file: str, count: int):
    lines = (ROOT / "data" / "source_cache" / source_file).read_text(encoding="utf-8").splitlines()
    heads = []
    for i, line in enumerate(lines):
        clean = line.replace("*", "").replace("#", "").replace("\u200c", " ").strip()
        match = re.match(r"^ماده\s*([۰-۹0-9]+)\b", clean)
        if match:
            heads.append((int(match.group(1).translate(D)), i))
    out = []
    for article_no in range(1, count + 1):
        pos = next(idx for idx, (num, _) in enumerate(heads) if num == article_no)
        begin = heads[pos][1]
        end = heads[pos + 1][1] if pos + 1 < len(heads) else len(lines)
        text = "\n".join(lines[begin:end])
        text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text).replace("**", "")
        text = text.replace("ي", "ی").replace("ك", "ک")
        text = re.sub(r"^\s*ماده\s*[۰-۹0-9]+\s*[-ـ–:]?\s*", "", text.strip(), 1)
        out.append((str(article_no), re.sub(r"[ \t]+", " ", text).strip()))
    return out


def upsert_doc(conn, doc: dict) -> int:
    authority = doc.get("authority", "مجلس شورای اسلامی")
    auth_type = "executive" if authority in {"هیئت وزیران", "وزارت نفت", "وزارت نیرو"} else "legislative"
    ensure_authority(conn, authority, auth_type)
    ref = doc["ref"]
    type_code = doc.get("type_code", "law")
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", ref)
    if not did:
        did = get_or_create_document(
            conn,
            title=doc["title"],
            short_title=doc["short"],
            type_code=type_code,
            issuing_authority=authority,
            status_code=doc.get("status_code", "in_force"),
            ratification_date=doc["date"],
            effective_date=doc["date"],
            reference_code=ref,
            notes=doc["notes"],
        )
    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            doc["title"], doc["short"], one(conn, "SELECT id FROM document_types WHERE code=?", type_code),
            one(conn, "SELECT id FROM authorities WHERE name_fa=?", authority),
            one(conn, "SELECT id FROM statuses WHERE code=?", doc.get("status_code", "in_force")),
            doc["date"], doc["date"], doc["notes"], did,
        ),
    )
    return did


def clear_owned(conn, did: int):
    for query in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(query, (did,))


def attach(conn, did: int, tags=()):
    for topic in ("حقوق عمومی", "انرژی، نفت، گاز و برق"):
        conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES(?)", (topic,))
        link_document_topic(conn, did, topic)
    for tag in sorted(set(("انرژی", "نفت و گاز", "برق", "بهره‌وری انرژی")) | set(tags)):
        link_document_tag(conn, did, add_tag(conn, tag))


def add_rows(conn, did: int, ref: str, date: str, rows, source: str):
    for raw_no, text in rows:
        article_no = str(raw_no).translate(F)
        key_no = str(raw_no).translate(D).replace(" ", "-")
        add_article(conn, did, article_no=article_no, article_key=f"{ref}:{key_no}", version_no=1, is_current=1, effective_date=date, text=text, source_note=source)


def add_rel(conn, from_ref: str, to_ref: str, rel_type: str = "cites", desc: str | None = None):
    from_doc = one(conn, "SELECT id FROM documents WHERE reference_code=?", from_ref)
    to_doc = one(conn, "SELECT id FROM documents WHERE reference_code=?", to_ref)
    if from_doc and to_doc:
        add_relation(conn, from_doc, rel_type, to_doc, description=desc or f"پیوند موضوعی {from_ref} با {to_ref}.")


def load_doc(conn, doc: dict, rows):
    did = upsert_doc(conn, doc)
    clear_owned(conn, did)
    attach(conn, did, doc.get("tags", ()))
    add_rows(conn, did, doc["ref"], doc["date"], rows, SOURCE_URLS[doc["ref"]])


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        for doc in SEED_DOCS:
            load_doc(conn, doc, doc["rows"])
        for doc in PARSED_DOCS:
            load_doc(conn, doc, parse_articles(doc["source_file"], doc["count"]))

        add_rel(conn, "QAEM-1389", "QN-1366", "cites", "قانون اصلاح الگوی مصرف انرژی به تکالیف مصرف و حامل‌های انرژی و وظایف وزارت نفت مرتبط است.")
        add_rel(conn, "QOBI-1346", "QMEP-1401", "cites", "قانون مانع‌زدایی از توسعه صنعت برق ادامه‌دهنده و روزآمدکننده چارچوب توسعه، انتقال، توزیع و تعرفه برق است.")
        add_rel(conn, "QMEP-1401", "QAEM-1389", "cites", "قانون مانع‌زدایی از توسعه صنعت برق در مواد ۱۱ و ۱۴ به سازوکارهای صرفه‌جویی و اصلاح الگوی مصرف انرژی ارجاع دارد.")
        add_rel(conn, "QMEP-1401", "QN-1366", "cites", "تکالیف وزارت نفت درباره سوخت نیروگاه‌ها و سوخت صرفه‌جویی‌شده با قانون نفت و وظایف حاکمیتی نفت مرتبط است.")
        add_rel(conn, "QMEP-1401", "QSATBA-1395", "cites", "توسعه نیروگاه‌های تجدیدپذیر و خرید تضمینی برق پاک با مأموریت ساتبا پیوند دارد.")
        add_rel(conn, "QSATBA-1395", "QAEM-1389", "implements", "ساتبا برای ارتقای بهره‌وری انرژی و توسعه انرژی‌های تجدیدپذیر تشکیل شده و با قانون اصلاح الگوی مصرف انرژی پیوند دارد.")
        add_rel(conn, "QSATBA-1395", "QOBI-1346", "cites", "ساتبا در حوزه تولید برق تجدیدپذیر و بهره‌وری انرژی برق در چارچوب کلان صنعت برق فعالیت می‌کند.")
        add_rel(conn, "QSATBA-1395", "QMEP-1401", "cites", "قانون مانع‌زدایی از توسعه صنعت برق، توسعه سالانه ظرفیت تجدیدپذیر را در مسیر مأموریت ساتبا تقویت می‌کند.")
        add_rel(conn, "AIPC-1395", "QN-1366", "implements", "الگوی قراردادهای بالادستی نفت و گاز بر پایه قانون نفت و اصلاح قانون نفت تنظیم شده است.")
        add_rel(conn, "AIPC-1395", "QMEP-1401", "cites", "الگوی IPC در حوزه قراردادها و سرمایه‌گذاری نفت و گاز با تأمین سوخت و توسعه نیروگاه‌های موضوع قانون صنعت برق پیوند موضوعی دارد.")
        add_rel(conn, "AIPC-1395", "QAEM-1389", "cites", "در قراردادهای بالادستی رعایت HSE، صیانت از منابع و بهره‌برداری بهینه با سیاست‌های بهره‌وری انرژی پیوند دارد.")
        add_rel(conn, "QVMN-1391", "QN-1366", "implements", "قانون وظایف وزارت نفت، اعمال حاکمیت و مالکیت عمومی بر منابع نفت و گاز را در چارچوب قانون نفت سامان می‌دهد.")
        add_rel(conn, "QVMN-1391", "AIPC-1395", "cites", "ماده ۷ قانون وظایف وزارت نفت، تصویب شرایط عمومی قراردادهای نفتی با پیشنهاد وزیر نفت را مقرر می‌کند.")
        add_rel(conn, "QVMN-1391", "QAEM-1389", "cites", "وزارت نفت در قانون وظایف خود مکلف به بهینه‌سازی مصرف سوخت در چارچوب قانون اصلاح الگوی مصرف انرژی است.")
        add_rel(conn, "QVMN-1391", "DAD-OIL-DEGREE-1404", "cites", "دادنامه استخدامی وزارت نفت با تفسیر حدود صلاحیت وزارت نفت و مقررات استخدامی صنعت نفت مرتبط است.")
        add_rel(conn, "QVMN-1391", "DAD-SS-OILTRANSPORT-1404", "cites", "دادنامه حق بیمه قراردادهای حمل‌ونقل مواد نفتی با فعالیت‌های پیمانکاری و زنجیره حمل مواد نفتی در حوزه وزارت نفت مرتبط است.")
        add_rel(conn, "QHSE-1394", "QOBI-1346", "cites", "قانون حمایت از صنعت برق، چارچوب مالی و حمایتی صنعت برق را بر بستر قانون سازمان برق ایران تکمیل می‌کند.")
        add_rel(conn, "QHSE-1394", "QMEP-1401", "cites", "قانون مانع‌زدایی از توسعه صنعت برق، احکام حمایتی و مالی صنعت برق را توسعه داده است.")
        add_rel(conn, "QHSE-1394", "QSATBA-1395", "cites", "عوارض ماده ۵ قانون حمایت از صنعت برق از منابع مالی سازمان ساتبا برای خرید تضمینی برق تجدیدپذیر است.")
        add_rel(conn, "QTMN-1353", "QOBI-1346", "cites", "قانون تأسیس وزارت نیرو جانشین وزارت آب و برق و عهده‌دار وظایف تولید، انتقال و توزیع برق شد.")
        add_rel(conn, "QTMN-1353", "QSATBA-1395", "cites", "اساسنامه ساتبا بخشی از وظایف مرتبط با انرژی تجدیدپذیر و بهره‌وری برق وزارت نیرو را از طریق این سازمان اعمال می‌کند.")
        add_rel(conn, "QTMN-1353", "QHSE-1394", "cites", "حمایت از صنعت برق و منابع مالی شبکه‌های برق در چارچوب وظایف وزارت نیرو قرار دارد.")
        add_rel(conn, "QTMN-1353", "QN-1366", "cites", "قانون تأسیس وزارت نیرو، شرکت ملی نفت را در نفت و گاز تابع قانون نفت و قوانین خاص خود دانسته و هماهنگی برنامه‌های انرژی را به وزارت نیرو می‌سپارد.")
        add_rel(conn, "QUG-1396", "QOBI-1346", "cites", "جرم استفاده غیرمجاز از برق و دستکاری وسایل اندازه‌گیری با نظام تأمین و فروش برق مرتبط است.")
        add_rel(conn, "QUG-1396", "QTMN-1353", "cites", "وزارت نیرو یکی از مراجع تهیه آیین‌نامه اجرایی قانون استفاده غیرمجاز از خدمات عمومی است.")
        add_rel(conn, "QUG-1396", "QVMN-1391", "cites", "وزارت نفت و حوزه گاز یکی از مراجع تهیه آیین‌نامه اجرایی قانون استفاده غیرمجاز از خدمات عمومی است.")
        add_rel(conn, "AHEPL-1394", "QOBI-1346", "implements", "تصویب‌نامه حریم خطوط برق در اجرای تبصره ۲ ماده ۱۸ قانون سازمان برق ایران تصویب شده است.")
        add_rel(conn, "AHEPL-1394", "QTMN-1353", "cites", "تعیین و اعمال حریم خطوط برق در چارچوب وظایف وزارت نیرو در انتقال و توزیع انرژی برق قرار دارد.")
        add_rel(conn, "AHEPL-1394", "QUG-1396", "cites", "حریم خطوط برق و حفاظت تأسیسات با پیشگیری از استفاده و تصرفات غیرمجاز در خدمات برق مرتبط است.")
        add_rel(conn, "ANGC-1356", "QN-1366", "cites", "اساسنامه شرکت ملی گاز، شرکت را فرعی شرکت ملی نفت و فعال در تهیه، انتقال، فروش و صدور گاز می‌داند.")
        add_rel(conn, "ANGC-1356", "QVMN-1391", "cites", "شرکت ملی گاز از شرکت‌های اصلی/تابعه وزارت نفت در چارچوب قانون وظایف و اختیارات وزارت نفت است.")
        add_rel(conn, "ANGC-1356", "QUG-1396", "cites", "استفاده غیرمجاز از گاز و انشعابات گاز با وظایف توزیع و فروش گاز شرکت ملی گاز مرتبط است.")
        add_rel(conn, "QWTE-1399", "QHSE-1394", "cites", "تعرفه پسماند قانون تبدیل پسماند به انرژی از منابع موضوع ماده ۵ قانون حمایت از صنعت برق تأمین می‌شود.")
        add_rel(conn, "QWTE-1399", "QSATBA-1395", "cites", "تبدیل پسماند عادی به انرژی و خرید تضمینی برق با مأموریت ساتبا در توسعه برق تجدیدپذیر و پاک مرتبط است.")
        add_rel(conn, "QWTE-1399", "QMEP-1401", "cites", "توسعه برق حاصل از پسماند با سیاست‌های توسعه صنعت برق، تجدیدپذیرها و خرید تضمینی مرتبط است.")
        add_rel(conn, "QWTE-1399", "QMP-1383", "cites", "قانون تبدیل پسماند به انرژی در چهارچوب قانون مدیریت پسماندها اجرا می‌شود.")
        add_rel(conn, "AIREP-1394", "QAEM-1389", "implements", "آیین‌نامه ماده ۶۱ سازوکار خرید تضمینی برق تجدیدپذیر را در اجرای قانون اصلاح الگوی مصرف انرژی تنظیم می‌کند.")
        add_rel(conn, "AIREP-1394", "QSATBA-1395", "cites", "سازمان ساتبا/انرژی‌های نو متولی قراردادها و پرداخت‌های خرید تضمینی برق تجدیدپذیر است.")
        add_rel(conn, "AIREP-1394", "QWTE-1399", "cites", "ضرایب افزاینده تولید برق از پسماند در آیین‌نامه ماده ۶۱ با سیاست تبدیل پسماند به انرژی پیوند دارد.")
        add_rel(conn, "AIREP-1394", "QHSE-1394", "cites", "منابع مالی و عوارض صنعت برق با خرید تضمینی برق تجدیدپذیر و پاک مرتبط است.")
        add_rel(conn, "AIREP-1394", "DMBE-1403", "cites", "خرید تضمینی و عرضه برق تجدیدپذیر در تابلو برق سبز بورس انرژی دو سازوکار مکمل حمایت از تجدیدپذیرها هستند.")
        add_rel(conn, "DTEP-1404", "QMEP-1401", "implements", "بخشنامه تعرفه‌های برق ۱۴۰۴ با استناد به قانون مانع‌زدایی از توسعه صنعت برق ابلاغ شده است.")
        add_rel(conn, "DTEP-1404", "QHSE-1394", "cites", "تعرفه‌ها، عوارض و هزینه تأمین برق با چارچوب حمایتی و مالی صنعت برق پیوند دارد.")
        add_rel(conn, "DTEP-1404", "QOBI-1346", "cites", "تعرفه‌های برق و شرایط عمومی بر بستر نظام فروش، انتقال و توزیع برق قانون سازمان برق ایران اعمال می‌شوند.")
        add_rel(conn, "DTEP-1404", "DMBE-1403", "cites", "در تجاوز از قدرت قراردادی برای مشترکان بزرگ به اصلاحیه دستورالعمل توسعه مبادلات برق در بورس انرژی ارجاع شده است.")
        add_rel(conn, "DTEP-1404", "AIEO-1403", "cites", "مدیریت مصرف، پاسخگویی بار و هزینه تأمین برق با سازوکارهای بهینه‌سازی مصرف انرژی پیوند موضوعی دارد.")
        add_rel(conn, "AIKBRE-1401", "QSATBA-1395", "cites", "ساتبا در آیین‌نامه ماده ۱۶ متولی محاسبه تعرفه تجدیدپذیر و سازوکارهای حمایتی است.")
        add_rel(conn, "AIKBRE-1401", "DMBE-1403", "cites", "واحدهای صنعتی مشمول می‌توانند برق تجدیدپذیر مورد نیاز را از بهابازار/بورس انرژی و تابلو برق سبز تأمین کنند.")
        add_rel(conn, "AIKBRE-1401", "AIREP-1394", "cites", "قرارداد خرید تضمینی برق با ساتبا و مازاد تولید در آیین‌نامه ماده ۱۶ با سازوکار ماده ۶۱ قانون اصلاح الگوی مصرف انرژی مرتبط است.")
        add_rel(conn, "AIKBRE-1401", "QMEP-1401", "cites", "الزام صنایع بزرگ به تأمین برق تجدیدپذیر با سیاست‌های توسعه و رفع موانع صنعت برق مرتبط است.")
        add_rel(conn, "AIKBRE-1401", "DTEP-1404", "cites", "تعرفه تجدیدپذیر و قبض برق واحدهای صنعتی مشمول در عمل با نظام تعرفه‌های برق و شرایط عمومی پیوند دارد.")
        add_rel(conn, "DAD-POWER-UNAUTH-1403", "QUG-1396", "interprets", "دادنامه هیأت تخصصی، مواد ۱ و ۲ قانون مجازات استفاده‌کنندگان غیرمجاز از خدمات عمومی را در زمینه برق و تکالیف پیگیری قضایی تفسیر می‌کند.")
        add_rel(conn, "DAD-POWER-UNAUTH-1403", "DTEP-1404", "cites", "رأی به آیین‌نامه/شرایط تعرفه‌ای برق و آثار مصرف غیرمجاز، قطع موقت انشعاب و محاسبه خسارت مرتبط است.")
        add_rel(conn, "DAD-POWER-UNAUTH-1403", "QOBI-1346", "cites", "استفاده غیرمجاز از برق و اصلاح انشعابات با چارچوب توزیع و فروش برق در قانون سازمان برق ایران پیوند دارد.")
        add_rel(conn, "DAD-POWERPLANT-ZARGAN-1381", "QTMN-1353", "cites", "واگذاری بهره‌برداری نیروگاه‌های رامین و زرگان در حوزه وظایف وزارت نیرو و سازماندهی صنعت برق مطرح شده است.")
        add_rel(conn, "DAD-POWERPLANT-ZARGAN-1381", "QOBI-1346", "cites", "موضوع رأی به تولید و بهره‌برداری نیروگاهی و ارتباط با ساختار سازمان برق ایران مربوط است.")
        add_rel(conn, "DAD-POWERPLANT-ZARGAN-1381", "QMEP-1401", "cites", "رویه واگذاری بهره‌برداری نیروگاه و نقش بخش غیردولتی با سیاست‌های توسعه صنعت برق ارتباط موضوعی دارد.")
        add_rel(conn, "DAD-ELECTRIC-DIGGING-1401", "QOBI-1346", "cites", "رأی درباره حفاری معابر، کاشت و جابه‌جایی تیر برق و تأسیسات شبکه توزیع با قانون سازمان برق ایران مرتبط است.")
        add_rel(conn, "DAD-ELECTRIC-DIGGING-1401", "AHEPL-1394", "cites", "جابه‌جایی تأسیسات و تیرهای برق با مقررات حریم و خطوط انتقال و توزیع نیروی برق پیوند دارد.")
        add_rel(conn, "DAD-ELECTRIC-DIGGING-1401", "QTMN-1353", "cites", "هماهنگی شبکه برق شهری و تأسیسات عمومی در چارچوب وظایف وزارت نیرو مطرح است.")
        add_rel(conn, "DAD-OIL-GAS-RETIRE-1400", "QVMN-1391", "interprets", "دادنامه حدود اختیارات وزارت نفت در نظام‌های اداری و استخدامی کارکنان صنعت نفت را با استناد به ماده ۱۰ قانون وظایف و اختیارات وزارت نفت بررسی می‌کند.")
        add_rel(conn, "DAD-OIL-GAS-RETIRE-1400", "ANGC-1356", "cites", "پرونده درباره کارکنان صنعت نفت و گاز و از جمله شرکت انتقال گاز/شرکت ملی گاز ایران مطرح شده است.")
        add_rel(conn, "DAD-OIL-GAS-RETIRE-1400", "QN-1366", "cites", "نظام اداری صنعت نفت و گاز با چارچوب حاکمیت و شرکت‌های تابعه صنعت نفت مرتبط است.")
        add_rel(conn, "AIEO-1403", "QAEM-1389", "implements", "آیین‌نامه حساب بهینه‌سازی مصرف انرژی در اجرای سیاست‌های اصلاح الگوی مصرف انرژی و گواهی صرفه‌جویی است.")
        add_rel(conn, "AIEO-1403", "QMEP-1401", "cites", "حساب بهینه‌سازی و بازپرداخت طرح‌های بهینه‌سازی با ماده ۱۴ قانون مانع‌زدایی از توسعه صنعت برق پیوند دارد.")
        add_rel(conn, "AIEO-1403", "QVMN-1391", "cites", "وزارت نفت و شرکت‌های تابعه در منابع و ناشران گواهی صرفه‌جویی این آیین‌نامه نقش دارند.")
        add_rel(conn, "AIEO-1403", "QSATBA-1395", "cites", "سازمان ساتبا در بند الف ماده ۴۶ برنامه هفتم و ساختار بهینه‌سازی انرژی مورد اشاره قرار گرفته است.")
        add_rel(conn, "DMBE-1403", "QTMN-1353", "implements", "دستورالعمل بورس انرژی برق بر مبنای اختیارات وزارت نیرو در قانون تأسیس وزارت نیرو ابلاغ شده است.")
        add_rel(conn, "DMBE-1403", "QMEP-1401", "cites", "مبادلات برق در بورس انرژی با احکام قانون مانع‌زدایی از توسعه صنعت برق و تعرفه‌ها پیوند دارد.")
        add_rel(conn, "DMBE-1403", "QSATBA-1395", "cites", "تابلوی برق سبز و گواهی تولید برق تجدیدپذیر با مأموریت ساتبا مرتبط است.")
        add_rel(conn, "DMBE-1403", "QHSE-1394", "cites", "مبادلات و تعرفه‌های برق در بورس انرژی با حمایت مالی و عوارض صنعت برق مرتبط است.")
        add_rel(conn, "DMBE-1403", "AIEO-1403", "cites", "بازار برق و بورس انرژی با بازار بهینه‌سازی و گواهی صرفه‌جویی انرژی پیوند موضوعی دارد.")
        conn.commit()
        print("loaded energy", len(SEED_DOCS) + len(PARSED_DOCS), "documents")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
