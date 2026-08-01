# -*- coding: utf-8 -*-
"""Integrity tests for the securities-market package."""
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
    "QBOV-1384", "AIBOV-1386", "QTNM-1388", "QTMZ-1402",
    "DSNM-1385", "DHSH-1401",
)


def require(value, message):
    if not value:
        raise AssertionError(message)


def doc(conn, ref):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    require(row, "missing " + ref)
    return row["id"]


def snapshot(conn):
    return tuple(conn.execute(
        """SELECT (SELECT COUNT(*) FROM documents),
                  (SELECT COUNT(*) FROM articles),
                  (SELECT COUNT(*) FROM articles WHERE is_current=1),
                  (SELECT COUNT(*) FROM articles WHERE is_current=0),
                  (SELECT COUNT(*) FROM relations),
                  (SELECT COUNT(*) FROM articles_fts)"""
    ).fetchone())


def count_doc(conn, did):
    return conn.execute(
        "SELECT COUNT(*) n,COALESCE(SUM(is_current),0) c,"
        "COALESCE(SUM(CASE WHEN is_current=0 THEN 1 ELSE 0 END),0) h "
        "FROM articles WHERE document_id=?", (did,)
    ).fetchone()


def main():
    conn = get_connection()
    docs = {ref: doc(conn, ref) for ref in REFS}

    market = count_doc(conn, docs["QBOV-1384"])
    require((market["n"], market["c"], market["h"]) == (62, 60, 2), "market counts")
    keys = {r[0] for r in conn.execute(
        "SELECT DISTINCT article_key FROM articles WHERE document_id=?", (docs["QBOV-1384"],)
    )}
    require(keys == {f"QBOV-1384:{n}" for n in range(1, 61)}, "market 1..60 coverage")
    for n in (7, 19):
        require(conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QBOV-1384:{n}",)
        ).fetchone()[0] == 2, f"market history {n}")
    current7 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QBOV-1384:7' AND is_current=1"
    ).fetchone()["text"]
    require("تأسیس و فعالیت" in current7 and "شرکت‌های سهامی عام ثبت شده نزد سازمان" in current7,
            "market current article 7")
    old7 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QBOV-1384:7' AND is_current=0"
    ).fetchone()["text"]
    require("شرکت‌های سهامی عام ثبت شده نزد سازمان" not in old7, "market old article 7")
    current19 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QBOV-1384:19' AND is_current=1"
    ).fetchone()["text"]
    require("کارگروه تعامل پذیری دولت الکترونیکی" in current19, "market current article 19")

    expected_counts = {
        "AIBOV-1386": (20, 20, 0),
        "QTNM-1388": (21, 18, 3),
        "QTMZ-1402": (46, 46, 0),
        "DSNM-1385": (7, 7, 0),
        "DHSH-1401": (48, 43, 5),
    }
    for ref, expected in expected_counts.items():
        got = count_doc(conn, docs[ref])
        require((got["n"], got["c"], got["h"]) == expected, f"counts {ref}")

    require(conn.execute(
        "SELECT COUNT(*) FROM articles WHERE article_key='QTNM-1388:14'"
    ).fetchone()[0] == 4, "four article-14 fine generations")
    current14 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QTNM-1388:14' AND is_current=1"
    ).fetchone()["text"]
    require("۱۰۰.۰۰۰.۰۰۰" in current14 and "۱۰.۰۰۰.۰۰۰.۰۰۰" in current14,
            "current administrative fine")

    for n in (4, 30, 36, 37, 43):
        require(conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (f"DHSH-1401:{n}",)
        ).fetchone()[0] == 2, f"governance history {n}")
    gov43 = conn.execute(
        "SELECT text FROM articles WHERE article_key='DHSH-1401:43' AND is_current=1"
    ).fetchone()["text"]
    require("۲۷، ۲۸، ۳۰" in gov43 and "ثبت شده‌اند" in gov43, "governance current 43")

    # Persian article numbers and no generated placeholder text.
    marks = ",".join("?" for _ in docs)
    rows = conn.execute(
        f"SELECT article_no,text FROM articles WHERE document_id IN ({marks})",
        tuple(docs.values()),
    ).fetchall()
    require(all(not re.search(r"[0-9]", r["article_no"]) for r in rows),
            "ASCII digit in article_no")
    require(all(r["text"].strip() for r in rows), "empty text")
    require(all("ساختار تکمیلی" not in r["text"] and "متن نمونه" not in r["text"]
                for r in rows), "filler text")

    # Relation network, including direct amendment of article 7 and company-law links.
    relation_count = conn.execute(
        f"SELECT COUNT(*) FROM relations WHERE from_document_id IN ({marks})",
        tuple(docs.values()),
    ).fetchone()[0]
    require(relation_count >= 25, "relation network")
    require(conn.execute(
        """SELECT COUNT(*) FROM relations r
           JOIN documents f ON f.id=r.from_document_id
           JOIN documents t ON t.id=r.to_document_id
           WHERE f.reference_code='QTMZ-1402' AND t.reference_code='QBOV-1384'
             AND r.relation_type='amends' AND r.from_article_id IS NOT NULL
             AND r.to_article_id IS NOT NULL"""
    ).fetchone()[0] == 1, "article 7 amendment relation")
    require(conn.execute(
        """SELECT COUNT(*) FROM relations r
           JOIN documents f ON f.id=r.from_document_id
           JOIN documents t ON t.id=r.to_document_id
           WHERE f.reference_code IN ('DSNM-1385','QTMZ-1402')
             AND t.reference_code='QRS-1310'"""
    ).fetchone()[0] == 2, "company registration links")

    # FTS5 over representative current terminology.
    for term in (
        "اوراق بهادار", "اطلاعات نهانی", "بازارگردان", "نهاد واسط",
        "صندوق سرمایه‌گذاری", "سامانه جامع وثایق", "حاکمیت شرکتی",
        "سهامداران اقلیت", "کمیته حسابرسی", "گزارش پایداری",
    ):
        found = conn.execute(
            """SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id
               WHERE articles_fts MATCH ? AND a.is_current=1""",
            (f'"{term}"',),
        ).fetchone()[0]
        require(found > 0, "FTS " + term)

    first_article = conn.execute(
        "SELECT id FROM articles WHERE document_id=? AND is_current=1 ORDER BY id LIMIT 1",
        (docs["QBOV-1384"],),
    ).fetchone()["id"]
    before = snapshot(conn)
    conn.close()

    for args in (
        ["stats"], ["history", "QBOV-1384:7"],
        ["history", "QTNM-1388:14"], ["search", "اطلاعات نهانی"],
    ):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "query.py"), *args],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=30,
        )
        require(proc.returncode == 0 and proc.stdout.strip(), "query.py " + " ".join(args))

    client = app.test_client()
    pages = ["/", "/?q=اوراق+بهادار", "/types", "/by-type/law", "/by-type/directive"]
    for did in docs.values():
        pages.extend((f"/doc/{did}", f"/doc/{did}?view=historical", f"/doc/{did}?view=all"))
    pages.append(f"/article/{first_article}")
    for page in pages:
        require(client.get(page).status_code == 200, "Flask " + page)

    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "load_securities_market.py")],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=90,
    )
    require(proc.returncode == 0, "idempotent loader: " + proc.stderr)
    conn = get_connection()
    after = snapshot(conn)
    conn.close()
    require(before == after, f"idempotency {before} != {after}")

    print("[OK] Securities Market Law: 60 numbers, 62 versions, 60 current, 2 historical")
    print("[OK] Bylaw=20; financial instruments=18/21 versions; financing law=46")
    print("[OK] Financial-entity registration=7; governance=43/48 versions")
    print("[OK] Coverage, Persian numbers, FTS5, relations, query.py, Flask and idempotency")


if __name__ == "__main__":
    main()
