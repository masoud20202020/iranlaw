# -*- coding: utf-8 -*-
"""Load transport-law package.

Phase 1: maritime, foreign transit and intercity transport bylaw.
Phase 2: aviation, rail access, road/rail safety and public-transport/fuel management.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "data", "seed")]

from importer import (  # noqa: E402
    add_article,
    add_relation,
    add_tag,
    get_or_create_document,
    link_document_tag,
    link_document_topic,
)
from schema import get_connection  # noqa: E402
from transport import MARITIME, ROAD, TRANSIT  # noqa: E402
from transport_phase2 import AIR_CIVIL, PUBLIC_TRANSPORT, RAIL_ACCESS, ROAD_RAIL_SAFETY  # noqa: E402
from transport_phase3 import (  # noqa: E402
    AIR_ACCIDENT_INVESTIGATION,
    AIR_LIABILITY,
    AIR_PASSENGER_RIGHTS,
    RAIL_COMPANIES_BYLAW,
    RAIL_MOVEMENT_OFFENCES,
    ROAD_WAYBILL_LAW,
    SAFETY_MANAGEMENT,
    TRAFFIC_VIOLATIONS,
    WARSAW_AIR_CONVENTION_CORE,
)

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

SOURCE_URLS = {
    "QDR-1343": "https://www.ekhtebar.ir/قانون-دريایی-مصوب-1343/",
    "QTAK-1374": "https://www.ekhtebar.ir/قانون-حمل-و-نقل-و-عبور-کالاهای-خارجی-از/",
    "AIRT-1391": "https://www.ekhtebar.ir/آیین-نامه-اجرایی-تبصره-یک-ماده-۳۱-و-ماده/",
    "QHAV-1328": "https://www.ekhtebar.ir/قانون-هواپیمایی-کشوری/",
    "QDAR-1384": "https://tarkibtrans.ir/قانون-دسترسی-آزاد-به-شبکه-حمل-و-نقل-ریلی/",
    "QERAH-1349": "https://www.ekhtebar.ir/قانون-ایمنی-راهها-و-راه-آهن/",
    "QTPTF-1386": "https://www.ekhtebar.com/قانون-توسعه-حمل-و-نقل-عمومی-و-مدیریت-مصرف/",
    "QTHAI-1391": "https://www.ekhtebar.ir/قانون-تعیین-حدود-مسؤولیت-شرکت‌های-هوا/",
    "DHRP-1403": "https://www.ekhtebar.ir/دستورالعمل-حقوق-مسافر-در-پروازهای-داخ/ ؛ https://www.tinn.ir/بخش-هوایی-42/248144-خسارت-پروازهای-تاخیردار-از-تا-درصد-قیمت-بلیـت",
    "QTRV-1389": "https://www.ekhtebar.ir/قانون-رسيدگي-به-تخلفات-رانندگي-مصوب-1389/",
    "AIRTF-1391": "https://www.vekalatonline.ir/articles/12379/آیین‌نامه-تعیین-انواع-تخلفات-و-جرایم-مربوط-به-سیر-و-حرکت-ناوگان-در-شبکه-حمل-و-نقل-ریلی-و-نحوه-رسیدگی-به-آنها/",
    "AITMS-1388": "https://www.ekhtebar.com/آیین‌نامه-مدیریت-ایمنی-حمل‌ونقل-و-سو/",
    "AITR-1389": "https://vindad.com/blog/iran-rules-reference/transport/p9450/",
    "QZB-1368": "https://vindad.com/blog/iran-rules-reference/transport/p9313/",
    "QWLG-1354": "https://www.ekhtebar.ir/قانون-اجازه-الحاق-دولت-ايران-به-كنوانس/",
    "AIAAI-1390": "https://qavanin.ir/Law/PrintText/185363",
}

DOC_SPECS = (
    {
        "ref": "QDR-1343",
        "title": "قانون دریایی با اصلاحات و الحاقات",
        "short": "قانون دریایی",
        "type": "law",
        "date": "1964-09-20",
        "status": "amended",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "note": "متن تلفیقی ۱۹۴ ماده‌ای با اصلاحات منعکس در منبع.",
        "rows": MARITIME,
        "article_note": "متن تلفیقی جاری.",
    },
    {
        "ref": "QTAK-1374",
        "title": "قانون حمل و نقل و عبور کالاهای خارجی از قلمرو جمهوری اسلامی ایران",
        "short": "ترانزیت خارجی کالا",
        "type": "law",
        "date": "1996-03-11",
        "status": "in_force",
        "authority": "مجلس شورای اسلامی",
        "note": "متن کامل ۲۶ ماده با اصلاحات منعکس در منبع.",
        "rows": TRANSIT,
        "article_note": "متن کامل.",
    },
    {
        "ref": "AIRT-1391",
        "title": "آیین‌نامه اجرایی تبصره یک ماده ۳۱ و ماده ۳۲ قانون رسیدگی به تخلفات رانندگی",
        "short": "آیین‌نامه حمل‌ونقل برون‌شهری",
        "type": "regulation",
        "date": "2012-09-16",
        "status": "in_force",
        "authority": "هیئت وزیران",
        "note": "متن کامل ۲۱ ماده آیین‌نامه؛ مواد ۳۱ و ۳۲ قانون مرجع که در صفحه بازنشر شده‌اند وارد این سند نشده‌اند.",
        "rows": ROAD,
        "article_note": "متن کامل آیین‌نامه.",
    },
    {
        "ref": "QHAV-1328",
        "title": "قانون هواپیمایی کشوری با اصلاحات و الحاقات بعدی",
        "short": "قانون هواپیمایی کشوری",
        "type": "law",
        "date": "1949-07-19",
        "status": "amended",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "note": "مرحله دوم حمل‌ونقل؛ متن ماده‌به‌ماده از بازنشر اختبار، شامل اصلاحات مندرج در منبع و تعدیل جزای نقدی ۱۴۰۳.",
        "rows": AIR_CIVIL,
        "article_note": "متن منبع‌دار؛ شامل اصلاحات و الحاقات منعکس در صفحه منبع.",
    },
    {
        "ref": "QDAR-1384",
        "title": "قانون دسترسی آزاد به شبکه حمل و نقل ریلی",
        "short": "دسترسی آزاد شبکه ریلی",
        "type": "law",
        "date": "2005-09-28",
        "status": "in_force",
        "authority": "مجلس شورای اسلامی",
        "note": "مرحله دوم حمل‌ونقل؛ متن ۱۱ ماده و ۱۴ تبصره از بازنشر شرکت ترکیب حمل‌ونقل؛ نیازمند مقابله بعدی با روزنامه رسمی/قوانین برای جزئیات تنقیحی نام وزارتخانه‌ها.",
        "rows": RAIL_ACCESS,
        "article_note": "متن بازنشرشده منبع‌دار؛ نیازمند مقابله رسمی نهایی برای تنقیح نام وزارتخانه‌ها.",
    },
    {
        "ref": "QERAH-1349",
        "title": "قانون ایمنی راه‌ها و راه‌آهن با اصلاحات و الحاقات بعدی",
        "short": "ایمنی راه‌ها و راه‌آهن",
        "type": "law",
        "date": "1970-06-28",
        "status": "amended",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "note": "مرحله دوم حمل‌ونقل؛ متن ماده‌به‌ماده از بازنشر اختبار، شامل اصلاحات ۱۳۷۹ و تعدیل جزای نقدی ۱۴۰۳.",
        "rows": ROAD_RAIL_SAFETY,
        "article_note": "متن منبع‌دار؛ شامل اصلاحات و الحاقات منعکس در صفحه منبع.",
    },
    {
        "ref": "QTPTF-1386",
        "title": "قانون توسعه حمل و نقل عمومی و مدیریت مصرف سوخت با اصلاحات و الحاقات بعدی",
        "short": "توسعه حمل‌ونقل عمومی و مصرف سوخت",
        "type": "law",
        "date": "2007-12-09",
        "status": "amended",
        "authority": "مجلس شورای اسلامی",
        "note": "مرحله دوم حمل‌ونقل؛ متن ۱۳ ماده از بازنشر اختبار، شامل اصلاحیه ۱۳۹۶ و اصلاحات ناشی از تشکیل وزارت راه و شهرسازی.",
        "rows": PUBLIC_TRANSPORT,
        "article_note": "متن منبع‌دار؛ جداول قانون در متن مواد ۶ و ۷ نگهداری شده‌اند.",
    },
    {
        "ref": "QTHAI-1391",
        "title": "قانون تعیین حدود مسؤولیت شرکت‌های هواپیمایی ایرانی",
        "short": "مسؤولیت شرکت‌های هواپیمایی ایرانی",
        "type": "law",
        "date": "2012-08-01",
        "status": "in_force",
        "authority": "مجلس شورای اسلامی",
        "note": "مرحله سوم حمل‌ونقل؛ متن کامل چهار ماده از بازنشر اختبار درباره حدود مسؤولیت شرکت‌های هواپیمایی ایرانی.",
        "rows": AIR_LIABILITY,
        "article_note": "متن ماده‌به‌ماده منبع‌دار.",
    },
    {
        "ref": "DHRP-1403",
        "title": "دستورالعمل حقوق مسافر در پروازهای داخلی و بین‌المللی (شیوه‌نامه ۱۹۴۰)",
        "short": "حقوق مسافر هوایی",
        "type": "directive",
        "date": "2024-11-17",
        "status": "in_force",
        "authority": "سازمان هواپیمایی کشوری",
        "note": "مرحله سوم حمل‌ونقل؛ خلاصه ساختاری منبع‌دار از شیوه‌نامه ۱۹۴۰ حقوق مسافر هوایی. رونوشت لفظ‌به‌لفظ کامل نیست.",
        "rows": AIR_PASSENGER_RIGHTS,
        "article_note": "خلاصه ساختاری منبع‌دار؛ رونوشت لفظ‌به‌لفظ کامل نیست.",
    },
    {
        "ref": "QTRV-1389",
        "title": "قانون رسیدگی به تخلفات رانندگی با اصلاحات و الحاقات بعدی",
        "short": "رسیدگی به تخلفات رانندگی",
        "type": "law",
        "date": "2011-02-27",
        "status": "amended",
        "authority": "مجلس شورای اسلامی",
        "note": "مرحله سوم حمل‌ونقل؛ متن ماده‌به‌ماده ۳۵ ماده از متن تنقیحی بازنشر اختبار/سخن‌آرا، شامل اصلاحات منعکس در منابع.",
        "rows": TRAFFIC_VIOLATIONS,
        "article_note": "متن ماده‌به‌ماده منبع‌دار؛ شامل اصلاحات منعکس در منابع.",
    },
    {
        "ref": "AIRTF-1391",
        "title": "آیین‌نامه تعیین انواع تخلفات و جرایم مربوط به سیر و حرکت ناوگان در شبکه حمل و نقل ریلی و نحوه رسیدگی به آنها",
        "short": "تخلفات سیر و حرکت ناوگان ریلی",
        "type": "regulation",
        "date": "2013-01-20",
        "status": "in_force",
        "authority": "هیئت وزیران",
        "note": "مرحله سوم حمل‌ونقل؛ نمایه ساختاری منبع‌دار از آیین‌نامه ۱۳۹۱. به دلیل محدودیت دسترسی به متن کامل، فقط مواد قابل اتکا/استخراج‌شده وارد شده و رونوشت کامل آیین‌نامه نیست.",
        "rows": RAIL_MOVEMENT_OFFENCES,
        "article_note": "نمایه ساختاری منبع‌دار؛ رونوشت لفظ‌به‌لفظ کامل آیین‌نامه نیست.",
    },
    {
        "ref": "AITMS-1388",
        "title": "آیین‌نامه مدیریت ایمنی حمل‌ونقل و سوانح رانندگی با آخرین اصلاحات ۱۳۹۷",
        "short": "مدیریت ایمنی حمل‌ونقل و سوانح رانندگی",
        "type": "regulation",
        "date": "2009-08-26",
        "status": "amended",
        "authority": "هیئت وزیران",
        "note": "مرحله تکمیلی حمل‌ونقل؛ متن ۱۸ ماده آیین‌نامه مدیریت ایمنی حمل‌ونقل و سوانح رانندگی از بازنشر اختبار، با اصلاحات منعکس در منبع تا ۱۳۹۷/۵/۱۴. پیوست‌های جدولی منبع وارد نشده‌اند.",
        "rows": SAFETY_MANAGEMENT,
        "article_note": "متن ماده‌به‌ماده منبع‌دار؛ پیوست‌های جدولی منبع وارد نشده‌اند.",
    },
    {
        "ref": "AITR-1389",
        "title": "آیین‌نامه تأسیس و فعالیت شرکت‌های حمل و نقل ریلی",
        "short": "تأسیس و فعالیت شرکت‌های حمل‌ونقل ریلی",
        "type": "regulation",
        "date": "2010-11-21",
        "status": "in_force",
        "authority": "شرکت راه‌آهن جمهوری اسلامی ایران / وزیر راه و ترابری",
        "note": "مرحله تکمیلی حمل‌ونقل؛ متن ۴ ماده، ۳۱ بند و ۱۲ تبصره از بازنشر وینداد. تاریخ دقیق تأیید وزیر در منبع خالی است؛ تاریخ سند بر مبنای عنوان منبع ثبت شده است.",
        "rows": RAIL_COMPANIES_BYLAW,
        "article_note": "متن ماده‌به‌ماده منبع‌دار؛ تاریخ دقیق تأیید وزیر در منبع خالی است.",
    },
    {
        "ref": "QZB-1368",
        "title": "قانون الزام شرکت‌ها و مؤسسات ترابری جاده‌ای به استفاده از صورت وضعیت مسافری و بارنامه با اصلاحات",
        "short": "الزام بارنامه و صورت‌وضعیت مسافری",
        "type": "law",
        "date": "1989-05-21",
        "status": "amended",
        "authority": "مجلس شورای اسلامی",
        "note": "مرحله تکمیلی حمل‌ونقل؛ متن جاری/تنقیحی مواد اصلی از بازنشر وینداد. ماده منسوخه ۵ پیشین در متن جاری وارد نشده و در یادداشت منبع مستند است.",
        "rows": ROAD_WAYBILL_LAW,
        "article_note": "متن جاری/تنقیحی منبع‌دار؛ ماده منسوخه ۵ پیشین وارد نشده است.",
    },
    {
        "ref": "QWLG-1354",
        "title": "قانون اجازه الحاق ایران به کنوانسیون ورشو، پروتکل لاهه، کنوانسیون گوادالاخارا و پروتکل گواتمالا",
        "short": "کنوانسیون‌های مسؤولیت حمل‌ونقل هوایی",
        "type": "treaty",
        "date": "1975-05-21",
        "status": "in_force",
        "authority": "مجلس شورای ملی (پیش از انقلاب)",
        "note": "مرحله تکمیلی حمل‌ونقل؛ ماده واحده الحاق و گزیده مواد کلیدی کنوانسیون ورشو درباره اسناد حمل، مسؤولیت متصدی، حدود مسؤولیت، مهلت و صلاحیت دادگاه. متن کامل ۴۱ ماده و پروتکل‌ها هنوز کامل ماده‌به‌ماده وارد نشده است.",
        "rows": WARSAW_AIR_CONVENTION_CORE,
        "article_note": "گزیده منبع‌دار از مواد کلیدی کنوانسیون ورشو و ماده واحده الحاق؛ رونوشت کامل همه پروتکل‌ها نیست.",
    },
    {
        "ref": "AIAAI-1390",
        "title": "آیین‌نامه بررسی سوانح و حوادث هوایی غیرنظامی",
        "short": "بررسی سوانح هوایی غیرنظامی",
        "type": "regulation",
        "date": "2011-08-21",
        "status": "in_force",
        "authority": "هیئت وزیران",
        "note": "مرحله تکمیلی حمل‌ونقل؛ خلاصه/گزیده منبع‌دار از نسخه چاپی قوه قوانین درباره بررسی سوانح و حوادث هوایی غیرنظامی. دسترسی مستقیم به منبع با محدودیت ۴۰۳ روبه‌رو بود؛ متن کامل آیین‌نامه هنوز کامل وارد نشده است.",
        "rows": AIR_ACCIDENT_INVESTIGATION,
        "article_note": "خلاصه و گزیده منبع‌دار؛ رونوشت لفظ‌به‌لفظ کامل آیین‌نامه نیست.",
    },
)


def one(conn, query, value):
    row = conn.execute(query, (value,)).fetchone()
    return row["id"] if row else None


def document(conn, spec):
    doc_id = one(conn, "SELECT id FROM documents WHERE reference_code=?", spec["ref"])
    if not doc_id:
        doc_id = get_or_create_document(
            conn,
            title=spec["title"],
            short_title=spec["short"],
            type_code=spec["type"],
            issuing_authority=spec["authority"],
            status_code=spec["status"],
            ratification_date=spec["date"],
            effective_date=spec["date"],
            reference_code=spec["ref"],
            notes=spec["note"],
        )

    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            spec["title"],
            spec["short"],
            one(conn, "SELECT id FROM document_types WHERE code=?", spec["type"]),
            one(conn, "SELECT id FROM authorities WHERE name_fa=?", spec["authority"]),
            one(conn, "SELECT id FROM statuses WHERE code=?", spec["status"]),
            spec["date"],
            spec["date"],
            spec["note"],
            doc_id,
        ),
    )
    return doc_id


def clear_document_owned_rows(conn, doc_id):
    # Preserve incoming relations from other packages, but rebuild this package's own outgoing graph.
    for query in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(query, (doc_id,))


def add_rows(conn, doc_id, ref, rows, date, note):
    ids = {}
    for number, text in rows:
        ids[number] = add_article(
            conn,
            doc_id,
            article_no=number.translate(FA_DIGITS),
            article_key=f"{ref}:{number}",
            version_no=1,
            is_current=1,
            effective_date=date,
            text=text,
            source_note=SOURCE_URLS[ref],
            notes=note,
        )
    return ids


def tag_and_topic(conn, doc_id, ref):
    conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES('حقوق حمل‌ونقل')")
    for topic in ("حقوق حمل‌ونقل", "حقوق تجارت"):
        link_document_topic(conn, doc_id, topic)

    tags = {"حمل‌ونقل"}
    if ref in {"QDR-1343", "QTAK-1374"}:
        tags.update({"ترانزیت", "کشتیرانی", "بارنامه"})
    if ref in {"QHAV-1328", "QTHAI-1391", "DHRP-1403", "QWLG-1354", "AIAAI-1390"}:
        tags.update({"هواپیمایی", "فرودگاه", "حمل‌ونقل هوایی", "پرواز"})
    if ref == "DHRP-1403":
        tags.update({"حقوق مسافر", "بلیت هواپیما", "تاخیر پرواز", "ابطال پرواز"})
    if ref in {"QTHAI-1391", "QWLG-1354"}:
        tags.update({"مسؤولیت مدنی", "سوانح هوایی", "کنوانسیون ورشو"})
    if ref == "QWLG-1354":
        tags.update({"پروتکل لاهه", "گوادالاخارا", "گواتمالا", "مسؤولیت متصدی حمل هوایی"})
    if ref == "AIAAI-1390":
        tags.update({"سانحه هوایی", "حادثه هوایی", "ایکائو", "گزارش نهایی", "توصیه ایمنی"})
    if ref in {"QDAR-1384", "QERAH-1349", "QTPTF-1386", "AIRTF-1391", "AITMS-1388", "AITR-1389"}: 
        tags.update({"راه‌آهن", "حمل‌ونقل ریلی", "ایمنی راه"})
    if ref == "QTPTF-1386":
        tags.update({"حمل‌ونقل عمومی", "مدیریت مصرف سوخت", "ناوگان عمومی"})
    if ref in {"AIRT-1391", "QTRV-1389", "QZB-1368"}:
        tags.update({"حمل‌ونقل برون‌شهری", "تخلفات رانندگی", "ناوگان مسافری"})
    if ref == "QTRV-1389":
        tags.update({"راهنمایی و رانندگی", "نمره منفی", "تصادفات رانندگی", "بارنامه شهری"})
    if ref == "AIRTF-1391":
        tags.update({"تخلفات ریلی", "سیر و حرکت", "ناوگان ریلی", "سوانح ریلی"})
    if ref == "AITMS-1388":
        tags.update({"سوانح رانندگی", "ایمنی ترافیک", "اورژانس", "نقاط حادثه‌خیز", "مدیریت صحنه تصادف"})
    if ref == "AITR-1389":
        tags.update({"شرکت حمل‌ونقل ریلی", "پروانه فعالیت", "تعرفه دسترسی", "مدیر فنی", "قرارداد دسترسی"})
    if ref == "QZB-1368":
        tags.update({"بارنامه", "صورت‌وضعیت مسافری", "حمل‌ونقل جاده‌ای", "دفترچه کار راننده"})
    for tag in sorted(tags):
        link_document_tag(conn, doc_id, add_tag(conn, tag))


def add_transport_relations(conn, docs, articles):
    def rel(fr, typ, to, desc, fa=None, ta=None):
        add_relation(
            conn,
            docs[fr],
            typ,
            docs[to],
            from_article_id=articles.get(fr, {}).get(fa) if fa else None,
            to_article_id=articles.get(to, {}).get(ta) if ta else None,
            description=desc,
        )

    rel("QTPTF-1386", "cites", "QDAR-1384", "اولویت توسعه و افزایش سهم حمل‌ونقل ریلی و سرمایه‌گذاری در شبکه ریلی.", "1")
    rel("QTPTF-1386", "cites", "QERAH-1349", "تکلیف به ایمن‌سازی، کاهش تلفات و اصلاح نقاط حادثه‌خیز راهی و ریلی.", "5")
    rel("QDAR-1384", "cites", "QERAH-1349", "رعایت شرایط فنی و ایمنی سیر و حرکت ناوگان در شبکه ریلی.", "2")
    rel("QERAH-1349", "cites", "QDAR-1384", "ارتباط قواعد ایمنی و حریم راه‌آهن با بهره‌برداری از شبکه ریلی.", "8")
    rel("AIRT-1391", "cites", "QERAH-1349", "آیین‌نامه حمل‌ونقل برون‌شهری در بستر ایمنی راه‌ها و مقررات تردد اجرا می‌شود.", "1")
    rel("QTAK-1374", "cites", "QDAR-1384", "ترانزیت خارجی کالا می‌تواند از شبکه ریلی و پایانه‌های راه‌آهن عبور کند.", "2")
    rel("QHAV-1328", "cites", "QTPTF-1386", "بخش حمل‌ونقل هوایی در کنار سیاست‌های کلان توسعه حمل‌ونقل عمومی و مدیریت سوخت قرار دارد.", "4")
    rel("QTPTF-1386", "cites", "QHAV-1328", "قانون توسعه حمل‌ونقل عمومی بر بهینه‌سازی عرضه خدمات حمل‌ونقل برون‌شهری از جمله شقوق هوایی اثر سیاستی دارد.", "1")
    rel("QTHAI-1391", "cites", "QHAV-1328", "حدود مسؤولیت شرکت‌های هواپیمایی ایرانی در نظام حقوق هوایی داخلی و بین‌المللی.", "1")
    rel("DHRP-1403", "implements", "QHAV-1328", "شیوه‌نامه حقوق مسافر بر پایه ماده ۵ قانون هواپیمایی کشوری تنظیم شده است.", "1", "5")
    rel("DHRP-1403", "cites", "QTHAI-1391", "شیوه‌نامه حقوق مسافر قانون تعیین حدود مسؤولیت شرکت‌های هواپیمایی ایرانی را از مبانی الزام خود می‌داند.", "1", "1")
    rel("AIRT-1391", "implements", "QTRV-1389", "آیین‌نامه حمل‌ونقل برون‌شهری ذیل تبصره یک ماده ۳۱ و ماده ۳۲ قانون رسیدگی به تخلفات رانندگی است.", "1", "31")
    rel("QTRV-1389", "cites", "QERAH-1349", "قواعد تخلفات رانندگی با ایمنی راه‌ها، حریم و مدیریت تصادفات پیوند مستقیم دارد.", "14")
    rel("QTRV-1389", "cites", "QTPTF-1386", "درآمدها و عوارض توقف/تخلفات به توسعه حمل‌ونقل عمومی و ایمنی تردد متصل شده‌اند.", "15")
    rel("AIRTF-1391", "implements", "QDAR-1384", "آیین‌نامه تخلفات سیر و حرکت ناوگان ریلی مستند به تبصره یک ماده ۲ قانون دسترسی آزاد به شبکه حمل‌ونقل ریلی است.", "2", "2")
    rel("AITMS-1388", "implements", "QTPTF-1386", "آیین‌نامه مدیریت ایمنی حمل‌ونقل و سوانح رانندگی در اجرای قانون توسعه حمل‌ونقل عمومی و مدیریت مصرف سوخت تصویب شده است.", "1", "5")
    rel("AITMS-1388", "cites", "QERAH-1349", "برنامه‌های ایمن‌سازی راه، نقاط پرتصادف و حریم/تجهیزات راه با قواعد ایمنی راه‌ها مرتبط است.", "2")
    rel("AITMS-1388", "cites", "QTRV-1389", "فرماندهی صحنه تصادف، ثبت تخلفات و کنترل رانندگان پرخطر با قانون رسیدگی به تخلفات رانندگی پیوند دارد.", "12")
    rel("AITR-1389", "implements", "QDAR-1384", "آیین‌نامه تأسیس و فعالیت شرکت‌های حمل‌ونقل ریلی سازوکار بهره‌برداری شرکت‌ها از شبکه ریلی را تکمیل می‌کند.", "4", "1")
    rel("AITR-1389", "cites", "AIRTF-1391", "فعالیت شرکت‌های حمل‌ونقل ریلی در چارچوب مقررات سیر و حرکت و تخلفات ناوگان ریلی انجام می‌شود.", "4", "2")
    rel("QZB-1368", "cites", "QTRV-1389", "ضمانت اجرای تخلفات بارنامه و صورت‌وضعیت با نظام رسیدگی به تخلفات رانندگی و دفترچه/برگ فعالیت رانندگان پیوند دارد.", "6")
    rel("QTRV-1389", "cites", "QZB-1368", "ماده ۳۱ قانون تخلفات رانندگی عدم رعایت ضوابط حمل بار و مسافر، بارنامه و صورت‌وضعیت را در نظام تخلفات حمل‌ونقل جاده‌ای پوشش می‌دهد.", "31", "5")
    rel("QZB-1368", "cites", "AIRT-1391", "آیین‌نامه حمل‌ونقل برون‌شهری ضوابط صدور بارنامه و صورت‌وضعیت موضوع قانون الزام را عملیاتی می‌کند.", "5", "8")
    rel("QWLG-1354", "cites", "QTHAI-1391", "قانون تعیین حدود مسؤولیت شرکت‌های هواپیمایی ایرانی به کنوانسیون ورشو و پروتکل لاهه ارجاع می‌دهد.", "accession", "1")
    rel("QTHAI-1391", "cites", "QWLG-1354", "حدود مسؤولیت شرکت‌های هواپیمایی در پروازهای بین‌المللی بر پایه کنوانسیون ورشو و پروتکل لاهه سنجیده می‌شود.", "1", "W22")
    rel("DHRP-1403", "cites", "QWLG-1354", "شیوه‌نامه حقوق مسافر، کنوانسیون ورشو و پروتکل‌های بعدی آن را از مبانی حقوق مسافر و خسارت می‌داند.", "1", "W19")
    rel("AIAAI-1390", "implements", "QHAV-1328", "آیین‌نامه بررسی سوانح و حوادث هوایی غیرنظامی بر مبنای ماده ۲۲ قانون هواپیمایی کشوری و مقررات بین‌المللی ایمنی تنظیم شده است.", "3", "22")
    rel("AIAAI-1390", "cites", "QWLG-1354", "فرآیند بررسی سوانح در کنار نظام بین‌المللی حمل‌ونقل هوایی و ایکائو فهم می‌شود؛ این رابطه برای پیوند موضوعی ایمنی/مسؤولیت ثبت شده است.", "4", "W17")


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        docs = {spec["ref"]: document(conn, spec) for spec in DOC_SPECS}
        article_ids = {}
        for spec in DOC_SPECS:
            ref = spec["ref"]
            clear_document_owned_rows(conn, docs[ref])
            tag_and_topic(conn, docs[ref], ref)
            article_ids[ref] = add_rows(conn, docs[ref], ref, spec["rows"], spec["date"], spec["article_note"])
        add_transport_relations(conn, docs, article_ids)
        conn.commit()
        print("loaded transport", sum(len(spec["rows"]) for spec in DOC_SPECS), "articles", len(DOC_SPECS), "documents")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
