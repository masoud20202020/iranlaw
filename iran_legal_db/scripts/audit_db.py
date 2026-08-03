#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ممیزی سراسری بانک اطلاعات حقوقی ایران.

این ابزار برای «فاز صفر» کنترل کیفیت پروژه ساخته شده است و بدون تغییر دادن دیتابیس،
سلامت ساختاری، کامل‌بودن حداقلی رکوردها، هماهنگی FTS5، روابط، نسخه‌بندی مواد و وضعیت
اسکریپت‌های loader/verifier را گزارش می‌کند.

نمونه استفاده:
    python3 scripts/audit_db.py
    python3 scripts/audit_db.py --format markdown
    python3 scripts/audit_db.py --format json --output exports/audit.json
    python3 scripts/audit_db.py --format markdown --output docs/گزارش_وضعیت_و_کیفیت_دیتابیس.md
    python3 scripts/audit_db.py --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from schema import DB_PATH, get_connection  # noqa: E402

LOCAL_DATE_GREGORIAN = "2026-08-04"
LOCAL_DATE_JALALI = "۱۴۰۵/۰۵/۱۳"

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ALLOWED_RELATION_TYPES = {
    "amends",
    "abrogates",
    "implements",
    "cites",
    "interprets",
    "ruled_by_divan",
    "overrules",
    "repealed_by",
    "has_historical_version",
}

ISSUE_LEVELS = ("error", "warning", "info")


@dataclass
class Issue:
    level: str
    code: str
    title: str
    count: int = 0
    samples: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class AuditReport:
    generated_at: str
    generated_at_jalali: str
    db_path: str
    summary: dict[str, Any]
    distributions: dict[str, list[dict[str, Any]]]
    issues: list[Issue]
    script_inventory: dict[str, Any]


def fa_num(value: Any) -> str:
    """Convert ASCII digits in a value to Persian digits for Markdown display."""
    return str(value).translate(PERSIAN_DIGITS)


def row_to_dict(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return {k: row[k] for k in row.keys()}
    return dict(row)


def rows_to_dicts(rows: Iterable[sqlite3.Row], limit: int = 10) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        d = row_to_dict(row) or {}
        out.append(d)
        if len(out) >= limit:
            break
    return out


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    row = conn.execute(sql, params).fetchone()
    return row[0] if row is not None else 0


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name=? AND type IN ('table','view')",
            (table,),
        ).fetchone()
    )


