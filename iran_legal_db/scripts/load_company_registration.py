# -*- coding: utf-8 -*-
"""Load the company-registration law and its principal regulations.

The loader is idempotent: package documents are upserted, package articles,
FTS rows, tags/topics and incoming/outgoing relations are rebuilt in one
transaction.
"""
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
from company_registration import (
    REGISTRATION_LAW_ORIGINAL,
    REGISTRATION_LAW_ART10_CONSOLIDATED,
    REGISTRATION_LAW_PENALTIES_1403,
    REGISTRATION_EXECUTIVE_REGULATION,
    TRADE_CODE_REGISTRATION_BYLAW,
    FOREIGN_BRANCH_LAW,
    FOREIGN_BRANCH_BYLAW,
    REGISTRY_ADMIN_REGULATION_1386,
    DIVAN_COMPANY_CONVERSION_RULING,
)

REF_LAW = "QRS-1310"
REF_EXEC = "NRS-1310"
REF_TRADE = "NM196-1311"
REF_FOREIGN = "QSF-1376"
REF_FOREIGN_BYLAW = "AINSF-1378"
REF_ADMIN = "EAIN-1386"
REF_DIVAN = "DHA-2167-1400"
PACKAGE_REFS = (
    REF_LAW, REF_EXEC, REF_TRADE, REF_FOREIGN,
    REF_FOREIGN_BYLAW, REF_ADMIN, REF_DIVAN,
)

D_LAW = "1931-05-24"       # 1310/03/02
D_EXEC = "1931-06-09"      # 1310/03/18
D_ART28 = "1931-09-15"     # 1310/06/23
D_ART34 = "1931-09-01"     # 1310/06/09
D_ART28B = "1932-01-24"    # 1310/11/04
D_ART35 = "1934-07-11"     # 1313/04/20
D_REPEAL_3132 = "1940-05-23"  # 1319/03/02
D_ART10 = "1995-03-19"     # 1373/12/28 consolidated tariff version
D_FINE = "2024-06-19"      # 1403/03/30
D_TRADE = "1932"           # source identifies the approval year only
D_TRADE_10 = "2020-10-21"  # 1399/07/30
D_FOREIGN = "1997-11-12"   # 1376/08/21
D_FOREIGN_BYLAW = "1999-03-31"  # 1378/01/11
D_ADMIN = "2007-05-14"     # 1386/02/24
D_ART36 = "2019-10-07"     # approval record 1398/07/15
D_DIVAN = "2021-10-19"     # 1400/07/27

SRC_LAW = (
    "قانون راجع به ثبت شرکت‌ها مصوب ۱۳۱۰/۰۳/۰۲؛ متن با نسخه‌های تلفیقی شناسنامه قانون، "
    "اختبار و منابع رسمی/تنقیحی مقابله شده است."
)
SRC_EXEC = (
    "نظامنامه اجرای قانون ثبت شرکت‌ها؛ متن جاری و سوابق نسخ با پایگاه نظامات "
    "https://nezamat.ir/post-202/ و شناسنامه قانون مقابله شده است."
)
SRC_TRADE = (
    "نظام‌نامه راجع به مواد ۱۹۶، ۱۹۷ و ۱۹۹ قانون تجارت؛ "
    "https://shenasname.ir/sabt/7456-نظام-نامه-ثبت-شرکتها"
)
SRC_FOREIGN = (
    "قانون اجازه ثبت شعبه یا نمایندگی شرکت‌های خارجی مصوب ۱۳۷۶/۰۸/۲۱؛ "
    "https://davoudabadi.ir/page/1256074/"
)
SRC_FOREIGN_BYLAW = (
    "آیین‌نامه اجرایی قانون اجازه ثبت شعبه یا نمایندگی شرکت‌های خارجی مصوب ۱۳۷۸/۰۱/۱۱؛ "
    "https://davoudabadi.ir/page/9067582/"
)
SRC_ADMIN = (
    "اصلاحیه طرح اصلاحی آیین‌نامه ثبت شرکت‌ها مصوب ۱۳۴۰، مصوب ۱۳۸۶/۰۲/۲۴ رئیس قوه قضائیه؛ "
    "متن روزنامه رسمی در گردآوری حقوقی مقابله شده است."
)
SRC_DIVAN = (
    "متن رأی شماره ۲۱۶۷ تا ۲۱۷۰ مورخ ۱۴۰۰/۰۷/۲۷ هیأت عمومی دیوان عدالت اداری؛ "
    "https://nezamat.ir/post-42580/"
)


