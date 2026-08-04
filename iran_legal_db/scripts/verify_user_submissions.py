#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifier for the five user-submitted legal texts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from verification_utils import get_connection, require, verify_package  # noqa: E402
from user_submissions import DOCUMENTS  # noqa: E402


if __name__ == "__main__":
    refs = tuple(d["ref"] for d in DOCUMENTS)
    counts = {d["ref"]: (d["article_count"], d["article_count"]) for d in DOCUMENTS}
    verify_package(
        package_name="user_submissions",
        refs=refs,
        expected_counts=counts,
        loader_script="load_user_submissions.py",
        search_terms=("مواد مخدر", "صحنه جرم", "اجرای احکام", "خدمات عمومی رایگان", "تالاب"),
        history_keys=("CIR-MM-714-1396:b01", "AICR-768-1396:a001", "AIM79-1393:a001"),
        relation_min=5,
    )
    expected_new = {
        "QPCP-1390-48": 6,
        "QSID-1370-217": 23,
        "QACID-1398-44": 7,
        "QESP-1404-86": 9,
        "QCBN-1368-85": 1,
    }
    conn = get_connection()
    try:
        for ref, count in expected_new.items():
            doc = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
            require(doc, f"missing new user law {ref}")
            row = conn.execute(
                "SELECT COUNT(*) AS n, SUM(CASE WHEN source_note LIKE '%novinlaw.ir%' THEN 1 ELSE 0 END) AS sourced FROM articles WHERE document_id=?",
                (doc["id"],),
            ).fetchone()
            require(row["n"] == count, f"count mismatch for {ref}: {row['n']} != {count}")
            require(row["sourced"] == count, f"missing NovinLaw source notes for {ref}")
        print("[OK] user_submissions new laws: 5 documents, 46 articles, source provenance")
    finally:
        conn.close()
