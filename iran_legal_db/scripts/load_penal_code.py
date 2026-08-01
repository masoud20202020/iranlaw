# -*- coding: utf-8 -*-
"""
بارگذاری قانون مجازات اسلامی ۱۳۹۲ (متن کامل بخش‌های اصلی) به دیتابیس.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "seed"))

from schema import get_connection
from importer import (
    get_or_create_document, add_article, add_relation,
    add_tag, link_document_tag, link_document_topic,
)
from penal_code_book1 import PENAL_BOOK1
from penal_code_book2 import PENAL_BOOK2
from penal_code_book3 import PENAL_BOOK3
from penal_code_book4 import PENAL_BOOK4, PENAL_EXTRA_ARTICLES


def to_persian_num(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def main():
    conn = get_connection()

    # ۱) حذف نسخه قبلی قانون مجازات (برای بارگذاری تمیز)
    old = conn.execute("SELECT id FROM documents WHERE reference_code='QMA-1392'").fetchone()
    if old:
        conn.execute("DELETE FROM articles_fts WHERE document_id=?", (old["id"],))
        conn.execute("DELETE FROM articles WHERE document_id=?", (old["id"],))
        conn.execute("DELETE FROM relations WHERE from_document_id=? OR to_document_id=?", (old["id"], old["id"]))
        conn.execute("DELETE FROM documents WHERE id=?", (old["id"],))
    conn.commit()

    # ۲) ایجاد سند
    penal_id = get_or_create_document(
        conn,
        title="قانون مجازات اسلامی (مصوب ۱۳۹۲/۲/۱، با آخرین اصلاحات)",
        short_title="ق.م.ا.",
        type_code="law",
        issuing_authority="مجلس شورای اسلامی",
        ratification_date="2013-04-21",
        effective_date="2013-07-22",  # ۹۰ روز پس از انتشار
        publication_date="2013-05-21",
        reference_code="QMA-1392",
        notes="مصوب ۱۳۹۲/۰۲/۰۱ با تأیید شورای نگهبان. شامل پنج کتاب: کلیات، حدود، قصاص، دیات، تعزیرات. قانون مجازات اسلامی ۱۳۷۰ از تاریخ اجرای این قانون نسخ گردیده است."
    )

    tags = ["کیفری", "قانون مادر", "حدود", "قصاص", "دیات", "تعزیرات"]
    for t in tags:
        tid = add_tag(conn, t)
        link_document_tag(conn, penal_id, tid)
    link_document_topic(conn, penal_id, "حقوق کیفری")

    # ۳) بارگذاری مواد
    all_articles = {}
    for art_list in (PENAL_BOOK1, PENAL_BOOK2, PENAL_BOOK3, PENAL_BOOK4, PENAL_EXTRA_ARTICLES):
        for no, text in art_list:
            all_articles[no] = text

    # یادداشت اینکه این بخش مواد اصلی/کلیدی از کل قانون است
    notes_general = "قانون مجازات اسلامی در مجموع ۷۲۸ ماده می‌باشد؛ در این نسخه، حدود ۲۰۰ ماده کلیدی از هر پنج کتاب (کلیات، حدود، قصاص، دیات، تعزیرات) به‌طور کامل درج شده است. برای مشاهده همه ۷۲۸ ماده می‌توانید از منابع رسمی docs/sources.md به ساختار بیفزایید."

    for no in sorted(all_articles.keys()):
        add_article(
            conn, penal_id,
            article_no=to_persian_num(no),
            text=all_articles[no],
            article_key=f"QMA:{no}",
            version_no=1, is_current=1,
            effective_date="2013-07-22",
            source_note="قانون مجازات اسلامی ۱۳۹۲ – سامانه ملی قوانین و مقررات",
        )

    # ۴) ارتباطات
    const = conn.execute("SELECT id FROM documents WHERE reference_code='QA-1358'").fetchone()
    if const:
        add_relation(conn, penal_id, "cites", const["id"],
                     description="ماده ۱ ق.م.ا. مستند به اصل ۱۶۷ قانون اساسی. همچنین اصول ۳۲ تا ۳۹ (برائت، ممنوعیت شکنجه، منع تبعید، ...) مورد استناد است.")
    civ = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()
    if civ:
        add_relation(conn, penal_id, "cites", civ["id"],
                     description="ارجاعات متقابل با قانون مدنی در مباحث مسئولیت، دیه و اهلیت.")
    crimproc = conn.execute("SELECT id FROM documents WHERE reference_code='QADK-1392'").fetchone()
    if crimproc:
        add_relation(conn, penal_id, "implements", crimproc["id"],
                     description="آیین دادرسی کیفری ۱۳۹۲ آیین رسیدگی به جرایم مقرر در این قانون است.")

    # ۵) آمار
    conn.commit()
    total_docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    total_arts = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
    penal_arts = conn.execute("SELECT COUNT(*) c FROM articles WHERE document_id=?", (penal_id,)).fetchone()["c"]
    rels = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]

    print(f"[OK] قانون مجازات اسلامی ۱۳۹۲ با {penal_arts} ماده در دیتابیس بارگذاری شد.")
    print(f"     مجموع اسناد: {total_docs} | مجموع مواد: {total_arts} | ارتباطات: {rels}")
    print(f"     {notes_general}")
    conn.close()


if __name__ == "__main__":
    main()
