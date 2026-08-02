# -*- coding: utf-8 -*-
"""Shared helpers for package verifiers."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "web")]

from schema import get_connection  # noqa: E402
from app import app  # noqa: E402


def require(condition, message):
    if not condition:
        raise AssertionError(message)


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


def verify_package(*, package_name, refs, expected_counts, loader_script, search_terms=(), history_keys=(), relation_min=0):
    """Verify a compact package with document/article counts, FTS, CLI, Flask and idempotency.

    refs: iterable of document reference_code values.
    expected_counts: dict[reference_code] = (total_articles, current_articles)
    loader_script: filename under scripts/, e.g. 'load_energy.py'
    """
    conn = get_connection()
    docs = {}
    try:
        for ref in refs:
            row = conn.execute("SELECT id,title FROM documents WHERE reference_code=?", (ref,)).fetchone()
            require(row, f"missing document {ref}")
            docs[ref] = row["id"]
        for ref, expected in expected_counts.items():
            row = conn.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(is_current),0) AS current FROM articles WHERE document_id=?",
                (docs[ref],),
            ).fetchone()
            require((row["total"], row["current"]) == expected, f"article count mismatch for {ref}: {(row['total'], row['current'])} != {expected}")
            rows = conn.execute("SELECT article_no, article_key, text, source_note FROM articles WHERE document_id=?", (docs[ref],)).fetchall()
            require(all(r["text"] and r["text"].strip() for r in rows), f"empty text in {ref}")
            require(all(r["source_note"] and r["source_note"].strip() for r in rows), f"missing source_note in {ref}")
            require(all(r["article_key"] and r["article_key"].strip() for r in rows), f"missing article_key in {ref}")
            require(all(not re.search(r"[0-9]", r["article_no"] or "") for r in rows), f"ASCII digit in article_no for {ref}")
            require(all("�" not in r["text"] for r in rows), f"replacement char leak in {ref}")
        if relation_min:
            placeholders = ",".join("?" * len(docs))
            count = conn.execute(
                f"SELECT COUNT(*) FROM relations WHERE from_document_id IN ({placeholders})",
                tuple(docs.values()),
            ).fetchone()[0]
            require(count >= relation_min, f"relations below minimum: {count} < {relation_min}")
        require(conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0], "FTS parity")
        require(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
        require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
        for term in search_terms:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM articles_fts f JOIN articles a ON a.id=f.article_id
                WHERE articles_fts MATCH ? AND a.is_current=1
                """,
                (f'"{term}"',),
            ).fetchone()[0]
            require(count > 0, f"FTS term not found: {term}")
        before = snapshot(conn)
        first_doc = next(iter(docs.values()))
        first_article = conn.execute("SELECT id FROM articles WHERE document_id=? ORDER BY id LIMIT 1", (first_doc,)).fetchone()["id"]
    finally:
        conn.close()

    query_tests = [["stats"], ["show", str(first_doc)]]
    for term in search_terms[:1]:
        query_tests.append(["search", term])
    for key in history_keys[:2]:
        query_tests.append(["history", key])
    for args in query_tests:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "query.py"), *args],
            cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
        )
        require(proc.returncode == 0 and proc.stdout.strip(), f"query.py failed: {' '.join(args)}\n{proc.stderr}")

    client = app.test_client()
    require(client.get("/").status_code == 200, "Flask home")
    require(client.get(f"/doc/{first_doc}").status_code == 200, "Flask doc")
    require(client.get(f"/article/{first_article}").status_code == 200, "Flask article")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / loader_script)],
        cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300,
    )
    require(proc.returncode == 0, f"loader idempotency run failed: {loader_script}\n{proc.stderr}")
    conn = get_connection()
    try:
        require(before == snapshot(conn), f"idempotency snapshot changed for {package_name}: {before} -> {snapshot(conn)}")
    finally:
        conn.close()
    print(f"[OK] {package_name}: {len(refs)} documents; counts, FTS, CLI, Flask and idempotency")
