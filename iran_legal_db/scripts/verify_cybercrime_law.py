# -*- coding: utf-8 -*-
"""Integrity, search, CLI, Flask and idempotency tests for the cyber package."""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "web")]
from schema import get_connection
from app import app

REFS = ("QJR-1388", "QADRE-1393", "AEEE-1393", "RVR-729-1391", "NM-679-1402")
PERSIAN = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def require(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def snapshot(conn):
    return tuple(
        conn.execute(
            """SELECT
               (SELECT COUNT(*) FROM documents),
               (SELECT COUNT(*) FROM articles),
               (SELECT COUNT(*) FROM articles WHERE is_current=1),
               (SELECT COUNT(*) FROM articles WHERE is_current=0),
               (SELECT COUNT(*) FROM relations),
               (SELECT COUNT(*) FROM articles_fts)"""
        ).fetchone()
    )


def main() -> None:
    conn = get_connection()
    docs = {}
    for ref in REFS:
        row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
        require(row, f"missing document {ref}")
        docs[ref] = row["id"]

    expected = {
        "QJR-1388": (96, 32, 64),
        "QADRE-1393": (47, 41, 6),
        "AEEE-1393": (48, 48, 0),
        "RVR-729-1391": (1, 1, 0),
        "NM-679-1402": (1, 1, 0),
    }
    for ref, counts in expected.items():
        row = conn.execute(
            """SELECT COUNT(*) AS total, SUM(is_current) AS current,
                      SUM(CASE WHEN is_current=0 THEN 1 ELSE 0 END) AS historical
               FROM articles WHERE document_id=?""",
            (docs[ref],),
        ).fetchone()
        require((row["total"], row["current"], row["historical"]) == counts, f"counts {ref}")

    law_keys = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT article_key FROM articles WHERE document_id=?", (docs["QJR-1388"],)
        )
    }
    require(law_keys == {f"QJR-1388:{n}" for n in range(1, 57)}, "law coverage 1-56")
    law_current = {
        row[0]
        for row in conn.execute(
            "SELECT article_key FROM articles WHERE document_id=? AND is_current=1",
            (docs["QJR-1388"],),
        )
    }
    require(
        law_current == {f"QJR-1388:{n}" for n in list(range(1, 28)) + list(range(52, 57))},
        "current/repealed law split",
    )
    for number, versions in ((1, 3), (13, 3), (16, 4), (24, 2), (28, 1), (51, 1)):
        count = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QJR-1388:{number}",)
        ).fetchone()[0]
        require(count == versions, f"law history {number}")
    for number in range(28, 52):
        row = conn.execute(
            "SELECT is_current, expiry_date FROM articles WHERE article_key=?",
            (f"QJR-1388:{number}",),
        ).fetchone()
        require(row and row["is_current"] == 0 and row["expiry_date"] == "2015-06-22", f"repeal {number}")

    article_16 = conn.execute(
        "SELECT id, text FROM articles WHERE article_key='QJR-1388:16' AND is_current=1"
    ).fetchone()
    require("چهل و پنج روز و دوازده ساعت تا یک سال" in article_16["text"], "article 16 imprisonment")
    require("۵۰٬۰۰۰٬۰۰۰" in article_16["text"] and "۳۳۰٬۰۰۰٬۰۰۰" in article_16["text"], "article 16 fine")
    article_13 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QJR-1388:13' AND is_current=1"
    ).fetchone()["text"]
    require("۱۶۵٬۰۰۰٬۰۰۰" in article_13 and "۸۲۵٬۰۰۰٬۰۰۰" in article_13, "article 13 current fine")

    proc_expected = {f"QADRE-1393:{n}" for n in range(649, 688)} | {"QADRE-1393:698", "QADRE-1393:699"}
    proc_current = {
        row[0]
        for row in conn.execute(
            "SELECT article_key FROM articles WHERE document_id=? AND is_current=1",
            (docs["QADRE-1393"],),
        )
    }
    require(proc_current == proc_expected, "procedure coverage")
    for number in (660, 661, 669):
        require(
            conn.execute("SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QADRE-1393:{number}",)).fetchone()[0] == 3,
            f"procedure fine history {number}",
        )
    p669 = conn.execute(
        "SELECT text FROM articles WHERE article_key='QADRE-1393:669' AND is_current=1"
    ).fetchone()["text"]
    require("۳۳٬۰۰۰٬۰۰۰" in p669 and "۶۶٬۰۰۰٬۰۰۰" in p669, "article 669 fine")

    bylaw_numbers = [
        row[0]
        for row in conn.execute(
            "SELECT article_no FROM articles WHERE document_id=? ORDER BY id", (docs["AEEE-1393"],)
        )
    ]
    require(bylaw_numbers == [str(n).translate(PERSIAN) for n in range(1, 49)], "bylaw sequence")
    b41 = conn.execute(
        "SELECT text FROM articles WHERE article_key='AEEE-1393:41'"
    ).fetchone()["text"]
    require("مدت ۵ روز" in b41 and "به صورت مستدل" in b41, "bylaw article 41 note")

    all_rows = conn.execute(
        "SELECT article_no, text FROM articles WHERE document_id IN (?,?,?,?,?)", tuple(docs.values())
    ).fetchall()
    require(all(row["text"].strip() for row in all_rows), "empty text")
    require(all(not re.search(r"[0-9]", row["article_no"]) for row in all_rows), "ASCII article number")
    require(all("متن نمونه" not in row["text"] and "ساختار تکمیلی" not in row["text"] for row in all_rows), "filler")

    for term in (
        "دسترسی غیرمجاز",
        "کلاهبرداری رایانه‌ای",
        "داده ترافیک",
        "زنجیره حفاظتی",
        "حفظ فوری",
        "ارز دیجیتال",
        "صلاحیت محلی",
    ):
        count = conn.execute(
            """SELECT COUNT(*) FROM articles_fts f
               JOIN articles a ON a.id=f.article_id
               WHERE articles_fts MATCH ? AND a.is_current=1""",
            (f'"{term}"',),
        ).fetchone()[0]
        require(count > 0, f"FTS {term}")
    require(
        conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
        == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "FTS parity",
    )

    abrogations = conn.execute(
        """SELECT COUNT(*) FROM relations
           WHERE from_document_id=? AND to_document_id=? AND relation_type='abrogates'""",
        (docs["QADRE-1393"], docs["QJR-1388"]),
    ).fetchone()[0]
    require(abrogations == 24, "24 procedural repeals")
    require(
        conn.execute(
            """SELECT COUNT(*) FROM relations
               WHERE from_document_id=? AND to_document_id=? AND relation_type='implements'""",
            (docs["AEEE-1393"], docs["QADRE-1393"]),
        ).fetchone()[0] >= 8,
        "bylaw relation network",
    )
    require(
        conn.execute(
            "SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='interprets'",
            (docs["RVR-729-1391"],),
        ).fetchone()[0] == 1,
        "ruling relation",
    )
    require(
        conn.execute(
            "SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='interprets'",
            (docs["NM-679-1402"],),
        ).fetchone()[0] == 1,
        "opinion relation",
    )
    require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign key check")
    before = snapshot(conn)
    conn.close()

    for args in (
        ["stats"],
        ["history", "QJR-1388:16"],
        ["history", "QADRE-1393:669"],
        ["search", "زنجیره حفاظتی"],
    ):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "query.py"), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        require(result.returncode == 0 and result.stdout.strip(), f"query.py {' '.join(args)}")

    client = app.test_client()
    pages = [
        "/",
        "/?q=کلاهبرداری+رایانه‌ای",
        "/types",
        "/by-type/law",
        "/by-type/regulation",
        "/by-type/unified_ruling",
        "/by-type/advisory_opinion",
    ]
    for document_id in docs.values():
        pages.extend(
            [
                f"/doc/{document_id}",
                f"/doc/{document_id}?view=all",
                f"/doc/{document_id}?view=historical",
            ]
        )
    pages.append(f"/article/{article_16['id']}")
    for page in pages:
        require(client.get(page).status_code == 200, f"Flask {page}")

    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "load_cybercrime_law.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    require(result.returncode == 0, result.stderr)
    conn = get_connection()
    after = snapshot(conn)
    require(before == after, f"idempotency {before} != {after}")
    require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity check")
    conn.close()

    print("[OK] Cybercrime Law: 56 numbers, 96 versions, 32 current, 64 historical")
    print("[OK] Electronic procedure=41/47 versions; evidence bylaw=48; ruling/opinion=1/1")
    print("[OK] Coverage, fine histories, repeals, Persian numbers, FTS5, relations, query.py, Flask and idempotency")


if __name__ == "__main__":
    main()
