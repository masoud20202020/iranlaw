# -*- coding: utf-8 -*-
"""Load the complete direct-tax law, its 1394 amendment and core implementing rules."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, 'data', 'seed')]
from schema import get_connection
from importer import *
from direct_tax import *

Q = 'QMMAL-1366'
E = 'EQMMAL-1394'
B95 = 'AIM95-1394'
B219 = 'AIM219-1398'
B187 = 'AIM187-1396'
I251 = 'DI251M-1401'
REFS = (Q, E, B95, B219, B187, I251)
SRC_Q = 'قانون مالیات‌های مستقیم مصوب ۱۳۶۶/۱۲/۰۳؛ متن تنقیحی جاری با اصلاحات ۱۴۰۴ و تطبیق نصاب‌های تعدیل‌شده ۱۴۰۱؛ منابع در data/source_cache.'
SRC_E = 'قانون اصلاح قانون مالیات‌های مستقیم مصوب ۱۳۹۴/۰۴/۳۱؛ متن کامل ۶۰ بند از شناسنامه قانون.'
SRC_95 = 'آیین‌نامه اجرایی ماده ۹۵ اصلاحی قانون مالیات‌های مستقیم؛ متن کامل ۱۷ ماده، با اعمال گروه‌بندی اصلاحی مؤدیان.'
SRC_219 = 'آیین‌نامه اجرایی موضوع ماده ۲۱۹ قانون مالیات‌های مستقیم مصوب ۱۳۹۸؛ متن تلفیقی ۵۱ ماده از نسخه داودآبادی.'
SRC_187 = 'آیین‌نامه اجرایی تبصره ۴ ماده ۱۸۷ قانون مالیات‌های مستقیم مصوب ۱۳۹۶؛ متن کامل ۱۴ ماده؛ پس از نسخ ماده ۱۸۷ صرفاً تاریخی.'
SRC_251 = 'دستورالعمل اجرایی موضوع ماده ۲۵۱ مکرر، شماره ۲۱۳۷۰۳ مورخ ۱۴۰۱/۱۰/۱۴؛ متن کامل ۴۰ ماده.'


def pn(x):
    return str(x).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))


def gi(c, table, column, value):
    row = c.execute(f'SELECT id FROM {table} WHERE {column}=?', (value,)).fetchone()
    return row['id'] if row else None


def up(c, ref, title, short, typ, authority, authority_type, status, ratification, effective, notes):
    row = c.execute('SELECT id FROM documents WHERE reference_code=?', (ref,)).fetchone()
    did = row['id'] if row else get_or_create_document(
        c, title=title, short_title=short, type_code=typ, issuing_authority=authority,
        status_code=status, ratification_date=ratification, effective_date=effective,
        reference_code=ref, notes=notes,
    )
    aid = gi(c, 'authorities', 'name_fa', authority)
    if aid is None:
        aid = c.execute('INSERT INTO authorities(name_fa,authority_type) VALUES(?,?)', (authority, authority_type)).lastrowid
    c.execute(
        '''UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,
           ratification_date=?,effective_date=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?''',
        (title, short, gi(c, 'document_types', 'code', typ), aid, gi(c, 'statuses', 'code', status),
         ratification, effective, notes, did),
    )
    return did


def clear(c, did):
    # Incoming document-level relations (notably QMS-1404 -> QMMAL-1366) deliberately survive.
    c.execute('DELETE FROM relations WHERE from_document_id=?', (did,))
    c.execute('DELETE FROM articles_fts WHERE document_id=?', (did,))
    c.execute('DELETE FROM articles WHERE document_id=?', (did,))
    c.execute('DELETE FROM document_tags WHERE document_id=?', (did,))
    c.execute('DELETE FROM document_topics WHERE document_id=?', (did,))


def decorate(c, did, tags, topics=('حقوق مالیاتی', 'حقوق تجارت')):
    for topic in topics:
        link_document_topic(c, did, topic)
    for tag in tags:
        link_document_tag(c, did, add_tag(c, tag))


def add_rows(c, did, ref, data, effective, source, current=True, expiry=None):
    ids = {}
    for key, text in data:
        ids[key] = add_article(
            c, did, article_no=pn(key), article_key=f'{ref}:{key}', version_no=1,
            is_current=int(current), effective_date=effective,
            expiry_date=expiry if not current else None, text=text, source_note=source,
        )
    return ids


def main():
    c = get_connection()
    try:
        c.execute('BEGIN')
        docs = {}
        specs = (
            (Q, 'قانون مالیات‌های مستقیم با اصلاحات و الحاقات تا ۱۴۰۴', 'قانون مالیات‌های مستقیم', 'law',
             'مجلس شورای اسلامی', 'legislative', 'amended', '1988-02-22', '1988-02-22',
             'پوشش کامل ۲۹۰ کلید ساختاری شامل مواد ۱ تا ۲۸۲ و هشت ماده مکرر؛ متن جاری ۲۳۰ ماده/مفاد و تاریخچه مواد منسوخ و مهم کسب‌وکار.'),
            (E, 'قانون اصلاح قانون مالیات‌های مستقیم مصوب ۱۳۹۴', 'اصلاحیه مالیات‌های مستقیم ۱۳۹۴', 'amendment',
             'مجلس شورای اسلامی', 'legislative', 'in_force', '2015-07-22', '2016-03-20',
             'متن کامل ۶۰ بند ماده‌واحده؛ اصلاح ساختار مالیات بر ارث، مشاغل، اشخاص حقوقی، اطلاعات مالیاتی، رسیدگی و جرائم.'),
            (B95, 'آیین‌نامه اجرایی ماده ۹۵ اصلاحی قانون مالیات‌های مستقیم', 'آیین‌نامه ماده ۹۵', 'regulation',
             'وزیر امور اقتصادی و دارایی', 'executive', 'amended', '2016-02-23', '2016-03-20',
             'متن کامل ۱۷ ماده درباره گروه‌بندی مؤدیان، دفاتر، اسناد، اظهارنامه و صورتحساب؛ گروه‌بندی اصلاحی در ماده ۲ اعمال شده است.'),
            (B219, 'آیین‌نامه اجرایی موضوع ماده ۲۱۹ قانون مالیات‌های مستقیم', 'آیین‌نامه ماده ۲۱۹', 'regulation',
             'وزیر امور اقتصادی و دارایی', 'executive', 'amended', '2019-11-30', '2019-11-30',
             'متن تلفیقی ۵۱ ماده درباره ساختار سازمانی، حسابرسی، اعتراض، دادرسی، وصول و خدمات مؤدیان.'),
            (B187, 'آیین‌نامه اجرایی تبصره ۴ ماده ۱۸۷ قانون مالیات‌های مستقیم (منسوخ تبعی)', 'آیین‌نامه ماده ۱۸۷', 'regulation',
             'رئیس قوه قضائیه', 'judicial', 'abrogated', '2018-01-07', '2018-01-07',
             'متن کامل ۱۴ ماده؛ با نسخ ماده ۱۸۷ از ۱۴۰۳/۰۴/۰۲، صرفاً برای تاریخچه معاملات و گواهی‌های مالیاتی پیشین نگهداری می‌شود.'),
            (I251, 'دستورالعمل اجرایی موضوع ماده ۲۵۱ مکرر قانون مالیات‌های مستقیم', 'دستورالعمل ماده ۲۵۱ مکرر', 'directive',
             'وزیر امور اقتصادی و دارایی', 'executive', 'in_force', '2023-01-04', '2023-01-04',
             'متن کامل ۴۰ ماده دستورالعمل شماره ۲۱۳۷۰۳ درباره سامانه دادما، رسیدگی هیأت سه‌نفره و مرکز عالی دادخواهی مالیاتی.'),
        )
        for ref, title, short, typ, authority, atype, status, rat, eff, note in specs:
            docs[ref] = up(c, ref, title, short, typ, authority, atype, status, rat, eff, note)
        for did in docs.values():
            clear(c, did)

        decorate(c, docs[Q], ('مالیات‌های مستقیم', 'مالیات بر درآمد', 'مالیات بر عایدی سرمایه', 'مالیات بر ارث',
                              'مالیات مشاغل', 'اشخاص حقوقی', 'هزینه قابل قبول', 'دادرسی مالیاتی', 'حق تمبر'))
        decorate(c, docs[E], ('اصلاحیه ۱۳۹۴', 'نرخ صفر', 'اظهارنامه مالیاتی', 'جرائم مالیاتی'))
        decorate(c, docs[B95], ('دفاتر قانونی', 'گروه‌بندی مؤدیان', 'صورتحساب', 'اظهارنامه'))
        decorate(c, docs[B219], ('حسابرسی مالیاتی', 'اظهارنامه برآوردی', 'حل اختلاف مالیاتی', 'وصول مالیات'))
        decorate(c, docs[B187], ('گواهی مالیاتی ملک', 'دفاتر اسناد رسمی', 'مقرره منسوخ'), ('حقوق مالیاتی', 'حقوق ثبت اسناد و املاک'))
        decorate(c, docs[I251], ('ماده ۲۵۱ مکرر', 'دادخواهی مالیاتی', 'سامانه دادما', 'هیأت سه نفره'), ('حقوق مالیاتی', 'حقوق اداری'))

        qids = {}
        qcurrent = {}
        for row in DIRECT_TAX_ROWS:
            aid = add_article(
                c, docs[Q], article_no=row['article_no'], article_key=f"{Q}:{row['key']}",
                version_no=row['version_no'], is_current=int(row['is_current']),
                effective_date=row['effective_date'], expiry_date=row['expiry_date'],
                text=row['text'], source_note=row['source_note'], notes=row['notes'],
            )
            qids[(row['key'], row['version_no'])] = aid
            if row['is_current']:
                qcurrent[row['key']] = aid

        eids = add_rows(c, docs[E], E, DIRECT_TAX_AMENDMENT_1394, '2016-03-20', SRC_E)
        b95ids = add_rows(c, docs[B95], B95, DIRECT_TAX_BYLAW_95, '2016-03-20', SRC_95)
        b219ids = add_rows(c, docs[B219], B219, DIRECT_TAX_BYLAW_219, '2019-11-30', SRC_219)
        b187ids = add_rows(c, docs[B187], B187, DIRECT_TAX_BYLAW_187, '2018-01-07', SRC_187, current=False, expiry='2024-06-22')
        i251ids = add_rows(c, docs[I251], I251, DIRECT_TAX_INSTRUCTION_251BIS, '2023-01-04', SRC_251)

        # Material links from the 1394 amending act to the consolidated law.
        links = (
            ('16', '84', 'تعیین سالانه معافیت مالیات بر درآمد حقوق.'),
            ('21', '95', 'جایگزینی تکالیف دفاتر، اسناد و اظهارنامه صاحبان مشاغل.'),
            ('23', '100', 'اصلاح موعد اظهارنامه و مالیات مقطوع مشاغل کوچک.'),
            ('24', '101', 'اعمال یک معافیت برای چند واحد شغلی.'),
            ('25', '105', 'الحاق تخفیف افزایش درآمد ابرازی اشخاص حقوقی.'),
            ('30', '131', 'جایگزینی نرخ‌های پلکانی درآمد اشخاص حقیقی.'),
            ('37', '147', 'الحاق تبصره‌های هزینه قابل قبول.'),
            ('38', '148', 'اصلاح هزینه‌های استخدامی، مالی و خدمات پس از فروش.'),
            ('41', '169', 'جایگزینی تکالیف شماره اقتصادی و فهرست معاملات.'),
            ('42', '169bis', 'جایگزینی پایگاه اطلاعات هویتی، عملکردی و دارایی.'),
            ('45', '186', 'الحاق تبصره‌های گواهی مالیاتی مجوزها و تسهیلات.'),
            ('53', '219', 'الحاق تبصره‌های طرح جامع مالیاتی و واگذاری خدمات.'),
            ('60', '274', 'الحاق فصل جرائم مالیاتی و مواد پایانی قانون.'),
        )
        for ek, qk, desc in links:
            add_relation(c, docs[E], 'amends', docs[Q], from_article_id=eids[ek], to_article_id=qcurrent[qk], description=desc)
        # Article 187 no longer has a current row; version 2 is its last substantive text.
        add_relation(c, docs[E], 'amends', docs[Q], from_article_id=eids['46'], to_article_id=qids[('187', 2)], description='الحاق تبصره‌های ۳ و ۴ به ماده ۱۸۷؛ این ماده از ۱۴۰۳ منسوخ است.')

        add_relation(c, docs[B95], 'implements', docs[Q], from_article_id=b95ids['1'], to_article_id=qcurrent['95'], description='نوع دفاتر، اسناد، گروه‌بندی مؤدیان و نحوه ارائه اظهارنامه.')
        add_relation(c, docs[B219], 'implements', docs[Q], from_article_id=b219ids['1'], to_article_id=qcurrent['219'], description='ساختار و رویه‌های شناسایی، حسابرسی، مطالبه، اعتراض و وصول.')
        add_relation(c, docs[B187], 'implements', docs[Q], from_article_id=b187ids['1'], to_article_id=qids[('187', 2)], description='اجرای تبصره ۴ ماده ۱۸۷ در دوره اعتبار آن تا ۱۴۰۳/۰۴/۰۲.')
        add_relation(c, docs[I251], 'implements', docs[Q], from_article_id=i251ids['1'], to_article_id=qcurrent['251bis'], description='ثبت و رسیدگی شکایت ناعادلانه بودن مالیات قطعی در سامانه دادما و هیأت سه‌نفره.')

        c.commit()
        total = c.execute('''SELECT (SELECT COUNT(*) FROM documents)d,(SELECT COUNT(*) FROM articles)a,
            (SELECT COUNT(*) FROM articles WHERE is_current=1)c,(SELECT COUNT(*) FROM articles WHERE is_current=0)h,
            (SELECT COUNT(*) FROM relations)r''').fetchone()
        qc = c.execute('SELECT COUNT(*) n, COALESCE(SUM(is_current),0) c FROM articles WHERE document_id=?', (docs[Q],)).fetchone()
        print(f"[OK] قانون مالیات‌های مستقیم: ۲۹۰ کلید | {qc['n']} ردیف | {qc['c']} جاری")
        print('[OK] اصلاحیه ۱۳۹۴=۶۰ بند | آیین‌نامه‌ها=۱۷+۵۱+۱۴ | دستورالعمل ۲۵۱ مکرر=۴۰')
        print(f"[TOTAL] اسناد: {total['d']} | مواد/نسخه‌ها: {total['a']} | جاری: {total['c']} | تاریخی: {total['h']} | روابط: {total['r']}")
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


if __name__ == '__main__':
    main()