def collect_distribution(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    return rows_to_dicts(conn.execute(sql), limit=10_000)


def sample_issue(
    conn: sqlite3.Connection,
    *,
    level: str,
    code: str,
    title: str,
    count_sql: str,
    sample_sql: str | None = None,
    recommendation: str = "",
    params: tuple[Any, ...] = (),
    sample_limit: int = 10,
) -> Issue | None:
    count = int(scalar(conn, count_sql, params))
    if count <= 0:
        return None
    samples: list[dict[str, Any]] = []
    if sample_sql:
        samples = rows_to_dicts(conn.execute(sample_sql, (*params, sample_limit)), sample_limit)
    return Issue(level=level, code=code, title=title, count=count, samples=samples, recommendation=recommendation)


def iso_date_issues(conn: sqlite3.Connection) -> list[Issue]:
    issues: list[Issue] = []
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    year_re = re.compile(r"^\d{4}$")

    doc_cols = ["ratification_date", "publication_date", "effective_date"]
    bad_docs: list[dict[str, Any]] = []
    partial_docs: list[dict[str, Any]] = []
    for row in conn.execute(
        "SELECT id, reference_code, title, ratification_date, publication_date, effective_date FROM documents"
    ):
        for col in doc_cols:
            val = row[col]
            if val and not iso_re.match(str(val)):
                item = {
                    "id": row["id"],
                    "reference_code": row["reference_code"],
                    "title": row["title"],
                    "field": col,
                    "value": val,
                }
                if year_re.match(str(val)):
                    partial_docs.append(item)
                else:
                    bad_docs.append(item)
                break
    if bad_docs:
        issues.append(
            Issue(
                level="warning",
                code="DOC_DATE_FORMAT",
                title="تاریخ‌های سند با قالب استاندارد قابل قبول سازگار نیستند",
                count=len(bad_docs),
                samples=bad_docs[:10],
                recommendation="تاریخ‌های سند را در قالب ISO YYYY-MM-DD تکمیل کنید؛ اگر فقط سال در منبع معلوم است، مقدار سال‌تنها را نگه دارید و در notes محدودیت منبع را توضیح دهید.",
            )
        )
    if partial_docs:
        issues.append(
            Issue(
                level="info",
                code="DOC_PARTIAL_YEAR_DATE",
                title="برخی تاریخ‌های سند فقط در سطح سال شناخته شده‌اند",
                count=len(partial_docs),
                samples=partial_docs[:10],
                recommendation="این مورد خطا نیست؛ اما برای فیلتر زمانی دقیق، در صورت یافتن منبع رسمی، ماه و روز تصویب/اجرا تکمیل شود.",
            )
        )

    art_cols = ["effective_date", "expiry_date"]
    bad_articles: list[dict[str, Any]] = []
    partial_articles: list[dict[str, Any]] = []
    for row in conn.execute(
        """
        SELECT a.id, d.reference_code, a.article_key, a.article_no, a.effective_date, a.expiry_date
        FROM articles a JOIN documents d ON d.id=a.document_id
        """
    ):
        for col in art_cols:
            val = row[col]
            if val and not iso_re.match(str(val)):
                item = {
                    "id": row["id"],
                    "reference_code": row["reference_code"],
                    "article_key": row["article_key"],
                    "article_no": row["article_no"],
                    "field": col,
                    "value": val,
                }
                if year_re.match(str(val)):
                    partial_articles.append(item)
                else:
                    bad_articles.append(item)
                break
    if bad_articles:
        issues.append(
            Issue(
                level="warning",
                code="ARTICLE_DATE_FORMAT",
                title="تاریخ‌های ماده با قالب استاندارد قابل قبول سازگار نیستند",
                count=len(bad_articles),
                samples=bad_articles[:10],
                recommendation="تاریخ اثر و پایان اعتبار نسخه‌ها را تکمیل کنید؛ اگر فقط سال در منبع معلوم است، مقدار سال‌تنها را نگه دارید و محدودیت منبع را مستند کنید.",
            )
        )
    if partial_articles:
        issues.append(
            Issue(
                level="info",
                code="ARTICLE_PARTIAL_YEAR_DATE",
                title="برخی تاریخ‌های ماده فقط در سطح سال شناخته شده‌اند",
                count=len(partial_articles),
                samples=partial_articles[:10],
                recommendation="این مورد خطا نیست؛ اما برای timeline دقیق‌تر، در صورت دسترسی به منبع رسمی، ماه و روز تکمیل شود.",
            )
        )
    return issues


def version_sequence_issues(conn: sqlite3.Connection) -> list[Issue]:
    duplicate_versions = rows_to_dicts(
        conn.execute(
            """
            SELECT article_key, version_no, COUNT(*) AS count
            FROM articles
            WHERE article_key IS NOT NULL AND TRIM(article_key) <> ''
            GROUP BY article_key, version_no
            HAVING COUNT(*) > 1
            ORDER BY count DESC, article_key
            """
        ),
        limit=10,
    )
    duplicate_count = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT article_key, version_no
            FROM articles
            WHERE article_key IS NOT NULL AND TRIM(article_key) <> ''
            GROUP BY article_key, version_no
            HAVING COUNT(*) > 1
        )
        """,
    )
    issues: list[Issue] = []
    if duplicate_count:
        issues.append(
            Issue(
                level="error",
                code="ARTICLE_DUPLICATE_VERSION_NO",
                title="برای یک article_key و version_no بیش از یک ردیف ثبت شده است",
                count=int(duplicate_count),
                samples=duplicate_versions,
                recommendation="برای هر کلید پایدار ماده، شماره نسخه‌ها باید یکتا باشد؛ loader بسته مربوط را اصلاح و دوباره اجرا کنید.",
            )
        )

    gaps: list[dict[str, Any]] = []
    for row in conn.execute(
        """
        SELECT article_key, GROUP_CONCAT(version_no, ',') AS versions
        FROM articles
        WHERE article_key IS NOT NULL AND TRIM(article_key) <> ''
        GROUP BY article_key
        HAVING COUNT(*) > 1
        ORDER BY article_key
        """
    ):
        versions = sorted({int(v) for v in str(row["versions"]).split(",") if str(v).strip().isdigit()})
        expected = list(range(1, max(versions) + 1)) if versions else []
        if versions and versions != expected:
            gaps.append({"article_key": row["article_key"], "versions": versions, "expected": expected})
    if gaps:
        issues.append(
            Issue(
                level="warning",
                code="ARTICLE_VERSION_GAP",
                title="شماره نسخه‌های بعضی مواد پیوسته نیست",
                count=len(gaps),
                samples=gaps[:10],
                recommendation="نسخه‌های تاریخی هر ماده را از ۱ تا n بدون شکاف شماره‌گذاری کنید.",
            )
        )
    return issues


def normalize_fa_label(value: str) -> str:
    value = (value or "").replace("\u200c", " ")
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.replace("هیئت", "هیات").replace("هیأت", "هیات")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalization_issues(conn: sqlite3.Connection) -> list[Issue]:
    issues: list[Issue] = []
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in conn.execute("SELECT id, name_fa FROM authorities ORDER BY id"):
        normalized = normalize_fa_label(row["name_fa"])
        groups.setdefault(normalized, []).append({"id": row["id"], "name_fa": row["name_fa"], "normalized": normalized})
    collisions = [g for g in groups.values() if len(g) > 1]
    if collisions:
        samples = []
        for group in collisions[:10]:
            samples.append({"normalized": group[0]["normalized"], "variants": "، ".join(item["name_fa"] for item in group)})
        issues.append(
            Issue(
                level="warning",
                code="AUTHORITY_NORMALIZATION_COLLISION",
                title="نام مرجع صادرکننده با گونه‌های املایی متفاوت تکرار شده است",
                count=len(collisions),
                samples=samples,
                recommendation="مراجع هم‌معنا را ادغام یا در loaderها به نام معیار تبدیل کنید؛ نمونه مهم: «هیئت وزیران» و «هیأت وزیران».",
            )
        )
    return issues


def fts_issues(conn: sqlite3.Connection) -> list[Issue]:
    """Validate articles_fts without slow joins on UNINDEXED FTS columns."""
    issues: list[Issue] = []
    articles: dict[int, dict[str, Any]] = {}
    for row in conn.execute(
        """
        SELECT a.id, a.document_id, a.article_no, a.text, a.article_key, d.reference_code
        FROM articles a JOIN documents d ON d.id=a.document_id
        """
    ):
        articles[int(row["id"])] = row_to_dict(row) or {}

    fts_rows = [row_to_dict(r) or {} for r in conn.execute("SELECT article_id, document_id, article_no, text, title FROM articles_fts")]
    fts_count = len(fts_rows)
    article_count = len(articles)

    if fts_count != article_count:
        issues.append(
            Issue(
                level="error",
                code="FTS_COUNT_MISMATCH",
                title="تعداد رکوردهای articles و articles_fts برابر نیست",
                count=1,
                samples=[{"articles": article_count, "fts_rows": fts_count}],
                recommendation="FTS را از روی articles بازسازی یا loaderهای ناقص را اصلاح کنید.",
            )
        )

    fts_by_article: dict[int, list[dict[str, Any]]] = {}
    orphan: list[dict[str, Any]] = []
    for row in fts_rows:
        try:
            article_id = int(row.get("article_id"))
        except (TypeError, ValueError):
            article_id = -1
        fts_by_article.setdefault(article_id, []).append(row)
        if article_id not in articles:
            orphan.append(
                {
                    "article_id": row.get("article_id"),
                    "document_id": row.get("document_id"),
                    "article_no": row.get("article_no"),
                    "title": row.get("title"),
                }
            )

    missing = [
        {
            "id": art["id"],
            "reference_code": art.get("reference_code"),
            "article_no": art.get("article_no"),
            "article_key": art.get("article_key"),
        }
        for aid, art in articles.items()
        if aid not in fts_by_article
    ]
    if missing:
        issues.append(
            Issue(
                level="error",
                code="FTS_MISSING_ARTICLE",
                title="موادی که در FTS رکورد متناظر ندارند",
                count=len(missing),
                samples=missing[:10],
                recommendation="برای هر ماده باید یک رکورد FTS درج شود.",
            )
        )

    if orphan:
        issues.append(
            Issue(
                level="error",
                code="FTS_ORPHAN_ARTICLE_ID",
                title="رکوردهای FTS که article_id متناظر در articles ندارند",
                count=len(orphan),
                samples=orphan[:10],
                recommendation="FTS orphan را پاک یا جدول FTS را بازسازی کنید.",
            )
        )

    duplicates = [
        {"article_id": aid, "count": len(rows)}
        for aid, rows in sorted(fts_by_article.items())
        if aid != -1 and len(rows) > 1
    ]
    if duplicates:
        issues.append(
            Issue(
                level="error",
                code="FTS_DUPLICATE_ARTICLE_ID",
                title="برای یک article_id بیش از یک رکورد FTS وجود دارد",
                count=len(duplicates),
                samples=duplicates[:10],
                recommendation="قبل از درج مجدد مواد، رکوردهای FTS متعلق به همان سند را پاک کنید.",
            )
        )

    mismatches: list[dict[str, Any]] = []
    for aid, rows in fts_by_article.items():
        art = articles.get(aid)
        if not art or not rows:
            continue
        row = rows[0]
        if row.get("document_id") != art.get("document_id") or row.get("article_no") != art.get("article_no") or row.get("text") != art.get("text"):
            mismatches.append(
                {
                    "id": aid,
                    "reference_code": art.get("reference_code"),
                    "article_no": art.get("article_no"),
                    "article_key": art.get("article_key"),
                }
            )
    if mismatches:
        issues.append(
            Issue(
                level="warning",
                code="FTS_CONTENT_MISMATCH",
                title="محتوای FTS با جدول articles همخوان نیست",
                count=len(mismatches),
                samples=mismatches[:10],
                recommendation="اگر متن ماده پس از درج FTS اصلاح شده، FTS را هم هم‌زمان به‌روز کنید.",
            )
        )
    return issues


def scan_scripts() -> dict[str, Any]:
    loads = sorted(p.stem.replace("load_", "") for p in SCRIPTS_DIR.glob("load_*.py"))
    verifies = sorted(p.stem.replace("verify_", "") for p in SCRIPTS_DIR.glob("verify_*.py") if p.name != "verify_all.py")
    builds = sorted(p.stem.replace("build_", "").replace("_seeds", "") for p in SCRIPTS_DIR.glob("build_*_seeds.py"))

    load_set = set(loads)
    verify_set = set(verifies)
    build_set = set(builds)

    return {
        "loaders_count": len(loads),
        "verifiers_count": len(verifies),
        "builders_count": len(builds),
        "loaders_without_verifier": sorted(load_set - verify_set),
        "verifiers_without_loader": sorted(verify_set - load_set),
        "builders_without_loader": sorted(build_set - load_set),
        "loaders_without_builder": sorted(load_set - build_set),
        "loaders": loads,
        "verifiers": verifies,
        "builders": builds,
    }


def build_audit_report(db_path: str = DB_PATH) -> AuditReport:
    conn = get_connection(db_path)
    issues: list[Issue] = []
    try:
        expected_tables = [
            "document_types",
            "authorities",
            "statuses",
            "topics",
            "documents",
            "articles",
            "relations",
            "tags",
            "document_tags",
            "article_tags",
            "document_topics",
            "articles_fts",
        ]
        missing_tables = [t for t in expected_tables if not table_exists(conn, t)]
        if missing_tables:
            issues.append(
                Issue(
                    level="error",
                    code="SCHEMA_MISSING_TABLES",
                    title="برخی جدول‌ها یا نمایه‌های اصلی schema وجود ندارند",
                    count=len(missing_tables),
                    samples=[{"table": t} for t in missing_tables],
                    recommendation="scripts/schema.py را اجرا و سپس دیتابیس را از نو کنترل کنید.",
                )
            )

        integrity = scalar(conn, "PRAGMA integrity_check")
        if integrity != "ok":
            issues.append(
                Issue(
                    level="error",
                    code="DB_INTEGRITY_CHECK",
                    title="PRAGMA integrity_check خطا گزارش کرده است",
                    count=1,
                    samples=[{"result": integrity}],
                    recommendation="قبل از هر توسعه جدید، دیتابیس را از backup یا seedهای قابل بازتولید ترمیم کنید.",
                )
            )

        fk_rows = rows_to_dicts(conn.execute("PRAGMA foreign_key_check"), limit=20)
        if fk_rows:
            issues.append(
                Issue(
                    level="error",
                    code="DB_FOREIGN_KEY_CHECK",
                    title="PRAGMA foreign_key_check خطا گزارش کرده است",
                    count=len(fk_rows),
                    samples=fk_rows[:10],
                    recommendation="رابطه‌های orphan یا رکوردهای وابسته را قبل از ادامه توسعه اصلاح کنید.",
                )
            )

        summary = {
            "documents": scalar(conn, "SELECT COUNT(*) FROM documents"),
            "articles_total": scalar(conn, "SELECT COUNT(*) FROM articles"),
            "articles_current": scalar(conn, "SELECT COUNT(*) FROM articles WHERE is_current=1"),
            "articles_historical": scalar(conn, "SELECT COUNT(*) FROM articles WHERE is_current=0"),
            "relations": scalar(conn, "SELECT COUNT(*) FROM relations"),
            "tags": scalar(conn, "SELECT COUNT(*) FROM tags"),
            "topics": scalar(conn, "SELECT COUNT(*) FROM topics"),
            "fts_rows": scalar(conn, "SELECT COUNT(*) FROM articles_fts"),
            "integrity_check": integrity,
            "foreign_key_errors": len(fk_rows),
        }

        distributions = {
            "document_types": collect_distribution(
                conn,
                """
                SELECT dt.code, dt.name_fa, COUNT(*) AS count
                FROM documents d JOIN document_types dt ON dt.id=d.type_id
                GROUP BY dt.id ORDER BY count DESC, dt.name_fa
                """,
            ),
            "statuses": collect_distribution(
                conn,
                """
                SELECT s.code, s.name_fa, COUNT(*) AS count
                FROM documents d JOIN statuses s ON s.id=d.status_id
                GROUP BY s.id ORDER BY count DESC, s.name_fa
                """,
            ),
            "authorities_top": collect_distribution(
                conn,
                """
                SELECT COALESCE(a.name_fa, '---') AS name_fa, COUNT(*) AS count
                FROM documents d LEFT JOIN authorities a ON a.id=d.issuing_authority_id
                GROUP BY a.id ORDER BY count DESC, name_fa LIMIT 30
                """,
            ),
            "relation_types": collect_distribution(
                conn,
                """
                SELECT relation_type, COUNT(*) AS count
                FROM relations GROUP BY relation_type ORDER BY count DESC, relation_type
                """,
            ),
            "article_volume_top": collect_distribution(
                conn,
                """
                SELECT d.id, d.reference_code, d.title,
                       COUNT(a.id) AS total_articles,
                       SUM(CASE WHEN a.is_current=1 THEN 1 ELSE 0 END) AS current_articles,
                       SUM(CASE WHEN a.is_current=0 THEN 1 ELSE 0 END) AS historical_articles
                FROM documents d LEFT JOIN articles a ON a.document_id=d.id
                GROUP BY d.id
                ORDER BY total_articles DESC, d.id
                LIMIT 30
                """,
            ),
        }

        checks = [
            dict(
                level="warning",
                code="DOC_MISSING_REFERENCE_CODE",
                title="اسناد بدون reference_code یکتا و پایدار",
                count_sql="SELECT COUNT(*) FROM documents WHERE reference_code IS NULL OR TRIM(reference_code)=''",
                sample_sql="SELECT id, title, short_title FROM documents WHERE reference_code IS NULL OR TRIM(reference_code)='' ORDER BY id LIMIT ?",
                recommendation="برای هر سند کد مرجع پایدار تعریف کنید تا روابط و بازاجرای loaderها قابل اتکا بماند.",
            ),
            dict(
                level="error",
                code="DOC_DUPLICATE_REFERENCE_CODE",
                title="reference_code تکراری در اسناد",
                count_sql="""
                    SELECT COUNT(*) FROM (
                      SELECT reference_code FROM documents
                      WHERE reference_code IS NOT NULL AND TRIM(reference_code) <> ''
                      GROUP BY reference_code HAVING COUNT(*) > 1
                    )
                """,
                sample_sql="""
                    SELECT reference_code, COUNT(*) AS count
                    FROM documents
                    WHERE reference_code IS NOT NULL AND TRIM(reference_code) <> ''
                    GROUP BY reference_code HAVING COUNT(*) > 1
                    ORDER BY count DESC, reference_code LIMIT ?
                """,
                recommendation="کد مرجع باید یکتا باشد؛ قبل از ورود بسته جدید، سندهای تکراری را ادغام یا اصلاح کنید.",
            ),
            dict(
                level="warning",
                code="DOC_WITHOUT_ARTICLES",
                title="اسنادی که هیچ ماده/مفاد متنی ندارند",
                count_sql="""
                    SELECT COUNT(*) FROM (
                      SELECT d.id FROM documents d
                      LEFT JOIN articles a ON a.document_id=d.id
                      GROUP BY d.id HAVING COUNT(a.id)=0
                    )
                """,
                sample_sql="""
                    SELECT d.id, d.reference_code, d.title
                    FROM documents d LEFT JOIN articles a ON a.document_id=d.id
                    GROUP BY d.id HAVING COUNT(a.id)=0
                    ORDER BY d.id LIMIT ?
                """,
                recommendation="اگر سند ماهیت متنی دارد، حداقل ماده‌واحده/خلاصه صریح منبع‌دار ثبت شود؛ اگر صرفاً placeholder است، وضعیت آن در notes روشن شود.",
            ),
            dict(
                level="warning",
                code="DOC_MISSING_AUTHORITY",
                title="اسناد بدون مرجع صادرکننده",
                count_sql="SELECT COUNT(*) FROM documents WHERE issuing_authority_id IS NULL",
                sample_sql="SELECT id, reference_code, title FROM documents WHERE issuing_authority_id IS NULL ORDER BY id LIMIT ?",
                recommendation="مرجع صادرکننده برای فیلتر حقوقی، اعتبارسنجی و استناد ضروری است.",
            ),
            dict(
                level="warning",
                code="DOC_MISSING_RATIFICATION_DATE",
                title="اسناد بدون تاریخ تصویب/صدور",
                count_sql="""
                    SELECT COUNT(*) FROM documents
                    WHERE (ratification_date IS NULL OR TRIM(ratification_date)='')
                      AND COALESCE(title,'') NOT LIKE '%خلاصه%'
                      AND COALESCE(notes,'') NOT LIKE '%خلاصه%'
                """,
                sample_sql="""
                    SELECT id, reference_code, title FROM documents
                    WHERE (ratification_date IS NULL OR TRIM(ratification_date)='')
                      AND COALESCE(title,'') NOT LIKE '%خلاصه%'
                      AND COALESCE(notes,'') NOT LIKE '%خلاصه%'
                    ORDER BY id LIMIT ?
                """,
                recommendation="در صورت امکان، تاریخ تصویب یا صدور سند را از منبع رسمی تکمیل کنید. اسناد خلاصه‌دار/ابلاغی جداگانه در سطح اطلاع گزارش می‌شوند.",
            ),
            dict(
                level="info",
                code="DOC_SUMMARY_MISSING_RATIFICATION_DATE",
                title="اسناد خلاصه‌دار بدون تاریخ دقیق تصویب/صدور",
                count_sql="""
                    SELECT COUNT(*) FROM documents
                    WHERE (ratification_date IS NULL OR TRIM(ratification_date)='')
                      AND (COALESCE(title,'') LIKE '%خلاصه%' OR COALESCE(notes,'') LIKE '%خلاصه%')
                """,
                sample_sql="""
                    SELECT id, reference_code, title FROM documents
                    WHERE (ratification_date IS NULL OR TRIM(ratification_date)='')
                      AND (COALESCE(title,'') LIKE '%خلاصه%' OR COALESCE(notes,'') LIKE '%خلاصه%')
                    ORDER BY id LIMIT ?
                """,
                recommendation="این مورد برای رکوردهای خلاصه ساختاری بحرانی نیست؛ در صورت دسترسی به نسخه رسمی مقرره، تاریخ تصویب تکمیل شود.",
            ),
            dict(
                level="error",
                code="ARTICLE_EMPTY_TEXT",
                title="مواد با متن خالی یا فقط فاصله",
                count_sql="SELECT COUNT(*) FROM articles WHERE text IS NULL OR TRIM(text)=''",
                sample_sql="""
                    SELECT a.id, d.reference_code, d.title, a.article_no, a.article_key
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.text IS NULL OR TRIM(a.text)=''
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="هیچ ماده‌ای نباید بدون متن وارد FTS و جست‌وجو شود.",
            ),
            dict(
                level="warning",
                code="ARTICLE_MISSING_SOURCE_NOTE",
                title="مواد بدون source_note",
                count_sql="SELECT COUNT(*) FROM articles WHERE source_note IS NULL OR TRIM(source_note)=''",
                sample_sql="""
                    SELECT a.id, d.reference_code, d.title, a.article_no, a.article_key
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.source_note IS NULL OR TRIM(a.source_note)=''
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="برای هر ماده منبع قابل رهگیری ثبت کنید؛ اگر خلاصه است، همین را صریحاً در منبع/یادداشت بیاورید.",
            ),
            dict(
                level="warning",
                code="ARTICLE_MISSING_KEY",
                title="مواد بدون article_key پایدار",
                count_sql="SELECT COUNT(*) FROM articles WHERE article_key IS NULL OR TRIM(article_key)=''",
                sample_sql="""
                    SELECT a.id, d.reference_code, d.title, a.article_no
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.article_key IS NULL OR TRIM(a.article_key)=''
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="کلید پایدار ماده برای تاریخچه، relation و API ضروری است.",
            ),
            dict(
                level="error",
                code="ARTICLE_MULTIPLE_CURRENT_VERSION",
                title="بیش از یک نسخه جاری برای یک article_key",
                count_sql="""
                    SELECT COUNT(*) FROM (
                      SELECT article_key FROM articles
                      WHERE is_current=1 AND article_key IS NOT NULL AND TRIM(article_key) <> ''
                      GROUP BY article_key HAVING COUNT(*) > 1
                    )
                """,
                sample_sql="""
                    SELECT article_key, COUNT(*) AS current_count
                    FROM articles
                    WHERE is_current=1 AND article_key IS NOT NULL AND TRIM(article_key) <> ''
                    GROUP BY article_key HAVING COUNT(*) > 1
                    ORDER BY current_count DESC, article_key LIMIT ?
                """,
                recommendation="loader بسته مربوط باید نسخه‌های قدیمی را historical کند و فقط یک نسخه جاری بگذارد.",
            ),
            dict(
                level="warning",
                code="ARTICLE_NO_ASCII_OR_ARABIC_DIGITS",
                title="شماره ماده شامل رقم لاتین یا عربی غیر فارسی است",
                count_sql="SELECT COUNT(*) FROM articles WHERE article_no GLOB '*[0-9٠-٩]*'",
                sample_sql="""
                    SELECT a.id, d.reference_code, a.article_no, a.article_key
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.article_no GLOB '*[0-9٠-٩]*'
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="شماره مواد را با ارقام فارسی ۰۱۲۳۴۵۶۷۸۹ ذخیره کنید.",
            ),
            dict(
                level="warning",
                code="ARTICLE_HISTORICAL_WITHOUT_EXPIRY",
                title="نسخه تاریخی بدون expiry_date",
                count_sql="SELECT COUNT(*) FROM articles WHERE is_current=0 AND (expiry_date IS NULL OR TRIM(expiry_date)='')",
                sample_sql="""
                    SELECT a.id, d.reference_code, a.article_no, a.article_key, a.version_no
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.is_current=0 AND (a.expiry_date IS NULL OR TRIM(a.expiry_date)='')
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="برای تحلیل زمانی، تا حد امکان تاریخ پایان اعتبار نسخه تاریخی را تکمیل کنید.",
            ),
            dict(
                level="error",
                code="ARTICLE_CURRENT_WITH_EXPIRY",
                title="نسخه جاری دارای expiry_date است",
                count_sql="SELECT COUNT(*) FROM articles WHERE is_current=1 AND expiry_date IS NOT NULL AND TRIM(expiry_date) <> ''",
                sample_sql="""
                    SELECT a.id, d.reference_code, a.article_no, a.article_key, a.expiry_date
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.is_current=1 AND a.expiry_date IS NOT NULL AND TRIM(a.expiry_date) <> ''
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="نسخه جاری نباید تاریخ پایان اعتبار داشته باشد؛ اگر منسوخ شده، is_current را صفر کنید.",
            ),
            dict(
                level="warning",
                code="ARTICLE_TEXT_HAS_URL_OR_HTML",
                title="متن ماده احتمالاً حاوی URL/HTML/نویسه خراب است",
                count_sql="""
                    SELECT COUNT(*) FROM articles
                    WHERE text LIKE '%http://%' OR text LIKE '%https://%' OR text LIKE '%<div%'
                       OR text LIKE '%</%' OR text LIKE '%�%'
                """,
                sample_sql="""
                    SELECT a.id, d.reference_code, a.article_no, a.article_key,
                           SUBSTR(a.text, 1, 180) AS text_sample
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.text LIKE '%http://%' OR a.text LIKE '%https://%' OR a.text LIKE '%<div%'
                       OR a.text LIKE '%</%' OR a.text LIKE '%�%'
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="متن حقوقی را از لینک، HTML، footer و خرابی OCR پاک‌سازی کنید؛ منبع در source_note کافی است.",
            ),
            dict(
                level="warning",
                code="ARTICLE_TEXT_HAS_SITE_NOISE",
                title="متن ماده احتمالاً حاوی نویز سایت یا بخش‌های غیرحقوقی است",
                count_sql="""
                    SELECT COUNT(*) FROM articles
                    WHERE text LIKE '%مطالب مرتبط%' OR text LIKE '%نظر شما%'
                       OR text LIKE '%ارسال دیدگاه%' OR text LIKE '%ثبت دیدگاه%'
                       OR text LIKE '%افزودن دیدگاه%' OR text LIKE '%اشتراک گذاری%'
                       OR text LIKE '%کپی لینک%'
                """,
                sample_sql="""
                    SELECT a.id, d.reference_code, a.article_no, a.article_key,
                           SUBSTR(a.text, 1, 180) AS text_sample
                    FROM articles a JOIN documents d ON d.id=a.document_id
                    WHERE a.text LIKE '%مطالب مرتبط%' OR a.text LIKE '%نظر شما%'
                       OR a.text LIKE '%ارسال دیدگاه%' OR a.text LIKE '%ثبت دیدگاه%'
                       OR a.text LIKE '%افزودن دیدگاه%' OR a.text LIKE '%اشتراک گذاری%'
                       OR a.text LIKE '%کپی لینک%'
                    ORDER BY a.id LIMIT ?
                """,
                recommendation="در builder مرز پایان متن سند را دقیق‌تر تعریف کنید.",
            ),
            dict(
                level="info",
                code="CURRENT_KEYS_WITH_NO_CURRENT_VERSION",
                title="article_keyهایی که فقط نسخه تاریخی دارند و نسخه جاری ندارند",
                count_sql="""
                    SELECT COUNT(*) FROM (
                      SELECT article_key
                      FROM articles
                      WHERE article_key IS NOT NULL AND TRIM(article_key) <> ''
                      GROUP BY article_key
                      HAVING SUM(CASE WHEN is_current=1 THEN 1 ELSE 0 END)=0
                    )
                """,
                sample_sql="""
                    SELECT article_key, COUNT(*) AS versions
                    FROM articles
                    WHERE article_key IS NOT NULL AND TRIM(article_key) <> ''
                    GROUP BY article_key
                    HAVING SUM(CASE WHEN is_current=1 THEN 1 ELSE 0 END)=0
                    ORDER BY article_key LIMIT ?
                """,
                recommendation="این مورد برای مواد منسوخ طبیعی است، اما باید source_note/notes صریحاً علت تاریخی بودن را توضیح دهد.",
            ),
            # FTS checks are implemented in Python by fts_issues().
            # Direct LEFT JOINs against FTS5 on article_id are slow because article_id is UNINDEXED.
            dict(
                level="warning",
                code="RELATION_DUPLICATES",
                title="روابط تکراری احتمالی",
                count_sql="""
                    SELECT COUNT(*) FROM (
                      SELECT from_document_id, COALESCE(from_article_id, -1), COALESCE(to_document_id, -1),
                             COALESCE(to_article_id, -1), relation_type, COALESCE(description, '')
                      FROM relations
                      GROUP BY from_document_id, COALESCE(from_article_id, -1), COALESCE(to_document_id, -1),
                               COALESCE(to_article_id, -1), relation_type, COALESCE(description, '')
                      HAVING COUNT(*) > 1
                    )
                """,
                sample_sql="""
                    SELECT from_document_id, from_article_id, to_document_id, to_article_id, relation_type,
                           COUNT(*) AS count
                    FROM relations
                    GROUP BY from_document_id, COALESCE(from_article_id, -1), COALESCE(to_document_id, -1),
                             COALESCE(to_article_id, -1), relation_type, COALESCE(description, '')
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC LIMIT ?
                """,
                recommendation="در loaderها پیش از درج روابط owned، روابط قبلی همان بسته را پاک یا INSERT OR IGNORE منطقی پیاده‌سازی کنید.",
            ),
            dict(
                level="error",
                code="RELATION_WITHOUT_TARGET",
                title="رابطه بدون مقصد سند یا ماده",
                count_sql="SELECT COUNT(*) FROM relations WHERE to_document_id IS NULL AND to_article_id IS NULL",
                sample_sql="SELECT id, from_document_id, from_article_id, relation_type, description FROM relations WHERE to_document_id IS NULL AND to_article_id IS NULL ORDER BY id LIMIT ?",
                recommendation="هر رابطه باید حداقل به یک سند یا ماده مقصد اشاره کند.",
            ),
            dict(
                level="warning",
                code="RELATION_UNKNOWN_TYPE",
                title="نوع رابطه خارج از فهرست استاندارد پروژه",
                count_sql=f"""
                    SELECT COUNT(*) FROM relations
                    WHERE relation_type NOT IN ({','.join('?' for _ in ALLOWED_RELATION_TYPES)})
                """,
                sample_sql=f"""
                    SELECT relation_type, COUNT(*) AS count
                    FROM relations
                    WHERE relation_type NOT IN ({','.join('?' for _ in ALLOWED_RELATION_TYPES)})
                    GROUP BY relation_type ORDER BY count DESC LIMIT ?
                """,
                params=tuple(sorted(ALLOWED_RELATION_TYPES)),
                recommendation="اگر نوع رابطه جدید لازم است، آن را در schema/docs استاندارد کنید؛ در غیر این صورت به یکی از انواع موجود تبدیل شود.",
            ),
        ]

        for check in checks:
            issue = sample_issue(conn, **check)
            if issue:
                issues.append(issue)

        issues.extend(fts_issues(conn))
        issues.extend(iso_date_issues(conn))
        issues.extend(version_sequence_issues(conn))
        issues.extend(normalization_issues(conn))

        script_inventory = scan_scripts()
        if script_inventory["loaders_without_verifier"]:
            issues.append(
                Issue(
                    level="warning",
                    code="SCRIPTS_LOADERS_WITHOUT_VERIFIER",
                    title="برخی loaderها verifier مستقل ندارند",
                    count=len(script_inventory["loaders_without_verifier"]),
                    samples=[{"package": x} for x in script_inventory["loaders_without_verifier"][:20]],
                    recommendation="برای هر بسته مهم، verify_<package>.py بسازید و سپس verify_all.py را روی همه آنها اجرا کنید.",
                )
            )
        if script_inventory["builders_without_loader"]:
            issues.append(
                Issue(
                    level="info",
                    code="SCRIPTS_BUILDERS_WITHOUT_LOADER",
                    title="برخی builderها loader متناظر ندارند",
                    count=len(script_inventory["builders_without_loader"]),
                    samples=[{"package": x} for x in script_inventory["builders_without_loader"][:20]],
                    recommendation="اگر builderها قدیمی یا ادغام‌شده‌اند، مستند کنید؛ در غیر این صورت loader متناظر بسازید.",
                )
            )
        if script_inventory["loaders_without_builder"]:
            issues.append(
                Issue(
                    level="info",
                    code="SCRIPTS_LOADERS_WITHOUT_BUILDER",
                    title="برخی loaderها builder متناظر ندارند",
                    count=len(script_inventory["loaders_without_builder"]),
                    samples=[{"package": x} for x in script_inventory["loaders_without_builder"][:20]],
                    recommendation="برای داده‌های تولیدشده دستی یا هسته‌ای، نبود builder می‌تواند پذیرفتنی باشد؛ ولی باید در docs توضیح داده شود.",
                )
            )

        order = {"error": 0, "warning": 1, "info": 2}
        issues.sort(key=lambda x: (order.get(x.level, 9), x.code))

        return AuditReport(
            generated_at=LOCAL_DATE_GREGORIAN,
            generated_at_jalali=LOCAL_DATE_JALALI,
            db_path=str(db_path),
            summary=summary,
            distributions=distributions,
            issues=issues,
            script_inventory=script_inventory,
        )
    finally:
        conn.close()


