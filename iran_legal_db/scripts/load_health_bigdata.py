#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load the additional health/medicine documents from the bigdata commit.

The loader is intentionally independent from ``load_health_law.py``.  It owns the
20 new stable reference codes in ``data/seed/health_bigdata.py`` and can be rerun
without duplicating documents, articles, FTS rows, tags, topics, or its relations.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "data" / "seed")]

from health_bigdata import DOCUMENTS  # noqa: E402
from importer import (  # noqa: E402
    add_article,
    add_relation,
    add_tag,
    get_or_create_document,
    link_document_tag,
    link_document_topic,
)
from schema import get_connection  # noqa: E402


EXECUTIVE_AUTHORITIES = {
    "هیئت وزیران",
    "وزارت بهداشت، درمان و آموزش پزشکی",
}
JUDICIAL_AUTHORITIES = {"رئیس قوه قضائیه"}


def one(conn, sql: str, value: str):
    row = conn.execute(sql, (value,)).fetchone()
    return row["id"] if row else None


def ensure_authority(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (name,)).fetchone()
    if row:
        return row["id"]
    if name in JUDICIAL_AUTHORITIES:
        authority_type = "judicial"
    elif name in EXECUTIVE_AUTHORITIES:
        authority_type = "executive"
    else:
        authority_type = "legislative"
    cur = conn.execute(
        "INSERT INTO authorities(name_fa, authority_type) VALUES(?, ?)",
        (name, authority_type),
    )
    return cur.lastrowid


def upsert_document(conn, doc: dict) -> int:
    authority_id = ensure_authority(conn, doc["authority"])
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", doc["ref"])
    if not did:
        did = get_or_create_document(
            conn,
            title=doc["title"],
            short_title=doc["short"],
            type_code=doc["type_code"],
            issuing_authority=doc["authority"],
            status_code=doc["status_code"],
            ratification_date=doc["date"],
            effective_date=doc["date"],
            reference_code=doc["ref"],
            notes=doc["notes"],
        )
    status_id = one(conn, "SELECT id FROM statuses WHERE code=?", doc["status_code"])
    type_id = one(conn, "SELECT id FROM document_types WHERE code=?", doc["type_code"])
    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            doc["title"],
            doc["short"],
            type_id,
            authority_id,
            status_id,
            doc["date"],
            doc["date"],
            doc["notes"],
            did,
        ),
    )
    return did


def clear_owned(conn, document_id: int) -> None:
    # Relations are owned by their source document.  We never delete incoming
    # relations created by another package.
    for sql in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(sql, (document_id,))


def attach_labels(conn, document_id: int, doc: dict) -> None:
    topics = {"حقوق سلامت، پزشکی و دارو"}
    if doc["ref"] in {"AIFU-1390", "AIFAC-1390", "QASAF-1390", "QEVB-1368"}:
        topics.add("حقوق اداری")
    if doc["ref"] in {"AICPN-1388", "QCP-1388"}:
        topics.add("حقوق کار و تأمین اجتماعی")
    if doc["ref"] in {"QDRA-1359", "AIMH-1398"}:
        topics.add("حقوق کیفری")
    if doc["ref"] == "DMEW-1386":
        topics.add("حقوق محیط زیست")

    for topic in sorted(topics):
        conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES(?)", (topic,))
        link_document_topic(conn, document_id, topic)

    common = {"حقوق سلامت", "پزشکی و دارو"}
    for tag in sorted(common | set(doc.get("tags", ()))):
        link_document_tag(conn, document_id, add_tag(conn, tag))


def add_rows(conn, document_id: int, doc: dict) -> None:
    historical_only = bool(doc.get("historical_only"))
    for row in doc["rows"]:
        effective_date = doc["date"]
        expiry_date = doc.get("expiry_date") if historical_only else None
        add_article(
            conn,
            document_id,
            article_no=row["article_no"],
            article_key=f"{doc['ref']}:{row['article_key_suffix']}",
            version_no=1,
            is_current=0 if historical_only else 1,
            effective_date=effective_date,
            expiry_date=expiry_date,
            text=row["text"],
            source_note=(
                f"{doc['source_url']}؛ متن خام commit در "
                f"data/بهداشت_و_درمان/{doc['raw_dir']}/مشاهده_متن_قانون.txt"
            ),
            notes=(
                "استخراج ماده‌به‌ماده توسط build_health_bigdata_seeds.py انجام شده است؛ "
                "رسم‌الخط متن منبع تا حد پاک‌سازی نویسه‌های عربی/فاصله حفظ شده است."
            ),
        )