def pn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def lookup_id(conn, table: str, column: str, value: str):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def upsert_document(conn, *, reference_code, title, short_title, type_code,
                    authority, status_code, ratification_date,
                    effective_date=None, publication_date=None,
                    official_newspaper_no=None, notes=None):
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
    # get_or_create_document also creates a missing authority; look it up after it.
    authority_id = lookup_id(conn, "authorities", "name_fa", authority)
    conn.execute(
        """UPDATE documents
           SET title=?, short_title=?, type_id=?, issuing_authority_id=?, status_id=?,
               ratification_date=?, publication_date=?, effective_date=?,
               official_newspaper_no=?, notes=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (title, short_title, lookup_id(conn, "document_types", "code", type_code),
         authority_id, lookup_id(conn, "statuses", "code", status_code),
         ratification_date, publication_date, effective_date or ratification_date,
         official_newspaper_no, notes, did),
    )
    return did


def clear_package(conn, document_ids):
    marks = ",".join("?" for _ in document_ids)
    # Rebuild package-owned links while preserving incoming links created by
    # later packages.  The only external incoming links owned here are those
    # from the already-existing 1403 penalty-adjustment instrument.
    conn.execute(
        f"DELETE FROM relations WHERE from_document_id IN ({marks})",
        tuple(document_ids),
    )
    fine = conn.execute(
        "SELECT id FROM documents WHERE reference_code='TMJN-1403'"
    ).fetchone()
    if fine:
        conn.execute(
            f"DELETE FROM relations WHERE from_document_id=? AND to_document_id IN ({marks})",
            (fine["id"], *document_ids),
        )
    for did in document_ids:
        conn.execute("DELETE FROM articles_fts WHERE document_id=?", (did,))
        conn.execute("DELETE FROM articles WHERE document_id=?", (did,))
        conn.execute("DELETE FROM document_tags WHERE document_id=?", (did,))
        conn.execute("DELETE FROM document_topics WHERE document_id=?", (did,))


def decorate(conn, did, tags, topics=("حقوق تجارت", "حقوق ثبت اسناد و املاک")):
    for topic in topics:
        link_document_topic(conn, did, topic)
    for tag in tags:
        link_document_tag(conn, did, add_tag(conn, tag))


def add_rows(conn, did, ref, rows, date, source, *, special_dates=None):
    ids = {}
    for key, text in rows:
        article_no = "۲۸ مکرر" if key == "28bis" else pn(key)
        effective = (special_dates or {}).get(key, date)
        aid = add_article(
            conn, did, article_no=article_no, article_key=f"{ref}:{key}",
            version_no=1, is_current=1, effective_date=effective,
            text=text, source_note=source,
        )
        ids[key] = aid
    return ids


def add_company_law(conn, did):
    original = dict(REGISTRATION_LAW_ORIGINAL)
    ids = {}
    historical = {}
    total = 0
    for n in range(1, 13):
        if n in REGISTRATION_LAW_PENALTIES_1403:
            stages = [
                (D_LAW, original[n], "متن مصوب ۱۳۱۰", D_FINE, 0),
                (D_FINE, REGISTRATION_LAW_PENALTIES_1403[n],
                 "نسخه جاری با مبالغ تعدیل‌شده ۱۴۰۳", None, 1),
            ]
        elif n == 10:
            stages = [
                (D_LAW, original[n], "تعرفه مصوب ۱۳۱۰", D_ART10, 0),
                (D_ART10, REGISTRATION_LAW_ART10_CONSOLIDATED,
                 "متن تلفیقی پس از اصلاحات ۱۳۴۶، ۱۳۵۲، ۱۳۶۲ و ۱۳۷۳", None, 1),
            ]
        else:
            stages = [(D_LAW, original[n], "متن مصوب ۱۳۱۰", None, 1)]
        for version, (effective, text, note, expiry, current) in enumerate(stages, 1):
            source = SRC_LAW
            if n in REGISTRATION_LAW_PENALTIES_1403 and version == 2:
                source += " تعدیل جزای نقدی: تصویب‌نامه ۱۴۰۳/۰۳/۳۰ هیئت وزیران."
            aid = add_article(
                conn, did, article_no=pn(n), article_key=f"{REF_LAW}:{n}",
                version_no=version, is_current=current,
                effective_date=effective, expiry_date=expiry, text=text,
                source_note=source, notes=note,
            )
            total += 1
            (ids if current else historical)[n] = aid
    return ids, historical, total


def add_executive_regulation(conn, did):
    data = dict(REGISTRATION_EXECUTIVE_REGULATION)
    order = list(range(1, 29)) + ["28bis"] + list(range(29, 37))
    special_dates = {28: D_ART28, "28bis": D_ART28B, 34: D_ART34,
                     35: D_ART35, 36: D_ART36}
    ids = {}
    historical = {}
    for key in order:
        current = 0 if key in (31, 32, 36) else 1
        expiry = D_REPEAL_3132 if key in (31, 32) else (D_DIVAN if key == 36 else None)
        note = None
        if key in (31, 32):
            note = "ملغی به موجب ماده ۱۹ آیین‌نامه مترجمان رسمی مصوب ۱۳۱۹/۰۳/۰۲"
        elif key == 36:
            note = "ابطال به موجب رأی ۲۱۶۷ تا ۲۱۷۰ هیأت عمومی دیوان عدالت اداری"
        aid = add_article(
            conn, did,
            article_no=("۲۸ مکرر" if key == "28bis" else pn(key)),
            article_key=f"{REF_EXEC}:{key}", version_no=1,
            is_current=current, effective_date=special_dates.get(key, D_EXEC),
            expiry_date=expiry, text=data[key], source_note=SRC_EXEC, notes=note,
        )
        (ids if current else historical)[key] = aid
    return ids, historical


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        docs = {}
        docs[REF_LAW] = upsert_document(
            conn, reference_code=REF_LAW,
            title="قانون راجع به ثبت شرکت‌ها (مصوب ۱۳۱۰، با اصلاحات و تعدیل مبالغ ۱۴۰۳)",
            short_title="ق.ث.ش.", type_code="law",
            authority="مجلس شورای ملی (پیش از انقلاب)", status_code="amended",
            ratification_date=D_LAW, effective_date="1931-06-06",
            notes=("۱۲ ماده؛ تاریخچه ماده ۱۰ و نسخه‌های پیش و پس از تعدیل جزای نقدی مواد ۲، ۵ و ۶. "
                   "مبالغ خدمات ثبتی در عمل ممکن است تابع قوانین درآمدی و تعرفه‌های بعدی نیز باشد."),
        )
        docs[REF_EXEC] = upsert_document(
            conn, reference_code=REF_EXEC,
            title="نظامنامه اجرای قانون ثبت شرکت‌ها (مصوب ۱۳۱۰، با الحاقات و وضعیت تنقیحی)",
            short_title="نظامنامه ثبت شرکت‌ها", type_code="regulation",
            authority="وزارت دادگستری", status_code="amended",
            ratification_date=D_EXEC, effective_date=D_EXEC,
            notes=("مواد ۱ تا ۳۶ همراه ماده ۲۸ مکرر؛ مواد ۳۱ و ۳۲ ملغی و ماده ۳۶ به موجب رأی "
                   "هیأت عمومی دیوان عدالت اداری ابطال شده است."),
        )
        docs[REF_TRADE] = upsert_document(
            conn, reference_code=REF_TRADE,
            title="نظام‌نامه راجع به مواد ۱۹۶، ۱۹۷ و ۱۹۹ قانون تجارت (با ماده ۱۰ الحاقی ۱۳۹۹)",
            short_title="نظامنامه ثبت شرکت‌های تجاری", type_code="regulation",
            authority="وزارت دادگستری", status_code="amended",
            ratification_date=D_TRADE, effective_date=D_TRADE,
            notes="۱۰ ماده؛ ماده ۱۰ درباره تبدیل شرکت‌های تجاری در سال ۱۳۹۹ الحاق شده است.",
        )
        docs[REF_FOREIGN] = upsert_document(
            conn, reference_code=REF_FOREIGN,
            title="قانون اجازه ثبت شعبه یا نمایندگی شرکت‌های خارجی",
            short_title="قانون شعب شرکت‌های خارجی", type_code="law",
            authority="مجلس شورای اسلامی", status_code="in_force",
            ratification_date=D_FOREIGN, effective_date=D_FOREIGN,
            notes="ماده‌واحده و یک تبصره؛ ثبت مشروط به عمل متقابل و فعالیت در زمینه‌های تعیین‌شده دولت.",
        )
        docs[REF_FOREIGN_BYLAW] = upsert_document(
            conn, reference_code=REF_FOREIGN_BYLAW,
            title="آیین‌نامه اجرایی قانون اجازه ثبت شعبه یا نمایندگی شرکت‌های خارجی",
            short_title="آیین‌نامه شعب خارجی", type_code="regulation",
            authority="هیئت وزیران", status_code="in_force",
            ratification_date=D_FOREIGN_BYLAW, effective_date=D_FOREIGN_BYLAW,
            official_newspaper_no="۹۳۰/ت۱۹۷۷۶هـ",
            notes="متن کامل ۱۰ ماده درباره زمینه فعالیت، مدارک، مسئولیت، حسابرسی و اداره شعبه یا نمایندگی.",
        )
        docs[REF_ADMIN] = upsert_document(
            conn, reference_code=REF_ADMIN,
            title="اصلاحیه طرح اصلاحی آیین‌نامه ثبت شرکت‌ها مصوب ۱۳۴۰",
            short_title="آیین‌نامه تشکیلات ثبت شرکت‌ها", type_code="regulation",
            authority="رئیس قوه قضائیه", status_code="in_force",
            ratification_date=D_ADMIN, effective_date=D_ADMIN,
            official_newspaper_no="۱۹۴۲/۸۶/۱",
            notes="۱۰ ماده و ۳ تبصره درباره ساختار و وظایف اداره کل ثبت شرکت‌ها و اداره کل مالکیت صنعتی.",
        )
        docs[REF_DIVAN] = upsert_document(
            conn, reference_code=REF_DIVAN,
            title="رأی شماره ۲۱۶۷ تا ۲۱۷۰ هیأت عمومی دیوان عدالت اداری درباره ثبت تبدیل شرکت‌های تجاری",
            short_title="رأی ۲۱۶۷ تا ۲۱۷۰", type_code="divan_ruling",
            authority="دیوان عدالت اداری", status_code="in_force",
            ratification_date=D_DIVAN, effective_date=D_DIVAN,
            official_newspaper_no="۲۱۶۷ تا ۲۱۷۰",
            notes="ابطال تصویب‌نامه هیئت وزیران و دستورالعمل معاون حقوقی رئیس‌جمهور به علت خروج از صلاحیت.",
        )

        clear_package(conn, list(docs.values()))

        decorate(conn, docs[REF_LAW], ["ثبت شرکت", "شرکت ایرانی", "شرکت خارجی", "حق‌الثبت", "قانون مادر"])
        decorate(conn, docs[REF_EXEC], ["ثبت شرکت", "اظهارنامه", "نماینده شرکت خارجی", "شعبه", "بیلان"])
        decorate(conn, docs[REF_TRADE], ["ثبت شرکت تجاری", "شرکتنامه", "انتشار آگهی", "تبدیل شرکت"])
        decorate(conn, docs[REF_FOREIGN], ["شرکت خارجی", "شعبه خارجی", "نمایندگی خارجی", "عمل متقابل"])
        decorate(conn, docs[REF_FOREIGN_BYLAW], ["شرکت خارجی", "شعبه خارجی", "نمایندگی خارجی", "حسابرسی"])
        decorate(conn, docs[REF_ADMIN], ["اداره ثبت شرکت‌ها", "مالکیت صنعتی", "مرجع ثبت"])
        decorate(conn, docs[REF_DIVAN], ["تبدیل شرکت", "ابطال مصوبه", "صلاحیت رئیس قوه قضائیه"],
                 topics=("حقوق تجارت", "حقوق اداری"))

        law_ids, law_old, law_versions = add_company_law(conn, docs[REF_LAW])
        exec_ids, exec_old = add_executive_regulation(conn, docs[REF_EXEC])
        trade_ids = add_rows(
            conn, docs[REF_TRADE], REF_TRADE, TRADE_CODE_REGISTRATION_BYLAW,
            D_TRADE, SRC_TRADE, special_dates={10: D_TRADE_10},
        )
        foreign_unit = add_article(
            conn, docs[REF_FOREIGN], article_no="واحده",
            article_key=f"{REF_FOREIGN}:MU", version_no=1, is_current=1,
            effective_date=D_FOREIGN, text=FOREIGN_BRANCH_LAW, source_note=SRC_FOREIGN,
        )
        foreign_bylaw_ids = add_rows(
            conn, docs[REF_FOREIGN_BYLAW], REF_FOREIGN_BYLAW,
            FOREIGN_BRANCH_BYLAW, D_FOREIGN_BYLAW, SRC_FOREIGN_BYLAW,
        )
        admin_ids = add_rows(
            conn, docs[REF_ADMIN], REF_ADMIN, REGISTRY_ADMIN_REGULATION_1386,
            D_ADMIN, SRC_ADMIN,
        )
        divan_aid = add_article(
            conn, docs[REF_DIVAN], article_no="رأی",
            article_key=f"{REF_DIVAN}:R", version_no=1, is_current=1,
            effective_date=D_DIVAN, text=DIVAN_COMPANY_CONVERSION_RULING,
            source_note=SRC_DIVAN,
        )

        # Core enabling relationships.
        add_relation(conn, docs[REF_EXEC], "implements", docs[REF_LAW],
                     from_article_id=exec_ids[1], to_article_id=law_ids[9],
                     description="نظامنامه اجرایی موضوع مواد ۸ و ۹ قانون ثبت شرکت‌ها.")
        add_relation(conn, docs[REF_EXEC], "implements", docs[REF_LAW],
                     from_article_id=exec_ids[30], to_article_id=law_ids[10],
                     description="ترتیب پرداخت حق‌الثبت هنگام تسلیم اظهارنامه.")
        add_relation(conn, docs[REF_EXEC], "implements", docs[REF_LAW],
                     from_article_id=exec_ids[3], to_article_id=law_ids[3],
                     description="ثبت شرکت خارجی و شعب آن در ایران.")
        add_relation(conn, docs[REF_EXEC], "implements", docs[REF_LAW],
                     from_article_id=exec_ids[28], to_article_id=law_ids[8],
                     description="مقررات تاریخی قراردادهای شرکت‌های بیمه.")

        # The 1311 regulation implements the named Commercial Code provisions.
        qt = conn.execute("SELECT id FROM documents WHERE reference_code='QT-1311'").fetchone()
        if qt:
            qt_ids = {}
            for n in (20, 196, 197, 199):
                row = conn.execute(
                    "SELECT id FROM articles WHERE article_key=? AND is_current=1",
                    (f"QT-1311:{n}",),
                ).fetchone()
                if row:
                    qt_ids[n] = row["id"]
            add_relation(conn, docs[REF_TRADE], "implements", qt["id"],
                         description="نظامنامه اجرایی مواد ۱۹۶، ۱۹۷ و ۱۹۹ قانون تجارت.")
            for own, target, desc in (
                (4, 196, "مدارک لازم برای ثبت شرکت."),
                (6, 197, "انتشار خلاصه شرکتنامه و منضمات."),
                (8, 199, "انتشار و ثبت در محل شعب شرکت."),
                (10, 20, "تبدیل انواع شرکت‌های تجاری موضوع ماده ۲۰."),
            ):
                if target in qt_ids:
                    add_relation(conn, docs[REF_TRADE], "implements", qt["id"],
                                 from_article_id=trade_ids[own], to_article_id=qt_ids[target],
                                 description=desc)

        add_relation(conn, docs[REF_FOREIGN], "cites", docs[REF_LAW],
                     from_article_id=foreign_unit, to_article_id=law_ids[3],
                     description="قانون ۱۳۷۶ امکان و چارچوب جدید ثبت شعبه یا نمایندگی شرکت خارجی را تکمیل می‌کند.")
        add_relation(conn, docs[REF_FOREIGN_BYLAW], "implements", docs[REF_FOREIGN],
                     from_article_id=foreign_bylaw_ids[1], to_article_id=foreign_unit,
                     description="آیین‌نامه اجرایی تبصره ماده‌واحده قانون ۱۳۷۶.")
        add_relation(conn, docs[REF_ADMIN], "implements", docs[REF_LAW],
                     from_article_id=admin_ids[2], to_article_id=law_ids[9],
                     description="تعیین ساختار و وظایف مرجع ثبت شرکت‌ها.")
        add_relation(conn, docs[REF_ADMIN], "cites", docs[REF_FOREIGN],
                     from_article_id=admin_ids[2], to_article_id=foreign_unit,
                     description="وظیفه ثبت شعبه یا نمایندگی شرکت‌های خارجی.")
        add_relation(conn, docs[REF_ADMIN], "cites", docs[REF_FOREIGN_BYLAW],
                     from_article_id=admin_ids[2], to_article_id=foreign_bylaw_ids[1],
                     description="ساختار اداری اجرای مقررات شعب و نمایندگی خارجی.")

        # Annulment of executive article 36 and the related conversion instrument.
        add_relation(conn, docs[REF_DIVAN], "overrules", docs[REF_EXEC],
                     from_article_id=divan_aid, to_article_id=exec_old[36],
                     description="ابطال مقرره تبدیل شرکت‌ها به علت خروج مرجع تصویب از حدود صلاحیت.")
        add_relation(conn, docs[REF_DIVAN], "interprets", docs[REF_LAW],
                     from_article_id=divan_aid, to_article_id=law_ids[9],
                     description="تفسیر صلاحیت وضع نظامنامه‌های موضوع ماده ۹ قانون ثبت شرکت‌ها.")

        # Reuse the already-loaded general 1403 penalty-adjustment instrument.
        fine_doc = conn.execute(
            "SELECT id FROM documents WHERE reference_code='TMJN-1403'"
        ).fetchone()
        if fine_doc:
            fine_art = conn.execute(
                "SELECT id FROM articles WHERE document_id=? AND is_current=1 ORDER BY id LIMIT 1",
                (fine_doc["id"],),
            ).fetchone()
            add_relation(conn, fine_doc["id"], "amends", docs[REF_LAW],
                         from_article_id=(fine_art["id"] if fine_art else None),
                         description="تعدیل مبالغ جزای نقدی مواد ۲، ۵ و ۶ قانون ثبت شرکت‌ها در ۱۴۰۳.")
            for n in (2, 5, 6):
                add_relation(conn, fine_doc["id"], "amends", docs[REF_LAW],
                             from_article_id=(fine_art["id"] if fine_art else None),
                             to_article_id=law_ids[n],
                             description=f"نسخه جاری مبلغ جزای نقدی ماده {pn(n)}.")
            conn.execute(
                """UPDATE documents SET notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                ("مبالغ جزای نقدی قوانین مختلف، از جمله قانون تجارت، لایحه اصلاحی ۱۳۴۷ "
                 "و مواد ۲، ۵ و ۶ قانون ثبت شرکت‌ها را به‌روز کرده است.", fine_doc["id"]),
            )

        conn.commit()
        totals = conn.execute(
            """SELECT (SELECT COUNT(*) FROM documents) docs,
                      (SELECT COUNT(*) FROM articles) versions,
                      (SELECT COUNT(*) FROM articles WHERE is_current=1) current_rows,
                      (SELECT COUNT(*) FROM articles WHERE is_current=0) historical,
                      (SELECT COUNT(*) FROM relations) relations"""
        ).fetchone()
        print(f"[OK] قانون ثبت شرکت‌ها: ۱۲ شماره ماده، {law_versions} نسخه، ۱۲ ماده جاری")
        print("[OK] نظامنامه اجرا: ۳۷ مفاد/ردیف، ۳۴ جاری، ۳ تاریخی")
        print("[OK] نظامنامه مواد ۱۹۶/۱۹۷/۱۹۹: ۱۰ | قانون شعب خارجی: ۱ | آیین‌نامه: ۱۰")
        print("[OK] آیین‌نامه تشکیلات ثبت: ۱۰ | رأی دیوان عدالت اداری: ۱")
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
