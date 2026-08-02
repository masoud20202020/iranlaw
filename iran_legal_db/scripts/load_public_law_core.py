# -*- coding: utf-8 -*-
"""Load public-law core package: full constitutional text and constitutional links."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]

from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic  # noqa: E402
from schema import get_connection  # noqa: E402

D = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
F = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

REF = "QA-1358"
SOURCE_FILE = ROOT / "data" / "source_cache" / "constitution_1368_full.md"
SOURCE_NOTE = "https://www.shora-gc.ir/fa/news/4707/قانون-اساسی-جمهوری-اسلامی-ایران ؛ https://fa.wikisource.org/wiki/قانون_اساسی_جمهوری_اسلامی_ایران_(مصوب_۱۳۶۸)"

PUBLIC_ACCOUNTING_REF = "QPA-1366"
PUBLIC_ACCOUNTING_FILE = ROOT / "data" / "source_cache" / "public_accounting_1366.md"
PUBLIC_ACCOUNTING_SOURCE_NOTE = "https://shenasname.ir/laws/641-قانون-محاسبات-عمومی-کشور ؛ https://shaghool.ir/downloadarea.php?id=1160 ؛ https://www.ekhtebar.ir/‌قانون-محاسبات-عمومی-کشور-مصوب-۱۳۶۶/"

TENDER_REF = "QBT-1383"
TENDER_FILE = ROOT / "data" / "source_cache" / "tender_law_1383.md"
TENDER_SOURCE_NOTE = "https://omranpooya.com/construction/rrules/rr-4 ؛ http://laws.tehran.ir/Law/MainLawView/93 ؛ https://monaghesegar.com/Articles/View/36/Law-tenders"

PARLIAMENT_RULES_REF = "QIRP-1378"
PARLIAMENT_RULES_FILE = ROOT / "data" / "source_cache" / "parliament_internal_rules_1378.md"
PARLIAMENT_RULES_SOURCE_NOTE = "https://vokalapress.ir/قانون-آیین‌-نامه-داخلی-مجلس/ ؛ https://www.tabnak.ir/fa/content/37 ؛ https://vakilan.net/LegalInformation/Law/5627"

PARLIAMENT_ELECTION_REF = "QEMP-1378"
PARLIAMENT_ELECTION_FILE = ROOT / "data" / "source_cache" / "parliament_election_law_1378.md"
PARLIAMENT_ELECTION_SOURCE_NOTE = "https://www.shora-gc.ir/fa/news/5730/قانون-انتخابات-مجلس-شورای-اسلامی ؛ https://www.mizanonline.ir/fa/news/4749580/قانون-انتخابات-مجلس-شورای-اسلامی-اصلاحات-و-الحاقات ؛ http://www.entekhabportal.ir/83"

PRESIDENTIAL_ELECTION_REF = "QERP-1364"
PRESIDENTIAL_ELECTION_FILE = ROOT / "data" / "source_cache" / "presidential_election_law_1364.md"
PRESIDENTIAL_ELECTION_SOURCE_NOTE = "https://www.shora-gc.ir/fa/news/5729/قوانین-و-مقررات-مرتبط-با-انتخابات-ریاست-جمهوری ؛ https://www.shora-gc.ir/fa/news/4703/قانون-انتخابات-ریاست-جمهوری-اسلامی-ایران ؛ https://www.ekhtebar.ir/‌قانون-انتخابات-ریاست-جمهوری-اسلامی-ایران/"

COUNCILS_REF = "QISC-1375"
COUNCILS_FILE = ROOT / "data" / "source_cache" / "islamic_councils_elections_mayors_1375.md"
COUNCILS_SOURCE_NOTE = "https://www.ekhtebar.ir/قانون-تشکیلات،-وظایف-و-انتخاب-شوراهای/ ؛ https://www.shora-gc.ir/fa/news/2913/قانون-تشکیلات-وظایف-و-انتخابات-شوراهای-اسلامی-کشور ؛ https://shenasname.ir/shahrdari/4125-قانون-تشکیلات،-وظایف-و-انتخابات-شورا ؛ https://qavanin.ir/Law/PrintText/259453"


def one(conn, query: str, value: str):
    row = conn.execute(query, (value,)).fetchone()
    return row["id"] if row else None


def ensure_authority(conn, name: str, authority_type: str = "constitutional") -> int:
    row = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO authorities(name_fa, authority_type) VALUES(?,?)", (name, authority_type))
    return cur.lastrowid


def ensure_topic(conn, name: str):
    conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES(?)", (name,))


def clear_owned(conn, did: int):
    for query in (
        "DELETE FROM relations WHERE from_document_id=?",
        "DELETE FROM articles_fts WHERE document_id=?",
        "DELETE FROM articles WHERE document_id=?",
        "DELETE FROM document_tags WHERE document_id=?",
        "DELETE FROM document_topics WHERE document_id=?",
    ):
        conn.execute(query, (did,))


def parse_constitution():
    text = SOURCE_FILE.read_text(encoding="utf-8")
    # Keep only the legal body after the quality/source header.
    marker = "\nمقدمه\n"
    if marker not in text:
        raise ValueError("constitution source missing preamble marker")
    body = text.split(marker, 1)[1]
    matches = list(re.finditer(r"(?m)^اصل\s+([۰-۹]+)\s*$", body))
    if len(matches) != 177:
        raise ValueError(f"expected 177 constitutional principles, got {len(matches)}")
    rows = [("مقدمه", body[: matches[0].start()].strip(), "preamble")]
    for idx, match in enumerate(matches, start=1):
        begin = match.end()
        end = matches[idx].start() if idx < len(matches) else len(body)
        num = int(match.group(1).translate(D))
        if num != idx:
            raise ValueError(f"constitutional principle numbering mismatch: {num} != {idx}")
        article_no = f"اصل {str(idx).translate(F)}"
        article_key_no = str(idx)
        article_text = body[begin:end].strip()
        article_text = re.sub(r"\n{3,}", "\n\n", article_text)
        rows.append((article_no, article_text, article_key_no))
    if any(not r[1] for r in rows):
        raise ValueError("empty constitutional row")
    return rows


def parse_structural_rows(source_file: Path, ref: str):
    text = source_file.read_text(encoding="utf-8")
    heads = list(re.finditer(r"(?m)^###\s+ردیف\s+([۰-۹]+)\s+[—-]\s*(.+)$", text))
    if not heads:
        raise ValueError(f"no structural rows in {source_file}")
    rows = []
    for pos, match in enumerate(heads):
        row_no = int(match.group(1).translate(D))
        begin = match.end()
        end = heads[pos + 1].start() if pos + 1 < len(heads) else len(text)
        title = match.group(2).strip()
        body = text[begin:end].strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        rows.append((str(row_no).translate(F), f"{title}\n\n{body}", str(row_no)))
    return rows


def parse_numbered_articles(source_file: Path, count: int):
    text = source_file.read_text(encoding="utf-8")
    heads = list(re.finditer(r"(?m)^ماده\s+([۰-۹]+)(?:\s+[—-].*)?$", text))
    if len(heads) != count:
        raise ValueError(f"expected {count} articles in {source_file}, got {len(heads)}")
    rows = []
    for pos, match in enumerate(heads):
        num = int(match.group(1).translate(D))
        if num != pos + 1:
            raise ValueError(f"article numbering mismatch in {source_file}: {num} != {pos + 1}")
        begin = match.end()
        end = heads[pos + 1].start() if pos + 1 < len(heads) else len(text)
        heading = match.group(0).strip()
        title = re.sub(r"^ماده\s+[۰-۹]+\s*[—-]?\s*", "", heading).strip()
        body = text[begin:end].strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        full_text = f"{title}\n\n{body}".strip() if title else body
        rows.append((str(num).translate(F), full_text, str(num)))
    return rows


def parse_flexible_numbered_articles(source_file: Path, count: int):
    """Parse article headings embedded as `ماده N- ...` lines.

    Used for consolidated web republications whose article text begins on the same
    line as the article marker and may contain Markdown-escaped hyphens/links.
    """
    text = source_file.read_text(encoding="utf-8")
    # Keep only the legal body and drop source/reporting notes or related posts.
    marker = "## متن ماده‌به‌ماده استخراج‌شده"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.split("<!-- پایان متن", 1)[0]
    text = text.replace("\\-", "-").replace("\\", "")
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"ماده\s*\n\s*([۰-۹0-9])", r"ماده \1", text)
    heads = list(re.finditer(r"(?m)^ماده\s+([۰-۹0-9]+)\s*(?:[ـ\-–—]\s*)?", text))
    if len(heads) != count:
        got = [int(m.group(1).translate(D)) for m in heads[:10]]
        tail = [int(m.group(1).translate(D)) for m in heads[-10:]] if heads else []
        raise ValueError(f"expected {count} articles in {source_file}, got {len(heads)}; first={got}; last={tail}")
    rows = []
    for pos, match in enumerate(heads):
        num = int(match.group(1).translate(D))
        if num != pos + 1:
            raise ValueError(f"article numbering mismatch in {source_file}: {num} != {pos + 1}")
        begin = match.end()
        end = heads[pos + 1].start() if pos + 1 < len(heads) else len(text)
        body = text[begin:end].strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        if not body:
            raise ValueError(f"empty article {num} in {source_file}")
        rows.append((str(num).translate(F), body, str(num)))
    return rows


def upsert_document(conn, *, ref: str, title: str, short: str, type_code: str, authority: str, status: str, date: str, notes: str) -> int:
    auth_type = "legislative" if "مجلس" in authority else "executive"
    ensure_authority(conn, authority, auth_type)
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", ref)
    if not did:
        did = get_or_create_document(
            conn,
            title=title,
            short_title=short,
            type_code=type_code,
            issuing_authority=authority,
            status_code=status,
            ratification_date=date,
            effective_date=date,
            reference_code=ref,
            notes=notes,
        )
    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            title,
            short,
            one(conn, "SELECT id FROM document_types WHERE code=?", type_code),
            one(conn, "SELECT id FROM authorities WHERE name_fa=?", authority),
            one(conn, "SELECT id FROM statuses WHERE code=?", status),
            date,
            date,
            notes,
            did,
        ),
    )
    return did


def upsert_constitution(conn) -> int:
    authority = "مجلس بررسی نهایی قانون اساسی و شورای بازنگری قانون اساسی"
    ensure_authority(conn, authority, "constitutional")
    did = one(conn, "SELECT id FROM documents WHERE reference_code=?", REF)
    notes = (
        "پوشش کامل شماره‌ای مقدمه و اصول ۱ تا ۱۷۷ قانون اساسی جمهوری اسلامی ایران با اصلاحات ۱۳۶۸؛ "
        "متن از بازنشرهای عمومی با مقابله اولیه استخراج شده و مقابله رسمی‌تر با PDF شورای نگهبان/روزنامه رسمی توصیه می‌شود."
    )
    if not did:
        did = get_or_create_document(
            conn,
            title="قانون اساسی جمهوری اسلامی ایران (با اصلاحات ۱۳۶۸)",
            short_title="قانون اساسی",
            type_code="constitution",
            issuing_authority=authority,
            status_code="amended",
            ratification_date="1979-12-03",
            publication_date="1979-12-03",
            effective_date="1979-12-03",
            reference_code=REF,
            notes=notes,
        )
    conn.execute(
        """
        UPDATE documents
        SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
            ratification_date=?, publication_date=?, effective_date=?, notes=?
        WHERE id=?
        """,
        (
            "قانون اساسی جمهوری اسلامی ایران (با اصلاحات ۱۳۶۸)",
            "قانون اساسی",
            one(conn, "SELECT id FROM document_types WHERE code=?", "constitution"),
            one(conn, "SELECT id FROM authorities WHERE name_fa=?", authority),
            one(conn, "SELECT id FROM statuses WHERE code=?", "amended"),
            "1979-12-03",
            "1979-12-03",
            "1979-12-03",
            notes,
            did,
        ),
    )
    return did


def attach(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق اساسی"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("قانون اساسی", "حقوق اساسی", "حقوق ملت", "حاکمیت", "شورای نگهبان", "دیوان عدالت اداری", "بازنگری قانون اساسی"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_public_accounting(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق مالیه عمومی", "حقوق اداری"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("محاسبات عمومی", "بودجه", "خزانه‌داری کل", "دیوان محاسبات", "ذی‌حساب", "معاملات دولتی", "اموال دولتی"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_tender(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق مالیه عمومی", "حقوق اداری", "معاملات و قراردادهای عمومی"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("مناقصه", "معاملات دولتی", "ترک تشریفات", "کمیسیون مناقصه", "ارزیابی کیفی", "تضمین مناقصه", "پایگاه ملی مناقصات"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_parliament_rules(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق اساسی", "حقوق پارلمانی و قانون‌گذاری"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("آیین‌نامه داخلی مجلس", "مجلس شورای اسلامی", "قانون‌گذاری", "نظارت پارلمانی", "کمیسیون‌های مجلس", "استیضاح", "تحقیق و تفحص", "اصل نود"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_parliament_election(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق اساسی", "انتخابات و احزاب", "حقوق پارلمانی و قانون‌گذاری"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("انتخابات مجلس", "مجلس شورای اسلامی", "شورای نگهبان", "نظارت استصوابی", "احزاب", "اعتبارنامه", "تبلیغات انتخاباتی", "سامانه انتخابات"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_presidential_election(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق اساسی", "انتخابات و احزاب"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("انتخابات ریاست جمهوری", "ریاست جمهوری", "شورای نگهبان", "نظارت انتخابات", "احراز صلاحیت", "اصل ۱۱۵", "صداوسیما", "انتخابات الکترونیکی"):
        link_document_tag(conn, did, add_tag(conn, tag))


def attach_councils(conn, did: int):
    for topic in ("حقوق عمومی", "حقوق اساسی", "انتخابات و احزاب", "شهرداری و مدیریت شهری"):
        ensure_topic(conn, topic)
        link_document_topic(conn, did, topic)
    for tag in ("شوراهای اسلامی", "شورای شهر", "شورای روستا", "شورای عالی استان‌ها", "انتخاب شهردار", "انتخابات شوراها", "شهرداری", "دهیاری"):
        link_document_tag(conn, did, add_tag(conn, tag))


def add_rows(conn, did: int, rows, source_note: str = SOURCE_NOTE, ref: str = REF):
    for article_no, text, key_no in rows:
        add_article(
            conn,
            did,
            article_no=article_no,
            article_key=f"{ref}:{key_no}",
            version_no=1,
            is_current=1,
            effective_date="1989-07-28" if key_no not in {"1", "2", "3", "4"} else "1979-12-03",
            text=text,
            source_note=source_note,
            notes="پوشش کامل شماره‌ای؛ مقابله رسمی‌تر با نسخه PDF شورای نگهبان توصیه می‌شود.",
        )


def add_rel(conn, from_ref: str, to_ref: str, rel_type: str = "cites", desc: str | None = None):
    from_doc = one(conn, "SELECT id FROM documents WHERE reference_code=?", from_ref)
    to_doc = one(conn, "SELECT id FROM documents WHERE reference_code=?", to_ref)
    if from_doc and to_doc:
        add_relation(conn, from_doc, rel_type, to_doc, description=desc or f"پیوند قانون اساسی با سند {to_ref}.")


def main():
    rows = parse_constitution()
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        did = upsert_constitution(conn)
        clear_owned(conn, did)
        attach(conn, did)
        add_rows(conn, did, rows, ref=REF)

        qpa_rows = parse_numbered_articles(PUBLIC_ACCOUNTING_FILE, 140)
        qpa_id = upsert_document(
            conn,
            ref=PUBLIC_ACCOUNTING_REF,
            title="قانون محاسبات عمومی کشور",
            short="محاسبات عمومی کشور",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status="amended",
            date="1987-08-23",
            notes="پوشش ماده‌به‌ماده کامل شماره‌ای ۱۴۰ ماده قانون محاسبات عمومی کشور از منابع نظامات/شاقول/شناسنامه/اختبار؛ برخی مواد بلند به‌صورت گزیده نزدیک به متن آمده و مقابله رسمی‌تر با روزنامه رسمی توصیه می‌شود.",
        )
        clear_owned(conn, qpa_id)
        attach_public_accounting(conn, qpa_id)
        add_rows(conn, qpa_id, qpa_rows, PUBLIC_ACCOUNTING_SOURCE_NOTE, ref=PUBLIC_ACCOUNTING_REF)

        tender_rows = parse_numbered_articles(TENDER_FILE, 30)
        tender_id = upsert_document(
            conn,
            ref=TENDER_REF,
            title="قانون برگزاری مناقصات",
            short="برگزاری مناقصات",
            type_code="law",
            authority="مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام",
            status="in_force",
            date="2005-01-22",
            notes="متن کامل ۳۰ ماده و ۱۰ تبصره قانون برگزاری مناقصات از بازنشر منبع‌دار؛ مقابله رسمی‌تر با روزنامه رسمی توصیه می‌شود.",
        )
        clear_owned(conn, tender_id)
        attach_tender(conn, tender_id)
        add_rows(conn, tender_id, tender_rows, TENDER_SOURCE_NOTE, ref=TENDER_REF)

        parliament_rows = parse_structural_rows(PARLIAMENT_RULES_FILE, PARLIAMENT_RULES_REF)
        parliament_id = upsert_document(
            conn,
            ref=PARLIAMENT_RULES_REF,
            title="قانون آیین‌نامه داخلی مجلس شورای اسلامی",
            short="آیین‌نامه داخلی مجلس",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status="amended",
            date="1999-10-10",
            notes="خلاصه/گزیده ساختاری منبع‌دار از قانون آیین‌نامه داخلی مجلس شورای اسلامی با اصلاحات بعدی؛ رونوشت لفظ‌به‌لفظ کامل ماده‌به‌ماده نیست.",
        )
        clear_owned(conn, parliament_id)
        attach_parliament_rules(conn, parliament_id)
        add_rows(conn, parliament_id, parliament_rows, PARLIAMENT_RULES_SOURCE_NOTE, ref=PARLIAMENT_RULES_REF)

        election_rows = parse_structural_rows(PARLIAMENT_ELECTION_FILE, PARLIAMENT_ELECTION_REF)
        election_id = upsert_document(
            conn,
            ref=PARLIAMENT_ELECTION_REF,
            title="قانون انتخابات مجلس شورای اسلامی",
            short="انتخابات مجلس شورای اسلامی",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status="amended",
            date="1999-12-01",
            notes="خلاصه/گزیده ساختاری منبع‌دار از قانون انتخابات مجلس شورای اسلامی با اصلاحات و الحاقات بعدی؛ رونوشت لفظ‌به‌لفظ کامل ماده‌به‌ماده نیست.",
        )
        clear_owned(conn, election_id)
        attach_parliament_election(conn, election_id)
        add_rows(conn, election_id, election_rows, PARLIAMENT_ELECTION_SOURCE_NOTE, ref=PARLIAMENT_ELECTION_REF)

        presidential_rows = parse_structural_rows(PRESIDENTIAL_ELECTION_FILE, PRESIDENTIAL_ELECTION_REF)
        presidential_id = upsert_document(
            conn,
            ref=PRESIDENTIAL_ELECTION_REF,
            title="قانون انتخابات ریاست‌جمهوری اسلامی ایران",
            short="انتخابات ریاست‌جمهوری",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status="amended",
            date="1985-06-26",
            notes="خلاصه/گزیده ساختاری منبع‌دار از قانون انتخابات ریاست‌جمهوری اسلامی ایران و مقررات مرتبط؛ رونوشت لفظ‌به‌لفظ کامل ماده‌به‌ماده نیست.",
        )
        clear_owned(conn, presidential_id)
        attach_presidential_election(conn, presidential_id)
        add_rows(conn, presidential_id, presidential_rows, PRESIDENTIAL_ELECTION_SOURCE_NOTE, ref=PRESIDENTIAL_ELECTION_REF)

        councils_rows = parse_flexible_numbered_articles(COUNCILS_FILE, 137)
        councils_id = upsert_document(
            conn,
            ref=COUNCILS_REF,
            title="قانون تشکیلات، وظایف و انتخابات شوراهای اسلامی کشور و انتخاب شهرداران",
            short="قانون شوراهای اسلامی کشور و انتخاب شهرداران",
            type_code="law",
            authority="مجلس شورای اسلامی",
            status="amended",
            date="1996-05-21",
            notes="پوشش ماده‌به‌ماده ۱۳۷ ماده از متن تجمیعی/تنقیحی قانون تشکیلات، وظایف و انتخابات شوراهای اسلامی کشور و انتخاب شهرداران و دهیاران با اصلاحات ۱۴۰۳/۱۲/۱۹ از بازنشرهای شناسنامه/اختبار/نظامات؛ رونوشت رسمی qavanin/روزنامه رسمی نیست و مقابله رسمی‌تر توصیه می‌شود.",
        )
        clear_owned(conn, councils_id)
        attach_councils(conn, councils_id)
        add_rows(conn, councils_id, councils_rows, COUNCILS_SOURCE_NOTE, ref=COUNCILS_REF)

        add_rel(conn, REF, "QDA-1392", "implements", "اصل ۱۷۳ قانون اساسی مبنای تشکیل و قانون‌گذاری دیوان عدالت اداری است.")
        add_rel(conn, REF, "EQDAD-1402", "implements", "اصلاح قانون دیوان عدالت اداری در امتداد اصل ۱۷۳ و سازوکار نظارت قضایی اداری است.")
        add_rel(conn, REF, "QADM-1379", "cites", "اصول ۳۴ و ۳۵ قانون اساسی مبنای حق دادخواهی، دسترسی به دادگاه صالح و حق وکیل در دادرسی مدنی است.")
        add_rel(conn, REF, "QADK-1392", "cites", "اصول ۳۲ تا ۳۹، ۱۶۵، ۱۶۶ و ۱۶۸ قانون اساسی از مبانی آیین دادرسی کیفری هستند.")
        add_rel(conn, REF, "QMA-1392", "cites", "اصول ۳۶، ۳۷، ۳۸، ۳۹ و ۱۶۹ قانون اساسی با اصل قانونی بودن جرم و مجازات و حقوق متهم پیوند دارد.")
        add_rel(conn, REF, "QM-1307", "cites", "قانون مدنی در بسیاری از حوزه‌های مالکیت، احوال شخصیه و تعهدات با اصول ۲۲، ۴۰، ۴۱، ۴۲، ۴۶ و ۴۷ قانون اساسی پیوند دارد.")
        add_rel(conn, REF, "QE44-1386", "implements", "قانون اجرای سیاست‌های کلی اصل ۴۴ در امتداد اصل ۴۴ قانون اساسی و تحول نظام اقتصادی تدوین شده است.")
        add_rel(conn, REF, "QCSM-1386", "cites", "قانون مدیریت خدمات کشوری با اصول مربوط به نظام اداری، اصل ۱۲۶ و قواعد استخدام عمومی پیوند دارد.")
        add_rel(conn, REF, "QDDA-1388", "cites", "حق دسترسی به اطلاعات و شفافیت با اصول ۲۴، ۲۵، ۵۵ و حق نظارت عمومی در قانون اساسی پیوند موضوعی دارد.")
        add_rel(conn, REF, "QTE-1382", "cites", "اعتبار داده‌پیام، ارتباطات و حریم اطلاعاتی با اصول ۲۴ و ۲۵ قانون اساسی و قواعد آزادی ارتباطات پیوند دارد.")
        add_rel(conn, REF, "QJR-1388", "cites", "قانون جرایم رایانه‌ای با اصول ۲۵، ۳۶، ۳۷، ۳۸، ۳۹ و ۱۶۹ قانون اساسی پیوند دارد.")
        add_rel(conn, REF, "QOBI-1346", "cites", "اصل ۴۴ قانون اساسی در نسخه بازنگری‌شده، تأمین نیرو و شبکه‌های بزرگ زیرساختی را در چارچوب نظام اقتصادی کشور قرار می‌دهد.")
        add_rel(conn, REF, "DAD-ELECTRIC-DIGGING-1401", "cites", "دادنامه‌های ابطال مقررات دولتی/محلی به اصول ۱۷۰ و ۱۷۳ قانون اساسی و صلاحیت دیوان عدالت اداری متکی هستند.")
        add_rel(conn, REF, "DAD-OIL-GAS-RETIRE-1400", "cites", "رأی درباره حدود اختیارات مقررات اداری صنعت نفت با اصول ۱۳۸، ۱۷۰ و ۱۷۳ قانون اساسی پیوند دارد.")
        add_rel(conn, REF, PUBLIC_ACCOUNTING_REF, "implements", "قانون محاسبات عمومی کشور سازوکار اجرای اصول ۵۲، ۵۳، ۵۴ و ۵۵ قانون اساسی درباره بودجه، خزانه و دیوان محاسبات را تنظیم می‌کند.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, REF, "cites", "قانون محاسبات عمومی کشور به‌طور مستقیم با اصول بودجه، خزانه‌داری کل و دیوان محاسبات در قانون اساسی پیوند دارد.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, "QCSM-1386", "cites", "تعاریف دستگاه اجرایی، شرکت دولتی، مؤسسات عمومی و مسئولیت‌های اداری-مالی با قانون مدیریت خدمات کشوری پیوند دارد.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, "QDA-1392", "cites", "تصمیمات و مقررات مالی اداری دولت در صورت مغایرت با قانون می‌توانند در چارچوب صلاحیت دیوان عدالت اداری قابل رسیدگی باشند.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, "DAD-OIL-GAS-RETIRE-1400", "cites", "مفهوم حدود اختیار مقررات اداری و مالی دستگاه‌ها با رویه دیوان عدالت اداری درباره صنعت نفت ارتباط دارد.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, "QOBI-1346", "cites", "تعریف شرکت دولتی، اموال و بودجه شرکت‌های دولتی با شرکت‌ها و مؤسسات بخش برق و نیرو پیوند موضوعی دارد.")
        add_rel(conn, PUBLIC_ACCOUNTING_REF, "DAD-ELECTRIC-DIGGING-1401", "cites", "حسابداری وجوه، عوارض و بهای خدمات عمومی با رویه ابطال بهای خدمات فاقد مبنای قانونی مرتبط است.")
        add_rel(conn, REF, TENDER_REF, "implements", "قانون برگزاری مناقصات سازوکار شفافیت و رقابت در معاملات عمومی را در امتداد اصول ۵۲، ۵۳، ۷۵، ۱۳۸ و اصل ۴۴ قانون اساسی تقویت می‌کند.")
        add_rel(conn, TENDER_REF, PUBLIC_ACCOUNTING_REF, "implements", "قانون برگزاری مناقصات مکمل مقررات معاملات دولتی در قانون محاسبات عمومی کشور است.")
        add_rel(conn, TENDER_REF, REF, "cites", "تصویب و ابلاغ قانون برگزاری مناقصات با اصول ۱۱۲ و ۱۲۳ قانون اساسی و حوزه معاملات عمومی پیوند دارد.")
        add_rel(conn, TENDER_REF, "QCSM-1386", "cites", "دستگاه‌های اجرایی و مقامات مجاز در فرایند مناقصه با نظام اداری و استخدامی دستگاه‌ها پیوند دارند.")
        add_rel(conn, TENDER_REF, "QE44-1386", "cites", "رقابت، منع انحصار و شفافیت در مناقصات با سیاست‌های کلی اصل ۴۴ و قانون اجرای آن مرتبط است.")
        add_rel(conn, TENDER_REF, "AIPC-1395", "cites", "قراردادهای بالادستی نفت و گاز و واگذاری پروژه‌های بزرگ در عمل با قواعد رقابت، تشخیص صلاحیت و فرایند ارجاع کار پیوند موضوعی دارند.")
        add_rel(conn, TENDER_REF, "QOBI-1346", "cites", "خرید، پیمانکاری، تجهیز و اجرای پروژه‌های صنعت برق در شرکت‌ها و مؤسسات عمومی با قواعد مناقصات مرتبط است.")
        add_rel(conn, TENDER_REF, "DAD-OIL-GAS-RETIRE-1400", "cites", "رویه دیوان درباره حدود اختیار مقررات دستگاه‌ها با رعایت قانون در فرایندهای اداری و معاملاتی مرتبط است.")
        add_rel(conn, REF, PARLIAMENT_RULES_REF, "implements", "قانون آیین‌نامه داخلی مجلس سازوکار اجرایی اصول ۶۲ تا ۹۹ قانون اساسی درباره مجلس، قانون‌گذاری و نظارت پارلمانی را تنظیم می‌کند.")
        add_rel(conn, PARLIAMENT_RULES_REF, REF, "cites", "آیین‌نامه داخلی مجلس مستند به اصول قانون اساسی درباره تشکیل، اداره و صلاحیت‌های مجلس است.")
        add_rel(conn, PARLIAMENT_RULES_REF, "QPA-1366", "cites", "بررسی بودجه، تفریغ بودجه و گزارش دیوان محاسبات در آیین‌نامه داخلی مجلس با قانون محاسبات عمومی پیوند دارد.")
        add_rel(conn, PARLIAMENT_RULES_REF, "QBT-1383", "cites", "قانون‌گذاری و نظارت بر معاملات عمومی و مناقصات در فرایندهای مجلس و کمیسیون‌ها قابل پیگیری است.")
        add_rel(conn, PARLIAMENT_RULES_REF, "QDA-1392", "cites", "نظارت مجلس، اصل نود و ارتباط با دیوان عدالت اداری در نظام نظارت عمومی و اداری پیوند موضوعی دارند.")
        add_rel(conn, PARLIAMENT_RULES_REF, "QDDA-1388", "cites", "انتشار مذاکرات، مستندسازی و دسترسی عمومی به اطلاعات مجلس با قانون انتشار و دسترسی آزاد به اطلاعات پیوند دارد.")
        add_rel(conn, PARLIAMENT_RULES_REF, "DAD-ELECTION-JUDGES-1404", "cites", "رویه دیوان درباره استعفای قضات برای انتخابات مجلس با قواعد نمایندگی و انتخابات پارلمانی مرتبط است.")
        add_rel(conn, REF, PARLIAMENT_ELECTION_REF, "implements", "قانون انتخابات مجلس سازوکار اجرای اصول ۶، ۵۶، ۶۲، ۶۴، ۶۵، ۶۷ و ۹۹ قانون اساسی درباره انتخابات مجلس را تنظیم می‌کند.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, REF, "cites", "قانون انتخابات مجلس مستند به اصول قانون اساسی درباره حاکمیت ملت، مجلس و نظارت شورای نگهبان است.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, PARLIAMENT_RULES_REF, "cites", "اعتبارنامه منتخبین، آغاز دوره نمایندگی و سازوکار داخلی مجلس با آیین‌نامه داخلی مجلس پیوند دارد.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, "QCSM-1386", "cites", "استعفای مقامات، سنوات خدمت، مأموریت کارکنان و همکاری دستگاه‌ها در انتخابات با نظام اداری و استخدامی مرتبط است.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, "QDDA-1388", "cites", "انتشار اطلاعات انتخاباتی، فهرست‌ها و شفافیت فرایند انتخابات با قانون دسترسی آزاد به اطلاعات پیوند دارد.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, "QTE-1382", "cites", "سامانه جامع انتخابات، امضای الکترونیک و داده‌پیام در انتخابات با قانون تجارت الکترونیکی مرتبط است.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, "QJR-1388", "cites", "جرایم و تخلفات انتخاباتی در بستر سامانه و فضای مجازی با قانون جرایم رایانه‌ای پیوند موضوعی دارد.")
        add_rel(conn, PARLIAMENT_ELECTION_REF, "DAD-ELECTION-JUDGES-1404", "cites", "دادنامه دیوان عدالت درباره الزام قضات متقاضی نامزدی انتخابات مجلس به استعفا با شرایط و موانع داوطلبی مرتبط است.")
        add_rel(conn, REF, PRESIDENTIAL_ELECTION_REF, "implements", "قانون انتخابات ریاست‌جمهوری سازوکار اجرای اصول ۶، ۹۹، ۱۱۴، ۱۱۵، ۱۱۷، ۱۱۹، ۱۲۱ و ۱۳۱ قانون اساسی را تنظیم می‌کند.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, REF, "cites", "قانون انتخابات ریاست‌جمهوری مستند به اصول قانون اساسی درباره انتخاب مستقیم رئیس‌جمهور، شرایط داوطلبان، تنفیذ و نظارت شورای نگهبان است.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, PARLIAMENT_ELECTION_REF, "cites", "قوانین انتخابات ریاست‌جمهوری و مجلس در قواعد عمومی انتخابات، نظارت شورای نگهبان، اخذ رأی و همکاری دستگاه‌ها هم‌خانواده هستند.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, "QCSM-1386", "cites", "سنوات ریاست‌جمهوری کارکنان دولت و همکاری دستگاه‌ها در انتخابات با نظام اداری و استخدامی پیوند دارد.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, "QDDA-1388", "cites", "اطلاع‌رسانی عمومی انتخابات، اعلامیه‌ها و دسترسی عمومی به اطلاعات انتخاباتی با قانون انتشار و دسترسی آزاد به اطلاعات مرتبط است.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, "QTE-1382", "cites", "سامانه و نرم‌افزارهای انتخاباتی، امضای الکترونیک و داده‌پیام با قانون تجارت الکترونیکی پیوند موضوعی دارد.")
        add_rel(conn, PRESIDENTIAL_ELECTION_REF, "QJR-1388", "cites", "امنیت نرم‌افزارها، سخت‌افزارها و تخلفات احتمالی سامانه انتخاباتی با قانون جرایم رایانه‌ای مرتبط است.")
        add_rel(conn, REF, COUNCILS_REF, "implements", "قانون شوراهای اسلامی کشور سازوکار اجرای اصول ۷، ۱۰۰، ۱۰۱، ۱۰۲، ۱۰۳، ۱۰۵ و ۱۰۶ قانون اساسی را تنظیم می‌کند.")
        add_rel(conn, COUNCILS_REF, REF, "cites", "قانون شوراها مستند به اصول قانون اساسی درباره شوراها، اداره محلی و شورای عالی استان‌ها است.")
        add_rel(conn, COUNCILS_REF, "QSH-1334", "cites", "وظایف شورای شهر و انتخاب شهردار با قانون شهرداری و اداره امور شهرداری پیوند مستقیم دارد.")
        add_rel(conn, COUNCILS_REF, "QDPSH-1401", "cites", "مصوبات شورا درباره عوارض، درآمدها و هزینه‌های شهری با قانون درآمد پایدار شهرداری‌ها و دهیاری‌ها مرتبط است.")
        add_rel(conn, COUNCILS_REF, "AISH-1346", "cites", "بودجه و امور مالی شهرداری‌ها و نقش شورای شهر با آیین‌نامه مالی شهرداری‌ها پیوند دارد.")
        add_rel(conn, COUNCILS_REF, PARLIAMENT_ELECTION_REF, "cites", "قواعد عمومی انتخابات، داوطلبی، تبلیغات و نظارت در انتخابات شوراها با قانون انتخابات مجلس هم‌خانواده است.")
        add_rel(conn, COUNCILS_REF, "QDA-1392", "cites", "مصوبات شوراها و عوارض محلی در صورت مغایرت با قانون می‌توانند در هیأت عمومی دیوان عدالت اداری مطرح شوند.")
        add_rel(conn, COUNCILS_REF, "DAD-ARAK-MOSHREF-1404", "cites", "دادنامه عوارض حق مشرفیت شهرداری اراک نمونه رویه دیوان عدالت اداری درباره حدود اختیار شوراها در وضع عوارض است.")
        conn.commit()
        print("loaded public law core", 7, "documents", len(rows) + len(qpa_rows) + len(tender_rows) + len(parliament_rows) + len(election_rows) + len(presidential_rows) + len(councils_rows), "rows")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