def add_rel(conn, from_ref: str, to_ref: str, relation_type: str, description: str) -> None:
    from_id = one(conn, "SELECT id FROM documents WHERE reference_code=?", from_ref)
    to_id = one(conn, "SELECT id FROM documents WHERE reference_code=?", to_ref)
    if not from_id or not to_id:
        raise RuntimeError(f"relation target missing: {from_ref} -> {to_ref}")
    # Exact replacement makes relations idempotent even when the source document
    # belongs to an older package (for example QMM-1367 -> QDRA-1359).
    conn.execute(
        """
        DELETE FROM relations
        WHERE from_document_id=? AND to_document_id=? AND relation_type=? AND description=?
        """,
        (from_id, to_id, relation_type, description),
    )
    add_relation(
        conn,
        from_id,
        relation_type,
        to_id,
        description=description,
    )


def load_document(conn, doc: dict) -> None:
    did = upsert_document(conn, doc)
    clear_owned(conn, did)
    attach_labels(conn, did, doc)
    add_rows(conn, did, doc)


def load_relations(conn) -> None:
    # The first import briefly used an outgoing relation from the existing
    # QMM-1367 document.  Remove that legacy direction so the older drug-law
    # verifier (which owns the exact relation count of QMM-1367) remains stable.
    old_from = one(conn, "SELECT id FROM documents WHERE reference_code=?", "QMM-1367")
    old_to = one(conn, "SELECT id FROM documents WHERE reference_code=?", "QDRA-1359")
    if old_from and old_to:
        conn.execute(
            """
            DELETE FROM relations
            WHERE from_document_id=? AND to_document_id=?
              AND relation_type='abrogates'
              AND description=?
            """,
            (
                old_from,
                old_to,
                "قانون مبارزه با مواد مخدر ۱۳۶۷ جایگزین و ناسخ قانون/لایحه مواد مخدر ۱۳۵۹ شده است.",
            ),
        )

    relations = [
        ("AIRDI-1368", "QMDA-1334", "implements", "آیین‌نامه ساخت و ورود دارو در اجرای ماده ۲۴ قانون مقررات امور پزشکی و دارویی ثبت شده است."),
        ("AIRDI-1368", "QMBH-1364", "cites", "آیین‌نامه ساخت و ورود دارو به قانون تشکیلات و وظایف وزارت بهداشت نیز استناد می‌کند."),
        ("AIDR-1393", "QMDA-1334", "implements", "آیین‌نامه ثبت دارو بر پایه کمیسیون‌های ماده ۲۰ قانون مقررات امور پزشکی و دارویی تنظیم شده است."),
        ("AIDR-1393", "QMBH-1364", "cites", "سازمان غذا و دارو و ساختار وزارت بهداشت، مرجع اجرای آیین‌نامه ثبت دارو هستند."),
        ("AIFU-1390", "QMBH-1364", "implements", "آیین‌نامه مالی و معاملاتی، امور مالی دانشگاه‌ها و مؤسسات وابسته به وزارت بهداشت را تنظیم می‌کند."),
        ("AIFAC-1390", "QMBH-1364", "cites", "آیین‌نامه استخدامی اعضای هیئت علمی در ساختار دانشگاه‌های علوم پزشکی و وزارت بهداشت اجرا می‌شود."),
        ("AIFAC-1390", "QCSM-1386", "cites", "مقررات استخدامی اعضای هیئت علمی با قواعد عمومی مدیریت خدمات کشوری ارتباط دارد."),
        ("AICPN-1388", "QCP-1388", "implements", "این آیین‌نامه در اجرای قانون ارتقاء بهره‌وری کارکنان بالینی نظام سلامت است."),
        ("QCP-1388", "QMBH-1364", "cites", "قانون بهره‌وری، اجرای سیاست‌های نیروی انسانی و خدمات بالینی وزارت بهداشت را هدف قرار می‌دهد."),
        ("AIMED-1393", "QMBH-1364", "cites", "رسیدگی پزشکی مشمولان خدمت وظیفه با وزارت بهداشت و شبکه کارشناسی پزشکی ارتباط دارد."),
        ("AIBRAND-1328", "QMKAB-1346", "implements", "آیین‌نامه علائم صنعتی با قواعد تولید و عرضه مواد خوردنی، آشامیدنی، آرایشی و بهداشتی مرتبط است."),
        ("AIBRAND-1328", "QMDA-1334", "cites", "اقلام دارویی و پزشکی موضوع آیین‌نامه در چارچوب مقررات امور پزشکی و دارویی قرار می‌گیرند."),
        ("AIMH-1398", "QADK-1392", "implements", "آیین‌نامه نگهداری و درمان مجانین در اجرای مقررات آیین دادرسی کیفری درباره متهمان مجنون است."),
        ("AIMH-1398", "QLMO-1372", "cites", "درمان و تشخیص وضعیت روانی مجانین با وظایف کارشناسی پزشکی قانونی ارتباط دارد."),
        ("BJC-1400", "QMBH-1364", "cites", "اساسنامه بیمارستان دادگستری در حوزه خدمات درمانی و نظارت تخصصی با وزارت بهداشت مرتبط است."),
        ("AIEPO-1396-11-04", "QMBH-1364", "implements", "اساسنامه اورژانس کشور سازمانی وابسته به وزارت بهداشت ایجاد می‌کند."),
        ("AIEPO-1396-11-28", "QMBH-1364", "implements", "نسخه متأخر اساسنامه اورژانس کشور سازمانی وابسته به وزارت بهداشت ایجاد می‌کند."),
        ("AIEPO-1396-11-28", "AIEPO-1396-11-04", "amends", "نسخه ۱۳۹۶/۱۱/۲۸ متن متفاوت و متأخر اساسنامه اورژانس کشور در داده خام است."),
        ("DMEW-1386", "QMP-1383", "implements", "ضوابط پسماند پزشکی در چارچوب قانون مدیریت پسماندها اجرا می‌شود."),
        ("DMEW-1386", "QMBH-1364", "cites", "مدیریت اجرایی پسماند پزشکی با تکالیف وزارت بهداشت و مراکز درمانی ارتباط دارد."),
        ("DMEW-1386", "AIHOSP-1383", "cites", "ضوابط پسماند پزشکی برای بیمارستان‌ها و مراکز درمانی موضوع آیین‌نامه بیمارستان‌ها کاربرد دارد."),
        ("QASAF-1390", "QCSM-1386", "cites", "قانون ارتقاء سلامت نظام اداری، دستگاه‌های موضوع قانون مدیریت خدمات کشوری را دربرمی‌گیرد."),
        ("QASAF-1390", "QSNM-1383", "cites", "سازمان نظام پزشکی از نمونه مؤسسات خصوصی حرفه‌ای عهده‌دار خدمات عمومی در قانون سلامت اداری است."),
        ("QEVB-1368", "QMBH-1364", "cites", "قانون تخلیه ساختمان‌ها بخشی از اموال و اماکن وزارت بهداشت و مؤسسات آموزشی آن را موضوع حکم قرار می‌دهد."),
        ("QVET-1350", "QMKAB-1346", "cites", "بهداشت فرآورده‌های خام دامی با قواعد بهداشت مواد غذایی و آشامیدنی ارتباط موضوعی دارد."),
        ("QLOP-1366", "AIMO-1363", "cites", "قانون محل مطب، مبنای کاربری محل فعالیت پزشکان و آیین‌نامه تأسیس مطب است."),
        ("QHAP-1397", "QMDA-1334", "amends", "ماده ۵ قانون ممنوعیت تبلیغات، ماده ۵ قانون مقررات امور پزشکی و دارویی را لغو می‌کند."),
        ("QHAP-1397", "QMKAB-1346", "cites", "ممنوعیت تبلیغات محصولات خوراکی، آرایشی و بهداشتی با قانون مواد خوردنی مرتبط است."),
        ("QDRA-1359", "QMM-1367", "repealed_by", "قانون تاریخی مواد مخدر ۱۳۵۹ با اجرای قانون مبارزه با مواد مخدر ۱۳۶۷ جایگزین و منسوخ شد."),
        ("DMCAP-1400", "QMBH-1364", "cites", "مصوبه افزایش ظرفیت پزشکی، وزارت بهداشت و دانشگاه‌های علوم پزشکی را مکلف به اجرای افزایش ظرفیت می‌کند."),
        ("DMCAP-1400", "QCSM-1386", "cites", "اجرای ظرفیت پذیرش پزشکی با برنامه‌ریزی نیروی انسانی و ساختار استخدامی دولت ارتباط دارد."),
    ]
    for relation in relations:
        add_rel(conn, *relation)


def main() -> None:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        for doc in DOCUMENTS:
            load_document(conn, doc)
        load_relations(conn)
        conn.commit()
        total_rows = sum(doc["article_count"] for doc in DOCUMENTS)
        print(f"loaded health bigdata: {len(DOCUMENTS)} documents / {total_rows} articles")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
