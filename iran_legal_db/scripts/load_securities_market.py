# -*- coding: utf-8 -*-
"""Load the Securities Market Law and principal listed-company regulations."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "data", "seed")]

from schema import get_connection
from importer import (
    add_article, add_relation, add_tag, get_or_create_document,
    link_document_tag, link_document_topic,
)
from securities_market import (
    SECURITIES_MARKET_ORIGINAL,
    SECURITIES_MARKET_CURRENT_UPDATES,
    SECURITIES_MARKET_BYLAW,
    FINANCIAL_INSTRUMENTS_LAW,
    FINANCIAL_INSTRUMENTS_ART14_VERSIONS,
    PRODUCTION_FINANCING_LAW,
    FINANCIAL_ENTITIES_REGISTRATION_DIRECTIVE,
    CORPORATE_GOVERNANCE_ORIGINAL,
    CORPORATE_GOVERNANCE_CURRENT_UPDATES,
)

REF_MARKET = "QBOV-1384"
REF_BYLAW = "AIBOV-1386"
REF_INSTRUMENTS = "QTNM-1388"
REF_FINANCING = "QTMZ-1402"
REF_REGISTRATION = "DSNM-1385"
REF_GOVERNANCE = "DHSH-1401"
PACKAGE_REFS = (
    REF_MARKET, REF_BYLAW, REF_INSTRUMENTS, REF_FINANCING,
    REF_REGISTRATION, REF_GOVERNANCE,
)

D_MARKET = "2005-11-22"          # 1384/09/01
D_BYLAW = "2007-06-24"           # 1386/04/03
D_INSTRUMENTS = "2009-12-16"     # 1388/09/25
D_FINE_1394 = "2015-05-03"       # 1394/02/13
D_FINE_1398 = "2019-04-28"       # 1398/02/08
D_FINE_1401 = "2022-10-02"       # 1401/07/10
D_DATA = "2022-09-21"            # 1401/06/30
D_FINANCING = "2024-03-12"       # 1402/12/22
D_FINANCING_EFFECT = "2024-05-07"
D_REGISTRATION = "2006-10-22"    # 1385/07/30
D_GOVERNANCE = "2022-10-10"      # 1401/07/18
D_GOVERNANCE_AMEND = "2023-05-01"  # circular dated 1402/02/11

SRC_MARKET = (
    "قانون بازار اوراق بهادار جمهوری اسلامی ایران مصوب ۱۳۸۴/۰۹/۰۱؛ متن با نسخه "
    "تلفیقی اختبار و متن سازمان بورس مقابله شده است."
)
SRC_BYLAW = (
    "آیین‌نامه اجرایی قانون بازار اوراق بهادار مصوب ۱۳۸۶/۰۴/۰۳ هیئت وزیران؛ "
    "https://davoudabadi.ir/page/3847016/"
)
SRC_INSTRUMENTS = (
    "قانون توسعه ابزارها و نهادهای مالی جدید مصوب ۱۳۸۸/۰۹/۲۵؛ "
    "https://shenasname.ir/laws/661-قانون-توسعه-ابزارها-و-نهادهای-مالی"
)
SRC_FINANCING = (
    "قانون تأمین مالی تولید و زیرساخت‌ها مصوب ۱۴۰۲/۱۲/۲۲؛ متن کامل ۴۶ ماده، "
    "مقابله‌شده با نسخه منتشرشده در اختبار."
)
SRC_REGISTRATION = (
    "دستورالعمل نحوه دریافت مجوز و ثبت بورس‌ها، کانون‌ها و نهادهای مالی، مصوب "
    "۱۳۸۵/۰۷/۳۰ هیئت مدیره سازمان بورس؛ https://nezamat.ir/post-1784/"
)
SRC_GOVERNANCE = (
    "دستورالعمل حاکمیت شرکتی ناشران ثبت‌شده نزد سازمان بورس مصوب ۱۴۰۱/۰۷/۱۸، "
    "ابلاغیه ۱۲۲/۱۱۷۶۳۵ و اصلاحیه ۱۲۲/۱۲۵۷۸۸ مورخ ۱۴۰۲/۰۲/۱۱."
)


def pn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def lookup_id(conn, table, column, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def ensure_authority(conn, name, authority_type="administrative"):
    conn.execute(
        "INSERT OR IGNORE INTO authorities(name_fa,authority_type) VALUES(?,?)",
        (name, authority_type),
    )


def upsert_document(conn, *, reference_code, title, short_title, type_code,
                    authority, status_code, ratification_date, effective_date=None,
                    publication_date=None, official_newspaper_no=None, notes=None):
    row = conn.execute(
        "SELECT id FROM documents WHERE reference_code=?", (reference_code,)
    ).fetchone()
    if row:
        did = row["id"]
    else:
        did = get_or_create_document(
            conn, title=title, short_title=short_title, type_code=type_code,
            issuing_authority=authority, status_code=status_code,
            ratification_date=ratification_date, effective_date=effective_date,
            publication_date=publication_date,
            official_newspaper_no=official_newspaper_no,
            reference_code=reference_code, notes=notes,
        )
    conn.execute(
        """UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,
           status_id=?,ratification_date=?,publication_date=?,effective_date=?,
           official_newspaper_no=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (title, short_title, lookup_id(conn, "document_types", "code", type_code),
         lookup_id(conn, "authorities", "name_fa", authority),
         lookup_id(conn, "statuses", "code", status_code), ratification_date,
         publication_date, effective_date or ratification_date,
         official_newspaper_no, notes, did),
    )
    return did


