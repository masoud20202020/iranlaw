# -*- coding: utf-8 -*-
"""Load the complete Cheque Issuance Law, its version history, and Sayad rules."""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "data", "seed"))

from schema import get_connection
from importer import (
    add_article,
    add_relation,
    add_tag,
    get_or_create_document,
    link_document_tag,
    link_document_topic,
)
from cheque_law import (
    CHEQUE_AMENDMENT_1372,
    CHEQUE_AMENDMENT_1382,
    CHEQUE_AMENDMENT_1397,
    CHEQUE_AMENDMENT_1400,
    CHEQUE_ART5BIS_BYLAW_1398,
    CHEQUE_CASE_RULES_1400,
    CHEQUE_CURRENT,
    CHEQUE_CURRENT_ORDER,
    CHEQUE_ELECTRONIC_INSTRUCTION_1402,
    CHEQUE_ORIGINAL_1355,
    CHEQUE_REPLACEMENTS_1372,
    CHEQUE_REPLACEMENTS_1376,
    CHEQUE_REPLACEMENTS_1382,
    CHEQUE_REPLACEMENTS_1397,
    CHEQUE_REPLACEMENTS_1400,
    SAYAD_CURRENT_ACCOUNT_1404_SUMMARY,
)

REF_MAIN = "QSC-1355"
REF_1372 = "ESCHK-1372"
REF_TAB2_1376 = "ECH2-1376"
REF_TAB14_1376 = "ECH14-1376"
REF_INTERP_1377 = "ISTCHK-1377"
REF_1382 = "ESCHK-1382"
REF_1397 = "ESCHK-1397"
REF_1400 = "ESCHK-1400"
REF_BYLAW_1398 = "AIN5M-1398"
REF_CASE_1400 = "CHKM-1400"
REF_ELECTRONIC_1402 = "CHKE-1402"
REF_SAYAD_1404 = "SAYAD-1404"

MANAGED_REFS = (
    REF_MAIN, REF_1372, REF_TAB2_1376, REF_TAB14_1376, REF_INTERP_1377,
    REF_1382, REF_1397, REF_1400, REF_BYLAW_1398, REF_CASE_1400,
    REF_ELECTRONIC_1402, REF_SAYAD_1404,
)

DATE_1355 = "1976-07-07"
DATE_1372 = "1993-11-02"
DATE_TAB2_1376 = "1997-05-31"
DATE_TAB14_1376 = "1998-01-04"
DATE_INTERP_1377 = "1998-12-12"
DATE_1382 = "2003-08-24"
DATE_1397 = "2018-11-04"
DATE_BYLAW_1398 = "2019-08-28"
DATE_CASE_1399 = "2021-03-07"
DATE_CASE_1400 = "2021-12-05"
DATE_1400 = "2021-04-18"
DATE_ELECTRONIC_1402 = "2024-02-17"
DATE_FINE_1403 = "2024-06-19"
DATE_SAYAD_1404 = "2025-09-09"

SOURCE_MAIN = (
    "قانون صدور چک مصوب ۱۳۵۵/۰۴/۱۶ با اصلاحات تا ۱۴۰۰/۰۱/۲۹؛ تطبیق رسمی: "
    "https://qavanin.ir/Law/PrintText/83598 ؛ متن منقح: پایگاه اختبار."
)
SOURCE_HISTORY = "سیر اصلاحات قانون صدور چک؛ متن مصوبات ۱۳۵۵، ۱۳۷۲ و ۱۳۸۲ با منابع رسمی مقابله شده است."
SOURCE_1397 = "قانون اصلاح قانون صدور چک مصوب ۱۳۹۷/۰۸/۱۳؛ https://qavanin.ir/Law/PrintText/263377"
SOURCE_1400 = "قانون اصلاح قانون صدور چک مصوب ۱۴۰۰/۰۱/۲۹؛ روزنامه رسمی شماره ۲۲۱۸۸، ویژه‌نامه ۱۴۰۹."
SOURCE_FINE_1403 = (
    "تصویب‌نامه اصلاح میزان مبالغ مربوط به جرائم و تخلفات مندرج در قوانین مختلف، "
    "مصوب ۱۴۰۳/۰۳/۳۰؛ ردیف قانون صدور چک."
)


