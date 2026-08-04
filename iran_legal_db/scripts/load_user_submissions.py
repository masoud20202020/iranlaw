#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load the five legal texts pasted by the user in chat."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "data" / "seed")]

from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic  # noqa: E402
from schema import get_connection  # noqa: E402
from user_submissions import DOCUMENTS  # noqa: E402


def one(conn, sql, value):
    row = conn.execute(sql, (value,)).fetchone()
    return row["id"] if row else None


def ensure_authority(conn, name):
    row = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (name,)).fetchone()
    if row:
        return row["id"]
    kind = "judicial" if "قوه" in name or "قضائیه" in name else ("executive" if "هیئت وزیران" in name else "legislative")
    return conn.execute("INSERT INTO authorities(name_fa, authority_type) VALUES(?,?)", (name, kind)).lastrowid


def upsert(conn, doc):
    authority_id = ensure_authority(conn, doc["authority"])
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", doc["ref"])
    if not did:
        did = get_or_create_document(
            conn, title=doc["title"], short_title=doc["short"], type_code=doc["type_code"],
            issuing_authority=doc["authority"], status_code=doc["status_code"],
            ratification_date=doc["date"], effective_date=doc["date"],
            reference_code=doc["ref"], notes=doc["notes"],
        )
    conn.execute(
        """UPDATE documents SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
           ratification_date=?, effective_date=?, notes=? WHERE id=?""",
        (doc["title"], doc["short"], one(conn, "SELECT id FROM document_types WHERE code=?", doc["type_code"]),
         authority_id, one(conn, "SELECT id FROM statuses WHERE code=?", doc["status_code"]),
         doc["date"], doc["date"], doc["notes"], did),
    )
    return did


def clear_owned(conn, did):
    for sql in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(sql, (did,))


def load_one(conn, doc):
    did = upsert(conn, doc)
    clear_owned(conn, did)
    topic = "حقوق کیفری" if doc["ref"] != "AIWET-1397-636" else "حقوق محیط زیست"
    conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES(?)", (topic,))
    link_document_topic(conn, did, topic)
    for tag in sorted(set(("متن ارسالی کاربر",) + tuple(doc.get("tags", ())))):
        link_document_tag(conn, did, add_tag(conn, tag))
    source = f"{doc['source_url']}؛ فایل خام: {doc['source_path']}"
    for row in doc["rows"]:
        add_article(
            conn, did, article_no=row["article_no"], article_key=f"{doc['ref']}:{row['article_key_suffix']}",
            version_no=1, is_current=1, effective_date=doc["date"], text=row["text"],
            source_note=source, notes="متن مستقیماً توسط کاربر ارسال شده است؛ برای استناد رسمی با منبع رسمی مقابله شود.",
        )
    return did