def report_to_dict(report: AuditReport) -> dict[str, Any]:
    d = asdict(report)
    d["issues_by_level"] = {
        level: sum(1 for issue in report.issues if issue.level == level) for level in ISSUE_LEVELS
    }
    return d


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], *, max_rows: int | None = None) -> str:
    if max_rows is not None:
        rows = rows[:max_rows]
    if not rows:
        return "_موردی یافت نشد._\n"
    out = []
    out.append("| " + " | ".join(title for _, title in columns) + " |")
    out.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        cells = []
        for key, _title in columns:
            val = row.get(key, "")
            if isinstance(val, (int, float)):
                val = fa_num(val)
            elif isinstance(val, list):
                val = fa_num(", ".join(map(str, val)))
            elif val is None:
                val = ""
            else:
                val = fa_num(str(val))
            val = val.replace("\n", " ").replace("|", "\\|")
            if len(val) > 220:
                val = val[:217] + "…"
            cells.append(val)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def render_markdown(report: AuditReport) -> str:
    issues_by_level = {level: [i for i in report.issues if i.level == level] for level in ISSUE_LEVELS}
    level_fa = {"error": "خطا", "warning": "هشدار", "info": "اطلاع"}
    summary = report.summary

    lines: list[str] = []
    lines.append('<div dir="rtl">')
    lines.append("")
    lines.append("# گزارش وضعیت و کنترل کیفیت بانک اطلاعات حقوقی ایران")
    lines.append("")
    lines.append(f"**تاریخ گزارش:** {report.generated_at_jalali} ({report.generated_at})  ")
    lines.append(f"**مسیر دیتابیس:** `{report.db_path}`  ")
    lines.append("**ابزار تولید گزارش:** `scripts/audit_db.py`  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ۱. خلاصه مدیریتی")
    lines.append("")
    lines.append(
        "این گزارش ممیزی سراسری، وضعیت فعلی دیتابیس را بدون تغییر دادن داده‌ها بررسی می‌کند. "
        "هدف آن مشخص کردن خطاهای ساختاری، ریسک‌های کیفیت داده و کارهای اولویت‌دار قبل از توسعه محتوایی بعدی است."
    )
    lines.append("")
    lines.append(
        markdown_table(
            [
                {"metric": "اسناد", "value": summary["documents"]},
                {"metric": "مواد/مفاد جاری", "value": summary["articles_current"]},
                {"metric": "نسخه‌های تاریخی", "value": summary["articles_historical"]},
                {"metric": "کل ردیف‌های مواد و نسخه‌ها", "value": summary["articles_total"]},
                {"metric": "ارتباطات", "value": summary["relations"]},
                {"metric": "برچسب‌ها", "value": summary["tags"]},
                {"metric": "موضوعات", "value": summary["topics"]},
                {"metric": "رکوردهای FTS5", "value": summary["fts_rows"]},
                {"metric": "PRAGMA integrity_check", "value": summary["integrity_check"]},
                {"metric": "خطاهای foreign_key_check", "value": summary["foreign_key_errors"]},
            ],
            [("metric", "شاخص"), ("value", "مقدار")],
        )
    )
    lines.append("")
    lines.append(
        markdown_table(
            [
                {"level": "خطا", "count": len(issues_by_level["error"])},
                {"level": "هشدار", "count": len(issues_by_level["warning"])},
                {"level": "اطلاع", "count": len(issues_by_level["info"])},
            ],
            [("level", "سطح"), ("count", "تعداد موارد گزارش‌شده")],
        )
    )
    lines.append("")
    if issues_by_level["error"]:
        lines.append("**نتیجه:** دیتابیس نیازمند اصلاح خطاهای ساختاری زیر پیش از توسعه بزرگ بعدی است.")
    elif issues_by_level["warning"]:
        lines.append("**نتیجه:** خطای بحرانی ساختاری دیده نشد، اما چند هشدار کیفیت داده باید در اولویت اصلاح قرار گیرد.")
    else:
        lines.append("**نتیجه:** در کنترل‌های فعلی خطا یا هشدار مهمی دیده نشد.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ۲. توزیع اسناد و داده‌ها")
    lines.append("")
    lines.append("### ۲.۱. انواع سند")
    lines.append(markdown_table(report.distributions["document_types"], [("name_fa", "نوع سند"), ("code", "کد"), ("count", "تعداد")]))
    lines.append("")
    lines.append("### ۲.۲. وضعیت اسناد")
    lines.append(markdown_table(report.distributions["statuses"], [("name_fa", "وضعیت"), ("code", "کد"), ("count", "تعداد")]))
    lines.append("")
    lines.append("### ۲.۳. مراجع صادرکننده پرتکرار")
    lines.append(markdown_table(report.distributions["authorities_top"], [("name_fa", "مرجع"), ("count", "تعداد")], max_rows=30))
    lines.append("")
    lines.append("### ۲.۴. انواع رابطه")
    lines.append(markdown_table(report.distributions["relation_types"], [("relation_type", "نوع رابطه"), ("count", "تعداد")]))
    lines.append("")
    lines.append("### ۲.۵. اسناد حجیم‌تر از نظر تعداد مواد")
    lines.append(
        markdown_table(
            report.distributions["article_volume_top"],
            [
                ("reference_code", "کد"),
                ("title", "عنوان"),
                ("total_articles", "کل ردیف‌ها"),
                ("current_articles", "جاری"),
                ("historical_articles", "تاریخی"),
            ],
            max_rows=30,
        )
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ۳. موجودی اسکریپت‌ها")
    inv = report.script_inventory
    lines.append(
        markdown_table(
            [
                {"metric": "Builderها", "value": inv["builders_count"]},
                {"metric": "Loaderها", "value": inv["loaders_count"]},
                {"metric": "Verifierها", "value": inv["verifiers_count"]},
                {"metric": "Loader بدون verifier", "value": len(inv["loaders_without_verifier"])},
                {"metric": "Builder بدون loader", "value": len(inv["builders_without_loader"])},
                {"metric": "Loader بدون builder", "value": len(inv["loaders_without_builder"])},
            ],
            [("metric", "شاخص"), ("value", "مقدار")],
        )
    )
    lines.append("")
    if inv["loaders_without_verifier"]:
        lines.append("### Loaderهای بدون verifier مستقل")
        lines.append(markdown_table([{"package": x} for x in inv["loaders_without_verifier"]], [("package", "بسته")], max_rows=100))
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ۴. یافته‌های ممیزی")
    lines.append("")
    if not report.issues:
        lines.append("هیچ موردی در کنترل‌های فعلی گزارش نشد.")
    for level in ISSUE_LEVELS:
        items = issues_by_level[level]
        if not items:
            continue
        lines.append(f"### ۴.{ISSUE_LEVELS.index(level)+1}. {level_fa[level]}ها")
        lines.append("")
        for issue in items:
            lines.append(f"#### `{issue.code}` — {issue.title}")
            lines.append("")
            lines.append(f"- **تعداد:** {fa_num(issue.count)}")
            if issue.recommendation:
                lines.append(f"- **پیشنهاد اصلاح:** {issue.recommendation}")
            if issue.samples:
                sample_keys = list(issue.samples[0].keys())
                lines.append("- **نمونه‌ها:**")
                lines.append("")
                lines.append(markdown_table(issue.samples, [(k, k) for k in sample_keys], max_rows=10))
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ۵. اولویت عملیاتی پیشنهادی")
    lines.append("")
    lines.append("۱. اگر خطای FTS یا نسخه جاری چندگانه وجود دارد، ابتدا همان‌ها اصلاح شود؛ چون روی جست‌وجو و تاریخچه اثر مستقیم دارد.  ")
    lines.append("۲. برای loaderهای بدون verifier، به ترتیب بسته‌های پرتکرار و مادر verifier مستقل ساخته شود.  ")
    lines.append("۳. اسناد/مواد بدون منبع یا تاریخ مهم، در فاز تکمیل منابع رسمی اصلاح شوند.  ")
    lines.append("۴. پس از کاهش هشدارهای اصلی، `verify_all.py` و تست وب/CLI سراسری اضافه شود.  ")
    lines.append("۵. سپس توسعه محتوایی جدید، مثل آرای وحدت رویه، ثبت اسناد/حدنگار و مقررات بانکی، با مسیر builder → loader → verifier ادامه یابد.  ")
    lines.append("")
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)