def clear_package(conn, ids):
    marks = ",".join("?" for _ in ids)
    # Only links owned by this package are rebuilt. Incoming links from other
    # loaders must survive a later idempotent refresh.
    conn.execute(
        f"DELETE FROM relations WHERE from_document_id IN ({marks})",
        tuple(ids),
    )
    for did in ids:
        conn.execute("DELETE FROM articles_fts WHERE document_id=?", (did,))
        conn.execute("DELETE FROM articles WHERE document_id=?", (did,))
        conn.execute("DELETE FROM document_tags WHERE document_id=?", (did,))
        conn.execute("DELETE FROM document_topics WHERE document_id=?", (did,))


def decorate(conn, did, tags, topics=("حقوق تجارت", "حقوق بازار سرمایه")):
    for topic in topics:
        link_document_topic(conn, did, topic)
    for tag in tags:
        link_document_tag(conn, did, add_tag(conn, tag))


def add_rows(conn, did, ref, rows, date, source):
    ids = {}
    for n, text in rows:
        ids[n] = add_article(
            conn, did, article_no=pn(n), article_key=f"{ref}:{n}",
            version_no=1, is_current=1, effective_date=date,
            text=text, source_note=source,
        )
    return ids


def add_market_law(conn, did):
    original = dict(SECURITIES_MARKET_ORIGINAL)
    current_updates = SECURITIES_MARKET_CURRENT_UPDATES
    ids, historical = {}, {}
    count = 0
    for n in range(1, 61):
        if n == 7:
            stages = [
                (D_MARKET, original[n], D_FINANCING_EFFECT, 0,
                 "متن مصوب ۱۳۸۴"),
                (D_FINANCING_EFFECT, current_updates[n], None, 1,
                 "اصلاح بندهای ۵، ۶ و ۷ به موجب ماده ۲۰ قانون تأمین مالی تولید و زیرساخت‌ها"),
            ]
        elif n == 19:
            stages = [
                (D_MARKET, original[n], D_DATA, 0, "متن مصوب ۱۳۸۴"),
                (D_DATA, current_updates[n], None, 1,
                 "اصلاح مرجع صدور مجوز دسترسی به اطلاعات به موجب قانون مدیریت داده‌ها و اطلاعات ملی"),
            ]
        else:
            stages = [(D_MARKET, original[n], None, 1, "متن مصوب ۱۳۸۴")]
        for version, (effective, text, expiry, current, note) in enumerate(stages, 1):
            version_source = SRC_MARKET
            if n == 7 and version == 2:
                version_source += " اصلاح: ماده ۲۰ قانون تأمین مالی تولید و زیرساخت‌ها مصوب ۱۴۰۲."
            elif n == 19 and version == 2:
                version_source += " اصلاح: قانون مدیریت داده‌ها و اطلاعات ملی مصوب ۱۴۰۱."
            aid = add_article(
                conn, did, article_no=pn(n), article_key=f"{REF_MARKET}:{n}",
                version_no=version, is_current=current, effective_date=effective,
                expiry_date=expiry, text=text, source_note=version_source, notes=note,
            )
            (ids if current else historical)[n] = aid
            count += 1
    return ids, historical, count


