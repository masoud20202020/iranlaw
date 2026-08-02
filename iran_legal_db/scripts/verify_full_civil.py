# -*- coding: utf-8 -*-
from verification_utils import get_connection, require, verify_package


def coverage_check():
    conn = get_connection()
    try:
        doc = conn.execute("SELECT id FROM documents WHERE reference_code='QM-1307'").fetchone()
        require(doc, "missing QM-1307")
        keys = set()
        for row in conn.execute("SELECT article_key FROM articles WHERE document_id=?", (doc["id"],)):
            key = row["article_key"] or ""
            if key.startswith("QM:") and key.split(":", 1)[1].isdigit():
                keys.add(int(key.split(":", 1)[1]))
        missing = [n for n in range(1, 1201) if n not in keys]
        require(not missing, f"missing civil article keys in 1..1200: {missing[:20]}")
        current_989 = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='QM:989' AND is_current=1",
            (doc["id"],),
        ).fetchone()[0]
        historical_981 = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='QM:981' AND is_current=0",
            (doc["id"],),
        ).fetchone()[0]
        require(current_989 == 1, "QM:989 must have one current version")
        require(historical_981 >= 1, "QM:981 historical version is expected")
    finally:
        conn.close()


if __name__ == "__main__":
    coverage_check()
    verify_package(
        package_name="full_civil",
        refs=("QM-1307",),
        expected_counts={"QM-1307": (1209, 1207)},
        loader_script="complete_civil_code.py",
        search_terms=("قرارداد", "تابعیت", "ارث"),
        history_keys=("QM:989", "QM:981"),
        relation_min=1,
    )
    coverage_check()
