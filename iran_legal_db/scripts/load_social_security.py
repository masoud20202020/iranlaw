# -*- coding: utf-8 -*-
"""Load the Social Security Law, 1403 invalid-provisions law and retirement reform."""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(SCRIPT_DIR)
sys.path[:0] = [SCRIPT_DIR, os.path.join(ROOT, "data", "seed")]

from schema import get_connection
from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic
from social_security import *

REF_SS = "QTA-1354"
REF_INVALID = "FNAT-SS-1403"
REF_PROGRAM = "QPH7-1403-A29"
REF_BYLAW = "A29P7-1403"
REFS = (REF_SS, REF_INVALID, REF_PROGRAM, REF_BYLAW)

D1354 = "1975-06-24"
D1358_REORG = "1979-07-19"
D1358_TREATMENT = "1979-12-03"
D1361 = "1982-07-04"
D1368 = "1989-11-12"
D1400 = "2021-10-16"
D1403_PROGRAM = "2024-05-21"
D1403_PROGRAM_EFFECTIVE = "2024-07-24"
D1403_INVALID = "2024-10-23"
D1403_BYLAW = "2025-02-12"
D1403_BYLAW_EFFECTIVE = "2025-02-23"

SRC_SS = "قانون تأمین اجتماعی مصوب ۱۳۵۴/۰۴/۰۳؛ متن ۱۱۸ ماده‌ای با نسخه‌های تنقیحی اختبار، بیدبرگ و شناسنامه قانون مقابله شده است."
SRC_INVALID = "قانون فهرست قوانین و احکام نامعتبر در حوزه تأمین اجتماعی مصوب ۱۴۰۳/۰۸/۰۲ مجلس شورای اسلامی؛ پیوست کامل ۷۱ ردیفی."
SRC_PROGRAM = "ماده ۲۹ قانون برنامه پنج‌ساله هفتم پیشرفت جمهوری اسلامی ایران مصوب ۱۴۰۳؛ متن رسمی حکم افزایش سنوات الزامی بیمه‌پردازی."
SRC_BYLAW = "آیین‌نامه اجرایی ماده ۲۹ قانون برنامه هفتم؛ تصویب‌نامه شماره ۱۸۸۰۳۱/ت۶۳۴۳۴هـ مورخ ۱۴۰۳/۱۲/۰۵، مصوب جلسه ۱۴۰۳/۱۱/۲۴ هیئت وزیران."


