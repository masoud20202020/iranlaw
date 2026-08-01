# -*- coding: utf-8 -*-
"""Load the cybercrime, electronic procedure and electronic-evidence package."""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path[:0] = [SCRIPT_DIR, os.path.join(ROOT, "data", "seed")]

from schema import get_connection
from importer import (
    add_article,
    add_relation,
    add_tag,
    get_or_create_document,
    link_document_tag,
    link_document_topic,
)
from cybercrime_law import *

REF_LAW = "QJR-1388"
REF_PROC = "QADRE-1393"
REF_BYLAW = "AEEE-1393"
REF_RULING = "RVR-729-1391"
REF_OPINION = "NM-679-1402"
REFS = (REF_LAW, REF_PROC, REF_BYLAW, REF_RULING, REF_OPINION)

D1388 = "2009-05-26"
D1391 = "2013-02-19"
D1393_BYLAW = "2014-08-03"
D1393_PROC = "2014-09-30"
D1394_EFFECTIVE = "2015-06-22"
D1399_REDUCTION = "2020-05-12"
D1399_FINE = "2021-01-27"
D1402_OPINION = "2023-12-02"
D1403_FINE = "2024-06-19"

SRC_LAW = (
    "قانون جرایم رایانه‌ای مصوب ۱۳۸۸/۰۳/۰۵؛ متن مستقل ۵۶ ماده‌ای با سامانه ملی قوانین "
    "(https://qavanin.ir/Law/PrintText/123407) و نسخه تنقیحی شناسنامه قانون مقابله شده است."
)
SRC_1399 = (
    "تصویب‌نامه تعدیل میزان مبالغ مجازات نقدی جرایم و تخلفات، مصوب ۱۳۹۹/۱۱/۰۸ هیئت وزیران."
)
SRC_1403 = (
    "تصویب‌نامه شماره ۵۶۲۶۱/ت۶۲۲۹۸هـ مورخ ۱۴۰۳/۰۴/۰۴ هیئت وزیران، مصوب جلسه ۱۴۰۳/۰۳/۳۰."
)
SRC_PROC = (
    "بخش‌های نهم و دهم قانون آیین دادرسی کیفری، الحاقی به موجب قانون آیین دادرسی جرائم "
    "نیروهای مسلح و دادرسی الکترونیکی مصوب ۱۳۹۳/۰۷/۰۸؛ متن با نسخه تنقیحی اختبار مقابله شده است."
)
SRC_BYLAW = (
    "آیین‌نامه جمع‌آوری و استنادپذیری ادله الکترونیکی، شماره ۱۰۰/۲۸۱۹۹/۹۰۰۰ مورخ "
    "۱۳۹۳/۰۵/۱۲ رئیس قوه قضائیه؛ روزنامه رسمی شماره ۲۰۲۱۸."
)
SRC_RULING = (
    "رأی وحدت رویه شماره ۷۲۹ مورخ ۱۳۹۱/۱۲/۰۱، گزارش وحدت رویه ردیف ۹۱/۲۱؛ "
    "روزنامه رسمی شماره ۱۹۸۶۲ مورخ ۱۳۹۲/۰۲/۲۴."
)
SRC_OPINION = (
    "نظریه مشورتی شماره ۷/۱۴۰۲/۶۷۹ مورخ ۱۴۰۲/۰۹/۱۱ اداره کل حقوقی قوه قضائیه."
)


