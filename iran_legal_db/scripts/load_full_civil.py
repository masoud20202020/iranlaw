# -*- coding: utf-8 -*-
"""
بارگذاری متن گسترده قانون مدنی (حدود ۳۶۰ ماده از مهم‌ترین مواد هر سه کتاب)
به دیتابیس. مواد قبلی پاک شده و نسخه یکپارچه بارگذاری می‌شود.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "seed"))

from schema import get_connection, DB_PATH
from importer import get_or_create_document, add_article, add_relation, add_tag, link_document_tag, link_document_topic

from civil_code_book1 import BOOK1_ARTICLES
from civil_code_book2 import BOOK2_KEY_ARTICLES
from civil_code_book3 import BOOK3_ARTICLES


def to_persian_num(n: int) -> str:
    m = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(n).translate(m)


def main():
    conn = get_connection()

    # ۱) حذف مواد قبلی قانون مدنی (به جز مواردی که نسخه‌بندی دمو بود)
    civil = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()
    if not civil:
        print("خطا: قانون مدنی در دیتابیس یافت نشد. ابتدا seed_core_laws را اجرا کنید.")
        return
    civil_id = civil["id"]

    # حذف دمو اصلاحیه ۱۰ (تاریخچه) تا نسخه تمیز بارگذاری شود
    conn.execute("DELETE FROM articles WHERE document_id=? OR article_key LIKE 'QM:%'", (civil_id,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (civil_id,))
    conn.execute("DELETE FROM relations WHERE from_document_id=? OR to_document_id=?", (civil_id, civil_id,))
    # حذف اسناد اصلاحی دمو
    conn.execute("DELETE FROM documents WHERE reference_code IN ('AQM-1370', 'AQM-1403')")

    # به‌روزرسانی عنوان (اگر لازم باشد) و وضعیت
    conn.execute("""UPDATE documents SET notes=? WHERE id=?""",
                 ("مصوب ۱۳۰۷/۲/۱۸؛ در این نسخه، مواد کلیدی از کتاب اول (اموال و تعهدات)، کتاب دوم (عقود معین) و کتاب سوم (اشخاص و ارث) با آخرین اصلاحات (تا ۱۴۰۳) وارد شده است. برای تکمیل نهایی، مواد باقی‌مانده را می‌توان از منابع رسمی (docs/sources.md) به این ساختار افزود.", civil_id))
    conn.commit()

    # ۲) تجمیع همه مواد
    all_articles = {}
    for no, text in BOOK1_ARTICLES + BOOK2_KEY_ARTICLES + BOOK3_ARTICLES:
        all_articles[no] = text

    # ۳) افزودن مواد (همه با article_key پایدار برای تاریخچه آتی)
    for no in sorted(all_articles.keys()):
        add_article(
            conn, civil_id,
            article_no=to_persian_num(no),
            text=all_articles[no],
            article_key=f"QM:{no}",
            version_no=1, is_current=1,
            effective_date="1929-05-23",
            source_note="قانون مدنی مصوب ۱۳۰۷ با اصلاحات بعدی (تا ۱۴۰۳) – سامانه ملی قوانین",
        )

    # ۴) برچسب و موضوع
    t1 = add_tag(conn, "مدنی")
    t2 = add_tag(conn, "قانون مادر")
    link_document_tag(conn, civil_id, t1)
    link_document_tag(conn, civil_id, t2)
    link_document_topic(conn, civil_id, "حقوق مدنی")
    link_document_topic(conn, civil_id, "حقوق خانواده")

    # ۵) روابط با سایر اسناد
    # قانون حمایت خانواده
    fam = conn.execute("SELECT id FROM documents WHERE reference_code='QHKH-1391'").fetchone()
    if fam:
        add_relation(conn, fam["id"], "amends", civil_id,
                     description="قانون حمایت خانواده ۱۳۹۱ موادی را در باب نکاح و طلاق اصلاح و تکمیل کرده است.")
    # قانون مسئولیت مدنی
    mm = conn.execute("SELECT id FROM documents WHERE reference_code='QMM-1339'").fetchone()
    if mm:
        add_relation(conn, mm["id"], "implements", civil_id,
                     description="قانون مسئولیت مدنی مکمل باب الزامات خارج از قرارداد (مواد ۳۲۸ به بعد) قانون مدنی است.")
    # قانون اساسی
    qa = conn.execute("SELECT id FROM documents WHERE reference_code='QA-1358'").fetchone()
    if qa:
        add_relation(conn, civil_id, "cites", qa["id"],
                     description="ماده ۱۶۷ قانون مدنی در پیوند با اصل ۱۶۷ قانون اساسی (مراجعه به منابع فقهی) است.")

    conn.commit()

    n_docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    n_arts = conn.execute("SELECT COUNT(*) c FROM articles").fetchone()["c"]
    n_civil = conn.execute("SELECT COUNT(*) c FROM articles WHERE document_id=?", (civil_id,)).fetchone()["c"]
    n_rel = conn.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"]

    print("[OK] قانون مدنی به‌روزرسانی شد.")
    print(f"    تعداد مواد قانون مدنی در دیتابیس: {n_civil}")
    print(f"    مجموع اسناد: {n_docs} | مجموع مواد: {n_arts} | ارتباطات: {n_rel}")
    conn.close()


if __name__ == "__main__":
    main()
