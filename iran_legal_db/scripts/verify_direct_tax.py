# -*- coding: utf-8 -*-
"""Deep verifier for the direct-tax package."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, 'web')]
from schema import get_connection
from app import app

Q = 'QMMAL-1366'; E = 'EQMMAL-1394'; B95 = 'AIM95-1394'; B219 = 'AIM219-1398'; B187 = 'AIM187-1396'; I251 = 'DI251M-1401'
REFS = (Q, E, B95, B219, B187, I251)


def q(value, message):
    if not value:
        raise AssertionError(message)


def snap(c):
    return tuple(c.execute('''SELECT
        (SELECT COUNT(*) FROM documents),
        (SELECT COUNT(*) FROM articles),
        (SELECT COUNT(*) FROM articles WHERE is_current=1),
        (SELECT COUNT(*) FROM articles WHERE is_current=0),
        (SELECT COUNT(*) FROM relations),
        (SELECT COUNT(*) FROM tags),
        (SELECT COUNT(*) FROM articles_fts)''').fetchone())


def art(c, key, current=1, version=None):
    sql = 'SELECT * FROM articles WHERE article_key=?'
    args = [key]
    if current is not None:
        sql += ' AND is_current=?'; args.append(current)
    if version is not None:
        sql += ' AND version_no=?'; args.append(version)
    sql += ' ORDER BY version_no DESC LIMIT 1'
    return c.execute(sql, args).fetchone()


def main():
    c = get_connection(); docs = {}
    for ref in REFS:
        row = c.execute('SELECT id FROM documents WHERE reference_code=?', (ref,)).fetchone()
        q(row, 'missing ' + ref); docs[ref] = row['id']

    expected = {Q: (333, 230, 290), E: (60, 60, 60), B95: (17, 17, 17),
                B219: (51, 51, 51), B187: (14, 0, 14), I251: (40, 40, 40)}
    for ref, want in expected.items():
        row = c.execute('SELECT COUNT(*) n,COALESCE(SUM(is_current),0)c,COUNT(DISTINCT article_key)k FROM articles WHERE document_id=?', (docs[ref],)).fetchone()
        q((row['n'], row['c'], row['k']) == want, f'counts {ref}: {tuple(row)}')

    expected_keys = {f'{Q}:{n}' for n in range(1, 283)} | {f'{Q}:{n}bis' for n in (40, 41, 54, 138, 143, 146, 169, 251)}
    got = {r[0] for r in c.execute('SELECT DISTINCT article_key FROM articles WHERE document_id=?', (docs[Q],))}
    q(got == expected_keys, f'direct-tax coverage missing={expected_keys-got} extra={got-expected_keys}')
    for ref, end in ((E, 60), (B95, 17), (B219, 51), (B187, 14), (I251, 40)):
        got = {r[0] for r in c.execute('SELECT DISTINCT article_key FROM articles WHERE document_id=?', (docs[ref],))}
        q(got == {f'{ref}:{n}' for n in range(1, end + 1)}, 'coverage ' + ref)

    # Current/repealed structure and material histories.
    q(c.execute('SELECT COUNT(*) FROM articles WHERE document_id=? AND is_current=0', (docs[Q],)).fetchone()[0] == 103, 'Q history count')
    q(art(c, f'{Q}:187', 1) is None and c.execute('SELECT COUNT(*) FROM articles WHERE article_key=?', (f'{Q}:187',)).fetchone()[0] == 3, 'article 187 repeal history')
    for n in range(4, 17): q(art(c, f'{Q}:{n}', 1) is None, 'repealed early article ' + str(n))
    for key, count in {'40':2,'44':2,'46':2,'76':2,'84':2,'93':2,'95':3,'100':2,'101':2,'105':3,
                       '119':2,'120':2,'124':2,'126':2,'131':4,'132':3,'147':3,'148':2,'169':2,
                       '169bis':2,'187':3,'202':2,'219':2,'238':2,'239':2,'251bis':2}.items():
        q(c.execute('SELECT COUNT(*) FROM articles WHERE article_key=?', (f'{Q}:{key}',)).fetchone()[0] == count, 'history ' + key)

    # 1404 consolidation and operative conditions.
    q('رمز دارایی' in art(c, f'{Q}:3')['text'] and 'کارپوشه غیرتجاری' in art(c, f'{Q}:3')['text'], 'article 3 definitions')
    q('اشخاص غیرتجاری' in art(c, f'{Q}:46')['text'] and 'انواع رمز دارایی' in art(c, f'{Q}:46')['text'], 'article 46 assets')
    q('ملک مسکونی' in art(c, f'{Q}:47')['text'] and 'سرپرست خانوار' in art(c, f'{Q}:47')['text'], 'article 47 exemptions')
    q('قیمت خرید' in art(c, f'{Q}:48')['text'] and 'شاخص' in art(c, f'{Q}:48')['text'], 'article 48 calculation')
    q('ده واحد درصد' in art(c, f'{Q}:49')['text'] and 'دوره تملک' in art(c, f'{Q}:49')['text'], 'article 49 rates')
    q('سه سال پس از استقرار' in art(c, f'{Q}:50')['text'] and 'استعلام برخط' in art(c, f'{Q}:50')['text'], 'article 50 payment')
    q('اقاله، فسخ' in art(c, f'{Q}:51')['text'] and 'معامله جدید' in art(c, f'{Q}:51')['text'], 'article 51 reversal')
    q('مشمول ماده (۷۷)' in art(c, f'{Q}:76')['text'], 'article 76')
    q('تبصره۹' in art(c, f'{Q}:93')['text'].replace(' ', '') and 'عایدی سرمایه' in art(c, f'{Q}:93')['text'], 'article 93 additions')
    q('تبصره۱۴' in art(c, f'{Q}:105')['text'].replace(' ', '') and 'عایدی ناشی از تورم' in art(c, f'{Q}:105')['text'], 'article 105 additions')
    q('اشخاص غیرتجاری' in art(c, f'{Q}:119')['text'] and 'اشخاص تجاری' in art(c, f'{Q}:119')['text'], 'article 119')
    q('ارزش روز موضوع تبصره (۱) ماده (۴۸)' in art(c, f'{Q}:120')['text'], 'article 120')
    q('مشروط به استقرار بستر اجرائی' in art(c, f'{Q}:124')['text'], 'article 124 condition')
    q('صد برابر معافیت' in art(c, f'{Q}:126')['text'] and 'کارپوشه غیرتجاری' in art(c, f'{Q}:126')['text'], 'article 126 thresholds')
    q('تبصره ۴' in art(c, f'{Q}:132')['text'] and 'مناطق آزاد' in art(c, f'{Q}:132')['text'], 'article 132 additions')
    q('تبصره ۱۱' in art(c, f'{Q}:169bis')['text'] and 'پایگاه خانوار' in art(c, f'{Q}:169bis')['text'], 'article 169bis additions')

    # 1401/1403 adjusted thresholds omitted in some general compilations but materialized here.
    t131 = art(c, f'{Q}:131')['text']; q('دو میلیارد (۲٫۰۰۰٫۰۰۰٫۰۰۰)' in t131 and 'چهار میلیارد (۴٫۰۰۰٫۰۰۰٫۰۰۰)' in t131 and 'مازاد بر چهل درصد' in t131, 'article 131 current thresholds')
    q('پانصد میلیون' in art(c, f'{Q}:131', 0, 2)['text'] and 'دو میلیارد' in art(c, f'{Q}:131', 0, 3)['text'], 'article 131 timeline')
    q('ده میلیارد (۱۰٫۰۰۰٫۰۰۰٫۰۰۰)' in art(c, f'{Q}:132')['text'], 'article 132 adjusted threshold')
    q('دویست میلیون (۲۰۰٫۰۰۰٫۰۰۰)' in art(c, f'{Q}:147')['text'], 'article 147 adjusted threshold')
    q('۲٫۵۰۰٫۰۰۰ ریال' in art(c, f'{Q}:148')['text'], 'article 148 adjusted threshold')
    t202 = art(c, f'{Q}:202')['text']; q(all(x in t202 for x in ('بیست میلیارد','هشت میلیارد','چهارصد میلیون')), 'article 202 thresholds')

    # Amendment and regulations.
    q('ماده (۸۴)' in art(c, f'{E}:16')['text'] and 'قانون بودجه سنواتی' in art(c, f'{E}:16')['text'], '1394 clause 16')
    q('ماده(۹۵)' in art(c, f'{E}:21')['text'] and 'اظهارنامه مالیاتی' in art(c, f'{E}:21')['text'], '1394 clause 21')
    q('مواد(۲۷۴) تا (۲۸۲)' in art(c, f'{E}:60')['text'] and 'جرم مالیاتی' in art(c, f'{E}:60')['text'], '1394 clause 60')
    b2 = art(c, f'{B95}:2')['text']; q('پنجاه و پنج میلیارد' in b2 and 'هجده میلیارد' in b2 and 'سی میلیارد' not in b2, 'bylaw 95 current grouping')
    q('صورتحساب نوع سوم' in art(c, f'{B95}:8')['text'] and 'کد رهگیری' in art(c, f'{B95}:8')['text'], 'bylaw 95 invoices')
    q('رتبه ریسک' in art(c, f'{B219}:24')['text'] and 'قطعی' in art(c, f'{B219}:24')['text'], 'bylaw 219 risk')
    q('عدم ارائه تمامی اسناد' in art(c, f'{B219}:41')['text'] and 'کتمان درآمد' in art(c, f'{B219}:41')['text'], 'bylaw 219 audit')
    q('شماره واحدی' in art(c, f'{B187}:10', 0)['text'] and 'سه ماه' in art(c, f'{B187}:10', 0)['text'], 'historical bylaw 187')
    q('سامانه دادما' in art(c, f'{I251}:3')['text'] and 'موافقت وزیر' in art(c, f'{I251}:12')['text'], '251 directive')
    q('دیوان عدالت اداری' in art(c, f'{I251}:25')['text'] and 'سه ماه' in art(c, f'{I251}:25')['text'], '251 judicial review')

    placeholders = ','.join('?' * len(docs))
    rows = c.execute(f'SELECT article_no,text,source_note FROM articles WHERE document_id IN ({placeholders})', tuple(docs.values())).fetchall()
    q(all(r['text'].strip() and r['source_note'] for r in rows), 'empty/source note')
    q(all(not re.search(r'[0-9]', r['article_no']) for r in rows), 'ASCII digit in article_no')
    q(all('https://' not in r['text'] and 'http://' not in r['text'] and '###' not in r['text'] and 'دریافت فایل' not in r['text'] and '�' not in r['text'] for r in rows), 'source leak')
    q(all(not re.match(r'^‌?ماده\s*[۰-۹]', r['text']) for r in rows), 'heading leaked into text')

    for term in ('مالیات بر عایدی سرمایه', 'هزینه‌های قابل قبول', 'اظهارنامه مالیاتی', 'حسابرسی مالیاتی', 'سامانه دادما', 'رمز دارایی'):
        n = c.execute('''SELECT COUNT(*) FROM articles_fts f JOIN articles a ON a.id=f.article_id
            WHERE articles_fts MATCH ? AND a.is_current=1''', (f'"{term}"',)).fetchone()[0]
        q(n > 0, 'FTS ' + term)
    q(c.execute('SELECT COUNT(*) FROM articles_fts').fetchone()[0] == c.execute('SELECT COUNT(*) FROM articles').fetchone()[0], 'FTS parity')
    q(c.execute(f'SELECT COUNT(*) FROM relations WHERE from_document_id IN ({placeholders})', tuple(docs.values())).fetchone()[0] == 18, 'relations count')
    q(c.execute('''SELECT COUNT(*) FROM relations r JOIN documents f ON f.id=r.from_document_id JOIN documents t ON t.id=r.to_document_id
        WHERE f.reference_code='QMS-1404' AND t.reference_code=? AND r.from_article_id IS NULL AND r.to_article_id IS NULL''', (Q,)).fetchone()[0] == 1, 'surviving QMS document relation')
    q(not c.execute('PRAGMA foreign_key_check').fetchall(), 'foreign keys')

    before = snap(c); direct_id = docs[Q]; aid = art(c, f'{Q}:131')['id']; c.close()
    commands = (
        ['stats'], ['show', str(direct_id)], ['history', f'{Q}:131'], ['history', f'{Q}:187'],
        ['history', f'{Q}:46'], ['search', 'مالیات بر عایدی سرمایه'], ['search', 'هزینه قابل قبول'],
        ['search', 'دادما'],
    )
    for args in commands:
        proc = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/query.py'), *args], cwd=ROOT,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        q(proc.returncode == 0 and proc.stdout.strip(), 'query ' + ' '.join(args) + ': ' + proc.stderr)

    client = app.test_client()
    pages = ['/', '/?q=مالیات+بر+عایدی+سرمایه', '/?q=حسابرسی+مالیاتی', '/?q=سامانه+دادما',
             '/types', '/by-type/law', '/by-type/amendment', '/by-type/regulation', '/by-type/directive']
    for did in docs.values():
        pages += [f'/doc/{did}', f'/doc/{did}?view=all', f'/doc/{did}?view=historical']
    pages.append(f'/article/{aid}')
    for page in pages:
        q(client.get(page).status_code == 200, 'Flask ' + page)

    proc = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/load_direct_tax.py')], cwd=ROOT,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    q(proc.returncode == 0, 'reload: ' + proc.stderr)
    c = get_connection()
    q(before == snap(c), f'idempotency before={before} after={snap(c)}')
    q(c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'integrity')
    q(not c.execute('PRAGMA foreign_key_check').fetchall(), 'foreign keys after reload')
    q(not c.execute('SELECT reference_code,COUNT(*) n FROM documents WHERE reference_code IS NOT NULL GROUP BY reference_code HAVING n>1').fetchall(), 'duplicate refs')
    q(not c.execute('SELECT article_key,COUNT(*) n FROM articles WHERE is_current=1 AND article_key IS NOT NULL GROUP BY article_key HAVING n>1').fetchall(), 'multiple current versions')
    c.close()
    print('[OK] Direct-tax law=290 keys/333 rows (230 current + 103 historical)')
    print('[OK] 1394 amendment=60; regulations=17+51+14 historical; article-251bis directive=40')
    print('[OK] 1401 thresholds, 1404 capital-gains consolidation, repeal status and business histories')
    print('[OK] Coverage, Persian numbers, FTS5, relations, query.py, Flask, integrity and idempotency')


if __name__ == '__main__':
    main()