def write_output(content: str, output: str | None) -> None:
    if output:
        path = Path(output)
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        print(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ممیزی سراسری دیتابیس حقوقی ایران")
    parser.add_argument("--db", default=DB_PATH, help="مسیر دیتابیس SQLite")
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text", help="قالب خروجی")
    parser.add_argument("--output", help="مسیر ذخیره خروجی؛ اگر داده نشود روی stdout چاپ می‌شود")
    parser.add_argument("--strict", action="store_true", help="در صورت وجود error با کد خروجی ۱ خارج شود")
    args = parser.parse_args(argv)

    report = build_audit_report(args.db)
    data = report_to_dict(report)

    if args.format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        content = render_markdown(report)
    else:
        errors = sum(1 for i in report.issues if i.level == "error")
        warnings = sum(1 for i in report.issues if i.level == "warning")
        infos = sum(1 for i in report.issues if i.level == "info")
        lines = [
            "Iran Legal DB audit",
            f"date: {report.generated_at_jalali} ({report.generated_at})",
            f"db: {report.db_path}",
            "",
            "summary:",
            f"  documents: {report.summary['documents']}",
            f"  current articles: {report.summary['articles_current']}",
            f"  historical articles: {report.summary['articles_historical']}",
            f"  total articles: {report.summary['articles_total']}",
            f"  relations: {report.summary['relations']}",
            f"  fts rows: {report.summary['fts_rows']}",
            f"  integrity_check: {report.summary['integrity_check']}",
            f"  foreign_key_errors: {report.summary['foreign_key_errors']}",
            "",
            f"issues: errors={errors}, warnings={warnings}, info={infos}",
        ]
        for issue in report.issues:
            lines.append(f"  [{issue.level}] {issue.code}: {issue.title} ({issue.count})")
        content = "\n".join(lines)

    write_output(content, args.output)
    if args.strict and any(issue.level == "error" for issue in report.issues):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
