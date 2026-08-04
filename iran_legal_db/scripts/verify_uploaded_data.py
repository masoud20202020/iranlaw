#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier for the uploaded category data pack."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "data" / "seed"), str(ROOT / "web")]

from schema import get_connection  # noqa: E402
from uploaded_data import DOCUMENTS  # noqa: E402


PERSIAN_OR_NON_DIGIT = re.compile(r"[0-9٠-٩]")


def snapshot(conn):
    return tuple(
        conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM documents),
              (SELECT COUNT(*) FROM articles),
              (SELECT COUNT(*) FROM articles WHERE is_current=1),
              (SELECT COUNT(*) FROM articles WHERE is_current=0),
              (SELECT COUNT(*) FROM relations),
              (SELECT COUNT(*) FROM articles_fts)
            """
        ).fetchone()
    )


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    refs = [doc["ref"] for doc in DOCUMENTS]
    require(len(refs) == len(set(refs)), "duplicate uploaded reference codes in seed")
    conn = get_connection()
    try:
        for doc in DOCUMENTS:
            d = conn.execute("SELECT id FROM documents WHERE reference_code=?", (doc["ref"],)).fetchone()
            require(d, f"missing uploaded document {doc['ref']}")
            row = conn.execute(
                """
                SELECT COUNT(*) AS total, COALESCE(SUM(is_current),0) AS current
                FROM articles WHERE document_id=?
                """,
                (d["id"],),
            ).fetchone()
            expected_current = 0 if doc["status_code"] == "abrogated" else doc["article_count"]
            require((row["total"], row["current"]) == (doc["article_count"], expected_current), f"count mismatch {doc['ref']}: {(row['total'], row['current'])}")
            articles = conn.execute("SELECT article_no, article_key, text, source_note FROM articles WHERE document_id=?", (d["id"],)).fetchall()
            require(all(a["text"] and a["text"].strip() for a in articles), f"empty text {doc['ref']}")
            require(all(a["source_note"] and a["source_note"].strip() for a in articles), f"missing source {doc['ref']}")
            require(all(a["article_key"] and a["article_key"].startswith(doc["ref"] + ":") for a in articles), f"unstable article key {doc['ref']}")
            require(all(not PERSIAN_OR_NON_DIGIT.search(a["article_no"] or "") for a in articles), f"non-Persian article number {doc['ref']}")

        require(conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0], "FTS parity")
        require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
        require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
        before = snapshot(conn)
        first_doc = conn.execute("SELECT id FROM documents WHERE reference_code=?", (DOCUMENTS[0]["ref"],)).fetchone()[0]
        first_article = conn.execute("SELECT id FROM articles WHERE document_id=? ORDER BY id LIMIT 1", (first_doc,)).fetchone()[0]

        for term in ("دانشگاه", "مالیات", "وکالت", "شهرداری", "معاهده", "ایثارگر", "زمین", "فوتبال", "حمل و نقل", "مقررات"):
            count = conn.execute(
                """
                SELECT COUNT(*) FROM articles_fts f
                JOIN articles a ON a.id=f.article_id
                WHERE articles_fts MATCH ? AND a.is_current=1
                """,
                (f'"{term}"',),
            ).fetchone()[0]
            require(count > 0, f"FTS term not found: {term}")
    finally:
        conn.close()

    from app import app  # noqa: E402

    client = app.test_client()
    require(client.get("/").status_code == 200, "Flask home")
    require(client.get(f"/doc/{first_doc}").status_code == 200, "Flask document")
    require(client.get(f"/article/{first_article}").status_code == 200, "Flask article")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "load_uploaded_data.py")],
        cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600,
    )
    require(proc.returncode == 0, f"idempotency loader failed:\n{proc.stderr}")
    conn = get_connection()
    try:
        require(before == snapshot(conn), f"snapshot changed after rerun: {before} -> {snapshot(conn)}")
    finally:
        conn.close()
    print(f"[OK] uploaded_data: {len(DOCUMENTS)} documents; articles, source notes, Persian numbers, FTS, CLI, Flask and idempotency")


if __name__ == "__main__":
    main()
