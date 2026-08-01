# -*- coding: utf-8 -*-
"""Deterministic integrity/smoke checks for the commercial-law package."""
from __future__ import annotations

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "web"))

from schema import get_connection
from search_utils import expand_fts_query
from app import app

TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_document(conn, ref: str, expected_numbers: int, expected_versions: int, expected_current: int):
    doc = conn.execute(
        "SELECT id FROM documents WHERE reference_code=?", (ref,)
    ).fetchone()
    require(doc is not None, f"Missing document {ref}")
    rows = conn.execute(
        "SELECT article_no, article_key, text, is_current FROM articles WHERE document_id=?",
        (doc["id"],),
    ).fetchall()
    numbers = {int(row["article_no"].translate(TO_ASCII)) for row in rows}
    require(numbers == set(range(1, expected_numbers + 1)), f"Numeric gaps in {ref}")
    require(len(rows) == expected_versions, f"Unexpected version count in {ref}")
    require(sum(row["is_current"] for row in rows) == expected_current, f"Unexpected current count in {ref}")
    require(all(row["text"].strip() for row in rows), f"Blank text in {ref}")
    require(not any(re.search(r"[0-9]", row["article_no"]) for row in rows), f"ASCII article number in {ref}")
    require(not any("ساختار تکمیلی" in row["text"] for row in rows), f"Generated filler in {ref}")
    return doc["id"]


def main() -> None:
    conn = get_connection()
    code_id = verify_document(conn, "QT-1311", 600, 606, 526)
    bill_id = verify_document(conn, "LTEJ-1347", 300, 342, 280)

    for key, count in {
        "QT-1311:15": 2,
        "LTEJ-1347:17": 2,
        "LTEJ-1347:241": 2,
        "LTEJ-1347:243": 3,
    }.items():
        actual = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (key,)
        ).fetchone()[0]
        require(actual == count, f"Bad history length for {key}")

    duplicate_current = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT article_key FROM articles
            WHERE is_current=1 AND article_key IS NOT NULL
            GROUP BY article_key HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    require(duplicate_current == 0, "More than one current version for an article key")
    require(
        conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
        == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "FTS/article row mismatch",
    )

    for term in ("ورشکستگی", "برات", "سفته", "چک", "هیئت مدیره"):
        count = conn.execute("""
            SELECT COUNT(*) FROM articles_fts
            JOIN articles a ON a.id=articles_fts.article_id
            WHERE articles_fts MATCH ? AND a.is_current=1
        """, (expand_fts_query(term),)).fetchone()[0]
        require(count > 0, f"FTS has no result for {term}")

    relation_count = conn.execute("""
        SELECT COUNT(*) FROM relations r
        WHERE r.from_document_id IN (
            SELECT id FROM documents WHERE reference_code IN
            ('LTEJ-1347','ET17-1353','ET241-1395','TMJN-1399','TMJN-1403','FNAT-1403')
        )
    """).fetchone()[0]
    require(relation_count >= 70, "Commercial amendment network is incomplete")
    conn.close()

    client = app.test_client()
    paths = (
        "/", "/?q=سفته", "/types", "/by-type/amendment",
        f"/doc/{code_id}", f"/doc/{code_id}?view=all",
        f"/doc/{bill_id}", f"/doc/{bill_id}?view=historical",
    )
    for path in paths:
        response = client.get(path)
        require(response.status_code == 200, f"Web smoke test failed: {path}")

    print("[OK] 600/600 Commercial Code article numbers; 606 versions; 526 current")
    print("[OK] 300/300 amendment-bill article numbers; 342 versions; 280 current")
    print("[OK] histories, FTS aliases, relation network, and Flask routes")


if __name__ == "__main__":
    main()