def pn(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def get_id(conn, table, column, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {column}=?", (value,)).fetchone()
    return row["id"] if row else None


def upsert(conn, ref, title, short, type_code, authority, status, ratification, effective, notes, official=None):
    row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
    if row:
        did = row["id"]
    else:
        did = get_or_create_document(
            conn, title=title, short_title=short, type_code=type_code,
            issuing_authority=authority, status_code=status, ratification_date=ratification,
            effective_date=effective, official_newspaper_no=official, reference_code=ref, notes=notes,
        )
    authority_id = get_id(conn, "authorities", "name_fa", authority)
    if authority_id is None:
        authority_id = conn.execute(
            "INSERT INTO authorities(name_fa,authority_type) VALUES(?,?)",
            (authority, "legislative" if "مجلس" in authority else "executive"),
        ).lastrowid
    conn.execute(
        """UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,
           ratification_date=?,effective_date=?,official_newspaper_no=?,notes=?,updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (title, short, get_id(conn,"document_types","code",type_code), authority_id,
         get_id(conn,"statuses","code",status), ratification, effective, official, notes, did),
    )
    return did


def clear(conn, did):
    conn.execute("DELETE FROM relations WHERE from_document_id=?", (did,))
    conn.execute("DELETE FROM articles_fts WHERE document_id=?", (did,))
    conn.execute("DELETE FROM articles WHERE document_id=?", (did,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (did,))
    conn.execute("DELETE FROM document_topics WHERE document_id=?", (did,))


def decorate(conn, did, tags):
    link_document_topic(conn, did, "حقوق کار و تأمین اجتماعی")
    for tag in tags:
        link_document_tag(conn, did, add_tag(conn, tag))


def addv(conn, did, ref, n, text, version, current, effective, expiry, source, note):
    return add_article(
        conn, did, article_no=pn(n), article_key=f"{ref}:{n}", version_no=version,
        is_current=int(current), effective_date=effective, expiry_date=expiry,
        text=text, source_note=source, notes=note,
    )


def repeal_date(n):
    if n == 9 or n == 92:
        return D1368
    if n == 11:
        return D1358_TREATMENT
    if 12 <= n <= 17 or 19 <= n <= 27:
        return D1358_REORG
    if n == 18:
        return D1403_INVALID
    if n in (46, 98, 99, 100):
        return D1361
    if n == 86:
        return D1400
    raise ValueError(n)


def main():
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        docs = {
            REF_SS: upsert(
                conn, REF_SS,
                "قانون تأمین اجتماعی (متن تنقیحی با وضعیت نسخ ۱۴۰۳)",
                "قانون تأمین اجتماعی", "law", "مجلس شورای ملی (پیش از انقلاب)", "amended",
                D1354, D1354,
                "پوشش کامل شماره‌های ۱ تا ۱۱۸؛ ۹۴ ماده جاری و ۲۴ ماده منسوخ. پنج ماده ۴، ۵۸، ۷۶، ۸۱ و ۸۲ برای حذف اجزاء مصوب ۱۴۰۳ نسخه‌بندی شده‌اند. متن هر ماده، نسخه تلفیقی آخر پیش از نسخ یا متن جاری است؛ همه نسل‌های اصلاحات پیش از ۱۴۰۳ جداگانه materialize نشده‌اند.",
            ),
            REF_INVALID: upsert(
                conn, REF_INVALID,
                "قانون فهرست قوانین و احکام نامعتبر در حوزه تأمین اجتماعی",
                "فهرست احکام نامعتبر تأمین اجتماعی", "amendment", "مجلس شورای اسلامی", "in_force",
                D1403_INVALID, D1403_INVALID,
                "متن کامل ماده‌واحده و پیوست ۷۱ ردیفی؛ ردیف ۲۳ آثار نسخ بر قانون تأمین اجتماعی را مشخص می‌کند.",
            ),
            REF_PROGRAM: upsert(
                conn, REF_PROGRAM,
                "حکم بازنشستگی ماده ۲۹ قانون برنامه پنج‌ساله هفتم پیشرفت",
                "ماده ۲۹ برنامه هفتم", "law", "مجلس شورای اسلامی", "in_force",
                D1403_PROGRAM, D1403_PROGRAM_EFFECTIVE,
                "متن کامل ماده ۲۹ و شش تبصره درباره افزایش پلکانی سنوات الزامی بیمه‌پردازی؛ این حکم طبق تبصره ۲ اصلاح دائمی قوانین صندوق‌ها است.",
            ),
            REF_BYLAW: upsert(
                conn, REF_BYLAW,
                "آیین‌نامه اجرایی ماده ۲۹ قانون برنامه هفتم درباره سنوات الزامی بیمه‌پردازی برای بازنشستگی",
                "آیین‌نامه سنوات بازنشستگی", "regulation", "هیئت وزیران", "in_force",
                D1403_BYLAW, D1403_BYLAW_EFFECTIVE,
                "متن کامل هفت ماده؛ جدول افزایش سنوات، سقف سنی و سابقه، استثنای مشاغل سخت و شیوه بازنشستگی پیش از تکمیل سنوات.",
                official="۱۸۸۰۳۱/ت۶۳۴۳۴هـ",
            ),
        }
        for did in docs.values():
            clear(conn, did)

        decorate(conn, docs[REF_SS], ("تأمین اجتماعی", "حق بیمه", "بازنشستگی", "ازکارافتادگی", "مستمری", "بیمه‌شده", "کارفرما"))
        decorate(conn, docs[REF_INVALID], ("تنقیح قوانین", "احکام نامعتبر", "نسخ"))
        decorate(conn, docs[REF_PROGRAM], ("برنامه هفتم", "سنوات بیمه‌پردازی", "بازنشستگی"))
        decorate(conn, docs[REF_BYLAW], ("سنوات بازنشستگی", "صندوق بازنشستگی", "بیمه‌پرداز", "مشاغل سخت و زیان‌آور"))

        pre = dict(SOCIAL_SECURITY_INTEGRATED_PRE1403)
        current = dict(SOCIAL_SECURITY_CURRENT)
        partial_old = dict(SOCIAL_SECURITY_PARTIAL_PRE1403)
        whole = set(SOCIAL_SECURITY_WHOLE_REPEALED)
        partial = set(SOCIAL_SECURITY_PARTIAL_1403)
        current_ids = {}
        old_ids = {}
        row_count = 0
        for n in range(1, 119):
            if n in whole:
                aid = addv(conn, docs[REF_SS], REF_SS, n, pre[n], 1, False, D1354, repeal_date(n), SRC_SS,
                           "متن آخر پیش از نسخ؛ تاریخ پایان بر پایه قانون ناسخ یا اعلام تنقیحی ثبت شده است.")
                old_ids[n] = aid
                row_count += 1
            elif n in partial:
                old_ids[n] = addv(conn, docs[REF_SS], REF_SS, n, partial_old[n], 1, False, D1354, D1403_INVALID, SRC_SS,
                                  "نسخه تلفیقی پیش از حذف جزء یا بند به موجب ردیف ۲۳ فهرست احکام نامعتبر ۱۴۰۳.")
                current_ids[n] = addv(conn, docs[REF_SS], REF_SS, n, current[n], 2, True, D1403_INVALID, None, SRC_INVALID,
                                      "نسخه جاری پس از حذف جزء یا بند مندرج در ردیف ۲۳ پیوست قانون ۱۴۰۳.")
                row_count += 2
            else:
                current_ids[n] = addv(conn, docs[REF_SS], REF_SS, n, current[n], 1, True, D1354, None, SRC_SS,
                                      "متن تلفیقی جاری؛ تاریخچه تمام اصلاحات میانی به صورت نسل‌های جداگانه ثبت نشده است.")
                row_count += 1

        invalid_id = add_article(
            conn, docs[REF_INVALID], article_no="ماده‌واحده و پیوست",
            article_key=f"{REF_INVALID}:single", version_no=1, is_current=1,
            effective_date=D1403_INVALID, text=INVALID_SOCIAL_SECURITY_1403,
            source_note=SRC_INVALID, notes="رونوشت کامل ۷۱ ردیف؛ این سند خلاصه نیست.",
        )
        program_id = add_article(
            conn, docs[REF_PROGRAM], article_no="۲۹", article_key=f"{REF_PROGRAM}:29",
            version_no=1, is_current=1, effective_date=D1403_PROGRAM_EFFECTIVE,
            text=PROGRAM7_ARTICLE29, source_note=SRC_PROGRAM,
        )
        bylaw_ids = {}
        for n, text in RETIREMENT_YEARS_BYLAW:
            bylaw_ids[n] = add_article(
                conn, docs[REF_BYLAW], article_no=pn(n), article_key=f"{REF_BYLAW}:{n}",
                version_no=1, is_current=1, effective_date=D1403_BYLAW_EFFECTIVE,
                text=text, source_note=SRC_BYLAW,
            )

        # Roster in row 23: 19 complete provisions plus five partial repeals.
        row23_whole = {9, *range(12, 16), 17, 18, *range(19, 28), 98, 99, 100}
        for n in sorted(row23_whole | partial):
            add_relation(
                conn, docs[REF_INVALID], "abrogates", docs[REF_SS],
                from_article_id=invalid_id, to_article_id=old_ids[n],
                description=f"اثر ردیف ۲۳ پیوست بر ماده/جزء {pn(n)} قانون تأمین اجتماعی.",
            )

        add_relation(conn, docs[REF_PROGRAM], "amends", docs[REF_SS], from_article_id=program_id,
                     to_article_id=current_ids[76], description="اصلاح دائمی شرایط سنوات الزامی بازنشستگی در کنار ماده ۷۶ قانون تأمین اجتماعی.")
        add_relation(conn, docs[REF_BYLAW], "implements", docs[REF_PROGRAM], from_article_id=bylaw_ids[1],
                     to_article_id=program_id, description="آیین‌نامه اجرایی ماده ۲۹ برنامه هفتم.")
        add_relation(conn, docs[REF_BYLAW], "implements", docs[REF_SS], from_article_id=bylaw_ids[2],
                     to_article_id=current_ids[76], description="نحوه اعمال سنوات و سقف‌های بازنشستگی برای مشمولان قانون تأمین اجتماعی.")

        for ref, desc in (
            ("QK-1369", "تکلیف بیمه‌کردن کارگران موضوع ماده ۱۴۸ قانون کار."),
            ("QBB-1369", "بیمه بیکاری به عنوان یکی از حمایت‌های تأمین اجتماعی."),
            ("RVR-720-1390", "رأی وحدت رویه درباره صلاحیت سازمان در مطالبه حق بیمه ایام اشتغال."),
        ):
            target = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
            if target:
                add_relation(conn, docs[REF_SS], "cites", target["id"], description=desc)

        conn.commit()
        totals = conn.execute("""SELECT (SELECT COUNT(*) FROM documents)d,(SELECT COUNT(*) FROM articles)a,
          (SELECT COUNT(*) FROM articles WHERE is_current=1)c,(SELECT COUNT(*) FROM articles WHERE is_current=0)h,
          (SELECT COUNT(*) FROM relations)r""").fetchone()
        print(f"[OK] قانون تأمین اجتماعی: ۱۱۸ شماره، {row_count} نسخه، ۹۴ ماده جاری، ۲۹ ردیف تاریخی")
        print("[OK] فهرست نامعتبر ۱۴۰۳: ماده‌واحده + ۷۱ ردیف کامل | ماده ۲۹ برنامه هفتم: ۱ | آیین‌نامه: ۷")
        print(f"[TOTAL] اسناد: {totals['d']} | مواد/نسخه‌ها: {totals['a']} | جاری: {totals['c']} | تاریخی: {totals['h']} | روابط: {totals['r']}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