def add_instruments(conn, did):
    base = dict(FINANCIAL_INSTRUMENTS_LAW)
    versions14 = FINANCIAL_INSTRUMENTS_ART14_VERSIONS
    ids, historical = {}, {}
    count = 0
    for n in range(1, 19):
        if n == 14:
            stages = [
                (D_INSTRUMENTS, versions14["1388"], D_FINE_1394, 0, "حدود مصوب ۱۳۸۸"),
                (D_FINE_1394, versions14["1394"], D_FINE_1398, 0, "تعدیل ۱۳۹۴"),
                (D_FINE_1398, versions14["1398"], D_FINE_1401, 0, "تعدیل ۱۳۹۸"),
                (D_FINE_1401, versions14["1401"], None, 1, "حدود جاری پس از تعدیل ۱۴۰۱"),
            ]
        else:
            stages = [(D_INSTRUMENTS, base[n], None, 1, "متن مصوب ۱۳۸۸")]
        for version, (effective, text, expiry, current, note) in enumerate(stages, 1):
            version_source = SRC_INSTRUMENTS
            if n == 14 and version > 1:
                version_source += (
                    " تعدیل حدود جریمه به موجب تصویب‌نامه‌های هیئت وزیران؛ "
                    "نسخه جاری: مصوبه ۱۴۰۱/۰۷/۱۰."
                )
            aid = add_article(
                conn, did, article_no=pn(n), article_key=f"{REF_INSTRUMENTS}:{n}",
                version_no=version, is_current=current, effective_date=effective,
                expiry_date=expiry, text=text, source_note=version_source,
                notes=note,
            )
            (ids if current else historical)[n] = aid
            count += 1
    return ids, historical, count


def add_governance(conn, did):
    original = dict(CORPORATE_GOVERNANCE_ORIGINAL)
    updates = CORPORATE_GOVERNANCE_CURRENT_UPDATES
    ids, historical = {}, {}
    count = 0
    for n in range(1, 44):
        if n in updates:
            stages = [
                (D_GOVERNANCE, original[n], D_GOVERNANCE_AMEND, 0, "نسخه مصوب ۱۴۰۱"),
                (D_GOVERNANCE_AMEND, updates[n], None, 1, "نسخه جاری اصلاحی ۱۴۰۲"),
            ]
        else:
            stages = [(D_GOVERNANCE, original[n], None, 1, "نسخه مصوب ۱۴۰۱")]
        for version, (effective, text, expiry, current, note) in enumerate(stages, 1):
            aid = add_article(
                conn, did, article_no=pn(n), article_key=f"{REF_GOVERNANCE}:{n}",
                version_no=version, is_current=current, effective_date=effective,
                expiry_date=expiry, text=text, source_note=SRC_GOVERNANCE,
                notes=note,
            )
            (ids if current else historical)[n] = aid
            count += 1
    return ids, historical, count


