# -*- coding: utf-8 -*-
"""Load the complete Labor Law, labor procedure and unemployment package."""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path[:0] = [SCRIPT_DIR, os.path.join(ROOT, "data", "seed")]

from schema import get_connection
from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic
from labor_law import *

REF_LABOR = "QK-1369"
REF_PROCEDURE = "AIDK-1391"
REF_UNEMPLOYMENT = "QBB-1369"
REF_UNEMPLOYMENT_BYLAW = "AIBB-1369"
REF_RULING = "RVR-720-1390"
REF_DIVAN = "DAD-17-20-1397"
REFS = (REF_LABOR, REF_PROCEDURE, REF_UNEMPLOYMENT, REF_UNEMPLOYMENT_BYLAW, REF_RULING, REF_DIVAN)
OBSOLETE_PLACEHOLDER = "AQK-1370"

D1369_LABOR = "1990-11-20"
D1369_UNEMPLOYMENT = "1990-09-17"
D1369_BYLAW = "1991-01-02"
D1383 = "2004-04-18"
D1390 = "2011-05-24"
D1391_APPROVAL = "2013-01-26"
D1392_EFFECTIVE = "2013-03-21"
D1394 = "2015-04-21"
D1397_ADDITION = "2019-03-18"
D1397_DIVAN = "2018-04-10"

SRC_LABOR = "قانون کار مصوب ۱۳۶۹/۰۸/۲۹ مجمع تشخیص مصلحت نظام؛ متن با نسخه‌های تنقیحی اختبار و شناسنامه قانون مقابله شده است."
SRC_AMEND_1383 = "قانون اصلاح تبصره ماده ۱۴ قانون کار و الحاق یک تبصره به آن، مصوب ۱۳۸۳/۰۱/۳۰، همراه استفساریه قانونی مربوط."
SRC_AMEND_1394 = "ماده ۴۱ قانون رفع موانع تولید رقابت‌پذیر و ارتقای نظام مالی کشور مصوب ۱۳۹۴/۰۲/۰۱."
SRC_PROCEDURE = "آیین دادرسی کار؛ تهیه‌شده در شورای عالی کار ۱۳۹۱/۰۸/۰۷ و مصوب وزیر تعاون، کار و رفاه اجتماعی در ۱۳۹۱/۱۱/۰۷."
SRC_EPROCEDURE = "الحاق فصل دادرسی الکترونیکی به آیین دادرسی کار؛ مصوب ۱۳۹۷/۱۲/۲۷، ابلاغی شماره ۷۰۶ مورخ ۱۳۹۸/۰۱/۰۵، با تبصره الحاقی ۱۳۹۹/۱۰/۰۳."
SRC_UNEMPLOYMENT = "قانون بیمه بیکاری مصوب ۱۳۶۹/۰۶/۲۶ مجلس شورای اسلامی، تأیید شورای نگهبان در ۱۳۶۹/۰۷/۱۰."
SRC_UNEMPLOYMENT_BYLAW = "آیین‌نامه اجرایی قانون بیمه بیکاری، تصویب‌نامه شماره ۱۲۲۶۲۶/ت۴۰۴هـ مورخ ۱۳۶۹/۱۰/۱۹ هیئت وزیران، مصوب جلسه ۱۳۶۹/۱۰/۱۲."
SRC_RULING = "رأی وحدت رویه شماره ۷۲۰ مورخ ۱۳۹۰/۰۳/۰۳ هیأت عمومی دیوان عالی کشور، پرونده ردیف ۸۹/۴۷."
SRC_DIVAN = "رأی ایجاد رویه شماره‌های ۱۷ تا ۲۰ مورخ ۱۳۹۷/۰۱/۲۱ هیأت عمومی دیوان عدالت اداری."


