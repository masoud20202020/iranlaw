"""
Simple command-line query tool for Iran Legal Database.
Usage:
    python3 scripts/query.py search "واژه"          # full-text search
    python3 scripts/query.py list                    # list all documents
    python3 scripts/query.py show <doc-id>           # show document + first 20 articles
    python3 scripts/query.py history <article-key>   # version history
    python3 scripts/query.py stats                   # statistics
"""
import sys
from schema import get_connection, DB_PATH
from search_utils import expand_fts_query


def stats(conn):
    for name, sql in [
        ("انواع اسناد", "SELECT dt.name_fa, COUNT(*) c FROM documents d JOIN document_types dt ON dt.id=d.type_id GROUP BY dt.id ORDER BY c DESC"),
        ("وضعیت اسناد", "SELECT s.name_fa, COUNT(*) c FROM documents d JOIN statuses s ON s.id=d.status_id GROUP BY s.id"),
        ("مراجع صادرکننده", "SELECT a.name_fa, COUNT(*) c FROM documents d JOIN authorities a ON a.id=d.issuing_authority_id GROUP BY a.id ORDER BY c DESC"),
    ]:
        print(f"\n=== {name} ===")
        for r in conn.execute(sql):
            print(f"  {r[0]:40s} {r[1]}")
    print("\n=== مجموع ===")
    print("اسناد:", conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
    print("مواد/مفاد جاری:", conn.execute("SELECT COUNT(*) FROM articles WHERE is_current=1").fetchone()[0])
    print("نسخه‌های تاریخی:", conn.execute("SELECT COUNT(*) FROM articles WHERE is_current=0").fetchone()[0])
    print("کل ردیف‌های مواد و نسخه‌ها:", conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
    print("ارتباطات:", conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0])
    print("برچسب‌ها:", conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0])


def list_docs(conn):
    print("\n=== فهرست اسناد ===")
    rows = conn.execute("""
        SELECT d.id, d.reference_code, d.short_title, d.title, dt.name_fa type, d.ratification_date, s.name_fa status
        FROM documents d
        JOIN document_types dt ON dt.id=d.type_id
        JOIN statuses s ON s.id=d.status_id
        ORDER BY d.id
    """)
    for r in rows:
        print(f"[{r['id']:3d}] {r['reference_code'] or '---':10s} {r['short_title'] or '':6s} | {r['type']:10s} | {r['status']:15s} | {r['title']}")


def show_doc(conn, doc_id, limit=0):
    d = conn.execute("""
        SELECT d.*, dt.name_fa type, s.name_fa status, a.name_fa authority
        FROM documents d
        JOIN document_types dt ON dt.id=d.type_id
        JOIN statuses s ON s.id=d.status_id
        LEFT JOIN authorities a ON a.id=d.issuing_authority_id
        WHERE d.id=?
    """, (doc_id,)).fetchone()
    if not d:
        print("سندی با این شناسه یافت نشد."); return
    print("="*80)
    print(f"شناسه: {d['id']}  |  کد: {d['reference_code']}  |  نوع: {d['type']}")
    print(f"عنوان: {d['title']}")
    print(f"عنوان کوتاه: {d['short_title']}")
    print(f"مرجع صادرکننده: {d['authority']}")
    print(f"وضعیت: {d['status']}")
    print(f"تاریخ تصویب: {d['ratification_date']}   تاریخ انتشار: {d['publication_date']}   تاریخ اجرا: {d['effective_date']}")
    if d['official_newspaper_no']:
        print(f"روزنامه رسمی شماره: {d['official_newspaper_no']}")
    if d['notes']:
        print(f"توضیحات: {d['notes']}")

    # relations
    rels = conn.execute("""
        SELECT r.relation_type, dt.title, dt.short_title
        FROM relations r
        LEFT JOIN documents dt ON dt.id=r.to_document_id
        WHERE r.from_document_id=?
    """, (doc_id,)).fetchall()
    if rels:
        print("ارتباطات:")
        for r in rels:
            print(f"   - {r['relation_type']:15s} -> {r['title']}")

    print("-"*80)
    sql = "SELECT article_no, text FROM articles WHERE document_id=? AND is_current=1 ORDER BY id"
    args = [doc_id]
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    arts = conn.execute(sql, args).fetchall()
    for a in arts:
        t = a['text']
        if len(t) > 500: t = t[:500] + " ..."
        print(f"\nماده {a['article_no']}:\n  {t}")


def search(conn, q):
    print(f"\n=== نتایج جست‌وجو برای «{q}» ===")
    rows = conn.execute("""
        SELECT a.article_no, a.text, d.title, d.short_title
        FROM articles_fts
        JOIN articles a ON a.id = articles_fts.article_id
        JOIN documents d ON d.id = a.document_id
        WHERE articles_fts MATCH ? AND a.is_current=1
        ORDER BY rank
        LIMIT 30
    """, (expand_fts_query(q),)).fetchall()
    if not rows:
        print("نتیجه‌ای یافت نشد.")
        return
    for i, r in enumerate(rows, 1):
        t = r['text']
        if len(t) > 300: t = t[:300] + " ..."
        print(f"\n[{i}] ({r['short_title']}) {r['title']} - ماده {r['article_no']}")
        print(f"    {t}")


def history(conn, key):
    print(f"\n=== تاریخچه ماده با کلید {key} ===")
    rows = conn.execute("""
        SELECT a.version_no, a.is_current, a.effective_date, a.expiry_date, a.text, d.short_title, a.article_no
        FROM articles a JOIN documents d ON d.id=a.document_id
        WHERE a.article_key=? ORDER BY a.version_no
    """, (key,)).fetchall()
    for r in rows:
        print(f"\nنسخه {r['version_no']}  |  {'[فعلی]' if r['is_current'] else '[قبلی]'}  |  اجرا: {r['effective_date']}  |  پایان: {r['expiry_date']}")
        print(f"  {r['text'][:400]}")


def main():
    conn = get_connection()
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "stats":
        stats(conn)
    elif cmd == "list":
        list_docs(conn)
    elif cmd == "show" and len(sys.argv) >= 3:
        show_doc(conn, int(sys.argv[2]))
    elif cmd == "search" and len(sys.argv) >= 3:
        search(conn, sys.argv[2])
    elif cmd == "history" and len(sys.argv) >= 3:
        history(conn, sys.argv[2])
    else:
        print(__doc__)
    conn.close()


if __name__ == "__main__":
    main()
