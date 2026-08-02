# -*- coding: utf-8 -*-
from verification_utils import ROOT, get_connection, require, verify_package


def coverage_check():
    conn = get_connection()
    try:
        doc = conn.execute("SELECT id FROM documents WHERE reference_code='QMA-1392'").fetchone()
        require(doc, "missing QMA-1392")
        keys = set()
        for row in conn.execute("SELECT article_key FROM articles WHERE document_id=? AND is_current=1", (doc["id"],)):
            key = row["article_key"] or ""
            if key.startswith("QMA:") and key.split(":", 1)[1].isdigit():
                keys.add(int(key.split(":", 1)[1]))
        missing = [n for n in range(1, 729) if n not in keys]
        require(not missing, f"missing penal article keys: {missing[:20]}")
    finally:
        conn.close()


if __name__ == "__main__":
    coverage_check()
    verify_package(
        package_name="penal_code",
        refs=("QMA-1392",),
        expected_counts={"QMA-1392": (728, 728)},
        loader_script="complete_penal_code.py",
        search_terms=("حدود", "قصاص", "تعزیر"),
        history_keys=("QMA:1", "QMA:728"),
        relation_min=2,
    )
    coverage_check()