def pn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def get_id(conn, table: str, column: str, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def upsert(conn, ref, title, short, type_code, authority, status, ratification, effective, notes, official=None):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    if row:
        document_id = row["id"]
    else:
        document_id = get_or_create_document(
            conn,
            title=title,
            short_title=short,
            type_code=type_code,
            issuing_authority=authority,
            status_code=status,
            ratification_date=ratification,
            effective_date=effective,
            official_newspaper_no=official,
            reference_code=ref,
            notes=notes,
        )
    authority_id = get_id(conn, "authorities", "name_fa", authority)
    if authority_id is None:
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa,authority_type) VALUES(?,?)",
            (authority, "judicial" if "دیوان" in authority or "وزیر" in authority else "legislative"),
        ).lastrowid
    conn.execute(
        """UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,
           ratification_date=?,effective_date=?,official_newspaper_no=?,notes=?,updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            title,
            short,
            get_id(conn, "document_types", "code", type_code),
            authority_id,
            get_id(conn, "statuses", "code", status),
            ratification,
            effective,
            official,
            notes,
            document_id,
        ),
    )
    return document_id


def clear(conn, document_id: int) -> None:
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (document_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (document_id,))


def remove_obsolete_placeholder(conn) -> None:
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (OBSOLETE_PLACEHOLDER,)).fetchone()
    if not row:
        return
    did = row["id"]
    conn.execute("DELETE FROM relations WHERE from_document_id=? OR to_document_id=?", (did, did))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (did,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (did,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (did,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (did,))
    conn.execute("DELETE FROM documents WHERE id=?", (did,))


def decorate(conn, did, topics, tags) -> None:
    for topic in topics:
        link_document_topic(conn, did, topic)
    for tag in tags:
        link_document_tag(conn, did, add_tag(conn, tag))


def addv(conn, did, ref, number, text, version, current, effective, expiry, source, note):
    return add_article(
        conn,
        did,
        article_no=pn(number),
        article_key=f"{ref}:{number}",
        version_no=version,
        is_current=int(current),
        effective_date=effective,
        expiry_date=expiry,
        text=text,
        source_note=source,
        notes=note,
    )


def main() -> None:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        remove_obsolete_placeholder(conn)
        docs = {
            REF_LABOR: upsert(
                conn, REF_LABOR,
                "قانون کار جمهوری اسلامی ایران (متن کامل با اصلاحات و الحاقات)",
                "قانون کار", "law", "مجمع تشخیص مصلحت نظام", "amended",
                D1369_LABOR, D1369_LABOR,
                "متن کامل ۲۰۳ ماده؛ تاریخچه مواد ۷، ۱۰، ۱۴ و ۲۱ نگهداری شده است. عناوین وزارت کار و وزیر کار مطابق قانون تشکیل وزارت تعاون، کار و رفاه اجتماعی به عنوان سازمانی جاری روزآمد شده‌اند.",
            ),
            REF_PROCEDURE: upsert(
                conn, REF_PROCEDURE,
                "آیین دادرسی کار با فصل الحاقی دادرسی الکترونیکی",
                "آیین دادرسی کار", "regulation", "وزیر تعاون، کار و رفاه اجتماعی", "amended",
                D1391_APPROVAL, D1392_EFFECTIVE,
                "متن جاری ۱۳۵ ماده؛ مواد ۱ تا ۱۱۶ آیین دادرسی کار و مواد ۱۱۷ تا ۱۳۵ فصل الحاقی دادرسی الکترونیکی، همراه اصلاحات مواد ۴۸، ۵۰، ۱۱۱ و تبصره الحاقی ماده ۱۳۳.",
            ),
            REF_UNEMPLOYMENT: upsert(
                conn, REF_UNEMPLOYMENT,
                "قانون بیمه بیکاری",
                "قانون بیمه بیکاری", "law", "مجلس شورای اسلامی", "in_force",
                D1369_UNEMPLOYMENT, D1369_UNEMPLOYMENT,
                "متن کامل ۱۴ ماده و ۲۱ تبصره درباره شمول، شرایط استحقاق، مدت و میزان مقرری، قطع مقرری و تکالیف اجرایی.",
            ),
            REF_UNEMPLOYMENT_BYLAW: upsert(
                conn, REF_UNEMPLOYMENT_BYLAW,
                "آیین‌نامه اجرایی قانون بیمه بیکاری",
                "آیین‌نامه بیمه بیکاری", "regulation", "هیئت وزیران", "in_force",
                D1369_BYLAW, D1369_BYLAW,
                "متن کامل ۲۴ ماده آیین‌نامه اجرایی؛ شامل تشخیص بیکاری غیرارادی، معرفی به تأمین اجتماعی، آموزش، اشتغال مجدد و تکالیف دستگاه‌ها.",
                official="۱۲۲۶۲۶/ت۴۰۴هـ",
            ),
            REF_RULING: upsert(
                conn, REF_RULING,
                "رأی وحدت رویه شماره ۷۲۰ هیأت عمومی دیوان عالی کشور درباره مرجع رسیدگی به حق بیمه ایام اشتغال",
                "رأی وحدت رویه ۷۲۰", "unified_ruling", "دیوان عالی کشور", "in_force",
                D1390, D1390,
                "متن کامل قسمت رأی؛ سازمان تأمین اجتماعی مرجع نخست رسیدگی به مطالبه حق بیمه پرداخت‌نشده ایام اشتغال است. مقدمه و گردش کار در ردیف ماده‌ای مستقل ثبت نشده است.",
            ),
            REF_DIVAN: upsert(
                conn, REF_DIVAN,
                "رأی ایجاد رویه شماره‌های ۱۷ تا ۲۰ هیأت عمومی دیوان عدالت اداری درباره تسویه‌حساب کارگر",
                "رأی تسویه‌حساب کارگر", "divan_ruling", "دیوان عدالت اداری", "in_force",
                D1397_DIVAN, D1397_DIVAN,
                "متن کامل قسمت رأی؛ صرف برگ تسویه‌حساب بدون اسناد مثبته پرداخت مزد و مزایا برای بری‌الذمه شدن کارفرما کافی نیست.",
            ),
        }
        for did in docs.values():
            clear(conn, did)

        decorate(conn, docs[REF_LABOR], ("حقوق کار و تأمین اجتماعی",), ("کارگر", "کارفرما", "قرارداد کار", "مزد", "مرخصی", "اخراج", "هیأت حل اختلاف"))
        decorate(conn, docs[REF_PROCEDURE], ("حقوق کار و تأمین اجتماعی",), ("آیین دادرسی کار", "هیأت تشخیص", "هیأت حل اختلاف", "دادرسی الکترونیکی", "سامانه جامع روابط کار"))
        decorate(conn, docs[REF_UNEMPLOYMENT], ("حقوق کار و تأمین اجتماعی",), ("بیمه بیکاری", "مقرری", "بیکار غیرارادی", "سابقه بیمه"))
        decorate(conn, docs[REF_UNEMPLOYMENT_BYLAW], ("حقوق کار و تأمین اجتماعی",), ("بیمه بیکاری", "اشتغال مجدد", "آموزش فنی و حرفه‌ای"))
        decorate(conn, docs[REF_RULING], ("حقوق کار و تأمین اجتماعی",), ("رأی وحدت رویه", "حق بیمه", "ایام اشتغال"))
        decorate(conn, docs[REF_DIVAN], ("حقوق کار و تأمین اجتماعی", "حقوق اداری"), ("رأی دیوان عدالت اداری", "تسویه‌حساب", "سند پرداخت", "مزد"))

        labor_current = dict(LABOR_CURRENT)
        labor_old = dict(LABOR_ORIGINAL_HISTORY)
        labor_ids = {}
        labor_rows = 0
        for n in range(1, 204):
            if n in labor_old:
                change_date = D1383 if n == 14 else D1394
                source = SRC_AMEND_1383 if n == 14 else SRC_AMEND_1394
                addv(conn, docs[REF_LABOR], REF_LABOR, n, labor_old[n], 1, False, D1369_LABOR, change_date, SRC_LABOR, "متن مصوب ۱۳۶۹.")
                labor_rows += 1
                labor_ids[n] = addv(conn, docs[REF_LABOR], REF_LABOR, n, labor_current[n], 2, True, change_date, None, source, "نسخه جاری پس از اصلاح یا الحاق؛ عنوان وزارتخانه مطابق ساختار جاری روزآمد شده است.")
                labor_rows += 1
            else:
                labor_ids[n] = addv(conn, docs[REF_LABOR], REF_LABOR, n, labor_current[n], 1, True, D1369_LABOR, None, SRC_LABOR, "متن جاری؛ تغییرات صرفاً سازمانی عنوان وزارتخانه جداگانه نسخه‌بندی نشده است.")
                labor_rows += 1

        procedure_ids = {}
        for n, text in LABOR_PROCEDURE_CURRENT:
            eff = D1392_EFFECTIVE if n <= 116 else D1397_ADDITION
            src = SRC_PROCEDURE if n <= 116 else SRC_EPROCEDURE
            procedure_ids[n] = add_article(
                conn, docs[REF_PROCEDURE], article_no=pn(n), article_key=f"{REF_PROCEDURE}:{n}",
                version_no=1, is_current=1, effective_date=eff, text=text, source_note=src,
                notes="متن جاری آیین دادرسی؛ اصلاحات میانی مندرج در شناسنامه منبع در این مرحله نسخه تاریخی جداگانه ندارند.",
            )

        unemployment_ids = {}
        for n, text in UNEMPLOYMENT_LAW:
            unemployment_ids[n] = add_article(
                conn, docs[REF_UNEMPLOYMENT], article_no=pn(n), article_key=f"{REF_UNEMPLOYMENT}:{n}",
                version_no=1, is_current=1, effective_date=D1369_UNEMPLOYMENT, text=text,
                source_note=SRC_UNEMPLOYMENT,
            )
        unemployment_bylaw_ids = {}
        for n, text in UNEMPLOYMENT_BYLAW:
            unemployment_bylaw_ids[n] = add_article(
                conn, docs[REF_UNEMPLOYMENT_BYLAW], article_no=pn(n), article_key=f"{REF_UNEMPLOYMENT_BYLAW}:{n}",
                version_no=1, is_current=1, effective_date=D1369_BYLAW, text=text,
                source_note=SRC_UNEMPLOYMENT_BYLAW,
            )

        ruling_id = add_article(
            conn, docs[REF_RULING], article_no="رأی", article_key=f"{REF_RULING}:holding",
            version_no=1, is_current=1, effective_date=D1390, text=UNIFIED_RULING_720,
            source_note=SRC_RULING, notes="قسمت لازم‌الاتباع رأی وحدت رویه.",
        )
        divan_id = add_article(
            conn, docs[REF_DIVAN], article_no="رأی", article_key=f"{REF_DIVAN}:holding",
            version_no=1, is_current=1, effective_date=D1397_DIVAN, text=DIVAN_RULING_17_20,
            source_note=SRC_DIVAN, notes="قسمت رأی ایجاد رویه؛ گردش کار و آرای نمونه جداگانه ماده‌بندی نشده‌اند.",
        )

        add_relation(conn, docs[REF_PROCEDURE], "implements", docs[REF_LABOR], from_article_id=procedure_ids[1], to_article_id=labor_ids[164], description="آیین دادرسی مراجع حل اختلاف موضوع ماده ۱۶۴ قانون کار.")
        add_relation(conn, docs[REF_PROCEDURE], "cites", docs[REF_LABOR], from_article_id=procedure_ids[1], to_article_id=labor_ids[157], description="رسیدگی هیأت‌های تشخیص و حل اختلاف به دعاوی موضوع ماده ۱۵۷.")
        add_relation(conn, docs[REF_UNEMPLOYMENT_BYLAW], "implements", docs[REF_UNEMPLOYMENT], from_article_id=unemployment_bylaw_ids[1], to_article_id=unemployment_ids[14], description="آیین‌نامه اجرایی موضوع ماده ۱۴ قانون بیمه بیکاری.")
        add_relation(conn, docs[REF_UNEMPLOYMENT], "cites", docs[REF_LABOR], from_article_id=unemployment_ids[4], to_article_id=labor_ids[23], description="حقوق و حمایت‌های کارگر بیکار و ارجاع به حمایت‌های تأمین اجتماعی.")
        add_relation(conn, docs[REF_UNEMPLOYMENT], "implements", docs[REF_LABOR], from_article_id=unemployment_ids[9], to_article_id=labor_ids[30], description="تکمیل حمایت مقرر برای کارگران بیکار ناشی از تعطیلی یا حوادث کارگاه.")
        add_relation(conn, docs[REF_RULING], "interprets", docs[REF_LABOR], from_article_id=ruling_id, to_article_id=labor_ids[148], description="تبیین مرجع رسیدگی به تکلیف بیمه‌کردن کارگر و پرداخت حق بیمه ایام اشتغال.")
        add_relation(conn, docs[REF_DIVAN], "interprets", docs[REF_LABOR], from_article_id=divan_id, to_article_id=labor_ids[37], description="لزوم ارائه اسناد مثبته پرداخت مزد موضوع ماده ۳۷.")
        add_relation(conn, docs[REF_DIVAN], "interprets", docs[REF_LABOR], from_article_id=divan_id, to_article_id=labor_ids[24], description="اثر اسناد پرداخت بر احراز تسویه مزایای پایان کار.")

        conn.commit()
        totals = conn.execute("""SELECT (SELECT COUNT(*) FROM documents)d,(SELECT COUNT(*) FROM articles)a,
          (SELECT COUNT(*) FROM articles WHERE is_current=1)c,(SELECT COUNT(*) FROM articles WHERE is_current=0)h,
          (SELECT COUNT(*) FROM relations)r""").fetchone()
        print(f"[OK] قانون کار: ۲۰۳ ماده جاری، {labor_rows} نسخه کل")
        print("[OK] آیین دادرسی کار: ۱۳۵ ماده | بیمه بیکاری: ۱۴ ماده | آیین‌نامه: ۲۴ ماده")
        print("[OK] رأی وحدت رویه ۷۲۰ و رأی ایجاد رویه ۱۷ تا ۲۰؛ حذف آیین‌نامه placeholder غیرواقعی")
        print(f"[TOTAL] اسناد: {totals['d']} | مواد/نسخه‌ها: {totals['a']} | جاری: {totals['c']} | تاریخی: {totals['h']} | روابط: {totals['r']}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
