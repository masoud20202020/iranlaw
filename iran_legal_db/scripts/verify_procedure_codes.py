# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data" / "seed"))

from verification_utils import get_connection, require, verify_package
from criminal_procedure_user_source import ARTICLES_1_317

if __name__ == "__main__":
    verify_package(
        package_name="procedure_codes",
        refs=("QADM-1379", "QADK-1392"),
        expected_counts={"QADM-1379": (539, 539), "QADK-1392": (570, 570)},
        loader_script="load_procedure_codes.py",
        search_terms=("دادخواست", "بازپرس", "تجدیدنظر"),
        history_keys=("QADM-1379:1", "QADK-1392:1"),
        relation_min=4,
    )
    conn = get_connection()
    try:
        doc = conn.execute("SELECT id FROM documents WHERE reference_code='QADK-1392'").fetchone()
        require(doc, "missing QADK-1392")
        rows = conn.execute(
            "SELECT article_no, article_key, text, source_note FROM articles WHERE document_id=? AND CAST(article_key AS TEXT) LIKE 'QADK-1392:%'",
            (doc["id"],),
        ).fetchall()
        by_no = {int(r["article_key"].rsplit(":", 1)[1]): r for r in rows}
        require(set(by_no) >= set(range(1, 318)), "source-backed article range 1–317 is incomplete")
        for number, expected_text in ARTICLES_1_317:
            row = by_no[number]
            require(row["text"] == expected_text, f"source text mismatch at article {number}")
            require("novinlaw.ir" in (row["source_note"] or ""), f"missing NovinLaw provenance at article {number}")
            require("مقررات تکمیلی" not in row["text"], f"synthetic placeholder remains at article {number}")
        print("[OK] procedure_codes source-backed text: articles 1–317 and provenance")
    finally:
        conn.close()
