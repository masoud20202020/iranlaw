# -*- coding: utf-8 -*-
"""بارگذاری نمونه‌های انواع سند به دیتابیس."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "seed"))

from schema import get_connection
from importer import (
    get_or_create_document, bulk_add_articles, add_relation,
    add_tag, link_document_tag, link_document_topic,
)
from other_docs import REGULATIONS, CIRCULARS, UNIFIED_RULINGS, ADVISORY_OPINIONS, DIVAN_RULINGS, TREATIES


def add_doc_list(conn, doc_list, tags=None, topics=None):
    tags = tags or []
    topics = topics or []
    for d in doc_list:
        # حذف قبلی در صورت وجود تا بارگذاری تکراری نباشد
        existing = conn.execute("SELECT id FROM documents WHERE reference_code=?", (d["reference_code"],)).fetchone()
        if existing:
            conn.execute("DELETE FROM articles WHERE document_id=?", (existing["id"],))
            conn.execute("DELETE FROM articles_fts WHERE document_id=?", (existing["id"],))
            conn.execute("DELETE FROM relations WHERE from_document_id=? OR to_document_id=?", (existing["id"], existing["id"]))
            conn.execute("DELETE FROM documents WHERE id=?", (existing["id"],))

        doc_id = get_or_create_document(
            conn,
            title=d["title"],
            short_title=d.get("short_title"),
            type_code=d["type_code"],
            issuing_authority=d["authority"],
            ratification_date=d.get("date"),
            effective_date=d.get("date"),
            reference_code=d["reference_code"],
            notes=d.get("notes"),
        )
        for t in tags:
            tid = add_tag(conn, t)
            link_document_tag(conn, doc_id, tid)
        for t in topics:
            link_document_topic(conn, doc_id, t)

        bulk_add_articles(conn, doc_id, [
            {"article_no": no, "text": text} for (no, text) in d["articles"]
        ])
        yield doc_id, d


def main():
    conn = get_connection()

    # ۱) آیین‌نامه‌ها
    for did, d in add_doc_list(conn, REGULATIONS,
                                tags=["آیین‌نامه"],
                                topics=["حقوق مدنی", "حقوق خانواده", "حقوق کار"]):
        pass

    # ۲) بخشنامه‌ها
    for did, d in add_doc_list(conn, CIRCULARS,
                                tags=["بخشنامه"],
                                topics=["حقوق خانواده", "حقوق کیفری", "آیین دادرسی مدنی"]):
        pass

    # ۳) آرای وحدت رویه → ارتباط تفسیری با قانون مدنی/تجارت/...
    civil_id = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()["id"]
    comm_id = conn.execute("SELECT id FROM documents WHERE reference_code='QT-1311'").fetchone()["id"]
    for did, d in add_doc_list(conn, UNIFIED_RULINGS,
                                tags=["رأی وحدت رویه"],
                                topics=["حقوق خانواده", "حقوق تجارت", "حقوق مدنی", "حقوق کیفری"]):
        # رابطه پیش‌فرض با قانون مدنی (در دیتای واقعی باید ماده خاص را هم پیدا کنید)
        short = d.get("short_title", "")
        if "طلاق" in d["title"] or "مهریه" in d["title"] or "ارث" in d["title"] or "زوجه" in d["title"]:
            add_relation(conn, did, "interprets", civil_id, description="تفسیر موادی از قانون مدنی")
        if "چک" in d["title"]:
            add_relation(conn, did, "interprets", comm_id, description="تفسیر ماده ۳۱۰ قانون تجارت (چک)")

    # ۴) نظریات مشورتی
    for did, d in add_doc_list(conn, ADVISORY_OPINIONS,
                                tags=["نظریه مشورتی"],
                                topics=["حقوق مدنی", "حقوق خانواده", "حقوق تجارت"]):
        add_relation(conn, did, "interprets", civil_id, description="نظریه مشورتی در خصوص موادی از قانون مدنی / مسئولیت مدنی")

    # ۵) آرای دیوان عدالت اداری (اغلب بخشنامه/آیین‌نامه را ابطال می‌کنند)
    for did, d in add_doc_list(conn, DIVAN_RULINGS,
                                tags=["دیوان عدالت اداری"],
                                topics=["حقوق اداری", "حقوق عمومی"]):
        pass

    # ۶) معاهدات
    for did, d in add_doc_list(conn, TREATIES,
                                tags=["معاهده", "بین‌الملل"],
                                topics=["حقوق بین‌الملل"]):
        pass

    conn.commit()

    # آمار
    print("=== آمار نهایی ===")
    for row in conn.execute("""SELECT dt.name_fa type, COUNT(*) c FROM documents d
                               JOIN document_types dt ON dt.id=d.type_id
                               GROUP BY dt.id ORDER BY c DESC"""):
        print(f"  {row['type']:25s} {row['c']}")
    print("مجموع اسناد:", conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"])
    print("مجموع مواد:", conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"])
    print("مجموع ارتباطات:", conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"])
    conn.close()


if __name__ == "__main__":
    main()
