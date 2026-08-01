# -*- coding: utf-8 -*-
"""Verification for the Labor Law, labor procedure and unemployment package."""
from __future__ import annotations
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "web")]
from schema import get_connection
from app import app

REFS = ("QK-1369", "AIDK-1391", "QBB-1369", "AIBB-1369", "RVR-720-1390", "DAD-17-20-1397")
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def req(value, message):
    if not value:
        raise AssertionError(message)


def snap(conn):
    return tuple(conn.execute("""SELECT (SELECT COUNT(*) FROM documents),(SELECT COUNT(*) FROM articles),
      (SELECT COUNT(*) FROM articles WHERE is_current=1),(SELECT COUNT(*) FROM articles WHERE is_current=0),
      (SELECT COUNT(*) FROM relations),(SELECT COUNT(*) FROM articles_fts)""").fetchone())


def main():
    conn = get_connection()
    docs = {}
    for ref in REFS:
        row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
        req(row, "missing " + ref)
        docs[ref] = row["id"]
    req(not conn.execute("SELECT 1 FROM documents WHERE reference_code='AQK-1370'").fetchone(), "obsolete placeholder remains")

    expected = {
        "QK-1369": (207, 203, 4), "AIDK-1391": (135, 135, 0),
        "QBB-1369": (14, 14, 0), "AIBB-1369": (24, 24, 0),
        "RVR-720-1390": (1, 1, 0), "DAD-17-20-1397": (1, 1, 0),
    }
    for ref, want in expected.items():
        row = conn.execute("""SELECT COUNT(*) n,SUM(is_current)c,
          SUM(CASE WHEN is_current=0 THEN 1 ELSE 0 END)h FROM articles WHERE document_id=?""", (docs[ref],)).fetchone()
        req((row["n"], row["c"], row["h"]) == want, "counts " + ref)

    labor_keys = {r[0] for r in conn.execute("SELECT DISTINCT article_key FROM articles WHERE document_id=?", (docs["QK-1369"],))}
    req(labor_keys == {f"QK-1369:{n}" for n in range(1, 204)}, "labor coverage")
    current_numbers = [r[0] for r in conn.execute("SELECT article_no FROM articles WHERE document_id=? AND is_current=1 ORDER BY id", (docs["QK-1369"],))]
    req(current_numbers == [str(n).translate(FA) for n in range(1, 204)], "labor current sequence")
    for n in (7, 10, 14, 21):
        req(conn.execute("SELECT COUNT(*) FROM articles WHERE article_key=?", (f"QK-1369:{n}",)).fetchone()[0] == 2, f"history {n}")
    a7 = conn.execute("SELECT text FROM articles WHERE article_key='QK-1369:7' AND is_current=1").fetchone()["text"]
    req("تبصره ۳" in a7 and "تبصره ۴" in a7, "article 7 additions")
    a14 = conn.execute("SELECT text FROM articles WHERE article_key='QK-1369:14' AND is_current=1").fetchone()["text"]
    req("تبصره ۲" in a14 and "کارهای سخت و زیان‌آور" in a14, "article 14 current")
    a21 = conn.execute("SELECT text FROM articles WHERE article_key='QK-1369:21' AND is_current=1").fetchone()["text"]
    req("اصلاح ساختار" in a21 and "بیمه بیکاری" in a21, "article 21 current")

    for ref, end in (("AIDK-1391", 135), ("QBB-1369", 14), ("AIBB-1369", 24)):
        keys = {r[0] for r in conn.execute("SELECT article_key FROM articles WHERE document_id=?", (docs[ref],))}
        req(keys == {f"{ref}:{n}" for n in range(1, end + 1)}, "coverage " + ref)
    p133 = conn.execute("SELECT text FROM articles WHERE article_key='AIDK-1391:133'").fetchone()["text"]
    req("جلسات رسیدگی" in p133 and "برخط" in p133 and "ویدئو کنفرانس" in p133, "electronic hearing")
    u7 = conn.execute("SELECT text FROM articles WHERE article_key='QBB-1369:7'").fetchone()["text"]
    req("۵۵%" in u7 and "۵۰" in u7 and "۳۶" in u7, "unemployment entitlement table")

    rows = conn.execute("SELECT article_no,text FROM articles WHERE document_id IN (?,?,?,?,?,?)", tuple(docs.values())).fetchall()
    req(all(r["text"].strip() for r in rows), "empty text")
    req(all(not re.search(r"[0-9]", r["article_no"]) for r in rows), "ASCII article number")
    req(all("متن نمونه" not in r["text"] and "ساختار تکمیلی" not in r["text"] for r in rows), "filler")
    req(all("https://" not in r["text"] for r in rows), "URL leaked into article text")

    for term in ("قرارداد کار", "هیأت حل اختلاف", "سامانه جامع روابط کار", "مقرری بیمه بیکاری", "غیرارادی بودن", "تسویه حساب", "حق بیمه"):
        count = conn.execute("""SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id
          WHERE articles_fts MATCH ? AND a.is_current=1""", (f'"{term}"',)).fetchone()[0]
        req(count > 0, "FTS " + term)
    req(conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0], "FTS parity")

    req(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id IN (?,?,?,?,?,?)", tuple(docs.values())).fetchone()[0] >= 8, "relations")
    req(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='implements'", (docs["AIDK-1391"],)).fetchone()[0] == 1, "procedure relation")
    req(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND relation_type='interprets'", (docs["DAD-17-20-1397"],)).fetchone()[0] == 2, "Divan relations")
    req(not conn.execute("PRAGMA foreign_key_check").fetchall(), "foreign keys")
    article_id = conn.execute("SELECT id FROM articles WHERE article_key='QK-1369:14' AND is_current=1").fetchone()[0]
    before = snap(conn)
    conn.close()

    for args in (["stats"], ["history", "QK-1369:14"], ["search", "سامانه جامع روابط کار"]):
        result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "query.py"), *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        req(result.returncode == 0 and result.stdout.strip(), "query " + " ".join(args))

    client = app.test_client()
    pages = ["/", "/?q=بیمه+بیکاری", "/types", "/by-type/law", "/by-type/regulation", "/by-type/unified_ruling", "/by-type/divan_ruling"]
    for did in docs.values():
        pages += [f"/doc/{did}", f"/doc/{did}?view=all", f"/doc/{did}?view=historical"]
    pages.append(f"/article/{article_id}")
    for page in pages:
        req(client.get(page).status_code == 200, "Flask " + page)

    result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "load_labor_law.py")], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    req(result.returncode == 0, result.stderr)
    conn = get_connection()
    after = snap(conn)
    req(before == after, f"idempotency {before} != {after}")
    req(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity")
    conn.close()
    print("[OK] Labor Law: 203 current articles, 207 total versions, 4 historical")
    print("[OK] Labor procedure=135; unemployment law/bylaw=14/24; rulings=2")
    print("[OK] Placeholder cleanup, coverage, histories, Persian numbers, FTS5, relations, query.py, Flask and idempotency")


if __name__ == "__main__":
    main()
