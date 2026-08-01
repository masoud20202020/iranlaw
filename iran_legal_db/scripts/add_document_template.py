"""
الگوی آماده برای افزودن یک سند جدید (قانون/آیین‌نامه/بخشنامه/رأی/...)
به دیتابیس. کافیست این فایل را کپی کرده و مقادیر را جایگزین کنید.

برای هر دسته از اسناد، به سادگی type_code را انتخاب کنید:
  constitution   - قانون اساسی
  law            - قانون عادی
  amendment      - قانون اصلاحی
  regulation     - آیین‌نامه
  bylaw          - اساسنامه / آیین‌نامه داخلی
  circular       - بخشنامه
  directive      - دستورالعمل / شیوه‌نامه
  unified_ruling - رأی وحدت رویه
  advisory_opinion - نظریه مشورتی
  divan_ruling   - رأی دیوان عدالت اداری
  judicial_precedent - رأی اصراری / رویه قضایی
  treaty         - قرارداد بین‌المللی
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from schema import get_connection
from importer import (
    get_or_create_document, bulk_add_articles, add_relation,
    add_tag, link_document_tag, link_document_topic,
)


def main():
    conn = get_connection()

    # ---------- ۱) شناسنامه سند ----------
    doc_id = get_or_create_document(
        conn,
        title="عنوان کامل سند",           # مثلاً: قانون اصلاح موادی از قانون تجارت
        short_title="ع.ک.",              # مثلاً: ق.ا.ق.ت.
        type_code="amendment",           # از لیست بالا انتخاب کنید
        issuing_authority="مجلس شورای اسلامی",
        ratification_date="2024-01-01",  # YYYY-MM-DD
        effective_date="2024-02-01",
        publication_date="2024-01-15",
        official_newspaper_no="۲۱۵۰۰",
        reference_code="AQT-1402",       # کد یکتا (اختیاری ولی توصیه می‌شود)
        notes="یادداشت‌های کلی درباره سند",
    )

    # ---------- ۲) برچسب‌ها و موضوع ----------
    tid = add_tag(conn, "اصلاحیه تجارت")
    link_document_tag(conn, doc_id, tid)
    link_document_topic(conn, doc_id, "حقوق تجارت")

    # ---------- ۳) مواد ----------
    bulk_add_articles(conn, doc_id, [
        {"article_no": "۱", "text": "متن ماده ۱...", "source_note": "روزنامه رسمی شماره ..."},
        {"article_no": "۲", "text": "متن ماده ۲..."},
        # ...
    ])

    # ---------- ۴) ارتباطات ----------
    # اگر اصلاح‌گر سندی دیگر است (مثلاً قانون تجارت با id=3):
    # add_relation(conn, doc_id, "amends", 3, description="اصلاح مواد ۲۰، ۵۸، ۱۱۶")
    #
    # اگر آیین‌نامه اجرایی است:
    # add_relation(conn, doc_id, "implements", <id_قانون_مادر>)
    #
    # اگر رأی وحدت رویه ناظر به ماده‌ای است:
    # add_relation(conn, doc_id, "interprets", <id_قانون>, to_article_id=<id_ماده>)
    #
    # اگر رأی دیوان، بخشنامه‌ای را ابطال می‌کند:
    # add_relation(conn, doc_id, "overrules", <id_بخشنامه>)

    conn.commit()
    print(f"[OK] Document added with id={doc_id}")
    conn.close()


if __name__ == "__main__":
    main()
