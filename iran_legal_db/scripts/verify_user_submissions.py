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
        "QKID-1353-66": 12,
        "AIPIGE-1354-821": 7,
        "QPIGE-1351-820": 1,
        "QHG-1367-72": 7,
        "QBRF-1367-41": 8,
        "QUCB-1384-435": 12,
        "AIGTE-1373-817": 36,
        "QGTE-1367-816": 56,
        "QAIR-1368-553": 23,
        "QPRP-1365-925": 19,
        "QPOL-1395-53": 6,
        "QEX-1339-226": 27,
        "QOIL-1336-77": 19,
        "QEXAM-1384-519": 13,
        "QLPR-1399-31": 15,
        "QHT-1383-56": 8,
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
        require("show/32" in (conn.execute("SELECT notes FROM documents WHERE reference_code='QJR-1388'").fetchone()[0] or ""), "missing existing cybercrime source registration")
        require("show/490" in (conn.execute("SELECT notes FROM documents WHERE reference_code='QHBJM-1346'").fetchone()[0] or ""), "missing existing forest-law source registration")
        qmk_notes = conn.execute("SELECT notes FROM documents WHERE reference_code='QMK-1392'").fetchone()[0] or ""
        require("show/697" in qmk_notes and "show/701" in qmk_notes and "show/706" in qmk_notes, "missing existing smuggling-law source registration")
        print("[OK] user_submissions new laws: 21 documents, 315 articles, source provenance; 3 existing sources deduplicated")
    finally:
        conn.close()
