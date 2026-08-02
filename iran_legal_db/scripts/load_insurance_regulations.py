# -*- coding: utf-8 -*-
"""Load phase-two insurance regulations, supervisory instruments and rulings."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "data", "seed")]

from schema import get_connection
from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic
from insurance_regulations import *

TP = "QST-1395"
CENTRAL = "QBMC-1350"

TP3 = "AITP3-1396"
TP5 = "AITP5-1397"
TP6 = "AITP6-1397"
TP12 = "AITP12-1397"
TP18 = "AITP18-1396"
TP30 = "AITP30-1396"
TP42 = "AITP42-1396"
TP57 = "AITP57-1398"
DIM = "DISTK-1403"
FUND = "AIFUND-1397"
R58 = "AIN58-1387"
R69 = "AIN69-1390"
R110 = "AIN110-1404"
R93 = "AIN93-1396"
R88 = "AIN88-1393"
R90 = "AIN90-1394"
R100 = "AIN100-1399"
R106 = "AIN106-1403"
R85 = "AIN85-1392"
R104 = "AIN104-1401"
U734 = "RVR-734-1393"
U766 = "RVR-766-1396"
U777 = "RVR-777-1398"
U781 = "RVR-781-1398"
U806 = "RVR-806-1399"
U869 = "RVR-869-1404"
DDIM = "DAD-DIM-1405"

REFS = (
    TP3, TP5, TP6, TP12, TP18, TP30, TP42, TP57, DIM, FUND,
    R58, R69, R110, R93, R88, R90, R100, R106, R85, R104,
    U734, U766, U777, U781, U806, U869, DDIM,
)
A2F = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def lookup_id(conn, table, column, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def upsert_doc(conn, ref, title, short, type_code, authority, authority_type, status, ratification, effective, notes):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    if row:
        doc_id = row["id"]
    else:
        doc_id = get_or_create_document(
            conn, title=title, short_title=short, type_code=type_code,
            issuing_authority=authority, status_code=status,
            ratification_date=ratification, effective_date=effective,
            reference_code=ref, notes=notes,
        )
    authority_id = lookup_id(conn, "authorities", "name_fa", authority)
    if not authority_id:
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa,authority_type) VALUES(?,?)",
            (authority, authority_type),
        ).lastrowid
    conn.execute("UPDATE authorities SET authority_type=? WHERE id=?", (authority_type, authority_id))
    conn.execute(
        """UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,
           ratification_date=?,effective_date=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (title, short, lookup_id(conn, "document_types", "code", type_code), authority_id,
         lookup_id(conn, "statuses", "code", status), ratification, effective, notes, doc_id),
    )
    return doc_id


def clear_owned(conn, doc_id):
    # Only outgoing relations are owned by this loader. Incoming document-level links survive.
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (doc_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (doc_id,))


def decorate(conn, doc_id, tags):
    link_document_topic(conn, doc_id, "حقوق بیمه")
    for tag in tags:
        link_document_tag(conn, doc_id, add_tag(conn, tag))


def add_rows(conn, doc_id, ref, data, date, source, *, current=1, expiry=None, notes=None):
    out = {}
    for no, text in data:
        out[str(no)] = add_article(
            conn, doc_id, article_no=str(no).translate(A2F), article_key=f"{ref}:{no}",
            version_no=1, is_current=current, effective_date=date, expiry_date=expiry,
            text=text, source_note=source, notes=notes,
        )
    return out


