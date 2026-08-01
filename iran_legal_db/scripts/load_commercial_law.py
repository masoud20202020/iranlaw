# -*- coding: utf-8 -*-
"""Load the complete Iranian Commercial Code and its principal amendment history.

Loaded instruments:
- قانون تجارت ۱۳۱۱: all 600 enacted articles
- لایحه قانونی اصلاح قسمتی از قانون تجارت ۱۳۴۷: all 300 articles
- 1353 amendment to article 17
- 1395 amendment to article 241
- 1399 and 1403 monetary-penalty adjustments
- 1403 invalid-provisions list affecting both instruments

The loader is idempotent. It replaces only the articles/outgoing relations/tags managed
by these document reference codes and preserves unrelated incoming document relations.
"""
from __future__ import annotations

import os
import sys
from typing import Any

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
from commercial_code_1311 import (
    COMMERCIAL_CODE_1311_CURRENT,
    COMMERCIAL_CODE_1311_ORIGINAL,
    COMMERCIAL_CODE_PENALTY_ARTICLES_1403,
)
from commercial_amendment_1347 import (
    COMMERCIAL_AMENDMENT_1347_ORIGINAL,
    COMMERCIAL_AMENDMENT_1399_PENALTY_TEXTS,
    COMMERCIAL_AMENDMENT_CURRENT,
    COMMERCIAL_AMENDMENT_PENALTY_ARTICLES_1403,
)

REF_CODE = "QT-1311"
REF_BILL = "LTEJ-1347"
REF_ART17 = "ET17-1353"
REF_ART241 = "ET241-1395"
REF_FINE_1399 = "TMJN-1399"
REF_FINE_1403 = "TMJN-1403"
REF_INVALID_1403 = "FNAT-1403"
MANAGED_REFS = (
    REF_CODE,
    REF_BILL,
    REF_ART17,
    REF_ART241,
    REF_FINE_1399,
    REF_FINE_1403,
    REF_INVALID_1403,
)

SOURCE_QT = (
    "متن مصوب قانون تجارت ۱۳۱۱؛ منبع رسمی تطبیق: سامانه ملی قوانین و مقررات "
    "https://qavanin.ir/Law/TreeText/83457 ؛ منبع متن تاریخی: مشروطه؛ "
    "PDF ارسالی کاربر (بانک سامان) صرفاً منبع تطبیقی تصویری است."
)
SOURCE_LTEJ = (
    "لایحه قانونی اصلاح قسمتی از قانون تجارت مصوب ۱۳۴۷/۱۲/۲۴؛ منبع رسمی تطبیق: "
    "https://qavanin.ir/Law/TreeText/83829 ؛ متن اولیه و متن تلفیقی با منابع ثانویه مقابله شده است."
)
SOURCE_1403 = (
    "تصویب‌نامه اصلاح میزان مبالغ مربوط به جرائم و تخلفات مندرج در قوانین مختلف، "
    "مصوب ۱۴۰۳/۰۳/۳۰ هیئت وزیران، شماره ۵۶۲۶۱/ت۶۲۲۹۸هـ؛ "
    "https://nezamat.ir/اصلاح-میزان-مبالغ-مربوط-به-جرائم-و-تخ/"
)
SOURCE_INVALID = (
    "قانون فهرست قوانین و احکام نامعتبر در حوزه تجارت، مصوب ۱۴۰۳/۱۱/۱۵؛ "
    "https://shenasname.ir/laws/70712-قوانین-و-احکام-نامعتبر-در-حوزه-تجارت"
)

# Original Commercial Code articles 21-93 (joint-stock companies) were replaced by
# the 300-article 1347 bill. Article 543 was expressly listed as invalid in 1403.
CODE_REPLACED_1347 = set(range(21, 94))
CODE_INVALID_1403 = {543}

# The 1403 invalid-provisions law lists bill article 51 and articles 53 through 71.
BILL_INVALID_1403 = {51, *range(53, 72)}

