# -*- coding: utf-8 -*-
"""Load cross-domain selected unified rulings and Divan rulings."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "data", "seed")]

from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic  # noqa: E402
from schema import get_connection  # noqa: E402
from judicial_precedents_phase1 import DIVAN_RULINGS_PHASE1, UNIFIED_RULINGS_PHASE1  # noqa: E402
from judicial_precedents_phase2 import DIVAN_RULINGS_PHASE2, UNIFIED_RULINGS_PHASE2  # noqa: E402
from judicial_precedents_phase3 import DIVAN_RULINGS_PHASE3, UNIFIED_RULINGS_PHASE3  # noqa: E402
from judicial_precedents_phase4 import DIVAN_RULINGS_PHASE4, UNIFIED_RULINGS_PHASE4  # noqa: E402
from judicial_precedents_phase5 import DIVAN_RULINGS_PHASE5, UNIFIED_RULINGS_PHASE5  # noqa: E402
from judicial_precedents_phase6 import DIVAN_RULINGS_PHASE6, UNIFIED_RULINGS_PHASE6  # noqa: E402
from judicial_precedents_phase7 import DIVAN_RULINGS_PHASE7, UNIFIED_RULINGS_PHASE7  # noqa: E402
from judicial_precedents_phase8 import DIVAN_RULINGS_PHASE8, UNIFIED_RULINGS_PHASE8  # noqa: E402
from judicial_precedents_phase9 import DIVAN_RULINGS_PHASE9, UNIFIED_RULINGS_PHASE9  # noqa: E402
from judicial_precedents_full_text import FULL_TEXT_OVERRIDES  # noqa: E402

UNIFIED_RULINGS = [*UNIFIED_RULINGS_PHASE1, *UNIFIED_RULINGS_PHASE2, *UNIFIED_RULINGS_PHASE3, *UNIFIED_RULINGS_PHASE4, *UNIFIED_RULINGS_PHASE5, *UNIFIED_RULINGS_PHASE6, *UNIFIED_RULINGS_PHASE7, *UNIFIED_RULINGS_PHASE8, *UNIFIED_RULINGS_PHASE9]
DIVAN_RULINGS = [*DIVAN_RULINGS_PHASE1, *DIVAN_RULINGS_PHASE2, *DIVAN_RULINGS_PHASE3, *DIVAN_RULINGS_PHASE4, *DIVAN_RULINGS_PHASE5, *DIVAN_RULINGS_PHASE6, *DIVAN_RULINGS_PHASE7, *DIVAN_RULINGS_PHASE8, *DIVAN_RULINGS_PHASE9]


def one(conn, query, value):
    row = conn.execute(query, (value,)).fetchone()
    return row["id"] if row else None


def ensure_topic(conn, name):
    conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES(?)", (name,))


def upsert_document(conn, item, type_code, authority, notes):
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", item["ref"])
    if not did:
        did = get_or_create_document(
            conn,
            title=item["title"],
            short_title=item["title"],
            type_code=type_code,
            issuing_authority=authority,
            status_code="in_force",
            ratification_date=item["date"],
            effective_date=item["date"],
            reference_code=item["ref"],
            notes=notes,
        )
    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            item["title"],
            item["title"],
            one(conn, "SELECT id FROM document_types WHERE code=?", type_code),
            one(conn, "SELECT id FROM authorities WHERE name_fa=?", authority),
            one(conn, "SELECT id FROM statuses WHERE code=?", "in_force"),
            item["date"],
            item["date"],
            notes,
            did,
        ),
    )
    return did


def clear_owned(conn, did):
    for query in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(query, (did,))


def attach_common(conn, did, item, topics, base_tags):
    for topic in topics:
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in sorted(set(base_tags) | set(item.get("tags", []))):
        link_document_tag(conn, did, add_tag(conn, tag))


def effective_item(item):
    override = FULL_TEXT_OVERRIDES.get(item["ref"])
    if not override:
        return item
    merged = dict(item)
    merged["text"] = override["text"]
    merged["source"] = override.get("source", item.get("source"))
    merged["article_notes"] = override.get("article_notes")
    merged["document_notes"] = override.get("document_notes")
    merged["tags"] = sorted(set(item.get("tags", [])) | set(override.get("tags", [])))
    return merged


def add_ruling_row(conn, did, item):
    return add_article(
        conn,
        did,
        article_no="رأی",
        article_key=f"{item['ref']}:ruling",
        version_no=1,
        is_current=1,
        effective_date=item["date"],
        text=item["text"],
        source_note=item["source"],
        notes=item.get("article_notes", "گزیده/خلاصه ساختاری منبع‌دار؛ رونوشت لفظ‌به‌لفظ کامل رأی نیست."),
    )


def add_target_relations(conn, from_doc, item, relation_type="interprets"):
    for ref in item.get("targets", []):
        target = one(conn, "SELECT id FROM documents WHERE reference_code=?", ref)
        if target:
            add_relation(
                conn,
                from_doc,
                relation_type,
                target,
                description=f"پیوند موضوعی/تفسیری رأی {item['ref']} با سند {ref}.",
            )


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        loaded = {}
        for raw_item in UNIFIED_RULINGS:
            item = effective_item(raw_item)
            did = upsert_document(
                conn,
                item,
                "unified_ruling",
                "دیوان عالی کشور",
                item.get("document_notes", "بسته آرای وحدت رویه و دیوان عدالت اداری ـ مرحله نخست؛ گزیده/خلاصه منبع‌دار."),
            )
            loaded[item["ref"]] = did
            clear_owned(conn, did)
            attach_common(
                conn,
                did,
                item,
                topics=("رویه قضایی و آراء", "آیین دادرسی کیفری", "آیین دادرسی مدنی"),
                base_tags=("رأی وحدت رویه", "دیوان عالی کشور", "رویه قضایی"),
            )
            add_ruling_row(conn, did, item)
            add_target_relations(conn, did, item, "interprets")

        for raw_item in DIVAN_RULINGS:
            item = effective_item(raw_item)
            did = upsert_document(
                conn,
                item,
                "divan_ruling",
                "هیأت عمومی دیوان عدالت اداری",
                item.get("document_notes", "بسته آرای وحدت رویه و دیوان عدالت اداری ـ مرحله نخست؛ گزیده/خلاصه منبع‌دار."),
            )
            loaded[item["ref"]] = did
            clear_owned(conn, did)
            attach_common(
                conn,
                did,
                item,
                topics=("رویه قضایی و آراء", "حقوق اداری"),
                base_tags=("رأی دیوان عدالت اداری", "هیأت عمومی دیوان عدالت اداری", "ابطال مقرره"),
            )
            add_ruling_row(conn, did, item)
            add_target_relations(conn, did, item, "cites")
            qda = one(conn, "SELECT id FROM documents WHERE reference_code=?", "QDA-1392")
            if qda:
                add_relation(conn, did, "cites", qda, description="رأی صادره از هیأت عمومی دیوان عدالت اداری و تابع قانون دیوان عدالت اداری.")

        conn.commit()
        print("loaded judicial precedents", len(loaded), "documents")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
