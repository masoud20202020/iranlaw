# -*- coding: utf-8 -*-
"""Integrity, FTS, history and Flask smoke tests for the cheque/Sayad package."""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "web"))

from schema import get_connection
from app import app

MAIN_REF = "QSC-1355"
REG_COUNTS = {"AIN5M-1398": 10, "CHKM-1400": 14, "CHKE-1402": 9, "SAYAD-1404": 1}
EXPECTED_CURRENT = [
    "۱", "۲", "۳", "۳ مکرر", "۴", "۵", "۵ مکرر", "۶", "۷", "۸", "۹", "۱۰",
    "۱۱", "۱۲", "۱۳", "۱۴", "۱۵", "۱۶", "۱۷", "۱۸", "۱۹", "۲۰", "۲۱", "۲۱ مکرر",
    "۲۲", "۲۳", "۲۴", "۲۵",
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    conn = get_connection()
    doc = conn.execute("SELECT id FROM documents WHERE reference_code=?", (MAIN_REF,)).fetchone()
    require(doc is not None, "Cheque law document is missing")
    doc_id = doc["id"]
    rows = conn.execute(
        "SELECT article_no,article_key,version_no,is_current,text FROM articles WHERE document_id=? ORDER BY id",
        (doc_id,),
    ).fetchall()
    require(len(rows) == 52, f"Expected 52 law versions, got {len(rows)}")
    current = [row for row in rows if row["is_current"]]
    require(len(current) == 28, f"Expected 28 current provisions, got {len(current)}")
    require([row["article_no"] for row in current] == EXPECTED_CURRENT, "Current provision sequence is wrong")
    require(len({row["article_key"] for row in rows}) == 28, "Stable-key coverage is incomplete")

    expected_histories = {"1": 2, "2": 2, "6": 3, "7": 4, "14": 3, "21": 3, "21bis": 2, "24": 1}
    for key, count in expected_histories.items():
        actual = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_key=?", (f"{MAIN_REF}:{key}",)
        ).fetchone()[0]
        require(actual == count, f"History length mismatch for article {key}")

    article7 = conn.execute(
        "SELECT text FROM articles WHERE article_key=? AND is_current=1", (f"{MAIN_REF}:7",)
    ).fetchone()["text"]
    require("۷۸۰٬۰۰۰٬۰۰۰" in article7 and "۳٬۹۰۰٬۰۰۰٬۰۰۰" in article7, "1403 amounts missing")
    article6_versions = conn.execute(
        "SELECT version_no,text FROM articles WHERE article_key=? ORDER BY version_no", (f"{MAIN_REF}:6",)
    ).fetchall()
    require("سه سال" in article6_versions[1]["text"], "1397 three-year validity history missing")
    require("حداکثر مدت اعتبار چک" not in article6_versions[-1]["text"], "Deleted validity remains in current article 6")

    for ref, count in REG_COUNTS.items():
        actual = conn.execute("""
            SELECT COUNT(*) FROM articles a JOIN documents d ON d.id=a.document_id
            WHERE d.reference_code=?
        """, (ref,)).fetchone()[0]
        require(actual == count, f"Unexpected article count for {ref}")

    duplicate_current = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT article_key FROM articles
            WHERE is_current=1 AND article_key IS NOT NULL
            GROUP BY article_key HAVING COUNT(*)>1
        )
    """).fetchone()[0]
    require(duplicate_current == 0, "Duplicate current article keys")
    require(
        conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
        == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "FTS row mismatch",
    )

    for term in ("صیاد", "چکاوک", "چکاد", "چک موردی", "چک الکترونیکی", "گواهینامه عدم پرداخت", "اجراییه"):
        count = conn.execute("""
            SELECT COUNT(*) FROM articles_fts
            JOIN articles a ON a.id=articles_fts.article_id
            WHERE articles_fts MATCH ? AND a.is_current=1
        """, (f'"{term}"',)).fetchone()[0]
        require(count > 0, f"No current FTS result for {term}")

    package_relations = conn.execute("""
        SELECT COUNT(*) FROM relations WHERE from_document_id IN (
            SELECT id FROM documents WHERE reference_code IN
            ('QSC-1355','ESCHK-1372','ECH2-1376','ECH14-1376','ISTCHK-1377',
             'ESCHK-1382','ESCHK-1397','ESCHK-1400','AIN5M-1398','CHKM-1400','CHKE-1402','SAYAD-1404')
        )
    """).fetchone()[0]
    require(package_relations >= 40, "Cheque amendment/relation network is incomplete")

    article7_id = conn.execute(
        "SELECT id FROM articles WHERE article_key=? AND is_current=1", (f"{MAIN_REF}:7",)
    ).fetchone()["id"]
    conn.close()

    client = app.test_client()
    paths = (
        "/", "/?q=صیاد", "/?q=چکاد", "/types", "/by-type/directive",
        f"/doc/{doc_id}", f"/doc/{doc_id}?view=all", f"/doc/{doc_id}?view=historical",
        f"/article/{article7_id}",
    )
    for path in paths:
        response = client.get(path)
        require(response.status_code == 200, f"Flask smoke test failed for {path}")

    print("[OK] Cheque Law: 28 current provisions, 52 total versions, 24 historical")
    print("[OK] Amendment acts: 1372, 1376, 1382, 1397, 1400; interpretation 1377; amounts 1403")
    print("[OK] Sayad rules: article-5-bis bylaw, case cheques, electronic cheques, 1404 official summary")
    print("[OK] FTS, relation network, stable keys and Flask routes")


if __name__ == "__main__":
    main()