def pn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def lookup_id(conn, table: str, column: str, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def upsert_document(
    conn,
    ref: str,
    title: str,
    short_title: str,
    type_code: str,
    authority: str,
    status_code: str,
    ratification_date: str,
    effective_date: str,
    notes: str,
    official_no: str | None = None,
):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    if row:
        document_id = row["id"]
    else:
        document_id = get_or_create_document(
            conn,
            title=title,
            short_title=short_title,
            type_code=type_code,
            issuing_authority=authority,
            status_code=status_code,
            ratification_date=ratification_date,
            effective_date=effective_date,
            official_newspaper_no=official_no,
            reference_code=ref,
            notes=notes,
        )
    authority_id = lookup_id(conn, "authorities", "name_fa", authority)
    if authority_id is None:
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa, authority_type) VALUES(?, 'judicial')", (authority,)
        ).lastrowid
    conn.execute(
        """UPDATE documents
           SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
               ratification_date=?, effective_date=?, official_newspaper_no=?, notes=?,
               updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            title,
            short_title,
            lookup_id(conn, "document_types", "code", type_code),
            authority_id,
            lookup_id(conn, "statuses", "code", status_code),
            ratification_date,
            effective_date,
            official_no,
            notes,
            document_id,
        ),
    )
    return document_id


def clear_document(conn, document_id: int) -> None:
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (document_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (document_id,))


def decorate(conn, document_id: int, topics: tuple[str, ...], tags: tuple[str, ...]) -> None:
    for topic in topics:
        link_document_topic(conn, document_id, topic)
    for tag in tags:
        link_document_tag(conn, document_id, add_tag(conn, tag))


def add_version(
    conn,
    document_id: int,
    ref: str,
    number,
    text: str,
    version: int,
    current: bool,
    effective: str,
    expiry: str | None,
    source: str,
    note: str,
):
    return add_article(
        conn,
        document_id,
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
        docs = {
            REF_LAW: upsert_document(
                conn,
                REF_LAW,
                "قانون جرایم رایانه‌ای (مصوب ۱۳۸۸، با تعدیلات و وضعیت تنقیحی جاری)",
                "قانون جرایم رایانه‌ای",
                "law",
                "مجلس شورای اسلامی",
                "amended",
                D1388,
                D1388,
                "متن کامل ۵۶ ماده؛ مواد ۲۸ تا ۵۱ از ۱۳۹۴/۰۴/۰۱ منسوخ و با مواد ۶۶۴ تا ۶۸۷ قانون آیین دادرسی کیفری جایگزین شده‌اند. تاریخچه تعدیل جزاهای نقدی ۱۳۹۹ و ۱۴۰۳ و کاهش حبس ماده ۱۶ نگهداری می‌شود.",
            ),
            REF_PROC: upsert_document(
                conn,
                REF_PROC,
                "بخش‌های نهم و دهم الحاقی قانون آیین دادرسی کیفری؛ دادرسی الکترونیکی و آیین دادرسی جرایم رایانه‌ای",
                "دادرسی الکترونیکی و جرایم رایانه‌ای",
                "law",
                "کمیسیون قضایی و حقوقی مجلس شورای اسلامی",
                "amended",
                D1393_PROC,
                D1394_EFFECTIVE,
                "متن کامل مواد ۶۴۹ تا ۶۸۷ به‌همراه مواد ۶۹۸ و ۶۹۹ مرتبط با نسخ و تاریخ اجرا؛ این سند گزیده بخش‌های مرتبط از قانون ۱۲۹ ماده‌ای مصوب ۱۳۹۳ است، نه رونوشت کل مواد ۵۷۱ تا ۶۹۹. جزاهای نقدی مواد ۶۶۰، ۶۶۱ و ۶۶۹ نسخه‌بندی شده‌اند.",
            ),
            REF_BYLAW: upsert_document(
                conn,
                REF_BYLAW,
                "آیین‌نامه جمع‌آوری و استنادپذیری ادله الکترونیکی",
                "آیین‌نامه ادله الکترونیکی",
                "regulation",
                "رئیس قوه قضائیه",
                "in_force",
                D1393_BYLAW,
                D1393_BYLAW,
                "متن کامل ۴۸ ماده و ۱۱ تبصره درباره نگهداری، حفاظت، ارائه، تفتیش، توقیف، زنجیره حفاظتی و استنادپذیری ادله الکترونیکی. آیین‌نامه پیش از جایگزینی مقررات شکلی قانون در سال ۱۳۹۴ تصویب شده و باید همراه مواد ۶۶۴ تا ۶۸۷ قانون آیین دادرسی کیفری خوانده شود.",
                official_no="۲۰۲۱۸",
            ),
            REF_RULING: upsert_document(
                conn,
                REF_RULING,
                "رأی وحدت رویه شماره ۷۲۹ هیئت عمومی دیوان عالی کشور درباره صلاحیت محلی در کلاهبرداری رایانه‌ای",
                "رأی وحدت رویه ۷۲۹",
                "unified_ruling",
                "دیوان عالی کشور",
                "in_force",
                D1391,
                D1391,
                "متن کامل قسمت «رأی» درباره صلاحیت دادگاه محل بانک افتتاح‌کننده حساب زیان‌دیده؛ مقدمه و گردش کار پرونده به‌صورت ردیف ماده‌ای جداگانه ثبت نشده است.",
                official_no="۱۹۸۶۲",
            ),
            REF_OPINION: upsert_document(
                conn,
                REF_OPINION,
                "نظریه مشورتی شماره ۷/۱۴۰۲/۶۷۹ درباره کلاهبرداری رایانه‌ای و استرداد ارز دیجیتال",
                "نظریه مشورتی ارز دیجیتال",
                "advisory_opinion",
                "اداره کل حقوقی قوه قضائیه",
                "in_force",
                D1402_OPINION,
                D1402_OPINION,
                "پاسخ کامل نظریه درباره تمایز کلاهبرداری رایانه‌ای از کلاهبرداری کلاسیک، مال بودن ارز دیجیتال و شیوه رد مال؛ متن استعلام در شناسنامه سند خلاصه نشده و پاسخ رسمی به‌طور کامل ثبت شده است.",
            ),
        }
        for document_id in docs.values():
            clear_document(conn, document_id)

        decorate(
            conn,
            docs[REF_LAW],
            ("حقوق کیفری", "حقوق تجارت الکترونیک"),
            (
                "جرایم رایانه‌ای",
                "دسترسی غیرمجاز",
                "شنود غیرمجاز",
                "جعل رایانه‌ای",
                "کلاهبرداری رایانه‌ای",
                "حریم خصوصی",
                "محتوای مجرمانه",
            ),
        )
        decorate(
            conn,
            docs[REF_PROC],
            ("آیین دادرسی کیفری", "حقوق تجارت الکترونیک"),
            ("دادرسی الکترونیکی", "صلاحیت", "داده ترافیک", "تفتیش رایانه‌ای", "توقیف داده"),
        )
        decorate(
            conn,
            docs[REF_BYLAW],
            ("آیین دادرسی کیفری", "حقوق تجارت الکترونیک"),
            ("ادله الکترونیکی", "زنجیره حفاظتی", "حفظ داده", "تفتیش و توقیف", "جرم‌یابی دیجیتال"),
        )
        decorate(
            conn,
            docs[REF_RULING],
            ("آیین دادرسی کیفری", "حقوق کیفری"),
            ("رأی وحدت رویه", "صلاحیت محلی", "کلاهبرداری رایانه‌ای"),
        )
        decorate(
            conn,
            docs[REF_OPINION],
            ("حقوق کیفری", "حقوق تجارت الکترونیک"),
            ("نظریه مشورتی", "ارز دیجیتال", "رد مال", "کلاهبرداری رایانه‌ای"),
        )

        original = dict(CYBER_ORIGINAL_1388)
        fine_1399 = dict(CYBER_FINE_1399)
        current = dict(CYBER_CURRENT_1403)
        law_current_ids: dict[int, int] = {}
        law_old_ids: dict[int, int] = {}
        law_row_count = 0
        fine_articles = set(CYBER_FINE_ARTICLES)
        repealed = set(CYBER_REPEALED_PROCEDURE)

        for number in range(1, 57):
            if number in repealed:
                stages = [
                    (D1388, original[number], SRC_LAW, "متن مصوب ۱۳۸۸؛ منسوخ از ۱۳۹۴/۰۴/۰۱ به موجب ماده ۶۹۸ قانون آیین دادرسی کیفری.")
                ]
            elif number == 16:
                stages = [
                    (D1388, original[number], SRC_LAW, "متن مصوب ۱۳۸۸."),
                    (D1399_REDUCTION, CYBER_ART16_REDUCTION_1399, "قانون کاهش مجازات حبس تعزیری مصوب ۱۳۹۹/۰۲/۲۳.", "کاهش حبس جرم قابل گذشت موضوع ماده ۱۶؛ پیش از تعدیل جزای نقدی ۱۳۹۹."),
                    (D1399_FINE, fine_1399[number], SRC_1399, "تعدیل جزای نقدی در ۱۳۹۹، با حفظ حبس کاهش‌یافته."),
                    (D1403_FINE, current[number], SRC_1403, "نسخه جاری با جزای نقدی تعدیل‌شده ۱۴۰۳."),
                ]
            elif number in fine_articles:
                stages = [(D1388, original[number], SRC_LAW, "متن مصوب ۱۳۸۸.")]
                # Article 24 retained the same figures in 1399; avoid a duplicate no-change version.
                if fine_1399[number] != original[number]:
                    stages.append((D1399_FINE, fine_1399[number], SRC_1399, "تعدیل جزای نقدی در ۱۳۹۹."))
                stages.append((D1403_FINE, current[number], SRC_1403, "نسخه جاری با جزای نقدی تعدیل‌شده ۱۴۰۳."))
            else:
                stages = [(D1388, original[number], SRC_LAW, "متن مصوب ۱۳۸۸.")]

            for index, (date, text, source, note) in enumerate(stages, 1):
                is_current = index == len(stages) and number not in repealed
                expiry = stages[index][0] if index < len(stages) else (D1394_EFFECTIVE if number in repealed else None)
                article_id = add_version(
                    conn,
                    docs[REF_LAW],
                    REF_LAW,
                    number,
                    text,
                    index,
                    is_current,
                    date,
                    expiry,
                    source,
                    note,
                )
                law_row_count += 1
                if is_current:
                    law_current_ids[number] = article_id
                else:
                    law_old_ids[number] = article_id

        proc_original = dict(ELECTRONIC_PROCEDURE_ORIGINAL_1393)
        proc_1399 = dict(ELECTRONIC_PROCEDURE_FINE_1399)
        proc_current = dict(ELECTRONIC_PROCEDURE_CURRENT_1403)
        proc_fines = set(ELECTRONIC_PROCEDURE_FINE_ARTICLES)
        proc_current_ids: dict[int, int] = {}
        proc_row_count = 0
        for number in list(range(649, 688)) + [698, 699]:
            if number in proc_fines:
                stages = [
                    (D1394_EFFECTIVE, proc_original[number], SRC_PROC, "متن لازم‌الاجرا از ۱۳۹۴/۰۴/۰۱."),
                    (D1399_FINE, proc_1399[number], SRC_1399, "تعدیل جزای نقدی در ۱۳۹۹."),
                    (D1403_FINE, proc_current[number], SRC_1403, "نسخه جاری با جزای نقدی تعدیل‌شده ۱۴۰۳."),
                ]
            else:
                stages = [(D1394_EFFECTIVE, proc_original[number], SRC_PROC, "متن لازم‌الاجرا از ۱۳۹۴/۰۴/۰۱.")]
            for index, (date, text, source, note) in enumerate(stages, 1):
                is_current = index == len(stages)
                expiry = stages[index][0] if index < len(stages) else None
                article_id = add_version(
                    conn,
                    docs[REF_PROC],
                    REF_PROC,
                    number,
                    text,
                    index,
                    is_current,
                    date,
                    expiry,
                    source,
                    note,
                )
                proc_row_count += 1
                if is_current:
                    proc_current_ids[number] = article_id

        bylaw_ids: dict[int, int] = {}
        for number, text in ELECTRONIC_EVIDENCE_BYLAW_1393:
            bylaw_ids[number] = add_article(
                conn,
                docs[REF_BYLAW],
                article_no=pn(number),
                article_key=f"{REF_BYLAW}:{number}",
                version_no=1,
                is_current=1,
                effective_date=D1393_BYLAW,
                text=text,
                source_note=SRC_BYLAW,
                notes="متن مصوب ۱۳۹۳؛ املای آشکارا مخدوش نسخه وب با مقابله منابع همسان اصلاح شده است.",
            )

        ruling_id = add_article(
            conn,
            docs[REF_RULING],
            article_no="رأی",
            article_key=f"{REF_RULING}:holding",
            version_no=1,
            is_current=1,
            effective_date=D1391,
            text=UNIFIED_RULING_729,
            source_note=SRC_RULING,
            notes="قسمت لازم‌الاتباع رأی وحدت رویه؛ شماره صحیح رأی ۷۲۹ است.",
        )
        opinion_id = add_article(
            conn,
            docs[REF_OPINION],
            article_no="پاسخ",
            article_key=f"{REF_OPINION}:answer",
            version_no=1,
            is_current=1,
            effective_date=D1402_OPINION,
            text=ADVISORY_1402_679,
            source_note=SRC_OPINION,
            notes="پاسخ رسمی اداره کل حقوقی؛ نظریه مشورتی برای مراجع قضایی الزام‌آور نیست.",
        )

        # Replacement of the old procedural block by the later Criminal Procedure Code.
        for number in range(28, 52):
            add_relation(
                conn,
                docs[REF_PROC],
                "abrogates",
                docs[REF_LAW],
                from_article_id=proc_current_ids[698],
                to_article_id=law_old_ids[number],
                description=f"نسخ ماده {pn(number)} قانون جرایم رایانه‌ای (ماده متناظر {pn(number + 728)} بخش تعزیرات) از ۱۳۹۴/۰۴/۰۱.",
            )

        q_adk = conn.execute("SELECT id FROM documents WHERE reference_code='QADK-1392'").fetchone()
        if q_adk:
            add_relation(
                conn,
                docs[REF_PROC],
                "amends",
                q_adk["id"],
                description="الحاق بخش‌های دادرسی الکترونیکی و آیین دادرسی جرایم رایانه‌ای به قانون آیین دادرسی کیفری.",
            )

        add_relation(
            conn,
            docs[REF_BYLAW],
            "implements",
            docs[REF_LAW],
            from_article_id=bylaw_ids[1],
            to_article_id=law_current_ids[54],
            description="آیین‌نامه موضوع ماده ۵۴ قانون جرایم رایانه‌ای درباره جمع‌آوری و استنادپذیری ادله الکترونیکی.",
        )
        add_relation(
            conn,
            docs[REF_BYLAW],
            "implements",
            docs[REF_PROC],
            description="مقررات اجرایی ادله الکترونیکی؛ قابل قرائت همراه مواد ۶۶۴ تا ۶۸۷ قانون آیین دادرسی کیفری.",
        )
        for own, target, description in (
            (2, 667, "نگهداری داده ترافیک و اطلاعات کاربران خدمات دسترسی."),
            (5, 668, "نگهداری اطلاعات کاربران و محتوای خدمات میزبانی."),
            (11, 669, "حفاظت فوری داده‌های ذخیره‌شده."),
            (17, 670, "ارائه داده‌های حفاظت‌شده به دستور مقام قضایی."),
            (24, 671, "شرایط و درخواست تفتیش و توقیف داده یا سامانه."),
            (34, 678, "گسترش دامنه تفتیش و حفظ فوری داده‌های مرتبط."),
            (47, 685, "اعتبار و استنادپذیری نسخه‌ها و داده‌های رایانه‌ای."),
        ):
            add_relation(
                conn,
                docs[REF_BYLAW],
                "implements",
                docs[REF_PROC],
                from_article_id=bylaw_ids[own],
                to_article_id=proc_current_ids[target],
                description=description,
            )

        add_relation(
            conn,
            docs[REF_RULING],
            "interprets",
            docs[REF_LAW],
            from_article_id=ruling_id,
            to_article_id=law_old_ids[29],
            description="تعیین صلاحیت محلی بر مبنای ماده ۲۹ تاریخی قانون جرایم رایانه‌ای.",
        )
        add_relation(
            conn,
            docs[REF_RULING],
            "cites",
            docs[REF_PROC],
            from_article_id=ruling_id,
            description="ارتباط رویه صلاحیت محلی رأی ۷۲۹ با قواعد جاری ماده ۶۶۵.",
        )
        add_relation(
            conn,
            docs[REF_OPINION],
            "interprets",
            docs[REF_LAW],
            from_article_id=opinion_id,
            to_article_id=law_current_ids[13],
            description="تفسیر شرایط کلاهبرداری رایانه‌ای و رد ارز دیجیتال موضوع ماده ۱۳.",
        )

        for external_ref, description in (
            ("QTE-1382", "ارتباط با داده‌پیام، امضای الکترونیکی، داده‌های شخصی و جرایم قانون تجارت الکترونیکی."),
            ("TMJN-1399", "مبنای نسخه‌های تاریخی جزاهای نقدی سال ۱۳۹۹."),
            ("TMJN-1403", "مبنای مبالغ جاری جزاهای نقدی مصوب ۱۴۰۳."),
        ):
            external = conn.execute(
                "SELECT id FROM documents WHERE reference_code=?", (external_ref,)
            ).fetchone()
            if external:
                add_relation(
                    conn,
                    docs[REF_LAW],
                    "cites",
                    external["id"],
                    description=description,
                )

        civil = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()
        if civil:
            add_relation(
                conn,
                docs[REF_OPINION],
                "cites",
                civil["id"],
                from_article_id=opinion_id,
                description="استناد نظریه به ماده ۳۱۲ قانون مدنی در رد مال مثلی.",
            )

        conn.commit()
        totals = conn.execute(
            """SELECT
               (SELECT COUNT(*) FROM documents) AS documents,
               (SELECT COUNT(*) FROM articles) AS articles,
               (SELECT COUNT(*) FROM articles WHERE is_current=1) AS current_articles,
               (SELECT COUNT(*) FROM articles WHERE is_current=0) AS historical_articles,
               (SELECT COUNT(*) FROM relations) AS relations"""
        ).fetchone()
        print(f"[OK] قانون جرایم رایانه‌ای: ۵۶ شماره، {law_row_count} نسخه، ۳۲ ماده جاری")
        print(f"[OK] دادرسی الکترونیکی/رایانه‌ای: ۴۱ شماره، {proc_row_count} نسخه | آیین‌نامه ادله: ۴۸ ماده")
        print("[OK] رأی وحدت رویه ۷۲۹ و نظریه مشورتی ۷/۱۴۰۲/۶۷۹")
        print(
            f"[TOTAL] اسناد: {totals['documents']} | مواد/نسخه‌ها: {totals['articles']} | "
            f"جاری: {totals['current_articles']} | تاریخی: {totals['historical_articles']} | "
            f"روابط: {totals['relations']}"
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
