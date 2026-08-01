# -*- coding: utf-8 -*-
"""Verify phase-two insurance regulations and their integration with the database."""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "web")]

from schema import get_connection
from app import app

TP = "QST-1395"
CENTRAL = "QBMC-1350"
REFS = (
    "AITP3-1396", "AITP5-1397", "AITP6-1397", "AITP12-1397", "AITP18-1396",
    "AITP30-1396", "AITP42-1396", "AITP57-1398", "DISTK-1403", "AIFUND-1397",
    "AIN58-1387", "AIN69-1390", "AIN110-1404", "AIN93-1396", "AIN88-1393",
    "AIN90-1394", "AIN100-1399", "AIN106-1403", "AIN85-1392", "AIN104-1401",
    "RVR-734-1393", "RVR-766-1396", "RVR-777-1398", "RVR-781-1398",
    "RVR-806-1399", "RVR-869-1404", "DAD-DIM-1405",
)
EXPECTED = {
    "AITP3-1396": (16, 16), "AITP5-1397": (6, 6), "AITP6-1397": (10, 10),
    "AITP12-1397": (7, 7), "AITP18-1396": (11, 11), "AITP30-1396": (8, 7),
    "AITP42-1396": (8, 8), "AITP57-1398": (25, 25), "DISTK-1403": (14, 13),
    "AIFUND-1397": (25, 25), "AIN58-1387": (18, 18), "AIN69-1390": (15, 15),
    "AIN110-1404": (1, 1), "AIN93-1396": (1, 1), "AIN88-1393": (12, 12),
    "AIN90-1394": (15, 15), "AIN100-1399": (21, 21), "AIN106-1403": (29, 29),
    "AIN85-1392": (19, 19), "AIN104-1401": (1, 1), "RVR-734-1393": (1, 1),
    "RVR-766-1396": (1, 1), "RVR-777-1398": (1, 1), "RVR-781-1398": (1, 1),
    "RVR-806-1399": (1, 1), "RVR-869-1404": (1, 1), "DAD-DIM-1405": (1, 1),
}
SEQUENTIAL = {
    "AITP3-1396": 16, "AITP5-1397": 6, "AITP6-1397": 10, "AITP12-1397": 7,
    "AITP18-1396": 11, "AITP30-1396": 7, "AITP42-1396": 8, "AITP57-1398": 25,
    "DISTK-1403": 13, "AIFUND-1397": 25, "AIN58-1387": 18, "AIN69-1390": 15,
    "AIN88-1393": 12, "AIN90-1394": 15, "AIN100-1399": 21, "AIN106-1403": 29,
    "AIN85-1392": 19,
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def snapshot(conn):
    return tuple(conn.execute(
        """SELECT (SELECT COUNT(*) FROM documents),(SELECT COUNT(*) FROM articles),
           (SELECT COUNT(*) FROM articles WHERE is_current=1),
           (SELECT COUNT(*) FROM articles WHERE is_current=0),
           (SELECT COUNT(*) FROM relations),(SELECT COUNT(*) FROM tags),
           (SELECT COUNT(*) FROM articles_fts)"""
    ).fetchone())


def article(conn, key, current=1):
    return conn.execute("SELECT * FROM articles WHERE article_key=? AND is_current=?", (key, current)).fetchone()


def run_script(name, *args, timeout=300):
    p = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", name), *args], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
    )
    require(p.returncode == 0, f"{name} failed: {p.stderr}\n{p.stdout}")
    return p.stdout


