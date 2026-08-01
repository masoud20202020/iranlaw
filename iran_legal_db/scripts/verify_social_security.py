# -*- coding: utf-8 -*-
"""Verification for Social Security Law and retirement-reform package."""
from __future__ import annotations
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "web")]
from schema import get_connection
from app import app

REFS = ("QTA-1354", "FNAT-SS-1403", "QPH7-1403-A29", "A29P7-1403")
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
WHOLE = {9, 11, *range(12, 28), 46, 86, 92, 98, 99, 100}
PARTIAL = {4, 58, 76, 81, 82}
ROW23_WHOLE = {9, *range(12, 16), 17, 18, *range(19, 28), 98, 99, 100}


def req(value, message):
    if not value:
        raise AssertionError(message)


def snap(conn):
    return tuple(conn.execute("""SELECT (SELECT COUNT(*) FROM documents),(SELECT COUNT(*) FROM articles),
      (SELECT COUNT(*) FROM articles WHERE is_current=1),(SELECT COUNT(*) FROM articles WHERE is_current=0),
      (SELECT COUNT(*) FROM relations),(SELECT COUNT(*) FROM articles_fts)""").fetchone())


def main():
    conn = get_connection()
    docs = {}
    for ref in REFS:
        row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
        req(row, "missing " + ref)
        docs[ref] = row["id"]
    expected = {
        "QTA-1354": (123, 94, 29), "FNAT-SS-1403": (1, 1, 0),
        "QPH7-1403-A29": (1, 1, 0), "A29P7-1403": (7, 7, 0),
    }
    for ref, want in expected.items():
        row = conn.execute("""SELECT COUNT(*)n,SUM(is_current)c,
          SUM(CASE WHEN is_current=0 THEN 1 ELSE 0 END)h FROM articles WHERE document_id=?""", (docs[ref],)).fetchone()
        req((row["n"], row["c"], row["h"]) == want, "counts " + ref)

    keys = {r[0] for r in conn.execute("SELECT DISTINCT article_key FROM articles WHERE document_id=?", (docs["QTA-1354"],))}
    req(keys == {f"QTA-1354:{n}" for n in range(1, 119)}, "coverage 1-118")
    current_keys = {r[0] for r in conn.execute("SELECT article_key FROM articles WHERE document_id=? AND is_current=1", (docs["QTA-1354"],))}
    req(current_keys == {f"QTA-1354:{n}" for n in range(1,119) if n not in WHOLE}, "current/repealed split")
    for n in PARTIAL:
        req(conn.execute("SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QTA-1354:{n}",)).fetchone()[0] == 2, f"partial history {n}")
    for n in WHOLE:
        row = conn.execute("SELECT is_current,expiry_date FROM articles WHERE article_key=?", (f"QTA-1354:{n}",)).fetchone()
        req(row and row["is_current"] == 0 and row["expiry_date"], f"whole repeal {n}")

    a4 = conn.execute("SELECT text FROM articles WHERE article_key='QTA-1354:4' AND is_current=1").fetchone()["text"]
    req("تبصره ۴" not in a4 and "صاحبان حرف" not in a4 and "تبصره ۵" in a4, "article 4 current")
    a76 = conn.execute("SELECT id,text FROM articles WHERE article_key='QTA-1354:76' AND is_current=1").fetchone()
    req("حداقل ده سال" not in a76["text"] and "سن مرد" in a76["text"] and "سخت و زیان‌آور" in a76["text"], "article 76 current")
    a81 = conn.execute("SELECT text FROM articles WHERE article_key='QTA-1354:81' AND is_current=1").fetchone()["text"]
    req("عیال دائم" not in a81 and "فرزندان متوفی" in a81, "article 81 current")
    a102 = conn.execute("SELECT text FROM articles WHERE article_key='QTA-1354:102' AND is_current=1").fetchone()["text"]
    req("۳٬۳۰۰٬۰۰۰" in a102 and "۶۶٬۰۰۰٬۰۰۰" in a102, "article 102 current fine")

    invalid = conn.execute("SELECT text,id FROM articles WHERE document_id=?", (docs["FNAT-SS-1403"],)).fetchone()
    for marker in ("۱-حقوق ورثه", "۲۳-قانون تأمین اجتماعی", "۷۱-قانون تمدید"):
        req(marker in invalid["text"], "invalid appendix " + marker)
    program = conn.execute("SELECT text,id FROM articles WHERE document_id=?", (docs["QPH7-1403-A29"],)).fetchone()
    for phrase in ("بیش از ۲۸ سال", "مردان از ۶۲ سال", "مردان ۳۵ سال", "زنان ۳۰ سال", "مشاغل سخت و زیان‌آور"):
        req(phrase in program["text"], "program 29 " + phrase)
    bylaw2 = conn.execute("SELECT text FROM articles WHERE article_key='A29P7-1403:2'").fetchone()["text"]
    req("از ۲۵ سال تا ۲۸ سال" in bylaw2 and "۲ ماه" in bylaw2 and "پنج سال" in bylaw2, "bylaw table")

    rows = conn.execute("SELECT article_no,text FROM articles WHERE document_id IN (?,?,?,?)", tuple(docs.values())).fetchall()
    req(all(r["text"].strip() for r in rows), "empty text")
    req(all(not re.search(r"[0-9]", r["article_no"]) for r in rows), "ASCII article number")
    req(all("https://" not in r["text"] and "متن نمونه" not in r["text"] for r in rows), "leaked URL/filler")
    for term in ("حق بیمه", "مستمری بازنشستگی", "سنوات الزامی بیمه‌پردازی", "مشاغل سخت و زیان‌آور", "احکام قانونی مذکور در پیوست", "کمیسیون پزشکی"):
        count = conn.execute("""SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id
          WHERE articles_fts MATCH ? AND a.is_current=1""", (f'"{term}"',)).fetchone()[0]
        req(count > 0, "FTS " + term)
    req(conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0], "FTS parity")

    abrogations = conn.execute("""SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=?
      AND relation_type='abrogates'""", (docs["FNAT-SS-1403"], docs["QTA-1354"])).fetchone()[0]
    req(abrogations == len(ROW23_WHOLE | PARTIAL) == 24, "1403 relation network")
    req(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='implements'", (docs["A29P7-1403"],)).fetchone()[0] == 2, "bylaw relations")
    req(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='amends'", (docs["QPH7-1403-A29"],)).fetchone()[0] == 1, "program relation")
    req(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
    before = snap(conn)
    article_id = a76["id"]
    conn.close()

    for args in (["stats"], ["history", "QTA-1354:76"], ["search", "سنوات الزامی بیمه پردازی"]):
        result = subprocess.run([sys.executable, os.path.join(ROOT,"scripts","query.py"), *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        req(result.returncode == 0 and result.stdout.strip(), "query " + " ".join(args))

    client = app.test_client()
    pages = ["/", "/?q=مستمری+بازنشستگی", "/types", "/by-type/law", "/by-type/amendment", "/by-type/regulation"]
    for did in docs.values():
        pages += [f"/doc/{did}", f"/doc/{did}?view=all", f"/doc/{did}?view=historical"]
    pages.append(f"/article/{article_id}")
    for page in pages:
        req(client.get(page).status_code == 200, "Flask " + page)

    result = subprocess.run([sys.executable, os.path.join(ROOT,"scripts","load_social_security.py")], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    req(result.returncode == 0, result.stderr)
    conn = get_connection(); after = snap(conn)
    req(before == after, f"idempotency {before} != {after}")
    req(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
    conn.close()
    print("[OK] Social Security Law: 118 numbers, 123 versions, 94 current, 29 historical")
    print("[OK] Invalid-provisions appendix=71 rows; Program 7 article 29=1; retirement bylaw=7")
    print("[OK] Coverage, repeal/partial histories, current fines, Persian numbers, FTS5, relations, query.py, Flask and idempotency")


if __name__ == "__main__":
    main()