def current_article(conn, key):
    row = conn.execute(
        "SELECT id FROM articles WHERE article_key=? AND is_current=1", (key,)
    ).fetchone()
    return row["id"] if row else None


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        conn.execute("INSERT OR IGNORE INTO topics(name_fa) VALUES('حقوق بازار سرمایه')")
        ensure_authority(conn, "هیئت مدیره سازمان بورس و اوراق بهادار")

        docs = {}
        docs[REF_MARKET] = upsert_document(
            conn, reference_code=REF_MARKET,
            title="قانون بازار اوراق بهادار جمهوری اسلامی ایران (مصوب ۱۳۸۴، با اصلاحات ۱۴۰۱ و ۱۴۰۲)",
            short_title="ق.ب.ا.ب.", type_code="law", authority="مجلس شورای اسلامی",
            status_code="amended", ratification_date=D_MARKET,
            effective_date="2006-03-22",
            notes="متن کامل ۶۰ ماده و ۲۹ تبصره؛ تاریخچه اصلاح مواد ۷ و ۱۹ نگهداری شده است.",
        )
        docs[REF_BYLAW] = upsert_document(
            conn, reference_code=REF_BYLAW,
            title="آیین‌نامه اجرایی قانون بازار اوراق بهادار جمهوری اسلامی ایران",
            short_title="آیین‌نامه قانون بازار", type_code="regulation",
            authority="هیئت وزیران", status_code="in_force",
            ratification_date=D_BYLAW, effective_date=D_BYLAW,
            notes="متن کامل ۲۰ ماده درباره نهادهای تحت نظارت، پذیرش، افشا و تخلفات بازار.",
        )
        docs[REF_INSTRUMENTS] = upsert_document(
            conn, reference_code=REF_INSTRUMENTS,
            title="قانون توسعه ابزارها و نهادهای مالی جدید به منظور تسهیل اجرای سیاست‌های کلی اصل چهل و چهارم قانون اساسی",
            short_title="قانون توسعه ابزارهای مالی", type_code="law",
            authority="مجلس شورای اسلامی", status_code="amended",
            ratification_date=D_INSTRUMENTS, effective_date=D_INSTRUMENTS,
            notes="۱۸ ماده؛ صندوق‌های سرمایه‌گذاری، نهاد واسط، معافیت‌های مالیاتی و چهار نسل مبلغ ماده ۱۴.",
        )
        docs[REF_FINANCING] = upsert_document(
            conn, reference_code=REF_FINANCING,
            title="قانون تأمین مالی تولید و زیرساخت‌ها",
            short_title="قانون تأمین مالی", type_code="law",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=D_FINANCING, effective_date=D_FINANCING_EFFECT,
            notes="متن کامل ۴۶ ماده؛ ماده ۲۰ اصلاح‌کننده ماده ۷ قانون بازار اوراق بهادار است.",
        )
        docs[REF_REGISTRATION] = upsert_document(
            conn, reference_code=REF_REGISTRATION,
            title="دستورالعمل نحوه دریافت مجوز و ثبت بورس‌ها، کانون‌ها و نهادهای مالی نزد مرجع ثبت شرکت‌ها",
            short_title="دستورالعمل ثبت نهادهای مالی", type_code="directive",
            authority="هیئت مدیره سازمان بورس و اوراق بهادار", status_code="in_force",
            ratification_date=D_REGISTRATION, effective_date=D_REGISTRATION,
            notes="۷ ماده درباره تأسیس، تغییرات، تبدیل، ادغام، تعلیق و تصفیه نهادهای مالی.",
        )
        docs[REF_GOVERNANCE] = upsert_document(
            conn, reference_code=REF_GOVERNANCE,
            title="دستورالعمل حاکمیت شرکتی ناشران ثبت‌شده نزد سازمان بورس و اوراق بهادار",
            short_title="دستورالعمل حاکمیت شرکتی", type_code="directive",
            authority="هیئت مدیره سازمان بورس و اوراق بهادار", status_code="amended",
            ratification_date=D_GOVERNANCE, effective_date=D_GOVERNANCE,
            official_newspaper_no="۱۲۲/۱۱۷۶۳۵",
            notes="۴۳ ماده و ۲۸ تبصره؛ تاریخچه اصلاحات ۱۴۰۲ مواد ۴، ۳۰، ۳۶، ۳۷ و ۴۳.",
        )

        clear_package(conn, list(docs.values()))

        decorate(conn, docs[REF_MARKET], ["بورس", "اوراق بهادار", "شورای عالی بورس", "سازمان بورس", "قانون مادر"])
        decorate(conn, docs[REF_BYLAW], ["بورس", "نهاد مالی", "تشکل خودانتظام", "پذیرش اوراق بهادار"])
        decorate(conn, docs[REF_INSTRUMENTS], ["صندوق سرمایه‌گذاری", "نهاد واسط", "سهام شناور آزاد", "صکوک"])
        decorate(conn, docs[REF_FINANCING], ["تأمین مالی", "وثیقه", "افزایش سرمایه", "زیرساخت"])
        decorate(conn, docs[REF_REGISTRATION], ["ثبت نهاد مالی", "مجوز سازمان بورس", "مرجع ثبت شرکت‌ها"])
        decorate(conn, docs[REF_GOVERNANCE], ["حاکمیت شرکتی", "سهامدار اقلیت", "کمیته حسابرسی", "گزارش پایداری"])

        market_ids, market_old, market_versions = add_market_law(conn, docs[REF_MARKET])
        bylaw_ids = add_rows(conn, docs[REF_BYLAW], REF_BYLAW, SECURITIES_MARKET_BYLAW, D_BYLAW, SRC_BYLAW)
        instrument_ids, instrument_old, instrument_versions = add_instruments(conn, docs[REF_INSTRUMENTS])
        financing_ids = add_rows(conn, docs[REF_FINANCING], REF_FINANCING, PRODUCTION_FINANCING_LAW, D_FINANCING_EFFECT, SRC_FINANCING)
        registration_ids = add_rows(conn, docs[REF_REGISTRATION], REF_REGISTRATION, FINANCIAL_ENTITIES_REGISTRATION_DIRECTIVE, D_REGISTRATION, SRC_REGISTRATION)
        governance_ids, governance_old, governance_versions = add_governance(conn, docs[REF_GOVERNANCE])

        # Executive regulation -> parent law, including article-level targets.
        add_relation(conn, docs[REF_BYLAW], "implements", docs[REF_MARKET],
                     from_article_id=bylaw_ids[1], to_article_id=market_ids[4],
                     description="آیین‌نامه اجرایی پیشنهادی موضوع بند ۳ ماده ۴ قانون.")
        for own, target, desc in (
            (2, 30, "معاملات پس از پذیرش اوراق بهادار."),
            (9, 45, "ضوابط نشر و افشای اطلاعات ناشران."),
            (16, 30, "تصویب دستورالعمل پذیرش اوراق بهادار."),
            (17, 35, "رسیدگی به تخلفات انضباطی اعضای بورس."),
            (19, 46, "مصادیق دستکاری و ظاهر گمراه‌کننده بازار."),
            (20, 46, "گزارش معاملات اشخاص دارای اطلاعات نهانی."),
        ):
            add_relation(conn, docs[REF_BYLAW], "implements", docs[REF_MARKET],
                         from_article_id=bylaw_ids[own], to_article_id=market_ids[target],
                         description=desc)

        # Development of instruments and the institutional framework.
        add_relation(conn, docs[REF_INSTRUMENTS], "implements", docs[REF_MARKET],
                     description="توسعه صندوق‌ها، نهاد واسط و ضمانت‌اجراهای قانون بازار.")
        for own, target, desc in (
            (2, 1, "شخصیت حقوقی و ثبت صندوق‌های سرمایه‌گذاری."),
            (5, 37, "صلاحیت هیئت داوری در اختلافات صندوق‌ها."),
            (10, 46, "تسری جرایم بازار به بورس‌های کالایی."),
            (14, 35, "جریمه اداری تخلفات ناشران و نهادهای مالی."),
            (16, 49, "الزام اشخاص تحت نظارت به ارائه اطلاعات."),
        ):
            add_relation(conn, docs[REF_INSTRUMENTS], "cites", docs[REF_MARKET],
                         from_article_id=instrument_ids[own], to_article_id=market_ids[target],
                         description=desc)

        # Production financing law directly amends article 7.
        add_relation(conn, docs[REF_FINANCING], "amends", docs[REF_MARKET],
                     from_article_id=financing_ids[20], to_article_id=market_ids[7],
                     description="اصلاح بندهای ۵ و ۶ و جایگزینی بند ۷ ماده ۷ قانون بازار.")
        add_relation(conn, docs[REF_FINANCING], "cites", docs[REF_INSTRUMENTS],
                     from_article_id=financing_ids[14],
                     description="تسهیلات مالیاتی ابزارها و نهادهای تأمین مالی.")

        # Company-law and registration links.
        qrs = conn.execute("SELECT id FROM documents WHERE reference_code='QRS-1310'").fetchone()
        ltej = conn.execute("SELECT id FROM documents WHERE reference_code='LTEJ-1347'").fetchone()
        if qrs:
            add_relation(conn, docs[REF_REGISTRATION], "implements", qrs["id"],
                         from_article_id=registration_ids[1],
                         description="لزوم ارائه تأییدیه سازمان بورس به مرجع ثبت شرکت‌ها.")
            add_relation(conn, docs[REF_FINANCING], "cites", qrs["id"],
                         from_article_id=financing_ids[19],
                         description="فرایندهای الکترونیکی ثبت شرکت‌های تحت نظارت.")
        add_relation(conn, docs[REF_REGISTRATION], "implements", docs[REF_MARKET],
                     from_article_id=registration_ids[1], to_article_id=market_ids[7],
                     description="اجرای صلاحیت صدور مجوز نهادهای مالی.")
        add_relation(conn, docs[REF_REGISTRATION], "cites", docs[REF_INSTRUMENTS],
                     from_article_id=registration_ids[5], to_article_id=instrument_ids[2],
                     description="تبدیل و ثبت صندوق‌ها و سایر نهادهای مالی.")
        if ltej:
            for own, target, desc in (
                (17, 173, "اعلامیه پذیره‌نویسی افزایش سرمایه شرکت سهامی عام."),
                (18, 166, "مهلت اعمال حق تقدم و پذیره‌نویسی."),
            ):
                target_aid = current_article(conn, f"LTEJ-1347:{target}")
                add_relation(conn, docs[REF_FINANCING], "cites", ltej["id"],
                             from_article_id=financing_ids[own], to_article_id=target_aid,
                             description=desc)
            target129 = current_article(conn, "LTEJ-1347:129")
            add_relation(conn, docs[REF_GOVERNANCE], "cites", ltej["id"],
                         from_article_id=governance_ids[7], to_article_id=target129,
                         description="معاملات مدیران و اشخاص وابسته.")

        # Corporate governance enforcement links.
        add_relation(conn, docs[REF_GOVERNANCE], "implements", docs[REF_MARKET],
                     from_article_id=governance_ids[3], to_article_id=market_ids[7],
                     description="حمایت از سرمایه‌گذاران و پیشگیری از تخلفات ناشران.")
        add_relation(conn, docs[REF_GOVERNANCE], "implements", docs[REF_INSTRUMENTS],
                     from_article_id=governance_ids[4], to_article_id=instrument_ids[13],
                     description="صلاحیت حرفه‌ای اعضای هیئت مدیره و مدیرعامل.")
        add_relation(conn, docs[REF_GOVERNANCE], "implements", docs[REF_INSTRUMENTS],
                     from_article_id=governance_ids[42], to_article_id=instrument_ids[14],
                     description="ضمانت اجرا و جریمه نقدی تخلفات حاکمیت شرکتی.")
        add_relation(conn, docs[REF_GOVERNANCE], "cites", docs[REF_MARKET],
                     from_article_id=governance_ids[37], to_article_id=market_ids[45],
                     description="افشای اطلاعات ناشران ثبت‌شده نزد سازمان.")

        conn.commit()
        totals = conn.execute(
            """SELECT (SELECT COUNT(*) FROM documents) docs,
                      (SELECT COUNT(*) FROM articles) versions,
                      (SELECT COUNT(*) FROM articles WHERE is_current=1) current_rows,
                      (SELECT COUNT(*) FROM articles WHERE is_current=0) historical,
                      (SELECT COUNT(*) FROM relations) relations"""
        ).fetchone()
        print(f"[OK] قانون بازار: ۶۰ ماده، {market_versions} نسخه، ۶۰ جاری")
        print(f"[OK] آیین‌نامه: ۲۰ | قانون ابزارهای مالی: ۱۸ ماده، {instrument_versions} نسخه")
        print("[OK] قانون تأمین مالی: ۴۶ | دستورالعمل ثبت نهادها: ۷")
        print(f"[OK] حاکمیت شرکتی: ۴۳ ماده، {governance_versions} نسخه، ۵ تاریخی")
        print(f"[TOTAL] اسناد: {totals['docs']} | مواد/نسخه‌ها: {totals['versions']} | "
              f"جاری: {totals['current_rows']} | تاریخی: {totals['historical']} | "
              f"روابط: {totals['relations']}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