def to_persian(value: int | str) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def lookup_id(conn, table: str, column: str, value: str) -> int:
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    if not row:
        raise ValueError(f"Unknown {table}.{column}: {value}")
    return row["id"]


def upsert_document(
    conn,
    *,
    ref: str,
    title: str,
    short_title: str,
    type_code: str,
    authority: str,
    status_code: str,
    ratification_date: str,
    publication_date: str | None = None,
    effective_date: str | None = None,
    official_no: str | None = None,
    notes: str,
) -> int:
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    if row:
        document_id = row["id"]
    else:
        document_id = get_or_create_document(
            conn, title=title, short_title=short_title, type_code=type_code,
            issuing_authority=authority, status_code=status_code,
            ratification_date=ratification_date, publication_date=publication_date,
            effective_date=effective_date or ratification_date,
            official_newspaper_no=official_no, reference_code=ref, notes=notes,
        )

    authority_row = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (authority,)).fetchone()
    if authority_row:
        authority_id = authority_row["id"]
    else:
        authority_type = "administrative" if "بانک مرکزی" in authority else "legislative"
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa, authority_type) VALUES(?,?)",
            (authority, authority_type),
        ).lastrowid

    conn.execute(
        """UPDATE documents SET title=?, short_title=?, type_id=?, issuing_authority_id=?,
           status_id=?, ratification_date=?, publication_date=?, effective_date=?,
           official_newspaper_no=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (
            title, short_title, lookup_id(conn, "document_types", "code", type_code),
            authority_id, lookup_id(conn, "statuses", "code", status_code),
            ratification_date, publication_date, effective_date or ratification_date,
            official_no, notes, document_id,
        ),
    )
    return document_id


def clear_managed(conn, document_id: int) -> None:
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (document_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (document_id,))


def decorate(conn, document_id: int, tags: list[str]) -> None:
    link_document_topic(conn, document_id, "حقوق تجارت")
    link_document_topic(conn, document_id, "حقوق پول و بانک")
    for tag in tags:
        link_document_tag(conn, document_id, add_tag(conn, tag))


def add_version(
    conn,
    doc_id: int,
    key: str,
    article_no: str,
    text: str,
    *,
    version: int,
    current: int,
    effective: str,
    expiry: str | None,
    source: str,
    notes: str | None = None,
) -> int:
    return add_article(
        conn, doc_id, article_no=article_no, article_key=f"{REF_MAIN}:{key}",
        version_no=version, is_current=current, effective_date=effective,
        expiry_date=expiry, text=text, source_note=source, notes=notes,
    )


def build_main_history() -> dict[str, list[tuple[str, str, str, str]]]:
    """key -> list of (date, text, source, note), in chronological order."""
    current = {key: text for key, (_, text) in zip(CHEQUE_CURRENT_ORDER, CHEQUE_CURRENT)}
    original = dict(CHEQUE_ORIGINAL_1355)
    schedules: dict[str, list[tuple[str, str, str, str]]] = {}

    # In 1372 a new article 1 was inserted and original articles 1-22 became 2-23.
    for original_no in range(1, 23):
        key = str(original_no + 1)
        schedules[key] = [
            (DATE_1355, original[original_no], SOURCE_HISTORY,
             f"متن مصوب ۱۳۵۵؛ در آن زمان شماره این ماده {to_persian(original_no)} بود."),
        ]

    def append_many(mapping, date, source, label):
        for key, text in mapping.items():
            schedules.setdefault(key, []).append((date, text, source, label))

    append_many(CHEQUE_REPLACEMENTS_1372, DATE_1372, SOURCE_HISTORY, "اصلاح/الحاق مصوب ۱۳۷۲/۰۸/۱۱.")
    schedules["2"].append((DATE_TAB2_1376, CHEQUE_REPLACEMENTS_1376["2"], SOURCE_MAIN,
                            "الحاق تبصره خسارات و هزینه‌های وصول چک در ۱۳۷۶."))
    schedules["14"].append((DATE_TAB14_1376, CHEQUE_REPLACEMENTS_1376["14"], SOURCE_MAIN,
                             "اصلاح تبصره ۱ و الحاق تبصره ۳ ماده ۱۴ در ۱۳۷۶/۱۰/۱۴."))
    append_many(CHEQUE_REPLACEMENTS_1382, DATE_1382, SOURCE_MAIN, "اصلاح/الحاق مصوب ۱۳۸۲/۰۶/۰۲.")
    append_many(CHEQUE_REPLACEMENTS_1397, DATE_1397, SOURCE_1397, "نسخه سامانه‌محور مصوب ۱۳۹۷/۰۸/۱۳.")
    append_many(CHEQUE_REPLACEMENTS_1400, DATE_1400, SOURCE_1400, "اصلاح تکمیلی مصوب ۱۴۰۰/۰۱/۲۹.")
    schedules["7"].append((DATE_FINE_1403, current["7"], SOURCE_FINE_1403,
                            "نسخه جاری با نصاب‌های تعدیل‌شده جزای نقدی ۱۴۰۳."))

    # Last stage always uses the clean consolidated current wording.
    for key in CHEQUE_CURRENT_ORDER:
        if key not in schedules:
            raise RuntimeError(f"No history schedule for current article {key}")
        date, _, source, note = schedules[key][-1]
        schedules[key][-1] = (date, current[key], source, note)
    return schedules


def load_main_articles(conn, doc_id: int):
    current_numbers = {key: number for key, (number, _) in zip(CHEQUE_CURRENT_ORDER, CHEQUE_CURRENT)}
    schedules = build_main_history()
    current_ids: dict[str, int] = {}
    inserted = 0
    for key in CHEQUE_CURRENT_ORDER:
        stages = schedules[key]
        for index, (date, text, source, note) in enumerate(stages, 1):
            is_current = int(index == len(stages))
            expiry = stages[index][0] if index < len(stages) else None
            article_id = add_version(
                conn, doc_id, key, current_numbers[key], text,
                version=index, current=is_current, effective=date, expiry=expiry,
                source=source, notes=note,
            )
            if is_current:
                current_ids[key] = article_id
            inserted += 1
    return current_ids, inserted


def add_rows(conn, doc_id: int, ref: str, rows, date: str, source: str):
    ids = {}
    for number, text in rows:
        article_no = to_persian(number)
        ids[number] = add_article(
            conn, doc_id, article_no=article_no, article_key=f"{ref}:{number}",
            version_no=1, is_current=1, effective_date=date, text=text,
            source_note=source,
        )
    return ids


def add_single(conn, doc_id: int, ref: str, no: str, text: str, date: str, source: str):
    return add_article(
        conn, doc_id, article_no=no, article_key=f"{ref}:1", version_no=1,
        is_current=1, effective_date=date, text=text, source_note=source,
    )


def main() -> None:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        docs = {}
        docs[REF_MAIN] = upsert_document(
            conn, ref=REF_MAIN,
            title="قانون صدور چک (مصوب ۱۳۵۵، با اصلاحات و الحاقات تا ۱۴۰۳)",
            short_title="ق.ص.چ.", type_code="law",
            authority="مجلس شورای ملی (پیش از انقلاب)", status_code="amended",
            ratification_date=DATE_1355, effective_date=DATE_1355,
            notes=(
                "متن منقح کامل شامل ۲۵ ماده اصلی و مواد ۳ مکرر، ۵ مکرر و ۲۱ مکرر؛ با تاریخچه "
                "نسخه‌های ۱۳۵۵، ۱۳۷۲، ۱۳۷۶، ۱۳۸۲، ۱۳۹۷ و ۱۴۰۰ و نصاب‌های جزای نقدی ۱۴۰۳."
            ),
        )
        docs[REF_1372] = upsert_document(
            conn, ref=REF_1372, title="قانون اصلاح موادی از قانون صدور چک مصوب تیرماه ۱۳۵۵ (اصلاحیه ۱۳۷۲)",
            short_title="اصلاح قانون چک ۱۳۷۲", type_code="amendment",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=DATE_1372, notes="هشت ماده؛ الحاق ماده ۱، تغییر شماره‌ها و اصلاح مواد کلیدی کیفری و بانکی.",
        )
        docs[REF_TAB2_1376] = upsert_document(
            conn, ref=REF_TAB2_1376, title="قانون الحاق یک تبصره به ماده ۲ قانون صدور چک",
            short_title="تبصره ماده ۲ چک", type_code="amendment",
            authority="مجمع تشخیص مصلحت نظام", status_code="in_force",
            ratification_date=DATE_TAB2_1376, notes="الحاق حکم مطالبه خسارات و هزینه‌های وصول چک.",
        )
        docs[REF_TAB14_1376] = upsert_document(
            conn, ref=REF_TAB14_1376, title="قانون اصلاح ذیل تبصره ۱ ماده ۱۴ قانون صدور چک و الحاق یک تبصره به آن",
            short_title="اصلاح ماده ۱۴ چک", type_code="amendment",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=DATE_TAB14_1376, notes="مصوب ۱۳۷۶/۱۰/۱۴؛ اصلاح تبصره ۱ و الحاق تبصره ۳.",
        )
        docs[REF_INTERP_1377] = upsert_document(
            conn, ref=REF_INTERP_1377, title="قانون استفساریه تبصره الحاقی به ماده ۲ قانون صدور چک",
            short_title="استفساریه خسارت چک", type_code="law",
            authority="مجمع تشخیص مصلحت نظام", status_code="in_force",
            ratification_date=DATE_INTERP_1377,
            notes="تعیین خسارت تأخیر تأدیه بر مبنای نرخ تورم از تاریخ چک تا زمان وصول.",
        )
        docs[REF_1382] = upsert_document(
            conn, ref=REF_1382, title="قانون اصلاح موادی از قانون صدور چک (مصوب ۱۳۸۲)",
            short_title="اصلاح قانون چک ۱۳۸۲", type_code="amendment",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=DATE_1382, notes="هشت ماده؛ اصلاح وصف کیفری، تاریخ وصول، خسارت، تأمین و اقامتگاه بانکی.",
        )
        docs[REF_1397] = upsert_document(
            conn, ref=REF_1397, title="قانون اصلاح قانون صدور چک (مصوب ۱۳۹۷)",
            short_title="اصلاح قانون چک ۱۳۹۷", type_code="amendment",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=DATE_1397, publication_date="2018-11-26",
            official_no="۲۱۴۶۷ / ویژه‌نامه ۱۱۰۵",
            notes="یازده ماده؛ ایجاد چارچوب سامانه صیاد، چک الکترونیکی، رفع سوءاثر و اجرائیه مستقیم.",
        )
        docs[REF_1400] = upsert_document(
            conn, ref=REF_1400, title="قانون اصلاح قانون صدور چک (مصوب ۱۴۰۰)",
            short_title="اصلاح قانون چک ۱۴۰۰", type_code="amendment",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=DATE_1400, publication_date="2021-05-23",
            official_no="۲۲۱۸۸ / ویژه‌نامه ۱۴۰۹",
            notes="سه ماده؛ حذف مهلت اعتبار سه‌ساله، اصلاح گذار صیاد و افزودن احکام چک تضمین‌شده.",
        )
        docs[REF_BYLAW_1398] = upsert_document(
            conn, ref=REF_BYLAW_1398,
            title="آیین‌نامه اجرایی تبصره ۱ ماده ۵ مکرر قانون صدور چک",
            short_title="آیین‌نامه ماده ۵ مکرر", type_code="regulation",
            authority="هیئت وزیران", status_code="in_force",
            ratification_date=DATE_BYLAW_1398, official_no="۷۲۲۰۸/ت۵۶۵۷۹هـ",
            notes="ده ماده؛ تعلیق یک‌ساله برخی محدودیت‌های بانکی بنگاه‌های اقتصادی با نظر شورای تأمین استان.",
        )
        docs[REF_CASE_1400] = upsert_document(
            conn, ref=REF_CASE_1400, title="مقررات ناظر بر اعطای چک موردی (با اصلاحات ۱۴۰۰)",
            short_title="مقررات چک موردی", type_code="directive",
            authority="بانک مرکزی جمهوری اسلامی ایران", status_code="in_force",
            ratification_date=DATE_CASE_1399, effective_date=DATE_CASE_1400,
            notes="چهارده ماده؛ متن تلفیقی مصوبه ۱۳۹۹/۱۲/۱۷ با اصلاحات ۱۴۰۰/۰۹/۱۴.",
        )
        docs[REF_ELECTRONIC_1402] = upsert_document(
            conn, ref=REF_ELECTRONIC_1402, title="دستورالعمل اجرایی چک الکترونیکی",
            short_title="دستورالعمل چک الکترونیکی", type_code="directive",
            authority="بانک مرکزی جمهوری اسلامی ایران", status_code="in_force",
            ratification_date=DATE_ELECTRONIC_1402,
            notes="نه ماده؛ صدور، انتقال، ضمانت، برگشت و رفع سوءاثر چک الکترونیکی در سامانه چکاد و صیاد.",
        )
        docs[REF_SAYAD_1404] = upsert_document(
            conn, ref=REF_SAYAD_1404,
            title="دستورالعمل حساب جاری (ریالی) و ضوابط اجرایی ماده ۶ اصلاحی قانون صدور چک (ابلاغ ۱۴۰۴)",
            short_title="ضوابط جاری صیاد ۱۴۰۴", type_code="directive",
            authority="بانک مرکزی جمهوری اسلامی ایران", status_code="in_force",
            ratification_date=DATE_SAYAD_1404,
            notes=(
                "این رکورد فعلاً خلاصه رسمی ابلاغ ۱۴۰۴ است، نه رونوشت کامل PDF. مصوبه ۱۴۰۴ مفاد دستورالعمل "
                "اجرایی ماده ۶ مصوب ۱۳۹۹ را با دستورالعمل حساب جاری تلفیق و جایگزین کرده است."
            ),
        )

        for document_id in docs.values():
            clear_managed(conn, document_id)

        decorate(conn, docs[REF_MAIN], ["چک", "صیاد", "چکاوک", "چک برگشتی", "قانون مادر"])
        decorate(conn, docs[REF_1372], ["چک", "اصلاح قانون چک"])
        decorate(conn, docs[REF_TAB2_1376], ["چک", "خسارت تأخیر تأدیه"])
        decorate(conn, docs[REF_TAB14_1376], ["چک", "دستور عدم پرداخت"])
        decorate(conn, docs[REF_INTERP_1377], ["چک", "خسارت تأخیر تأدیه", "استفساریه"])
        decorate(conn, docs[REF_1382], ["چک", "اصلاح قانون چک"])
        decorate(conn, docs[REF_1397], ["چک", "صیاد", "اصلاح قانون چک"])
        decorate(conn, docs[REF_1400], ["چک", "صیاد", "چک تضمین‌شده"])
        decorate(conn, docs[REF_BYLAW_1398], ["چک برگشتی", "رفع سوءاثر"])
        decorate(conn, docs[REF_CASE_1400], ["چک موردی", "صیاد"])
        decorate(conn, docs[REF_ELECTRONIC_1402], ["چک الکترونیکی", "چکاد", "صیاد"])
        decorate(conn, docs[REF_SAYAD_1404], ["حساب جاری", "صیاد", "اعتبارسنجی"])

        main_current_ids, main_version_count = load_main_articles(conn, docs[REF_MAIN])
        act_ids = {}
        act_ids[REF_1372] = add_rows(conn, docs[REF_1372], REF_1372, CHEQUE_AMENDMENT_1372, DATE_1372, SOURCE_HISTORY)
        act_ids[REF_1382] = add_rows(conn, docs[REF_1382], REF_1382, CHEQUE_AMENDMENT_1382, DATE_1382, SOURCE_MAIN)
        act_ids[REF_1397] = add_rows(conn, docs[REF_1397], REF_1397, CHEQUE_AMENDMENT_1397, DATE_1397, SOURCE_1397)
        act_ids[REF_1400] = add_rows(conn, docs[REF_1400], REF_1400, CHEQUE_AMENDMENT_1400, DATE_1400, SOURCE_1400)

        tab2_text = (
            "ماده واحده- دارنده چک می‌تواند محکومیت صادرکننده را نسبت به پرداخت کلیه خسارات و هزینه‌های "
            "واردشده که مستقیماً و به‌طور متعارف در جهت وصول طلب خود متحمل شده است، از دادگاه تقاضا نماید."
        )
        tab14_text = (
            "ماده واحده- در تبصره ۱ ماده ۱۴ عبارت «در موردی که ذی‌نفع دستور عدم پرداخت می‌دهد» به عبارت "
            "«در موردی که دستور عدم پرداخت مطابق این ماده صادر می‌شود» تغییر می‌یابد و تبصره ۳ درباره "
            "ممنوعیت توقف پرداخت چک تضمین‌شده و مسافرتی، مگر در فرض ادعای جعل بانک صادرکننده، الحاق می‌شود."
        )
        interp_text = (
            "ماده واحده- منظور از کلیه خسارات و هزینه‌های واردشده در تبصره ماده ۲، خسارت تأخیر تأدیه بر "
            "مبنای نرخ تورم از تاریخ چک تا زمان وصول که توسط بانک مرکزی اعلام می‌شود و هزینه دادرسی و "
            "حق‌الوکاله بر اساس تعرفه‌های قانونی است."
        )
        single_ids = {
            REF_TAB2_1376: add_single(conn, docs[REF_TAB2_1376], REF_TAB2_1376, "ماده واحده", tab2_text, DATE_TAB2_1376, SOURCE_MAIN),
            REF_TAB14_1376: add_single(conn, docs[REF_TAB14_1376], REF_TAB14_1376, "ماده واحده", tab14_text, DATE_TAB14_1376, "https://qavanin.ir/Law/PrintText/84070"),
            REF_INTERP_1377: add_single(conn, docs[REF_INTERP_1377], REF_INTERP_1377, "ماده واحده", interp_text, DATE_INTERP_1377, SOURCE_MAIN),
        }

        reg_ids = {}
        reg_ids[REF_BYLAW_1398] = add_rows(
            conn, docs[REF_BYLAW_1398], REF_BYLAW_1398, CHEQUE_ART5BIS_BYLAW_1398,
            DATE_BYLAW_1398, "تصویب‌نامه شماره ۷۲۲۰۸/ت۵۶۵۷۹هـ هیئت وزیران."
        )
        reg_ids[REF_CASE_1400] = add_rows(
            conn, docs[REF_CASE_1400], REF_CASE_1400, CHEQUE_CASE_RULES_1400,
            DATE_CASE_1400, "مقررات بانک مرکزی؛ مصوب ۱۳۹۹/۱۲/۱۷ با اصلاحات ۱۴۰۰/۰۹/۱۴."
        )
        reg_ids[REF_ELECTRONIC_1402] = add_rows(
            conn, docs[REF_ELECTRONIC_1402], REF_ELECTRONIC_1402,
            CHEQUE_ELECTRONIC_INSTRUCTION_1402, DATE_ELECTRONIC_1402,
            "مصوب ۱۴۰۲/۱۱/۲۸ کمیسیون ابزارهای پرداخت و تسویه بانک مرکزی."
        )
        summary_id = add_single(
            conn, docs[REF_SAYAD_1404], REF_SAYAD_1404, "خلاصه ابلاغ",
            SAYAD_CURRENT_ACCOUNT_1404_SUMMARY, DATE_SAYAD_1404,
            "خلاصه رسمی ابلاغ بانک مرکزی؛ https://www.yjc.ir/fa/news/9007856/"
        )

        # Amendment relations, article by article.
        maps = {
            REF_1372: {1: "1", 2: "7", 3: "8", 4: "10", 5: "13", 6: "14", 7: "18", 8: "21"},
            REF_1382: {1: "3", 2: "3bis", 3: "7", 4: "12", 5: "13", 6: "18", 7: "22"},
            REF_1397: {1: "1", 2: "4", 3: "5", 4: "5bis", 5: "6", 6: "21", 7: "21", 8: "21bis", 9: "23", 10: "25"},
            REF_1400: {1: "6", 2: "21bis", 3: "24"},
        }
        for ref, mapping in maps.items():
            for act_no, target_key in mapping.items():
                add_relation(
                    conn, docs[ref], "amends", docs[REF_MAIN],
                    from_article_id=act_ids[ref][act_no], to_article_id=main_current_ids[target_key],
                    description=f"اثرگذاری ماده {to_persian(act_no)} سند اصلاحی بر ماده {target_key.replace('bis',' مکرر')} قانون صدور چک.",
                )

        add_relation(conn, docs[REF_TAB2_1376], "amends", docs[REF_MAIN],
                     from_article_id=single_ids[REF_TAB2_1376], to_article_id=main_current_ids["2"],
                     description="الحاق تبصره خسارات به ماده ۲.")
        add_relation(conn, docs[REF_TAB14_1376], "amends", docs[REF_MAIN],
                     from_article_id=single_ids[REF_TAB14_1376], to_article_id=main_current_ids["14"],
                     description="اصلاح تبصره ۱ و الحاق تبصره ۳ ماده ۱۴.")
        add_relation(conn, docs[REF_INTERP_1377], "interprets", docs[REF_MAIN],
                     from_article_id=single_ids[REF_INTERP_1377], to_article_id=main_current_ids["2"],
                     description="تفسیر دامنه خسارات و مبدأ خسارت تأخیر تأدیه.")

        add_relation(conn, docs[REF_BYLAW_1398], "implements", docs[REF_MAIN],
                     from_article_id=reg_ids[REF_BYLAW_1398][1], to_article_id=main_current_ids["5bis"],
                     description="آیین‌نامه اجرایی تبصره ۱ ماده ۵ مکرر.")
        for key in ("6", "21bis"):
            add_relation(conn, docs[REF_CASE_1400], "implements", docs[REF_MAIN],
                         from_article_id=reg_ids[REF_CASE_1400][1], to_article_id=main_current_ids[key],
                         description="ضوابط چک موردی و ثبت آن در سامانه صیاد.")
        for key in ("1", "6", "21bis"):
            add_relation(conn, docs[REF_ELECTRONIC_1402], "implements", docs[REF_MAIN],
                         from_article_id=reg_ids[REF_ELECTRONIC_1402][1], to_article_id=main_current_ids[key],
                         description="اجرای چک الکترونیکی در بستر چکاد و صیاد.")
        for key in ("6", "21bis"):
            add_relation(conn, docs[REF_SAYAD_1404], "implements", docs[REF_MAIN],
                         from_article_id=summary_id, to_article_id=main_current_ids[key],
                         description="ضوابط تجمیعی جاری حساب جاری، دسته‌چک و سامانه صیاد مصوب ۱۴۰۴.")

        # 1403 monetary adjustment already exists in the database from the commercial-law package.
        fine_doc = conn.execute("SELECT id FROM documents WHERE reference_code='TMJN-1403'").fetchone()
        if fine_doc:
            fine_article = conn.execute(
                "SELECT id FROM articles WHERE document_id=? ORDER BY id LIMIT 1", (fine_doc["id"],)
            ).fetchone()
            add_relation(conn, fine_doc["id"], "amends", docs[REF_MAIN],
                         from_article_id=fine_article["id"] if fine_article else None,
                         to_article_id=main_current_ids["7"],
                         description="تعدیل نصاب‌های مبلغی بندهای الف، ب و ج ماده ۷ در سال ۱۴۰۳.")

        # Link the special cheque law to the general Commercial Code.
        commercial = conn.execute("SELECT id FROM documents WHERE reference_code='QT-1311'").fetchone()
        if commercial:
            add_relation(conn, docs[REF_MAIN], "cites", commercial["id"],
                         description="قانون خاص صدور چک در کنار مقررات چک و اسناد تجاری قانون تجارت.")

        conn.commit()

        totals = conn.execute("""
            SELECT (SELECT COUNT(*) FROM documents) docs,
                   (SELECT COUNT(*) FROM articles) articles,
                   (SELECT COUNT(*) FROM articles WHERE is_current=1) current_articles,
                   (SELECT COUNT(*) FROM articles WHERE is_current=0) historical,
                   (SELECT COUNT(*) FROM relations) relations
        """).fetchone()
        current_count = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE document_id=? AND is_current=1", (docs[REF_MAIN],)
        ).fetchone()[0]
        print(f"[OK] قانون صدور چک: ۲۸ مفاد جاری، {main_version_count} نسخه کل")
        print("[OK] اصلاحیه‌ها: ۱۳۷۲، دو مصوبه ۱۳۷۶، استفساریه ۱۳۷۷، اصلاحات ۱۳۸۲، ۱۳۹۷ و ۱۴۰۰")
        print("[OK] مقررات: آیین‌نامه ماده ۵ مکرر (۱۰)، چک موردی (۱۴)، چک الکترونیکی (۹)، خلاصه ابلاغ صیاد ۱۴۰۴")
        print(f"[TOTAL] اسناد: {totals['docs']} | مواد/نسخه‌ها: {totals['articles']} | جاری: {totals['current_articles']} | تاریخی: {totals['historical']} | روابط: {totals['relations']}")
        if current_count != 28:
            raise AssertionError(f"Expected 28 current cheque-law provisions, got {current_count}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