def add_rel(conn, from_ref, to_ref, relation_type, description):
    a = one(conn, "SELECT id FROM documents WHERE reference_code=?", from_ref)
    b = one(conn, "SELECT id FROM documents WHERE reference_code=?", to_ref)
    if not a or not b:
        return
    conn.execute("DELETE FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type=? AND description=?", (a, b, relation_type, description))
    add_relation(conn, a, relation_type, b, description=description)


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        for doc in DOCUMENTS:
            load_one(conn, doc)
        add_rel(conn, "CIR-MM-714-1396", "E45MM-1396", "implements", "این بخشنامه در اجرای قانون الحاق یک ماده به قانون مبارزه با مواد مخدر مصوب ۱۳۹۶ صادر شده است.")
        add_rel(conn, "AICR-768-1396", "QADK-1392", "cites", "آیین‌نامه بررسی صحنه جرم در اجرای مقررات آیین دادرسی کیفری و وظایف مقامات قضایی است.")
        add_rel(conn, "AICR-774-1395", "QADK-1392-EXEC", "implements", "این آیین‌نامه شیوه استقرار واحد اجرای احکام کیفری را برای بخش اجرای احکام کیفری تنظیم می‌کند.")
        add_rel(conn, "AIM79-1393", "QMA-1392", "implements", "آیین‌نامه ماده ۷۹ قانون مجازات اسلامی، خدمات عمومی رایگان و مجازات‌های جایگزین حبس را اجرا می‌کند.")
        add_rel(conn, "AIWET-1397-636", "QHBE-1353", "cites", "آیین‌نامه تالاب‌ها با چارچوب عمومی حفاظت و بهسازی محیط زیست ارتباط موضوعی دارد.")
        add_rel(conn, "AICOMP-772-1393", "QMA-1392", "implements", "آیین‌نامه اجرای مجازات‌های تکمیلی در اجرای ماده ۲۳ قانون مجازات اسلامی است.")
        add_rel(conn, "AIECJ-915-1395", "QASAF-1390", "implements", "آیین‌نامه شرایط قضات مفاسد اقتصادی در اجرای احکام قانون ارتقاء سلامت نظام اداری و مقابله با فساد است.")
        add_rel(conn, "AIPARD-763-1387", "QMA-1392", "cites", "آیین‌نامه کمیسیون عفو و تخفیف مجازات در چارچوب احکام قانون مجازات اسلامی اجرا می‌شود.")
        add_rel(conn, "AIQK-27-1395", "QMK-1392", "implements", "آیین‌نامه ماده ۲۷، حکم قانون مبارزه با قاچاق کالا و ارز درباره کالاهای سلامت‌محور را اجرا می‌کند.")
        add_rel(conn, "DIQK-AUCTION-1402", "AIQK-5556-1401", "cites", "دستورالعمل حراج عمومی در شبکه اجرای مواد ۵۵ و ۵۶ قانون قاچاق کالا و ارز قرار دارد.")
        add_rel(conn, "AIQK-59-1402", "QMK-1392", "implements", "مصادیق ماده ۵۹ در اجرای قانون مبارزه با قاچاق کالا و ارز ثبت شده است.")
        add_rel(conn, "AILEGAL-918-1398", "AICOMP-772-1393", "cites", "آیین‌نامه ۱۳۹۸ در نحوه اجرای مجازات‌های تکمیلی موضوع ماده ۲۳ به آیین‌نامه ۱۳۹۳ ارجاع می‌دهد.")
        add_rel(conn, "AILEGAL-918-1398", "AIM79-1393", "cites", "آیین‌نامه ۱۳۹۸ نحوه اجرای خدمات عمومی رایگان را به آیین‌نامه اجرایی ماده ۷۹ مرتبط می‌کند.")
        add_rel(conn, "AILEGAL-918-1398", "AIME-1397", "cites", "آیین‌نامه ۱۳۹۸ اجرای آزادی تحت نظارت تجهیزات الکترونیکی را به آیین‌نامه مراقبت‌های الکترونیکی مرتبط می‌کند.")
        add_rel(conn, "CIR-POL-730-1399", "QADK-1392", "cites", "بخشنامه اجرای قانون جرم سیاسی به مقررات آیین دادرسی کیفری و رسیدگی دادگاه‌ها ارجاع دارد.")
        add_rel(conn, "CIR-342-721-1395", "QADK-1392", "cites", "بخشنامه تبصره الحاقی ماده ۳۴۲ در چارچوب آیین دادرسی کیفری و مطالبه دیه از دولت اجرا می‌شود.")
        add_rel(conn, "DRUG-LIST-1338", "QMM-1367", "cites", "فهرست تاریخی مواد مخدر مبنای مقررات قدیمی و مقایسه تاریخی قانون مبارزه با مواد مخدر است.")
        add_rel(conn, "DCC-722-1397", "QADK-1392", "implements", "دستورالعمل کنترل مجرمان حرفه‌ای و سابقه‌دار در اجرای قواعد آیین دادرسی کیفری و پایش کیفری است.")
        conn.commit()
        print(f"loaded user submissions: {len(DOCUMENTS)} documents / {sum(d['article_count'] for d in DOCUMENTS)} articles")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
