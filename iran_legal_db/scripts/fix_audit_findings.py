#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اصلاح‌های کم‌ریسک و تکرارپذیر بر پایه خروجی scripts/audit_db.py.

دامنه این اسکریپت عمداً محدود است:
  1) برای مواد قدیمی/نمونه که article_key ندارند، کلید پایدار deterministic می‌سازد.
  2) برای مواد بدون source_note، یادداشت منبع/ماهیت داده را صریح و غیرادعایی اضافه می‌کند.
  3) گونه املایی تکراری «هیأت/هیئت وزیران» را به مرجع معیار schema ادغام می‌کند.
  4) لینک‌های Markdown خالی و خط «منبع: URL» را، اگر به اشتباه داخل متن ماده مانده باشد، از متن حذف و FTS را همگام می‌کند.

این اسکریپت متن حقوقی را بازنویسی ماهوی نمی‌کند و تاریخ‌های ناقص/سال‌تنها را تغییر نمی‌دهد.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from schema import get_connection  # noqa: E402

PERSIAN_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

CORE_STARTER_REFS = {"QA-1358", "QMM-1339", "QS-1310"}


def key_fragment(article_no: str) -> str:
    raw = (article_no or "").strip().translate(PERSIAN_TO_ASCII)
    raw = raw.replace("ماده‌", "ماده ").replace("اصل‌", "اصل ")
    raw = re.sub(r"^(?:ماده|اصل)\s+", "", raw).strip()
    mapping = {
        "متن رأی": "ruling",
        "رأی": "ruling",
        "پاسخ": "response",
        "خلاصه": "summary",
        "ماده واحده": "single",
        "ماده‌واحده": "single",
    }
    if raw in mapping:
        return mapping[raw]
    raw = raw.replace(" ", "_").replace("/", "_").replace("-", "_")
    raw = re.sub(r"[^0-9A-Za-z_آ-ی]+", "", raw)
    return raw or "single"


def default_source_note(reference_code: str, doc_type_code: str) -> str:
    if reference_code in CORE_STARTER_REFS:
        return (
            "scripts/seed_core_laws.py؛ رکورد هسته اولیه و گزینشی پروژه است و "
            "برای استناد حرفه‌ای باید با متن رسمی/کامل منبع مقابله شود."
        )
    if doc_type_code in {"unified_ruling", "advisory_opinion", "divan_ruling", "circular", "treaty", "regulation"}:
        return (
            "data/seed/other_docs.py؛ رکورد نمونه/خلاصه ساختاری منبع‌دار پروژه است و "
            "رونوشت کامل رسمی محسوب نمی‌شود مگر در notes سند خلاف آن تصریح شده باشد."
        )
    return "رکورد قدیمی پروژه؛ منبع دقیق باید در مرحله تکمیل منابع رسمی بازبینی و تکمیل شود."


def clean_article_text(text: str) -> str:
    original = text or ""
    text = re.sub(r"!?\[\]\([^)]+\)", "", original)
    text = re.sub(r"(?m)^\s*منبع\s*:\s*https?://\S+\s*$", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def update_fts(conn, article_id: int, document_id: int, article_no: str, text: str) -> None:
    title = conn.execute("SELECT title FROM documents WHERE id=?", (document_id,)).fetchone()["title"]
    conn.execute("DELETE FROM articles_fts WHERE article_id=?", (article_id,))
    conn.execute(
        "INSERT INTO articles_fts(article_id, document_id, title, article_no, text) VALUES(?,?,?,?,?)",
        (article_id, document_id, title, article_no, text),
    )


def merge_cabinet_authority(conn) -> int:
    canonical = conn.execute("SELECT id FROM authorities WHERE name_fa=?", ("هیئت وزیران",)).fetchone()
    if not canonical:
        canonical_id = conn.execute(
            "INSERT INTO authorities(name_fa, authority_type) VALUES(?, 'executive')",
            ("هیئت وزیران",),
        ).lastrowid
    else:
        canonical_id = canonical["id"]
    duplicate = conn.execute("SELECT id FROM authorities WHERE name_fa=?", ("هیأت وزیران",)).fetchone()
    changed = 0
    if duplicate and duplicate["id"] != canonical_id:
        changed += conn.execute(
            "UPDATE documents SET issuing_authority_id=? WHERE issuing_authority_id=?",
            (canonical_id, duplicate["id"]),
        ).rowcount
        conn.execute("DELETE FROM authorities WHERE id=?", (duplicate["id"],))
    conn.execute("UPDATE authorities SET authority_type='executive' WHERE id=?", (canonical_id,))
    return changed


def patch_missing_article_metadata(conn) -> tuple[int, int]:
    key_updates = 0
    source_updates = 0
    rows = conn.execute(
        """
        SELECT a.id, a.document_id, a.article_no, a.article_key, a.source_note,
               d.reference_code, dt.code AS type_code
        FROM articles a
        JOIN documents d ON d.id=a.document_id
        JOIN document_types dt ON dt.id=d.type_id
        WHERE a.article_key IS NULL OR TRIM(a.article_key)=''
           OR a.source_note IS NULL OR TRIM(a.source_note)=''
        ORDER BY a.id
        """
    ).fetchall()
    for row in rows:
        updates = {}
        if not (row["article_key"] or "").strip():
            base = f"{row['reference_code']}:{key_fragment(row['article_no'])}"
            key = base
            i = 2
            while conn.execute("SELECT 1 FROM articles WHERE article_key=? AND id<>?", (key, row["id"])).fetchone():
                key = f"{base}_{i}"
                i += 1
            updates["article_key"] = key
            key_updates += 1
        if not (row["source_note"] or "").strip():
            updates["source_note"] = default_source_note(row["reference_code"], row["type_code"])
            source_updates += 1
        if updates:
            sets = ", ".join(f"{col}=?" for col in updates)
            conn.execute(f"UPDATE articles SET {sets} WHERE id=?", (*updates.values(), row["id"]))
    return key_updates, source_updates


def patch_text_noise(conn) -> int:
    changed = 0
    rows = conn.execute(
        """
        SELECT id, document_id, article_no, text
        FROM articles
        WHERE text LIKE '%[](%' OR text LIKE '%منبع: http://%' OR text LIKE '%منبع: https://%'
        """
    ).fetchall()
    for row in rows:
        new_text = clean_article_text(row["text"])
        if new_text and new_text != row["text"]:
            conn.execute("UPDATE articles SET text=? WHERE id=?", (new_text, row["id"]))
            update_fts(conn, row["id"], row["document_id"], row["article_no"], new_text)
            changed += 1
    return changed


def main() -> int:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        key_updates, source_updates = patch_missing_article_metadata(conn)
        authority_doc_updates = merge_cabinet_authority(conn)
        text_updates = patch_text_noise(conn)
        conn.commit()
        print("[OK] fix_audit_findings")
        print("  article_key updates:", key_updates)
        print("  source_note updates:", source_updates)
        print("  authority document updates:", authority_doc_updates)
        print("  article text/FTS cleanups:", text_updates)
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