def add_single(conn, doc_id, ref, article_no, text, date, source, *, key="holding", notes=None):
    return add_article(
        conn, doc_id, article_no=article_no, article_key=f"{ref}:{key}", version_no=1,
        is_current=1, effective_date=date, text=text, source_note=source, notes=notes,
    )


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        docs = {}
        specs = (
            (TP3, "آیین‌نامه اجرایی ماده ۳ قانون بیمه اجباری شخص ثالث (بیمه حوادث راننده مسبب حادثه)", "آیین‌نامه حوادث راننده", "regulation", "هیئت وزیران", "executive", "amended", "2017-07-19", "2017-07-19", "متن تلفیقی ۱۶ ماده با اصلاح ماده ۴ مورخ ۱۳۹۶/۰۷/۱۹."),
            (TP5, "آیین‌نامه اجرایی ماده ۵ قانون بیمه اجباری شخص ثالث درباره مجوز فعالیت", "آیین‌نامه مجوز شخص ثالث", "regulation", "هیئت وزیران", "executive", "in_force", "2018-05-06", "2018-05-12", "متن کامل ۶ ماده درباره شرایط شرکت بیمه و مجوز رشته شخص ثالث."),
            (TP6, "آیین‌نامه اجرایی نحوه انتقال تخفیفات حاصل از نداشتن حوادث منجر به خسارت", "آیین‌نامه انتقال تخفیف", "regulation", "هیئت وزیران", "executive", "in_force", "2018-10-07", "2018-10-07", "متن کامل ۱۰ ماده موضوع تبصره ماده ۶ قانون شخص ثالث."),
            (TP12, "آیین‌نامه تعیین میزان ظرفیت مجاز وسایل نقلیه موضوع ماده ۱۲ قانون بیمه اجباری", "آیین‌نامه ظرفیت مجاز", "regulation", "هیئت وزیران", "executive", "in_force", "2018-06-10", "2018-06-10", "متن کامل ۷ ماده درباره ظرفیت وسایل نقلیه زمینی و ریلی."),
            (TP18, "آیین‌نامه تعیین سقف حق‌بیمه شخص ثالث و نحوه تخفیف، افزایش یا تقسیط آن", "آیین‌نامه حق‌بیمه شخص ثالث", "regulation", "هیئت وزیران", "executive", "amended", "2017-10-18", "2017-10-18", "متن تلفیقی ۱۱ ماده با اصلاحات و جداول جاری تا ۱۴۰۲/۱۰/۲۰."),
            (TP30, "آیین‌نامه اجرایی ماده ۳۰ قانون بیمه اجباری شخص ثالث درباره مراجعه مستقیم و پرداخت خسارت", "آیین‌نامه پرداخت مستقیم خسارت", "regulation", "هیئت وزیران", "executive", "amended", "2017-07-30", "2017-08-07", "هفت ماده؛ ماده ۷ با اصلاح ۱۴۰۳ درباره کسر قیمت نسخه‌بندی شده است."),
            (TP42, "آیین‌نامه نحوه توقیف وسایل نقلیه فاقد بیمه‌نامه شخص ثالث", "آیین‌نامه توقیف وسیله فاقد بیمه", "regulation", "هیئت وزیران", "executive", "in_force", "2017-06-25", "2017-06-25", "متن کامل ۸ ماده موضوع ماده ۴۲ قانون شخص ثالث."),
            (TP57, "آیین‌نامه نحوه رسیدگی به قصور یا تخلف شرکت‌های بیمه", "آیین‌نامه تخلفات شرکت‌های بیمه", "regulation", "هیئت وزیران", "executive", "in_force", "2019-04-28", "2019-04-28", "متن کامل ۲۵ ماده موضوع ماده ۵۷ قانون شخص ثالث."),
            (DIM, "دستورالعمل نحوه محاسبه خسارت کسر قیمت وسیله نقلیه", "دستورالعمل کسر قیمت خودرو", "directive", "شورای عالی بیمه", "oversight", "amended", "2024-10-23", "2024-12-21", "متن ۱۳ ماده و جداول ضریب تصادف و سن؛ فرمولِ راست‌به‌چپ به نگارش ریاضی صریح نوسازی شد؛ تبصره ماده ۶ در ۱۴۰۵/۰۳/۱۲ ابطال و نسخه جاری تنقیح شد."),
            (FUND, "اساسنامه صندوق تأمین خسارت‌های بدنی با اصلاحات", "اساسنامه صندوق خسارت‌های بدنی", "bylaw", "هیئت وزیران", "executive", "amended", "2018-05-06", "2018-05-12", "متن کامل ۲۵ ماده با اصلاحات ۱۳۹۷/۰۳/۳۰."),
            (R58, "آیین‌نامه شماره ۵۸ ذخایر فنی مؤسسات بیمه با اصلاحات", "آیین‌نامه ذخایر فنی", "regulation", "شورای عالی بیمه", "oversight", "amended", "2009-01-14", "2009-01-14", "متن تلفیقی ۱۸ ماده درباره ذخایر فنی بیمه‌های زندگی و غیرزندگی."),
            (R69, "آیین‌نامه شماره ۶۹ نحوه محاسبه و نظارت بر توانگری مالی مؤسسات بیمه", "آیین‌نامه توانگری مالی ۶۹", "regulation", "شورای عالی بیمه", "oversight", "amended", "2012-02-15", "2012-02-15", "متن کامل ۱۵ ماده و جداول پیوست؛ در سال مالی ۱۴۰۵ هم‌زمان با آیین‌نامه ۱۱۰ مورد محاسبه است."),
            (R110, "آیین‌نامه شماره ۱۱۰ نحوه محاسبه و نظارت بر توانگری مالی مؤسسات بیمه ـ خلاصه رسمی ابلاغ", "آیین‌نامه توانگری مالی ۱۱۰ ـ خلاصه", "regulation", "شورای عالی بیمه", "oversight", "in_force", "2025-07-30", "2025-09-07", "فقط خلاصه رسمی ابلاغ ثبت شده است؛ نه رونوشت کامل ۱۲ ماده و پیوست‌های فنی."),
            (R93, "آیین‌نامه شماره ۹۳ حاکمیت شرکتی در مؤسسات بیمه ـ خلاصه ساختاری منبع‌دار", "آیین‌نامه حاکمیت شرکتی ـ خلاصه", "regulation", "شورای عالی بیمه", "oversight", "amended", "2017-06-06", "2017-06-06", "خلاصه ساختاری منبع‌دار؛ متن کامل تلفیقی اصلاحیه‌های ۹۳/۱ و ۹۳/۲ هنوز درج نشده است."),
            (R88, "آیین‌نامه شماره ۸۸ گزارشگری و افشای اطلاعات مؤسسات بیمه", "آیین‌نامه گزارشگری و افشا", "regulation", "شورای عالی بیمه", "oversight", "in_force", "2014-12-16", "2014-12-16", "متن کامل ۱۲ ماده درباره گزارشگری، افشا و سنهاب."),
            (R90, "آیین‌نامه شماره ۹۰ نحوه احراز صلاحیت حرفه‌ای کارکنان کلیدی و عملیاتی مؤسسات بیمه", "آیین‌نامه صلاحیت حرفه‌ای", "regulation", "شورای عالی بیمه", "oversight", "amended", "2015-06-16", "2015-06-16", "متن تلفیقی ۱۵ ماده با اصلاحات و الحاقات بعدی منبع."),
            (R100, "آیین‌نامه شماره ۱۰۰ ضوابط تأسیس و فعالیت مؤسسات بیمه غیردولتی", "آیین‌نامه مؤسسات بیمه غیردولتی", "regulation", "شورای عالی بیمه", "oversight", "in_force", "2020-09-22", "2020-09-22", "متن کامل ۲۱ ماده؛ تاریخ منبع در دسترس ۲۰۲۰/۰۹/۲۲ است و جایگزین آیین‌نامه شماره ۴۰ و مکمل‌های آن شده است."),
            (R106, "آیین‌نامه شماره ۱۰۶ تنظیم امور نمایندگی بیمه", "آیین‌نامه نمایندگی بیمه ۱۰۶", "regulation", "شورای عالی بیمه", "oversight", "in_force", "2024-06-24", "2024-06-24", "متن کامل ۲۹ ماده؛ جایگزین آیین‌نامه شماره ۷۵ و اصلاحات آن."),
            (R85, "آیین‌نامه شماره ۸۵ تنظیم امور ارزیابی خسارت بیمه‌ای با اصلاحات", "آیین‌نامه ارزیابان خسارت", "regulation", "شورای عالی بیمه", "oversight", "amended", "2013-12-17", "2014-03-21", "متن جاری ۱۹ ماده پس از اصلاحیه شماره ۸۵/۱، حذف ماده ۸ سابق و تنقیح شماره مواد."),
            (R104, "آیین‌نامه شماره ۱۰۴ سرمایه‌گذاری مؤسسات بیمه ـ خلاصه ساختاری منبع‌دار", "آیین‌نامه سرمایه‌گذاری ۱۰۴ ـ خلاصه", "regulation", "شورای عالی بیمه", "oversight", "amended", None, None, "خلاصه ساختاری منبع‌دار همراه حکم شناخته‌شده مکمل ۱/۱۰۴؛ نه رونوشت کامل آیین‌نامه."),
            (U734, "رأی وحدت رویه شماره ۷۳۴ درباره مطالبه خسارت بدنی از صندوق", "رأی وحدت رویه ۷۳۴", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2014-10-14", "2014-10-14", "قسمت لازم‌الاتباع درباره صلاحیت دادگاه عمومی جزایی و عدم ضرورت دادخواست حقوقی."),
            (U766, "رأی وحدت رویه شماره ۷۶۶ درباره عدم تسری تبصره ماده ۵۵۱ به جنایات پیشین", "رأی وحدت رویه ۷۶۶", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2018-02-06", "2018-02-06", "قسمت لازم‌الاتباع درباره عدم عطف‌به‌ماسبق شدن تعهد صندوق."),
            (U777, "رأی وحدت رویه شماره ۷۷۷ درباره مابه‌التفاوت دیه زنان از صندوق", "رأی وحدت رویه ۷۷۷", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2019-05-21", "2019-05-21", "قسمت لازم‌الاتباع درباره همه جنایات علیه نفس یا اعضای زنان."),
            (U781, "رأی وحدت رویه شماره ۷۸۱ درباره تسری حمایت بیمه‌ای به راننده مسبب حادثه", "رأی وحدت رویه ۷۸۱", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2019-09-17", "2019-09-17", "قسمت لازم‌الاتباع درباره بیمه‌نامه‌های بند ب ماده ۱۱۵ برنامه پنجم و خسارات پرداخت‌نشده."),
            (U806, "رأی وحدت رویه شماره ۸۰۶ درباره راننده مسبب حادثه فاقد گواهینامه", "رأی وحدت رویه ۸۰۶", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2021-02-02", "2021-02-02", "قسمت لازم‌الاتباع درباره خروج راننده فاقد گواهینامه از پوشش حوادث راننده."),
            (U869, "رأی وحدت رویه شماره ۸۶۹ درباره محاسبه خسارت راننده مسبب به قیمت زمان پرداخت", "رأی وحدت رویه ۸۶۹", "unified_ruling", "دیوان عالی کشور", "judicial", "in_force", "2025-09-16", "2025-09-16", "قسمت لازم‌الاتباع درباره نرخ یوم‌الاداء و خسارت مازاد بر مبلغ مندرج در بیمه‌نامه."),
            (DDIM, "دادنامه هیأت عمومی دیوان عدالت اداری درباره ابطال محدودیت ده‌سال در خسارت کسر قیمت خودرو", "ابطال محدودیت ده‌سال کسر قیمت", "divan_ruling", "دیوان عدالت اداری", "judicial", "in_force", "2026-06-02", "2026-06-02", "دادنامه شماره ۱۴۰۵۳۱۳۹۰۰۰۰۶۰۷۸۸۵؛ ابطال تبصره ماده ۶ دستورالعمل کسر قیمت."),
        )
        for spec in specs:
            docs[spec[0]] = upsert_doc(conn, *spec)
        for doc_id in docs.values():
            clear_owned(conn, doc_id)

        tags = {
            TP3: ("راننده مسبب حادثه", "بیمه حوادث راننده", "خسارت بدنی"),
            TP5: ("مجوز بیمه شخص ثالث", "توانگری مالی", "پرداخت خسارت"),
            TP6: ("تخفیف عدم خسارت", "انتقال مالکیت", "سوابق بیمه‌ای"),
            TP12: ("ظرفیت مجاز", "سرنشین", "وسیله نقلیه ریلی"),
            TP18: ("حق‌بیمه شخص ثالث", "تخفیف عدم خسارت", "تقسیط حق‌بیمه"),
            TP30: ("مراجعه مستقیم", "پرداخت خسارت", "کسر قیمت خودرو"),
            TP42: ("توقیف وسیله نقلیه", "فقدان بیمه‌نامه", "پلیس راهور"),
            TP57: ("تخلف شرکت بیمه", "سلب صلاحیت", "جریمه بیمه‌گر"),
            DIM: ("کسر قیمت خودرو", "افت قیمت خودرو", "ضریب سن", "ضریب تصادف"),
            FUND: ("صندوق تأمین خسارت‌های بدنی", "خسارت بدنی", "بازیافت خسارت"),
            R58: ("ذخایر فنی", "ذخیره خسارت معوق", "ذخیره ریاضی"),
            R69: ("توانگری مالی", "سرمایه الزامی", "ریسک بیمه‌گری"),
            R110: ("توانگری مالی", "آیین‌نامه ۱۱۰", "خلاصه رسمی"),
            R93: ("حاکمیت شرکتی", "کنترل داخلی", "مدیریت ریسک", "خلاصه ساختاری"),
            R88: ("افشای اطلاعات", "گزارشگری", "سنهاب"),
            R90: ("صلاحیت حرفه‌ای", "کارکنان کلیدی", "مدیران بیمه"),
            R100: ("مؤسسات بیمه غیردولتی", "پروانه تأسیس", "سهامداران بیمه"),
            R106: ("نماینده بیمه", "پروانه نمایندگی", "بازاریاب بیمه"),
            R85: ("ارزیاب خسارت بیمه‌ای", "تعارض منافع", "پروانه ارزیابی"),
            R104: ("سرمایه‌گذاری مؤسسات بیمه", "ذخایر فنی", "خلاصه ساختاری"),
            U734: ("رأی وحدت رویه", "صندوق تأمین خسارت‌های بدنی", "صلاحیت کیفری"),
            U766: ("رأی وحدت رویه", "عطف به ماسبق", "مابه‌التفاوت دیه"),
            U777: ("رأی وحدت رویه", "دیه زنان", "صندوق تأمین خسارت‌های بدنی"),
            U781: ("رأی وحدت رویه", "راننده مسبب حادثه", "برنامه پنجم"),
            U806: ("رأی وحدت رویه", "فقدان گواهینامه", "راننده مسبب حادثه"),
            U869: ("رأی وحدت رویه", "نرخ یوم‌الاداء", "راننده مسبب حادثه"),
            DDIM: ("رأی دیوان عدالت اداری", "کسر قیمت خودرو", "ابطال مقرره"),
        }
        for ref, values in tags.items():
            decorate(conn, docs[ref], values)

        arts = {}
        arts[TP3] = add_rows(conn, docs[TP3], TP3, TP_DRIVER, "2017-07-19", "آیین‌نامه اجرایی ماده ۳؛ متن تلفیقی با اصلاح ماده ۴.")
        arts[TP5] = add_rows(conn, docs[TP5], TP5, TP_LICENSE, "2018-05-12", "روزنامه رسمی و بازنشر مقابله‌ای آیین‌نامه ماده ۵.")
        arts[TP6] = add_rows(conn, docs[TP6], TP6, TP_DISCOUNT, "2018-10-07", "آیین‌نامه انتقال تخفیفات عدم خسارت؛ متن کامل ۱۰ ماده.")
        arts[TP12] = add_rows(conn, docs[TP12], TP12, TP_CAPACITY, "2018-06-10", "آیین‌نامه ظرفیت مجاز؛ متن کامل ۷ ماده.")
        arts[TP18] = add_rows(conn, docs[TP18], TP18, TP_PREMIUM, "2017-10-18", "متن تلفیقی داودآبادی با جداول و اصلاحات تا ۱۴۰۲/۱۰/۲۰.")

        arts[TP30] = {}
        for no, text in TP_CLAIMS:
            if no == "7":
                old = add_article(conn, docs[TP30], article_no="۷", article_key=f"{TP30}:7", version_no=1, is_current=0,
                                  effective_date="2017-08-07", expiry_date="2024-06-09", text=TP_CLAIMS_ARTICLE7_HISTORICAL,
                                  source_note="نسخه پیش از اصلاح ۱۴۰۳ ماده ۷؛ بازسازی از متن مقابله‌ای دادنامه دیوان عدالت و متن جاری.",
                                  notes="نسخه تاریخی پیش از افزوده‌شدن کسر قیمت به اقلام قابل پرداخت.")
                cur = add_article(conn, docs[TP30], article_no="۷", article_key=f"{TP30}:7", version_no=2, is_current=1,
                                  effective_date="2024-06-09", text=text,
                                  source_note="ماده ۷ اصلاحی مصوب ۱۴۰۳/۰۳/۲۰ هیئت وزیران؛ متن جاری.")
                arts[TP30]["7_old"] = old
                arts[TP30]["7"] = cur
            else:
                arts[TP30][no] = add_article(conn, docs[TP30], article_no=no.translate(A2F), article_key=f"{TP30}:{no}",
                                             version_no=1, is_current=1, effective_date="2017-08-07", text=text,
                                             source_note="آیین‌نامه اجرایی ماده ۳۰؛ متن کامل و مقابله‌ای.")
        arts[TP42] = add_rows(conn, docs[TP42], TP42, TP_IMPOUND, "2017-06-25", "آیین‌نامه توقیف وسیله فاقد بیمه؛ متن کامل ۸ ماده.")
        arts[TP57] = add_rows(conn, docs[TP57], TP57, TP_VIOLATIONS, "2019-04-28", "آیین‌نامه قصور یا تخلف شرکت‌های بیمه؛ متن کامل ۲۵ ماده.")
        arts[FUND] = add_rows(conn, docs[FUND], FUND, FUND_STATUTE, "2018-05-12", "اساسنامه صندوق؛ متن تلفیقی با اصلاحات ۱۳۹۷/۰۳/۳۰.")

        arts[DIM] = {}
        for no, text in DIMINUTION:
            if no == "6":
                old = add_article(conn, docs[DIM], article_no="۶", article_key=f"{DIM}:6", version_no=1, is_current=0,
                                  effective_date="2024-12-21", expiry_date="2026-06-02", text=DIMINUTION_ARTICLE6_HISTORICAL,
                                  source_note="نسخه مصوب ۱۴۰۳/۰۸/۰۲ پیش از دادنامه ۱۴۰۵/۰۳/۱۲ دیوان عدالت اداری.",
                                  notes="تبصره محدودکننده خودروهای ده‌سال و بیشتر در این نسخه تاریخی وجود دارد.")
                cur = add_article(conn, docs[DIM], article_no="۶", article_key=f"{DIM}:6", version_no=2, is_current=1,
                                  effective_date="2026-06-02", text=text,
                                  source_note="نسخه جاری تنقیح‌شده پس از ابطال تبصره ماده ۶ به موجب دادنامه ۱۴۰۵۳۱۳۹۰۰۰۰۶۰۷۸۸۵.",
                                  notes="تبصره محدودیت ده‌سال از متن جاری حذف شده است.")
                arts[DIM]["6_old"] = old
                arts[DIM]["6"] = cur
            else:
                arts[DIM][no] = add_article(conn, docs[DIM], article_no=no.translate(A2F), article_key=f"{DIM}:{no}",
                                            version_no=1, is_current=1, effective_date="2024-12-21", text=text,
                                            source_note="دستورالعمل ۱۳ ماده‌ای کسر قیمت؛ جداول تصویرمحور با منبع متنی مقابله شده و فرمول راست‌به‌چپ بدون تغییر محتوا به نگارش ریاضی صریح نوسازی شده است.")

        arts[R58] = add_rows(conn, docs[R58], R58, RESERVES_58, "2009-01-14", "متن تلفیقی آیین‌نامه شماره ۵۸ از پایگاه صلح.")
        arts[R69] = add_rows(conn, docs[R69], R69, SOLVENCY_69, "2012-02-15", "متن کامل آیین‌نامه شماره ۶۹ و پیوست‌های فنی از پایگاه صلح.")
        arts[R88] = add_rows(conn, docs[R88], R88, DISCLOSURE_88, "2014-12-16", "متن کامل آیین‌نامه شماره ۸۸ از پایگاه صلح.")
        arts[R90] = add_rows(conn, docs[R90], R90, QUALIFICATION_90, "2015-06-16", "متن تلفیقی آیین‌نامه شماره ۹۰ از پایگاه صلح.")
        arts[R100] = add_rows(conn, docs[R100], R100, PRIVATE_INSURANCE_100, "2020-09-22", "متن کامل آیین‌نامه شماره ۱۰۰؛ بازنشر دادگران بیمه خراسان؛ تاریخ منبع در دسترس ۲۰۲۰/۰۹/۲۲.")
        arts[R106] = add_rows(conn, docs[R106], R106, AGENTS_106, "2024-06-24", "متن کامل آیین‌نامه شماره ۱۰۶؛ نسخه جاری جایگزین آیین‌نامه ۷۵.")
        arts[R85] = add_rows(conn, docs[R85], R85, ADJUSTERS_85, "2020-02-19", "متن جاری تنقیح‌شده آیین‌نامه ۸۵ با اعمال مکمل ۸۵/۱؛ نوسازی رسم‌الخط مستند است.")

        summary_note = "این رکورد صریحاً خلاصه است و نباید به عنوان رونوشت لفظ‌به‌لفظ مقرره استفاده شود."
        arts[R93] = {"summary": add_single(conn, docs[R93], R93, "خلاصه", GOVERNANCE_93_SUMMARY, "2017-06-06", "خلاصه ساختاری منبع‌دار بر پایه آیین‌نامه ۹۳، اصلاحیه‌ها و دستورالعمل ماده ۱۱.", key="summary", notes=summary_note)}
        arts[R110] = {"summary": add_single(conn, docs[R110], R110, "خلاصه", SOLVENCY_110_SUMMARY, "2025-09-07", "خلاصه رسمی ابلاغ بیمه مرکزی و خبرگزاری مهر؛ PDF کامل متن‌پذیر نبود.", key="summary", notes=summary_note)}
        arts[R104] = {"summary": add_single(conn, docs[R104], R104, "خلاصه", INVESTMENT_104_SUMMARY, "2026-02-12", "خلاصه ساختاری منبع‌دار از مقررات جاری سرمایه‌گذاری و اولویت نظارتی رسمی ۱۴۰۵.", key="summary", notes=summary_note)}

        holding_sources = {
            U734: (RULING_734, "2014-10-14", "قسمت لازم‌الاتباع رأی وحدت رویه ۷۳۴؛ بازنشر روزنامه رسمی در اختبار."),
            U766: (RULING_766, "2018-02-06", "قسمت لازم‌الاتباع رأی وحدت رویه ۷۶۶؛ پایگاه صلح."),
            U777: (RULING_777, "2019-05-21", "قسمت لازم‌الاتباع رأی وحدت رویه ۷۷۷؛ بازنشر مقابله‌ای."),
            U781: (RULING_781, "2019-09-17", "قسمت لازم‌الاتباع رأی وحدت رویه ۷۸۱؛ بازنشر مرکز پژوهشی حقوقی."),
            U806: (RULING_806, "2021-02-02", "قسمت لازم‌الاتباع رأی وحدت رویه ۸۰۶؛ بازنشر روزنامه رسمی در اختبار."),
            U869: (RULING_869, "2025-09-16", "قسمت لازم‌الاتباع رأی وحدت رویه ۸۶۹؛ متن منتشرشده در شناسنامه قانون."),
        }
        for ref, (text, date, source) in holding_sources.items():
            number = ref.split("-")[1].translate(A2F)
            arts[ref] = {"holding": add_single(conn, docs[ref], ref, f"رأی وحدت رویه {number}", text, date, source)}
        arts[DDIM] = {"holding": add_single(conn, docs[DDIM], DDIM, "رأی", DIVAN_DIMINUTION_1405, "2026-06-02", "قسمت حکم و استدلال لازم دادنامه ۱۴۰۵۳۱۳۹۰۰۰۰۶۰۷۸۸۵؛ بازنشر اختبار.")}

        tp_id = lookup_id(conn, "documents", "reference_code", TP)
        central_id = lookup_id(conn, "documents", "reference_code", CENTRAL)
        if not tp_id or not central_id:
            raise RuntimeError("core insurance documents must be loaded first")

        targets = {
            TP3: "اجرای ماده ۳: بیمه حوادث راننده مسبب حادثه.", TP5: "اجرای ماده ۵: مجوز فعالیت رشته شخص ثالث.",
            TP6: "اجرای تبصره ماده ۶: انتقال تخفیف عدم خسارت.", TP12: "اجرای ماده ۱۲: تعیین ظرفیت مجاز.",
            TP18: "اجرای ماده ۱۸: حق‌بیمه، تخفیف، افزایش و تقسیط.", TP30: "اجرای ماده ۳۰: مراجعه مستقیم و پرداخت خسارت.",
            TP42: "اجرای ماده ۴۲: توقیف وسیله نقلیه فاقد بیمه.", TP57: "اجرای ماده ۵۷: رسیدگی به قصور و تخلف بیمه‌گر.",
            DIM: "دستورالعمل محاسبه کسر قیمت در اجرای ماده ۷ آیین‌نامه ماده ۳۰.", FUND: "اساسنامه صندوق در اجرای ماده ۲۸ قانون.",
        }
        for ref, description in targets.items():
            add_relation(conn, docs[ref], "implements", tp_id, description=description)
        add_relation(conn, docs[DIM], "implements", docs[TP30], description="اجرای ماده ۷ آیین‌نامه مراجعه مستقیم و پرداخت خسارت.")
        add_relation(conn, docs[DDIM], "overrules", docs[DIM], to_article_id=arts[DIM]["6_old"], description="ابطال تبصره محدودیت ده‌سال در نسخه تاریخی ماده ۶.")
        add_relation(conn, docs[DDIM], "interprets", tp_id, description="تفسیر دامنه خسارت مالی و کسر قیمت در قانون شخص ثالث.")

        for ref in (R58, R69, R110, R93, R88, R90, R100, R106, R85, R104):
            add_relation(conn, docs[ref], "implements", central_id, description="مقرره نظارتی صنعت بیمه در اجرای قانون تأسیس بیمه مرکزی و بیمه‌گری.")
        add_relation(conn, docs[R110], "amends", docs[R69], description="گذار مرحله‌ای از روش آیین‌نامه ۶۹ به آیین‌نامه ۱۱۰؛ محاسبه هم‌زمان در سال مالی ۱۴۰۵.")

        add_relation(conn, docs[U734], "interprets", docs[FUND], description="نحوه مراجعه قضایی در صورت امتناع صندوق از پرداخت.")
        add_relation(conn, docs[U734], "interprets", tp_id, description="اثر رأی در نظام جاری حمایت صندوق، با رعایت تغییر قانون ۱۳۹۵.")
        add_relation(conn, docs[U766], "interprets", docs[FUND], description="عدم عطف‌به‌ماسبق شدن تعهد مابه‌التفاوت دیه.")
        add_relation(conn, docs[U777], "interprets", docs[FUND], description="تعهد صندوق به مابه‌التفاوت دیه همه جنایات علیه زنان.")
        add_relation(conn, docs[U781], "interprets", tp_id, description="تسری حمایت بیمه‌ای قانون به خسارات پرداخت‌نشده راننده مسبب.")
        add_relation(conn, docs[U781], "interprets", docs[TP3], description="تفسیر پوشش حوادث راننده در امتداد بند ب ماده ۱۱۵ برنامه پنجم.")
        add_relation(conn, docs[U806], "interprets", tp_id, description="عدم پوشش خسارت بدنی راننده مسبب فاقد گواهینامه.")
        add_relation(conn, docs[U806], "interprets", docs[TP3], description="تفسیر بند پ ماده ۱۰ آیین‌نامه حوادث راننده.")
        add_relation(conn, docs[U869], "interprets", tp_id, description="محاسبه خسارت راننده مسبب به قیمت زمان پرداخت.")
        add_relation(conn, docs[U869], "interprets", docs[TP3], description="اثر یوم‌الاداء بر خسارت موضوع بیمه حوادث راننده.")
        add_relation(conn, docs[U869], "cites", docs[U781], description="استناد صریح به ملاک رأی وحدت رویه ۷۸۱.")

        conn.commit()
        total = conn.execute(
            """SELECT (SELECT COUNT(*) FROM documents)d,(SELECT COUNT(*) FROM articles)a,
               (SELECT COUNT(*) FROM articles WHERE is_current=1)c,
               (SELECT COUNT(*) FROM articles WHERE is_current=0)h,
               (SELECT COUNT(*) FROM relations)r"""
        ).fetchone()
        package = conn.execute(
            f"SELECT COUNT(*) a,COALESCE(SUM(is_current),0)c FROM articles WHERE document_id IN ({','.join('?' * len(docs))})",
            tuple(docs.values()),
        ).fetchone()
        print(f"[OK] مرحله دوم بیمه: {len(docs)} سند | {package['a']} ردیف | {package['c']} جاری | {package['a']-package['c']} تاریخی")
        print(f"[TOTAL] اسناد: {total['d']} | مواد/نسخه‌ها: {total['a']} | جاری: {total['c']} | تاریخی: {total['h']} | روابط: {total['r']}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