DATE_QT = "1932-05-05"       # 1311/02/13
DATE_LTEJ = "1969-03-15"     # 1347/12/24
DATE_LTEJ_PUB = "1969-03-30" # 1348/01/10
DATE_ART17 = "1975-02-11"    # 1353/11/22
DATE_ART241 = "2016-05-09"   # 1395/02/20
DATE_FINE_1399 = "2021-01-27"# 1399/11/08
DATE_FINE_1403 = "2024-06-19"# 1403/03/30
DATE_INVALID_1403 = "2025-03-16"  # publication/notification record used for chronology


def to_persian_num(value: int | str) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def lookup_id(conn, table: str, code_column: str, code: str) -> int:
    row = conn.execute(
        f"SELECT id FROM {table} WHERE {code_column}=?", (code,)
    ).fetchone()
    if not row:
        raise ValueError(f"Unknown {table}.{code_column}: {code}")
    return row["id"]


def upsert_document(
    conn,
    *,
    reference_code: str,
    title: str,
    short_title: str,
    type_code: str,
    authority: str,
    status_code: str,
    ratification_date: str,
    publication_date: str | None = None,
    effective_date: str | None = None,
    official_newspaper_no: str | None = None,
    notes: str,
) -> int:
    row = conn.execute(
        "SELECT id FROM documents WHERE reference_code=?", (reference_code,)
    ).fetchone()
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
            publication_date=publication_date,
            effective_date=effective_date,
            official_newspaper_no=official_newspaper_no,
            reference_code=reference_code,
            notes=notes,
        )

    type_id = lookup_id(conn, "document_types", "code", type_code)
    status_id = lookup_id(conn, "statuses", "code", status_code)
    authority_row = conn.execute(
        "SELECT id FROM authorities WHERE name_fa=?", (authority,)
    ).fetchone()
    if authority_row:
        authority_id = authority_row["id"]
    else:
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa, authority_type) VALUES(?, 'legislative')",
            (authority,),
        ).lastrowid

    conn.execute(
        """UPDATE documents
           SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
               ratification_date=?, publication_date=?, effective_date=?,
               official_newspaper_no=?, notes=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            title,
            short_title,
            type_id,
            authority_id,
            status_id,
            ratification_date,
            publication_date,
            effective_date,
            official_newspaper_no,
            notes,
            document_id,
        ),
    )
    return document_id


def clear_managed_content(conn, document_id: int) -> None:
    # Keep unrelated incoming document-level relations (e.g. a unified ruling that
    # interprets the Commercial Code), but replace all outgoing relations we manage.
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (document_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (document_id,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (document_id,))


def decorate(conn, document_id: int, tags: list[str]) -> None:
    link_document_topic(conn, document_id, "حقوق تجارت")
    for tag in tags:
        link_document_tag(conn, document_id, add_tag(conn, tag))


def insert_version(
    conn,
    document_id: int,
    ref: str,
    number: int,
    text: str,
    *,
    version_no: int,
    is_current: int,
    effective_date: str,
    expiry_date: str | None,
    source_note: str,
    notes: str | None = None,
) -> int:
    return add_article(
        conn,
        document_id,
        article_no=to_persian_num(number),
        article_key=f"{ref}:{number}",
        version_no=version_no,
        is_current=is_current,
        effective_date=effective_date,
        expiry_date=expiry_date,
        text=text,
        source_note=source_note,
        notes=notes,
    )


def load_code(conn, document_id: int) -> tuple[dict[int, int], int]:
    original = dict(COMMERCIAL_CODE_1311_ORIGINAL)
    current = dict(COMMERCIAL_CODE_1311_CURRENT)
    penalty_articles = set(COMMERCIAL_CODE_PENALTY_ARTICLES_1403)
    current_ids: dict[int, int] = {}
    inserted = 0

    for number in range(1, 601):
        if number in penalty_articles:
            insert_version(
                conn, document_id, REF_CODE, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_QT,
                expiry_date=DATE_FINE_1403, source_note=SOURCE_QT,
                notes="مبلغ جزای نقدی این نسخه به موجب تصویب‌نامه ۱۴۰۳ تعدیل شده است.",
            )
            inserted += 1
            current_ids[number] = insert_version(
                conn, document_id, REF_CODE, number, current[number],
                version_no=2, is_current=1, effective_date=DATE_FINE_1403,
                expiry_date=None, source_note=SOURCE_1403,
                notes="نسخه جاری با مبلغ تعدیل‌شده جزای نقدی مصوب ۱۴۰۳/۰۳/۳۰.",
            )
            inserted += 1
            continue

        if number in CODE_REPLACED_1347:
            insert_version(
                conn, document_id, REF_CODE, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_QT,
                expiry_date=DATE_LTEJ, source_note=SOURCE_QT,
                notes="مقررات شرکت‌های سهامی؛ به موجب لایحه قانونی اصلاح قسمتی از قانون تجارت ۱۳۴۷ جایگزین شد.",
            )
            inserted += 1
            continue

        if number in CODE_INVALID_1403:
            insert_version(
                conn, document_id, REF_CODE, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_QT,
                expiry_date=DATE_INVALID_1403, source_note=SOURCE_INVALID,
                notes="به موجب قانون فهرست قوانین و احکام نامعتبر در حوزه تجارت مصوب ۱۴۰۳ منسوخ اعلام شد.",
            )
            inserted += 1
            continue

        current_ids[number] = insert_version(
            conn, document_id, REF_CODE, number, original[number],
            version_no=1, is_current=1, effective_date=DATE_QT,
            expiry_date=None, source_note=SOURCE_QT,
        )
        inserted += 1

    return current_ids, inserted


def load_bill(conn, document_id: int) -> tuple[dict[int, int], int]:
    original = dict(COMMERCIAL_AMENDMENT_1347_ORIGINAL)
    current_rows = {number: (text, label) for number, text, label in COMMERCIAL_AMENDMENT_CURRENT}
    penalty_1399 = dict(COMMERCIAL_AMENDMENT_1399_PENALTY_TEXTS)
    penalty_articles = set(COMMERCIAL_AMENDMENT_PENALTY_ARTICLES_1403)
    current_ids: dict[int, int] = {}
    inserted = 0

    for number in range(1, 301):
        current_text, label = current_rows[number]
        invalid = number in BILL_INVALID_1403
        invalid_expiry = DATE_INVALID_1403 if invalid else None
        invalid_note = (
            "به موجب قانون فهرست قوانین و احکام نامعتبر در حوزه تجارت مصوب ۱۴۰۳ منسوخ اعلام شد."
            if invalid else None
        )

        if number == 17:
            insert_version(
                conn, document_id, REF_BILL, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_LTEJ,
                expiry_date=DATE_ART17, source_note=SOURCE_LTEJ,
                notes="نسخه اولیه مصوب ۱۳۴۷؛ در ۱۳۵۳ اصلاح و یک تبصره به آن الحاق شد.",
            )
            inserted += 1
            current_ids[number] = insert_version(
                conn, document_id, REF_BILL, number, current_text,
                version_no=2, is_current=1, effective_date=DATE_ART17,
                expiry_date=None, source_note="قانون اصلاح ماده ۱۷ مصوب ۱۳۵۳/۱۱/۲۲.",
                notes="نسخه جاری ماده ۱۷ به همراه تبصره الحاقی.",
            )
            inserted += 1
            continue

        if number == 241:
            insert_version(
                conn, document_id, REF_BILL, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_LTEJ,
                expiry_date=DATE_ART241, source_note=SOURCE_LTEJ,
                notes="نسخه اولیه با سقف پاداش پنج و ده درصد.",
            )
            inserted += 1
            current_ids[number] = insert_version(
                conn, document_id, REF_BILL, number, current_text,
                version_no=2, is_current=1, effective_date=DATE_ART241,
                expiry_date=None,
                source_note="قانون اصلاح ماده ۲۴۱ مصوب ۱۳۹۵/۰۲/۲۰؛ https://qavanin.ir/Law/TreeText/254251",
                notes="نسخه جاری با سقف سه و شش درصد و دو تبصره الحاقی.",
            )
            inserted += 1
            continue

        if number in penalty_articles:
            insert_version(
                conn, document_id, REF_BILL, number, original[number],
                version_no=1, is_current=0, effective_date=DATE_LTEJ,
                expiry_date=DATE_FINE_1399, source_note=SOURCE_LTEJ,
                notes="نسخه اولیه مبلغ جزای نقدی.",
            )
            insert_version(
                conn, document_id, REF_BILL, number, penalty_1399[number],
                version_no=2, is_current=0, effective_date=DATE_FINE_1399,
                expiry_date=DATE_FINE_1403,
                source_note="تصویب‌نامه تعدیل جزای نقدی مصوب ۱۳۹۹/۱۱/۰۸ هیئت وزیران.",
                notes="مبلغ تعدیل‌شده ۱۳۹۹؛ در ۱۴۰۳ مجدداً تعدیل شد.",
            )
            inserted += 2
            current_ids[number] = insert_version(
                conn, document_id, REF_BILL, number, current_text,
                version_no=3, is_current=1, effective_date=DATE_FINE_1403,
                expiry_date=None, source_note=SOURCE_1403,
                notes="نسخه جاری با مبلغ تعدیل‌شده ۱۴۰۳/۰۳/۳۰.",
            )
            inserted += 1
            continue

        article_id = insert_version(
            conn, document_id, REF_BILL, number, current_text,
            version_no=1,
            is_current=0 if invalid else 1,
            effective_date=DATE_LTEJ,
            expiry_date=invalid_expiry,
            source_note=SOURCE_INVALID if invalid else SOURCE_LTEJ,
            notes=invalid_note or (f"یادداشت منبع: {label}" if label else None),
        )
        if not invalid:
            current_ids[number] = article_id
        inserted += 1

    return current_ids, inserted


def add_single_article_document(
    conn,
    document_id: int,
    ref: str,
    text: str,
    effective_date: str,
    source_note: str,
) -> int:
    return add_article(
        conn,
        document_id,
        article_no="ماده واحده",
        article_key=f"{ref}:MU",
        version_no=1,
        is_current=1,
        effective_date=effective_date,
        text=text,
        source_note=source_note,
    )


def main() -> None:
    conn = get_connection()
    try:
        conn.execute("BEGIN")

        docs: dict[str, int] = {}
        docs[REF_CODE] = upsert_document(
            conn,
            reference_code=REF_CODE,
            title="قانون تجارت (مصوب ۱۳۱۱، با وضعیت تنقیحی و تعدیلات بعدی)",
            short_title="ق.ت.",
            type_code="law",
            authority="مجلس شورای ملی (پیش از انقلاب)",
            status_code="amended",
            ratification_date=DATE_QT,
            effective_date=DATE_QT,
            notes=(
                "متن کامل ۶۰۰ ماده قانون تجارت مصوب ۱۳۱۱/۰۲/۱۳. مواد ۲۱ تا ۹۳ مربوط به شرکت سهامی "
                "با لایحه ۱۳۴۷ جایگزین شده‌اند؛ ماده ۵۴۳ در ۱۴۰۳ منسوخ اعلام شده و مبالغ جزای نقدی "
                "مواد ۱۵، ۱۶، ۱۸، ۲۰۱، ۲۲۰ و ۳۴۶ مطابق تصویب‌نامه ۱۴۰۳ نسخه‌بندی شده‌اند."
            ),
        )
        docs[REF_BILL] = upsert_document(
            conn,
            reference_code=REF_BILL,
            title="لایحه قانونی اصلاح قسمتی از قانون تجارت (شرکت‌های سهامی، مصوب ۱۳۴۷)",
            short_title="ل.ا.ق.ت.",
            type_code="amendment",
            authority="مجلس شورای ملی (پیش از انقلاب)",
            status_code="amended",
            ratification_date=DATE_LTEJ,
            publication_date=DATE_LTEJ_PUB,
            effective_date=DATE_LTEJ,
            official_newspaper_no="۷۰۳۸",
            notes=(
                "متن کامل ۳۰۰ ماده درباره شرکت‌های سهامی عام و خاص، همراه تاریخچه ماده ۱۷، ماده ۲۴۱، "
                "تعدیلات جزای نقدی ۱۳۹۹ و ۱۴۰۳ و وضعیت نسخ مواد ۵۱ و ۵۳ تا ۷۱ در سال ۱۴۰۳."
            ),
        )
        docs[REF_ART17] = upsert_document(
            conn,
            reference_code=REF_ART17,
            title="قانون اصلاح ماده ۱۷ لایحه قانونی اصلاح قسمتی از قانون تجارت و الحاق یک تبصره",
            short_title="اصلاح ماده ۱۷ ق.ت.",
            type_code="amendment",
            authority="مجلس شورای ملی (پیش از انقلاب)",
            status_code="in_force",
            ratification_date=DATE_ART17,
            effective_date=DATE_ART17,
            notes="مصوب ۱۳۵۳/۱۱/۲۲؛ اصلاح نحوه انتشار دعوت و اطلاعیه‌های صاحبان سهام.",
        )
        docs[REF_ART241] = upsert_document(
            conn,
            reference_code=REF_ART241,
            title="قانون اصلاح ماده ۲۴۱ لایحه قانونی اصلاح قسمتی از قانون تجارت",
            short_title="اصلاح ماده ۲۴۱ ق.ت.",
            type_code="amendment",
            authority="مجلس شورای اسلامی",
            status_code="in_force",
            ratification_date=DATE_ART241,
            effective_date=DATE_ART241,
            notes="مصوب ۱۳۹۵/۰۲/۲۰ و تأیید شورای نگهبان در ۱۳۹۵/۰۲/۲۹.",
        )
        docs[REF_FINE_1399] = upsert_document(
            conn,
            reference_code=REF_FINE_1399,
            title="تصویب‌نامه تعدیل میزان مبالغ مجازات نقدی جرایم و تخلفات مندرج در قوانین مختلف (۱۳۹۹)",
            short_title="تعدیل جزای نقدی ۱۳۹۹",
            type_code="regulation",
            authority="هیئت وزیران",
            status_code="amended",
            ratification_date=DATE_FINE_1399,
            effective_date=DATE_FINE_1399,
            official_newspaper_no="۱۵۳۹۷۳/ت۵۷۷۵۲هـ",
            notes="مبالغ مرتبط با مقررات جزایی لایحه ۱۳۴۷ را تعدیل کرد و در ۱۴۰۳ مجدداً تعدیل شد.",
        )
        docs[REF_FINE_1403] = upsert_document(
            conn,
            reference_code=REF_FINE_1403,
            title="تصویب‌نامه اصلاح میزان مبالغ مربوط به جرائم و تخلفات مندرج در قوانین مختلف (۱۴۰۳)",
            short_title="تعدیل جزای نقدی ۱۴۰۳",
            type_code="regulation",
            authority="هیئت وزیران",
            status_code="in_force",
            ratification_date=DATE_FINE_1403,
            publication_date="2024-07-13",
            effective_date=DATE_FINE_1403,
            official_newspaper_no="۵۶۲۶۱/ت۶۲۲۹۸هـ",
            notes="مبالغ جزای نقدی مواد مرتبط قانون تجارت ۱۳۱۱ و لایحه ۱۳۴۷ را به‌روز کرده است.",
        )
        docs[REF_INVALID_1403] = upsert_document(
            conn,
            reference_code=REF_INVALID_1403,
            title="قانون فهرست قوانین و احکام نامعتبر در حوزه تجارت",
            short_title="فهرست احکام نامعتبر تجارت",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status_code="in_force",
            ratification_date="2025-02-03",
            publication_date=DATE_INVALID_1403,
            effective_date=DATE_INVALID_1403,
            notes=(
                "در بخش مرتبط با این بارگذاری، ماده ۵۴۳ قانون تجارت و مواد ۵۱ و ۵۳ تا ۷۱ لایحه قانونی "
                "اصلاح قسمتی از قانون تجارت را منسوخ اعلام کرده است."
            ),
        )

        for document_id in docs.values():
            clear_managed_content(conn, document_id)

        decorate(conn, docs[REF_CODE], ["قانون مادر", "تجارت", "تاجر", "ورشکستگی", "اسناد تجاری"])
        decorate(conn, docs[REF_BILL], ["شرکت سهامی", "سهامی عام", "سهامی خاص", "اصلاح قانون تجارت"])
        decorate(conn, docs[REF_ART17], ["اصلاح قانون تجارت", "مجمع عمومی"])
        decorate(conn, docs[REF_ART241], ["اصلاح قانون تجارت", "پاداش هیئت مدیره"])
        decorate(conn, docs[REF_FINE_1399], ["جزای نقدی", "تعدیل مبلغ"])
        decorate(conn, docs[REF_FINE_1403], ["جزای نقدی", "تعدیل مبلغ"])
        decorate(conn, docs[REF_INVALID_1403], ["تنقیح قوانین", "نسخ", "تجارت"])

        code_current_ids, code_inserted = load_code(conn, docs[REF_CODE])
        bill_current_ids, bill_inserted = load_bill(conn, docs[REF_BILL])

        art17_text = next(
            text for number, text, _ in COMMERCIAL_AMENDMENT_CURRENT if number == 17
        )
        art241_text = next(
            text for number, text, _ in COMMERCIAL_AMENDMENT_CURRENT if number == 241
        )
        companion_article_ids: dict[str, int] = {}
        companion_article_ids[REF_ART17] = add_single_article_document(
            conn,
            docs[REF_ART17],
            REF_ART17,
            "ماده ۱۷ لایحه قانونی اصلاح قسمتی از قانون تجارت به شرح متن اصلاحی زیر جایگزین و یک تبصره به آن الحاق می‌شود: " + art17_text,
            DATE_ART17,
            "قانون اصلاح ماده ۱۷ مصوب ۱۳۵۳/۱۱/۲۲.",
        )
        companion_article_ids[REF_ART241] = add_single_article_document(
            conn,
            docs[REF_ART241],
            REF_ART241,
            "ماده ۲۴۱ لایحه قانونی اصلاح قسمتی از قانون تجارت به شرح زیر اصلاح و دو تبصره به آن الحاق می‌شود: " + art241_text,
            DATE_ART241,
            "سامانه ملی قوانین و مقررات؛ https://qavanin.ir/Law/TreeText/254251",
        )

        penalty_1399_numbers = list(COMMERCIAL_AMENDMENT_PENALTY_ARTICLES_1403)
        companion_article_ids[REF_FINE_1399] = add_single_article_document(
            conn,
            docs[REF_FINE_1399],
            REF_FINE_1399,
            "میزان مبالغ مجازات نقدی جرایم و تخلفات مندرج در قوانین و مقررات مختلف طبق جداول پیوست تعدیل می‌شود. "
            "مواد مرتبط لایحه قانونی اصلاح قسمتی از قانون تجارت: "
            + "، ".join(to_persian_num(n) for n in penalty_1399_numbers)
            + ".",
            DATE_FINE_1399,
            "تصویب‌نامه شماره ۱۵۳۹۷۳/ت۵۷۷۵۲هـ مصوب جلسه ۱۳۹۹/۱۱/۰۸ هیئت وزیران.",
        )
        companion_article_ids[REF_FINE_1403] = add_single_article_document(
            conn,
            docs[REF_FINE_1403],
            REF_FINE_1403,
            "میزان مبالغ مربوط به جرائم و تخلفات مندرج در قوانین مختلف طبق جداول شماره ۱ و ۲ پیوست اصلاح می‌شود. "
            "مواد مرتبط قانون تجارت ۱۳۱۱: "
            + "، ".join(to_persian_num(n) for n in COMMERCIAL_CODE_PENALTY_ARTICLES_1403)
            + "؛ مواد مرتبط لایحه ۱۳۴۷: "
            + "، ".join(to_persian_num(n) for n in penalty_1399_numbers)
            + ".",
            DATE_FINE_1403,
            SOURCE_1403,
        )
        companion_article_ids[REF_INVALID_1403] = add_single_article_document(
            conn,
            docs[REF_INVALID_1403],
            REF_INVALID_1403,
            "از تاریخ لازم‌الاجرا شدن این قانون، احکام قانونی مذکور در پیوست منسوخ اعلام می‌گردد. "
            "ردیف مرتبط: قانون تجارت مصوب ۱۳۱۱، از جمله ماده ۵۴۳؛ و لایحه قانونی اصلاح قسمتی از قانون تجارت مصوب ۱۳۴۷، مواد ۵۱ و ۵۳ تا ۷۱ و تبصره‌های آنها.",
            DATE_INVALID_1403,
            SOURCE_INVALID,
        )

        # Document-level and article-level amendment/abrogation network.
        add_relation(
            conn, docs[REF_BILL], "amends", docs[REF_CODE],
            from_article_id=bill_current_ids[299],
            description="مواد ۱ تا ۳۰۰ لایحه ۱۳۴۷ جایگزین مقررات شرکت‌های سهامی در مواد ۲۱ تا ۹۳ قانون تجارت شد.",
        )
        add_relation(
            conn, docs[REF_ART17], "amends", docs[REF_BILL],
            from_article_id=companion_article_ids[REF_ART17],
            to_article_id=bill_current_ids[17],
            description="اصلاح ماده ۱۷ و الحاق تبصره در ۱۳۵۳.",
        )
        add_relation(
            conn, docs[REF_ART241], "amends", docs[REF_BILL],
            from_article_id=companion_article_ids[REF_ART241],
            to_article_id=bill_current_ids[241],
            description="اصلاح سقف پاداش هیئت مدیره و الحاق دو تبصره در ۱۳۹۵.",
        )
        add_relation(
            conn, docs[REF_FINE_1399], "amends", docs[REF_BILL],
            from_article_id=companion_article_ids[REF_FINE_1399],
            description="تعدیل مبالغ جزای نقدی در ۱۳۹۹.",
        )
        for number in penalty_1399_numbers:
            add_relation(
                conn, docs[REF_FINE_1399], "amends", docs[REF_BILL],
                from_article_id=companion_article_ids[REF_FINE_1399],
                to_article_id=bill_current_ids[number],
                description=f"تعدیل مبلغ جزای نقدی ماده {to_persian_num(number)} در ۱۳۹۹؛ نسخه بعدی در ۱۴۰۳.",
            )

        add_relation(
            conn, docs[REF_FINE_1403], "amends", docs[REF_CODE],
            from_article_id=companion_article_ids[REF_FINE_1403],
            description="تعدیل مبالغ جزای نقدی قانون تجارت در ۱۴۰۳.",
        )
        add_relation(
            conn, docs[REF_FINE_1403], "amends", docs[REF_BILL],
            from_article_id=companion_article_ids[REF_FINE_1403],
            description="تعدیل مبالغ جزای نقدی لایحه ۱۳۴۷ در ۱۴۰۳.",
        )
        for number in COMMERCIAL_CODE_PENALTY_ARTICLES_1403:
            add_relation(
                conn, docs[REF_FINE_1403], "amends", docs[REF_CODE],
                from_article_id=companion_article_ids[REF_FINE_1403],
                to_article_id=code_current_ids[number],
                description=f"تعدیل مبلغ جزای نقدی ماده {to_persian_num(number)} در ۱۴۰۳.",
            )
        for number in penalty_1399_numbers:
            add_relation(
                conn, docs[REF_FINE_1403], "amends", docs[REF_BILL],
                from_article_id=companion_article_ids[REF_FINE_1403],
                to_article_id=bill_current_ids[number],
                description=f"تعدیل مبلغ جزای نقدی ماده {to_persian_num(number)} در ۱۴۰۳.",
            )

        add_relation(
            conn, docs[REF_INVALID_1403], "abrogates", docs[REF_CODE],
            from_article_id=companion_article_ids[REF_INVALID_1403],
            description="اعلام نسخ ماده ۵۴۳ و سایر احکام مندرج در پیوست قانون ۱۴۰۳.",
        )
        add_relation(
            conn, docs[REF_INVALID_1403], "abrogates", docs[REF_BILL],
            from_article_id=companion_article_ids[REF_INVALID_1403],
            description="اعلام نسخ مواد ۵۱ و ۵۳ تا ۷۱ و تبصره‌های آنها.",
        )
        old_code_543 = conn.execute(
            "SELECT id FROM articles WHERE document_id=? AND article_key=? ORDER BY version_no DESC LIMIT 1",
            (docs[REF_CODE], f"{REF_CODE}:543"),
        ).fetchone()["id"]
        add_relation(
            conn, docs[REF_INVALID_1403], "abrogates", docs[REF_CODE],
            from_article_id=companion_article_ids[REF_INVALID_1403],
            to_article_id=old_code_543,
            description="ماده ۵۴۳ قانون تجارت در فهرست احکام نامعتبر ۱۴۰۳.",
        )
        for number in sorted(BILL_INVALID_1403):
            old_id = conn.execute(
                "SELECT id FROM articles WHERE document_id=? AND article_key=? ORDER BY version_no DESC LIMIT 1",
                (docs[REF_BILL], f"{REF_BILL}:{number}"),
            ).fetchone()["id"]
            add_relation(
                conn, docs[REF_INVALID_1403], "abrogates", docs[REF_BILL],
                from_article_id=companion_article_ids[REF_INVALID_1403],
                to_article_id=old_id,
                description=f"اعلام نسخ ماده {to_persian_num(number)} لایحه ۱۳۴۷ در سال ۱۴۰۳.",
            )

        conn.commit()

        total_docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
        total_articles = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
        total_relations = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]
        code_current_count = conn.execute(
            "SELECT COUNT(*) c FROM articles WHERE document_id=? AND is_current=1", (docs[REF_CODE],)
        ).fetchone()["c"]
        bill_current_count = conn.execute(
            "SELECT COUNT(*) c FROM articles WHERE document_id=? AND is_current=1", (docs[REF_BILL],)
        ).fetchone()["c"]

        print(f"[OK] قانون تجارت ۱۳۱۱: ۶۰۰ شماره ماده، {code_inserted} نسخه، {code_current_count} ماده جاری")
        print(f"[OK] لایحه اصلاحی ۱۳۴۷: ۳۰۰ شماره ماده، {bill_inserted} نسخه، {bill_current_count} ماده جاری")
        print(f"[OK] اسناد اصلاحی/تنقیحی همراه: ۵ سند")
        print(f"[TOTAL] اسناد: {total_docs} | نسخه‌های مواد: {total_articles} | ارتباطات: {total_relations}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
