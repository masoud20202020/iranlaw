"""
Demo: نشان می‌دهد چگونه تاریخچه تغییرات/اصلاحیه‌ها در دیتابیس ثبت می‌شود.
مثال: اصلاح ماده ۱۰ قانون مدنی (قراردادهای خصوصی) در سال ۱۳۷۰ و ۱۴۰۳
"""
from schema import get_connection, init_db
from importer import get_or_create_document, add_article, add_relation


def run_demo():
    conn = get_connection()

    # شناسه قانون مدنی
    civil = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()
    if not civil:
        print("ابتدا seed_core_laws.py را اجرا کنید."); return
    civil_id = civil["id"]

    # یافتن ماده ۱۰ فعلی
    old = conn.execute("""SELECT id FROM articles
                          WHERE document_id=? AND article_no='۱۰' AND is_current=1""",
                       (civil_id,)).fetchone()
    old_id = old["id"] if old else None

    # ===== نسخه‌بندی: نسخه قدیمی را بایگانی می‌کنیم =====
    if old_id:
        conn.execute(
            "UPDATE articles SET is_current=0, expiry_date='1991-07-23' WHERE id=?",
            (old_id,),
        )
        # به‌روزرسانی FTS
        conn.execute("DELETE FROM articles_fts WHERE article_id=?", (old_id,))

    # نسخه ۲ ماده ۱۰ (مثلاً اصلاحی ۱۳۷۰/۵/۱)
    v2_id = add_article(
        conn, civil_id,
        article_no="۱۰",
        article_key="QM:10",
        text="قراردادهای خصوصی نسبت به کسانی که آن را منعقد نموده‌اند در صورتی که مخالف صریح قانون و موازین شرعی نباشد نافذ است. قراردادهای خصوصی نمی‌تواند شامل اموری که مربوط به نظم عمومی می‌گردد باشد.",
        version_no=2, is_current=0,
        effective_date="1991-07-23",
        expiry_date="2024-10-06",
        source_note="اصلاحی ۱۳۷۰/۵/۱ – روزنامه رسمی",
        notes="نسخه میانی اصلاحی ۱۳۷۰"
    )

    # نسخه ۳ ماده ۱۰ (مثلاً اصلاحی ۱۴۰۳)
    v3_id = add_article(
        conn, civil_id,
        article_no="۱۰",
        article_key="QM:10",
        text="قراردادهای خصوصی نسبت به کسانی که آن را منعقد نموده‌اند در صورتی که مخالف صریح قانون و موازین اسلامی نباشد و متضمن ضرر به شخص ثالث و خلاف نظم عمومی و اخلاق حسنه نباشد نافذ است.",
        version_no=3, is_current=1,
        effective_date="2024-10-06",
        source_note="اصلاحی ۱۴۰۳/۷/۱۴",
        notes="نسخه نهایی فعلی"
    )

    # کلید پایدار برای نسخه اول هم ست شود تا تاریخچه کامل شود
    if old_id:
        conn.execute("UPDATE articles SET article_key='QM:10', version_no=1, is_current=0, effective_date='1929-05-23' WHERE id=?", (old_id,))
        d = conn.execute("SELECT title, article_no, text FROM articles a JOIN documents d ON d.id=a.document_id WHERE a.id=?", (old_id,)).fetchone()
        conn.execute(
            "INSERT INTO articles_fts(article_id, document_id, title, article_no, text) VALUES(?,?,?,?,?)",
            (old_id, civil_id, d["title"], d["article_no"], d["text"]),
        )

    # سند اصلاحی ۱۳۷۰
    amend_70 = get_or_create_document(
        conn,
        title="قانون اصلاح موادی از قانون مدنی (۱۳۷۰)",
        short_title="ق.ا.ق.م. ۱۳۷۰",
        type_code="amendment",
        issuing_authority="مجلس شورای اسلامی",
        ratification_date="1991-07-23",
        reference_code="AQM-1370",
    )
    add_relation(conn, amend_70, "amends", civil_id,
                 from_article_id=v2_id, to_article_id=old_id,
                 description="نسخه ۲ ماده ۱۰ (افزودن قید موازین شرعی و نظم عمومی)")

    # سند اصلاحی ۱۴۰۳
    amend_1403 = get_or_create_document(
        conn,
        title="قانون اصلاح موادی از قانون مدنی (مصوب ۱۴۰۳)",
        short_title="ق.ا.ق.م. ۱۴۰۳",
        type_code="amendment",
        issuing_authority="مجلس شورای اسلامی",
        ratification_date="2024-10-06",
        reference_code="AQM-1403",
    )
    add_relation(conn, amend_1403, "amends", civil_id,
                 from_article_id=v3_id, to_article_id=v2_id,
                 description="نسخه ۳ ماده ۱۰ (افزودن قید عدم ضرر به ثالث و اخلاق حسنه)")

    conn.commit()
    print("[OK] Demo history created for article 10 of civil code (versions 1, 2, 3)")

    # نمایش
    print("\n=== تاریخچه ماده ۱۰ قانون مدنی ===")
    for r in conn.execute("""
        SELECT a.version_no, a.is_current, a.effective_date, a.expiry_date, a.text
        FROM articles a WHERE a.article_key='QM:10' ORDER BY a.version_no
    """):
        print(f"\nنسخه {r['version_no']}  |  {'[فعلی]' if r['is_current'] else '[منسوخ]'}"
              f"  |  اجرا: {r['effective_date']}  |  پایان: {r['expiry_date']}")
        print(f"متن: {r['text']}")

    conn.close()


if __name__ == "__main__":
    run_demo()
