# -*- coding: utf-8 -*-
"""بارگذاری کامل آیین دادرسی مدنی (۱۳۷۹) و آیین دادرسی کیفری (۱۳۹۲) به دیتابیس."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "seed"))

from schema import get_connection
from importer import get_or_create_document, add_article, add_relation, add_tag, link_document_tag, link_document_topic
from civil_procedure import CIVIL_PROCEDURE_ALL
from criminal_procedure import CRIMINAL_PROCEDURE_ALL
try:
    from criminal_procedure_user_source import SOURCE_NOTE_BY_ARTICLE
except ImportError:  # pragma: no cover - legacy seed-only mode
    SOURCE_NOTE_BY_ARTICLE = {}


def to_persian_num(n) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def load(conn, *, title, short_title, ref_code, authority, rat, eff, articles, tags, topics, note, rel_docs):
    existing = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref_code,)).fetchone()
    if existing:
        doc_id = existing["id"]
        conn.execute("DELETE FROM articles_fts WHERE document_id=?", (doc_id,))
        conn.execute("DELETE FROM articles WHERE document_id=?", (doc_id,))
        # Only outgoing relations are owned by this loader. Incoming document-level
        # relations from thematic packages must survive reloading the procedure texts.
        conn.execute("DELETE FROM relations WHERE from_document_id=?", (doc_id,))
        conn.execute("DELETE FROM document_tags WHERE document_id=?", (doc_id,))
        conn.execute("DELETE FROM document_topics WHERE document_id=?", (doc_id,))
    else:
        doc_id = get_or_create_document(conn,
                                       title=title, short_title=short_title,
                                       type_code="law", issuing_authority=authority,
                                       ratification_date=rat, effective_date=eff,
                                       reference_code=ref_code, notes=note)
    for t in tags:
        tid = add_tag(conn, t); link_document_tag(conn, doc_id, tid)
    for t in topics:
        link_document_topic(conn, doc_id, t)
    cnt = 0
    for no, text in articles:
        if not isinstance(no, int): continue
        add_article(conn, doc_id,
                    article_no=to_persian_num(no),
                    text=text,
                    article_key=f"{ref_code}:{no}",
                    version_no=1, is_current=1,
                    effective_date=eff,
                    source_note=SOURCE_NOTE_BY_ARTICLE.get(no, note))
        cnt += 1
    # relations
    for rel_type, target_code, desc in rel_docs:
        tgt = conn.execute("SELECT id FROM documents WHERE reference_code=?", (target_code,)).fetchone()
        if tgt:
            add_relation(conn, doc_id, rel_type, tgt["id"], description=desc)
    conn.commit()
    return doc_id, cnt


def main():
    conn = get_connection()
    # آیین دادرسی مدنی
    cid, ccnt = load(
        conn,
        title="قانون آیین دادرسی دادگاه‌های عمومی و انقلاب در امور مدنی (با اصلاحات بعدی)",
        short_title="ق.آ.د.م.",
        ref_code="QADM-1379",
        authority="مجلس شورای اسلامی",
        rat="2000-04-09",
        eff="2000-04-09",
        articles=CIVIL_PROCEDURE_ALL,
        tags=["آیین دادرسی", "مدنی", "قانون مادر"],
        topics=["آیین دادرسی مدنی"],
        note="مصوب ۱۳۷۹/۰۱/۲۱ با اصلاحات بعدی، آیین دادرسی مدنی در بر گیرنده مقررات صلاحیت، احضار، رسیدگی، احکام، تجدیدنظر، فرجام، اجرای احکام مدنی، داوری، امور حسبی، دستور موقت و تأمین دلیل است.",
        rel_docs=[
            ("cites", "QA-1358", "مبتنی بر اصل ۳۴ و ۳۵ قانون اساسی (حق دادخواهی، حق وکیل)"),
            ("implements", "QM-1307", "آیین شکلی رسیدگی به دعاوی مدنی در اجرای حقوق مدنی"),
        ],
    )
    print(f"[OK] آیین دادرسی مدنی: {ccnt} ماده (سند {cid})")

    # آیین دادرسی کیفری
    kid, kcnt = load(
        conn,
        title="قانون آیین دادرسی کیفری (مصوب ۱۳۹۲، لازم‌الاجرا ۱۳۹۴)",
        short_title="ق.آ.د.ک.",
        ref_code="QADK-1392",
        authority="مجلس شورای اسلامی",
        rat="2014-02-16",
        eff="2015-06-22",
        articles=CRIMINAL_PROCEDURE_ALL,
        tags=["آیین دادرسی", "کیفری", "قانون مادر"],
        topics=["آیین دادرسی کیفری"],
        note="مصوب ۱۳۹۲/۱۲/۴، لازم‌الاجرا از ۱۳۹۴/۰۴/۰۱؛ مواد ۱ تا ۳۱۷ با متن بخش‌های ارسالی کاربر از صفحات نوین‌لاو (منابع در source_note ماده‌ها) تنقیح اولیه شده‌اند؛ مواد ۳۱۸ تا ۵۷۰ همچنان از بذر پایه پروژه هستند و برای استناد رسمی باید با روزنامه رسمی مقابله شوند.",
        rel_docs=[
            ("cites", "QA-1358", "مبتنی بر اصول ۳۲ تا ۳۹ قانون اساسی (برائت، منع شکنجه، حق وکیل، علنی بودن محاکمه)"),
            ("implements", "QMA-1392", "آیین شکلی رسیدگی به جرایم مقرر در قانون مجازات اسلامی"),
        ],
    )
    print(f"[OK] آیین دادرسی کیفری: {kcnt} ماده (سند {kid})")

    n_docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    n_arts = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
    rels = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]
    cid_n = conn.execute("SELECT COUNT(*) c FROM articles WHERE document_id=?", (cid,)).fetchone()["c"]
    kid_n = conn.execute("SELECT COUNT(*) c FROM articles WHERE document_id=?", (kid,)).fetchone()["c"]
    print(f"\n=== مجموع ===")
    print(f"اسناد: {n_docs}  |  مجموع مواد: {n_arts}  |  ارتباطات: {rels}")
    print(f"قانون مدنی مواد: {conn.execute('SELECT COUNT(*) c FROM articles WHERE document_id=(SELECT id FROM documents WHERE reference_code=%r)' % 'QM-1307').fetchone()['c']}")
    print(f"قانون مجازات مواد: {conn.execute('SELECT COUNT(*) c FROM articles WHERE document_id=(SELECT id FROM documents WHERE reference_code=%r)' % 'QMA-1392').fetchone()['c']}")
    print(f"آیین دادرسی مدنی مواد: {cid_n}")
    print(f"آیین دادرسی کیفری مواد: {kid_n}")
    conn.close()


if __name__ == "__main__":
    main()
