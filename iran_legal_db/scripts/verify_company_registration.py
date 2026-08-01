# -*- coding: utf-8 -*-
"""Integrity tests for the company-registration package."""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "web")]

from schema import get_connection
from app import app

REFS = (
    "QRS-1310", "NRS-1310", "NM196-1311", "QSF-1376",
    "AINSF-1378", "EAIN-1386", "DHA-2167-1400",
)


def require(value, message):
    if not value:
        raise AssertionError(message)


def doc(conn, ref):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    require(row, f"missing document {ref}")
    return row["id"]


def global_snapshot(conn):
    return tuple(conn.execute(
        """SELECT (SELECT COUNT(*) FROM documents),
                  (SELECT COUNT(*) FROM articles),
                  (SELECT COUNT(*) FROM articles WHERE is_current=1),
                  (SELECT COUNT(*) FROM articles WHERE is_current=0),
                  (SELECT COUNT(*) FROM relations),
                  (SELECT COUNT(*) FROM articles_fts)"""
    ).fetchone())


def main():
    conn = get_connection()
    docs = {ref: doc(conn, ref) for ref in REFS}

    # Law: 12 continuous article numbers, four historical rows.
    law_rows = conn.execute(
        "SELECT article_no,article_key,version_no,is_current,text FROM articles "
        "WHERE document_id=? ORDER BY id", (docs["QRS-1310"],)
    ).fetchall()
    require(len(law_rows) == 16, "QRS versions")
    require(sum(r["is_current"] for r in law_rows) == 12, "QRS current")
    require(len({r["article_key"] for r in law_rows}) == 12, "QRS coverage")
    expected_law = {f"QRS-1310:{n}" for n in range(1, 13)}
    require({r["article_key"] for r in law_rows} == expected_law, "QRS gap")
    for n in (2, 5, 6, 10):
        require(conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QRS-1310:{n}",)
        ).fetchone()[0] == 2, f"QRS history {n}")
    current5 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QRS-1310:5' AND is_current=1"
    ).fetchone()["text"]
    require("۸۲٬۵۰۰٬۰۰۰" in current5 and "۶۶٬۰۰۰٬۰۰۰" in current5,
            "QRS current penalties")
    require(conn.execute(
        "SELECT COUNT(*) FROM articles WHERE article_key='QRS-1310:10' AND is_current=0 "
        "AND text LIKE '%پنج تومان%'"
    ).fetchone()[0] == 1, "QRS original article 10")

    # Executive regulation: 1..36 plus article 28 bis. 31/32/36 are historical.
    exec_rows = conn.execute(
        "SELECT article_no,article_key,is_current,expiry_date,text FROM articles "
        "WHERE document_id=? ORDER BY id", (docs["NRS-1310"],)
    ).fetchall()
    require(len(exec_rows) == 37, "NRS row count")
    require(len({r["article_key"] for r in exec_rows}) == 37, "NRS unique keys")
    expected_exec = {f"NRS-1310:{n}" for n in range(1, 37)} | {"NRS-1310:28bis"}
    require({r["article_key"] for r in exec_rows} == expected_exec, "NRS gap")
    require(sum(r["is_current"] for r in exec_rows) == 34, "NRS current count")
    for key in (31, 32, 36):
        row = conn.execute(
            "SELECT is_current,expiry_date FROM articles WHERE article_key=?",
            (f"NRS-1310:{key}",),
        ).fetchone()
        require(row and not row["is_current"] and row["expiry_date"], f"NRS repeal {key}")

    expected_counts = {
        "NM196-1311": (10, 10), "QSF-1376": (1, 1),
        "AINSF-1378": (10, 10), "EAIN-1386": (10, 10),
        "DHA-2167-1400": (1, 1),
    }
    for ref, (rows, current) in expected_counts.items():
        got = conn.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(is_current),0) c FROM articles WHERE document_id=?",
            (docs[ref],),
        ).fetchone()
        require((got["n"], got["c"]) == (rows, current), f"count {ref}")

    # Every number stored by this package uses Persian digits, and no filler is present.
    marks = ",".join("?" for _ in docs)
    package_rows = conn.execute(
        f"SELECT article_no,text FROM articles WHERE document_id IN ({marks})",
        tuple(docs.values()),
    ).fetchall()
    require(all(not re.search(r"[0-9]", r["article_no"]) for r in package_rows),
            "ASCII digit in article_no")
    require(all(r["text"].strip() for r in package_rows), "empty text")
    require(all("ساختار تکمیلی" not in r["text"] and "متن نمونه" not in r["text"]
                for r in package_rows), "filler text")

    # Material and document links, including the Divan annulment and 1403 adjustment.
    require(conn.execute(
        f"SELECT COUNT(*) FROM relations WHERE from_document_id IN ({marks}) "
        f"OR to_document_id IN ({marks})", tuple(docs.values()) + tuple(docs.values())
    ).fetchone()[0] >= 20, "relations")
    require(conn.execute(
        """SELECT COUNT(*) FROM relations r
           JOIN documents f ON f.id=r.from_document_id
           JOIN documents t ON t.id=r.to_document_id
           WHERE f.reference_code='DHA-2167-1400' AND t.reference_code='NRS-1310'
             AND r.relation_type='overrules' AND r.to_article_id IS NOT NULL"""
    ).fetchone()[0] == 1, "Divan article relation")
    require(conn.execute(
        """SELECT COUNT(*) FROM relations r
           JOIN documents f ON f.id=r.from_document_id
           JOIN documents t ON t.id=r.to_document_id
           WHERE f.reference_code='TMJN-1403' AND t.reference_code='QRS-1310'
             AND r.relation_type='amends'"""
    ).fetchone()[0] == 4, "fine relations")

    # FTS5 over current texts.
    for term in (
        "ثبت شرکت", "شرکت ایرانی", "نماینده عمده", "شرکتنامه",
        "عمل متقابل", "گزارش مالی", "تبدیل شرکت", "مالکیت صنعتی",
    ):
        found = conn.execute(
            """SELECT COUNT(*) FROM articles_fts f
               JOIN articles a ON a.id=f.article_id
               WHERE articles_fts MATCH ? AND a.is_current=1""",
            (f'"{term}"',),
        ).fetchone()[0]
        require(found > 0, "FTS " + term)

    first_article = conn.execute(
        "SELECT id FROM articles WHERE document_id=? AND is_current=1 ORDER BY id LIMIT 1",
        (docs["QRS-1310"],),
    ).fetchone()["id"]
    before = global_snapshot(conn)
    conn.close()

    # CLI commands are part of the public interface.
    for args in (
        ["stats"], ["history", "QRS-1310:5"], ["search", "ثبت شرکت"],
    ):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "query.py"), *args],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=30,
        )
        require(proc.returncode == 0 and proc.stdout.strip(), "query.py " + " ".join(args))

    # Flask routes in all three document view modes.
    client = app.test_client()
    pages = ["/", "/?q=ثبت+شرکت", "/types", "/by-type/law", "/by-type/regulation"]
    for did in docs.values():
        pages.extend((f"/doc/{did}", f"/doc/{did}?view=historical", f"/doc/{did}?view=all"))
    pages.append(f"/article/{first_article}")
    for page in pages:
        require(client.get(page).status_code == 200, "Flask " + page)

    # A full second loader run must not alter global row counts.
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "load_company_registration.py")],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=60,
    )
    require(proc.returncode == 0, "idempotent loader: " + proc.stderr)
    conn = get_connection()
    after = global_snapshot(conn)
    conn.close()
    require(before == after, f"idempotency counts {before} != {after}")

    print("[OK] Company-registration law: 12 numbers, 16 versions, 12 current, 4 historical")
    print("[OK] Executive regulation: 37 provisions, 34 current, 3 historical")
    print("[OK] Trade bylaw=10; foreign branch law/bylaw=1/10; administration=10; Divan ruling=1")
    print("[OK] Persian article numbers, references, FTS5, query.py, Flask and idempotency")


if __name__ == "__main__":
    main()
