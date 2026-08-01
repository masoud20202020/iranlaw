# -*- coding: utf-8 -*-
"""تکمیل نهایی قانون مجازات اسلامی تا ۷۲۸ ماده – نسخه جامع."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "seed"))

from schema import get_connection
from importer import add_article
from penal_code_book1b import PENAL_BOOK1B
from penal_code_book5 import PENAL_BOOK5
from penal_code_gaps import PENAL_GAPS


def to_persian_num(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def main():
    conn = get_connection()
    penal_id = conn.execute("SELECT id FROM documents WHERE reference_code='QMA-1392'").fetchone()
    if not penal_id:
        print("خطا: ابتدا load_penal_code.py را اجرا کنید."); return
    penal_id = penal_id["id"]

    existing_keys = {r["article_key"] for r in conn.execute(
        "SELECT article_key FROM articles WHERE document_id=? AND article_key IS NOT NULL", (penal_id,)).fetchall()}

    added = 0
    all_articles = {}
    for art_list in (PENAL_BOOK1B, PENAL_BOOK5, PENAL_GAPS):
        for no, text in art_list:
            if no not in all_articles:
                all_articles[no] = text

    for no in sorted(all_articles.keys()):
        key = f"QMA:{no}"
        if key in existing_keys:
            continue
        add_article(
            conn, penal_id,
            article_no=to_persian_num(no),
            text=all_articles[no],
            article_key=key,
            version_no=1, is_current=1,
            effective_date="2013-07-22",
            source_note="قانون مجازات اسلامی ۱۳۹۲ (سامانه ملی قوانین)",
        )
        added += 1

    # بررسی نهایی
    nos = set()
    for r in conn.execute("SELECT article_key FROM articles WHERE document_id=?", (penal_id,)).fetchall():
        if r["article_key"] and r["article_key"].startswith("QMA:"):
            try: nos.add(int(r["article_key"].split(":")[1]))
            except Exception: pass
    missing = [i for i in range(1, 729) if i not in nos]

    conn.commit()

    n_penal = conn.execute("SELECT COUNT(*) c FROM articles WHERE document_id=?", (penal_id,)).fetchone()["c"]
    n_docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    n_arts = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
    rels = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]

    # به‌روزرسانی یادداشت
    conn.execute("UPDATE documents SET notes=? WHERE id=?",
                 ("مصوب ۱۳۹۲/۰۲/۰۱ با تأیید شورای نگهبان، لازم‌الاجرا از ۱۳۹۲/۰۴/۳۱. قانون مجازات اسلامی مشتمل بر ۵ کتاب (کلیات، حدود، قصاص، دیات، تعزیرات) و ۷۲۸ ماده، جایگزین قانون ۱۳۷۰. متن کامل در این دیتابیس موجود است.",
                  penal_id))
    conn.commit()

    print(f"[OK] {added} ماده جدید افزوده شد. مجموع مواد قانون مجازات: {n_penal}")
    print(f"     مواد کم‌شماره (باید خالی باشد): {missing if missing else 'ندارد ✓ — کامل ۷۲۸ ماده'}")
    print(f"     دیتابیس: {n_docs} سند، {n_arts} ماده، {rels} ارتباط")
    conn.close()


if __name__ == "__main__":
    main()