def main():
    conn = get_connection()
    docs = {}
    for ref in REFS:
        row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
        require(row, "missing document " + ref)
        docs[ref] = row["id"]

    # Exact document/material counts and contiguous structural coverage.
    for ref, expected in EXPECTED.items():
        row = conn.execute(
            "SELECT COUNT(*) n,COALESCE(SUM(is_current),0)c FROM articles WHERE document_id=?",
            (docs[ref],),
        ).fetchone()
        require(tuple(row) == expected, f"count mismatch {ref}: {tuple(row)} != {expected}")
    require(sum(x[0] for x in EXPECTED.values()) == 269, "package total")
    require(sum(x[1] for x in EXPECTED.values()) == 267, "package current total")
    for ref, end in SEQUENTIAL.items():
        got = {row[0] for row in conn.execute("SELECT DISTINCT article_key FROM articles WHERE document_id=?", (docs[ref],))}
        expected = {f"{ref}:{n}" for n in range(1, end + 1)}
        require(got == expected, f"coverage {ref}: missing={expected-got}, extra={got-expected}")

    # Core third-party content.
    require("دیه مرد مسلمان" in article(conn, "AITP3-1396:2")["text"], "driver cover")
    require("حداقل به میزان دیه" in article(conn, "AITP3-1396:4")["text"], "driver amended amount")
    require("گواهینامه رانندگی" in article(conn, "AITP3-1396:10")["text"], "driver licence evidence")
    require("سطح (۲)" in article(conn, "AITP5-1397:2")["text"], "third-party licence solvency")
    require("همسر" in article(conn, "AITP6-1397:2")["text"] and "اولاد بلاواسطه" in article(conn, "AITP6-1397:2")["text"], "discount transfer")
    require("موتورسیکلت" in article(conn, "AITP12-1397:3")["text"], "capacity")
    require("هفتاد درصد" in article(conn, "AITP18-1396:6")["text"] and "عدم خسارت" in article(conn, "AITP18-1396:6")["text"], "premium discount")
    require("کسر قیمت وسیله نقلیه" in article(conn, "AITP30-1396:7")["text"], "claims current diminution")
    require("کسر قیمت وسیله نقلیه را در نظر گیرد" not in article(conn, "AITP30-1396:7", 0)["text"], "claims history")
    require("توقیف" in article(conn, "AITP42-1396:4")["text"], "impound")
    require("مصادیق قصور یا تخلف" in article(conn, "AITP57-1398:2")["text"], "violations")
    require("نهاد عمومی غیردولتی" in article(conn, "AIFUND-1397:1")["text"], "fund personality")
    require("مبالغ بازیافتی" in article(conn, "AIFUND-1397:19")["text"], "fund resources")

    # Diminution tables and the 1405 Divan history.
    dim4 = article(conn, "DISTK-1403:4")["text"]
    require("جدول شماره ۱" in dim4 and "بلوکه سیلندر" in dim4 and "کف اتاق" in dim4, "accident table")
    dim6 = article(conn, "DISTK-1403:6")["text"]
    dim6_old = article(conn, "DISTK-1403:6", 0)["text"]
    require("جدول شماره ۲" in dim6 and "۲/۰۵" in dim6, "age table")
    require("ده سال یا بیشتر" not in dim6 and "ده سال یا بیشتر" in dim6_old, "Divan consolidation")
    require(article(conn, "DISTK-1403:6")["version_no"] == 2, "dim version")
    require("خارج از حدود اختیار" in article(conn, "DAD-DIM-1405:holding")["text"], "Divan holding")

    # Supervisory regulations and explicit summary labels.
    require("ذخیره خسارات معوق" in article(conn, "AIN58-1387:1")["text"], "technical reserves")
    require("سطح ۱" in article(conn, "AIN69-1390:7")["text"] and "۱۰۰ درصد" in article(conn, "AIN69-1390:7")["text"], "solvency levels")
    require("جدول شماره ۵" in article(conn, "AIN69-1390:15")["text"], "solvency appendices")
    for ref in ("AIN110-1404", "AIN93-1396", "AIN104-1401"):
        row = article(conn, f"{ref}:summary")
        require("خلاصه" in row["text"] and "رونوشت لفظ‌به‌لفظ" in row["text"], "summary label " + ref)
        require("خلاصه" in (row["notes"] or ""), "summary notes " + ref)
    require("صورت‌های مالی حسابرسی‌شده سال مالی ۱۴۰۵" in article(conn, "AIN110-1404:summary")["text"], "solvency 110 transition")
    require("کنترل داخلی" in article(conn, "AIN93-1396:summary")["text"] and "مدیریت ریسک" in article(conn, "AIN93-1396:summary")["text"], "governance summary")
    require("هشتاد درصد" in article(conn, "AIN104-1401:summary")["text"], "investment summary")
    require("گزارش وضعیت توانگری" in article(conn, "AIN88-1393:7")["text"], "disclosure")
    require("صلاحیت" in article(conn, "AIN90-1394:2")["text"], "professional qualification")
    require("جایگزین ضوابط" in article(conn, "AIN100-1399:21")["text"] and "آیین‌نامه شماره ۴۰" in article(conn, "AIN100-1399:21")["text"], "private institutions")
    require("شخص حقیقی یا حقوقی" in article(conn, "AIN106-1403:1")["text"] and "شخص کارفرمای" not in article(conn, "AIN106-1403:1")["text"], "agent OCR correction")
    require("قرارداد کتبی" in article(conn, "AIN85-1392:8")["text"], "adjuster renumber")
    require("کارشناسان رسمی دادگستری" in article(conn, "AIN85-1392:3")["text"], "adjuster amendment")

    # Binding insurance rulings.
    require("دادگاه عمومی جزایی" in article(conn, "RVR-734-1393:holding")["text"], "ruling 734")
    require("حاکمیت ندارد" in article(conn, "RVR-766-1396:holding")["text"], "ruling 766")
    require("کلیه جنایات علیه زنان" in article(conn, "RVR-777-1398:holding")["text"], "ruling 777")
    require("قابل تسری و تعمیم" in article(conn, "RVR-781-1398:holding")["text"], "ruling 781")
    require("فاقد گواهینامه" in article(conn, "RVR-806-1399:holding")["text"], "ruling 806")
    require("قیمت زمان پرداخت" in article(conn, "RVR-869-1404:holding")["text"], "ruling 869")

    # Text quality, Persian article numbers, FTS and relation graph.
    placeholders = ",".join("?" * len(docs))
    rows = conn.execute(
        f"SELECT article_no,text,source_note,notes FROM articles WHERE document_id IN ({placeholders})",
        tuple(docs.values()),
    ).fetchall()
    require(len(rows) == 269, "rows package")
    require(all(row["text"].strip() and row["source_note"] for row in rows), "empty/source note")
    require(all(not re.search(r"[0-9]", row["article_no"]) for row in rows), "ASCII article_no")
    require(all("http://" not in row["text"] and "https://" not in row["text"] and "�" not in row["text"] for row in rows), "text leak")
    require(all("متن نمونه" not in row["text"] and "لورم" not in row["text"] for row in rows), "filler")
    require(conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0], "FTS parity")
    for term in ("کسر قیمت وسیله نقلیه", "توانگری مالی", "حاکمیت شرکتی", "راننده مسبب حادثه", "ذخایر فنی"):
        count = conn.execute(
            """SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id
               WHERE articles_fts MATCH ? AND a.is_current=1""",
            (f'"{term}"',),
        ).fetchone()[0]
        require(count > 0, "FTS " + term)
    rel_count = conn.execute(
        f"SELECT COUNT(*) FROM relations WHERE from_document_id IN ({placeholders})",
        tuple(docs.values()),
    ).fetchone()[0]
    require(rel_count == 35, f"relations {rel_count}")
    require(conn.execute(
        """SELECT COUNT(*) FROM relations r JOIN documents d ON d.id=r.from_document_id
           WHERE d.reference_code=? AND r.relation_type='overrules'""", ("DAD-DIM-1405",)
    ).fetchone()[0] == 1, "Divan overrule relation")

    require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
    require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
    require(not conn.execute("SELECT reference_code,COUNT(*) FROM documents GROUP BY reference_code HAVING reference_code IS NOT NULL AND COUNT(*)>1").fetchall(), "duplicate refs")
    require(not conn.execute("SELECT article_key,COUNT(*) FROM articles WHERE is_current=1 AND article_key IS NOT NULL GROUP BY article_key HAVING COUNT(*)>1").fetchall(), "multiple current")
    before = snapshot(conn)
    doc_ids = dict(docs)
    aid = article(conn, "DISTK-1403:6")["id"]
    conn.close()

    # CLI and web pages.
    for args in (("stats",), ("show", str(doc_ids["DISTK-1403"])), ("history", "DISTK-1403:6"), ("search", "کسر قیمت وسیله نقلیه")):
        output = run_script("query.py", *args, timeout=120)
        require(output.strip(), "query output")
    client = app.test_client()
    for path in ["/", f"/article/{aid}", *[f"/doc/{doc_id}" for doc_id in doc_ids.values()]]:
        require(client.get(path).status_code == 200, "Flask " + path)

    # Destination-loader rerun must not delete document-level cross-package relations.
    run_script("load_insurance_core.py", timeout=300)
    conn = get_connection()
    rel_after_core = conn.execute(
        f"SELECT COUNT(*) FROM relations WHERE from_document_id IN ({placeholders})",
        tuple(doc_ids.values()),
    ).fetchone()[0]
    require(rel_after_core == 35, "cross-package relations survived core rerun")
    conn.close()

    # Own loader is idempotent.
    run_script("load_insurance_regulations.py", timeout=300)
    conn = get_connection()
    require(before == snapshot(conn), f"idempotency: {before} != {snapshot(conn)}")
    require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity after rerun")
    require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys after rerun")
    require(not conn.execute("SELECT article_key,COUNT(*) FROM articles WHERE is_current=1 AND article_key IS NOT NULL GROUP BY article_key HAVING COUNT(*)>1").fetchall(), "multiple current after rerun")
    conn.close()

    print("[OK] 27 insurance phase-two documents | 269 rows | 267 current | 2 historical | 35 relations")
    print("[OK] Coverage, Persian numbers, sourced summaries, diminution history, FTS5, CLI, Flask, integrity and idempotency")


if __name__ == "__main__":
    main()
