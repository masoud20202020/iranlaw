# -*- coding: utf-8 -*-
"""Verify miscellaneous sample documents that remain in the final database.

`load_other_docs.py` is a legacy/bootstrap loader used early in rebuilds. Several of its
placeholder records are intentionally superseded by later full packages, so this verifier
checks the final curated state instead of re-running that legacy loader.
"""
import re
import subprocess
import sys

from verification_utils import ROOT, app, get_connection, require, snapshot

ACTIVE_REFS = {
    "AQS-1311": (5, 5),
    "AQHKH-1392": (75, 67),  # superseded by the full family-law package
    "BS-1382-10000": (3, 3),
    "BS-1399-9000": (2, 2),
    "BS-1389-939": (2, 2),
    "RVR-452-1366": (1, 1),
    "RVR-540-1371": (1, 1),
    "RVR-462-1377": (1, 1),
    "RVR-578-1388": (1, 1),
    "NM-1665-1378": (1, 1),
    "NM-1382-84": (1, 1),
    "NM-2039-1392": (1, 1),
    "NM-1250-1400": (1, 1),
    "RD-120-1394": (1, 1),
    "RD-430-1397": (1, 1),
    "RD-10-1400": (1, 1),
    "RD-SH10-1398-1": (1, 1),
    "TREATY-VC": (3, 3),
    "TREATY-CRC": (5, 5),
}
REMOVED_OR_SUPERSEDED = {"AQK-1370"}


def main():
    conn = get_connection()
    try:
        before = snapshot(conn)
        docs = {}
        for ref, expected in ACTIVE_REFS.items():
            row = conn.execute("SELECT id,title FROM documents WHERE reference_code=?", (ref,)).fetchone()
            require(row, f"missing {ref}")
            docs[ref] = row["id"]
            counts = conn.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(is_current),0) AS current FROM articles WHERE document_id=?",
                (row["id"],),
            ).fetchone()
            require((counts["total"], counts["current"]) == expected, f"count mismatch {ref}: {(counts['total'], counts['current'])} != {expected}")
            for art in conn.execute("SELECT article_no,article_key,text,source_note FROM articles WHERE document_id=?", (row["id"],)):
                require(art["text"] and art["text"].strip(), f"empty text {ref}")
                require(art["source_note"] and art["source_note"].strip(), f"missing source_note {ref}")
                require(art["article_key"] and art["article_key"].strip(), f"missing article_key {ref}")
                require(not re.search(r"[0-9]", art["article_no"] or ""), f"ASCII article_no {ref}")
        for ref in REMOVED_OR_SUPERSEDED:
            require(not conn.execute("SELECT 1 FROM documents WHERE reference_code=?", (ref,)).fetchone(), f"legacy placeholder should remain removed: {ref}")
        require(conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0], "FTS parity")
        require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
        require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
        for term in ("مهریه", "کودک", "استرداد"):
            count = conn.execute(
                "SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id WHERE articles_fts MATCH ? AND a.is_current=1",
                (f'"{term}"',),
            ).fetchone()[0]
            require(count > 0, f"FTS term not found: {term}")
        first_doc = docs["TREATY-CRC"]
        first_article = conn.execute("SELECT id FROM articles WHERE document_id=? ORDER BY id LIMIT 1", (first_doc,)).fetchone()["id"]
    finally:
        conn.close()

    for args in (["stats"], ["show", str(first_doc)], ["search", "کنوانسیون کودک"]):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "query.py"), *args], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        require(proc.returncode == 0 and proc.stdout.strip(), f"query failed: {args}\n{proc.stderr}")
    client = app.test_client()
    require(client.get("/").status_code == 200, "Flask home")
    require(client.get(f"/doc/{first_doc}").status_code == 200, "Flask doc")
    require(client.get(f"/article/{first_article}").status_code == 200, "Flask article")
    conn = get_connection()
    try:
        require(before == snapshot(conn), "other_docs verifier must not mutate database")
    finally:
        conn.close()
    print(f"[OK] other_docs: {len(ACTIVE_REFS)} active miscellaneous documents; legacy placeholder AQK-1370 remains superseded")


if __name__ == "__main__":
    main()
