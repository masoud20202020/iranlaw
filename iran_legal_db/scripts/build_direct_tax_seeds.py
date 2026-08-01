# -*- coding: utf-8 -*-
"""Build seeds for direct-tax law, its 1394 amendment and core implementing rules."""
from __future__ import annotations
import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data' / 'source_cache'
OUT = ROOT / 'data' / 'seed' / 'direct_tax.py'
F2A = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
A2F = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def unlink(s: str) -> str:
    s = re.sub(r'!\[[^]]*\]\([^)]+\)', '', s)
    return re.sub(r'\[([^]]*)\]\([^)]+\)', r'\1', s)


def clean(s: str) -> str:
    s = unlink(s).replace('**', '').replace('__', '').replace('\\-', '-').replace('\ufeff', '')
    s = s.replace('\u200e', '‌').replace('\u200f', '‌').replace('\u00ad', '‌')
    for a, b in {
        'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'مودیان': 'مؤدیان', 'مودی': 'مؤدی',
        'هیات': 'هیأت', 'مسوول': 'مسئول', 'موسسات': 'مؤسسات', 'آئین': 'آیین',
        'ذی ربط': 'ذی‌ربط', 'می باشد': 'می‌باشد', 'می شود': 'می‌شود',
        'می گردد': 'می‌گردد', 'می نماید': 'می‌نماید', 'لازم الاجرا': 'لازم‌الاجرا',
        'صورت حساب': 'صورت‌حساب', 'مالیاتهای': 'مالیات‌های', 'قانونگذار': 'قانون‌گذار',
        'جداگان های': 'جداگانه‌ای', 'مق ررات': 'مقررات', 'کردهاند': 'کرده‌اند',
        'آن‌ها از برای': 'آن‌ها برای', 'بیشتر‌است': 'بیشتر است',
    }.items():
        s = s.replace(a, b)
    s = re.sub(r'(?m)^#{1,6}\s*.*$', '', s)
    s = re.sub(r'(?m)^>\s?', '', s)
    s = re.sub(r'\[\]\([^)]*\)', '', s)
    s = re.sub(r'(?m)^\s*\*\s*\*\s*\*\s*$', '', s)
    s = re.sub(r'(?m)^\s*\*\s+', '- ', s)
    s = re.sub(r'[ \t]*‌[ \t]*', '‌', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' *\n *', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.translate(A2F).strip(' \n-*')


def norm_heading(line: str) -> str:
    return re.sub(r'\s+', ' ', unlink(line).replace('*', '').replace('‌', ' ').replace('ـ', '-')).strip()


def strip_article_heading(text: str) -> str:
    """Remove an article/range heading while preserving the substantive text on that line."""
    text = clean(text).lstrip('‌ ')
    text = re.sub(
        r'^(?:ماده|مواد)\s*[۰-۹]+(?:\s*مکرر)?(?:\s*(?:و|تا|الی)\s*[۰-۹]+)?'
        r'(?:\s*\([^\n]*?\))?\s*[-–]?\s*', '', text, count=1
    )
    return text.strip()


def direct_law() -> tuple[dict[str, str], dict[str, list[str]], dict[str, str]]:
    """Parse the current compilation and editorial repeal notices."""
    lines = (CACHE / 'direct_tax_current.md').read_text().splitlines()
    hits = []
    for i, line in enumerate(lines):
        if not line.lstrip().startswith('**'):
            continue
        x = norm_heading(line)
        rg = re.match(r'^(?:ماده|مواد)\s*([۰-۹]+)\s*(?:تا|الی)\s*([۰-۹]+)', x)
        pair = re.match(r'^(?:ماده|مواد)\s*([۰-۹]+)\s*و\s*([۰-۹]+)', x)
        one = re.match(r'^ماده\s*([۰-۹]+)(?:\s*(مکرر))?(?:\s|\(|-|–|$)', x)
        if rg:
            hits.append((i, 'range', rg.groups(), x))
        elif pair:
            hits.append((i, 'range', pair.groups(), x))
        elif one:
            hits.append((i, 'one', one.groups(), x))
    current: dict[str, str] = {}
    notices: dict[str, list[str]] = {}
    headings: dict[str, str] = {}
    for j, (start, kind, nums, heading) in enumerate(hits):
        end = hits[j + 1][0] if j + 1 < len(hits) else len(lines)
        body = strip_article_heading('\n'.join(lines[start:end]))
        body = body.split('قانون فوق مشتمل', 1)[0].strip()
        if kind == 'range':
            first, last = (int(x.translate(F2A)) for x in nums)
            # Article 3 and articles 40-43 were later reused by the 1404 amendment.
            if first == 3:
                first = 4
            for n in range(first, last + 1):
                notices.setdefault(str(n), []).append(body)
            continue
        no, bis = nums
        key = str(int(no.translate(F2A))) + ('bis' if bis else '')
        headings[key] = heading
        is_notice = (
            ('نسخ صریح شده' in body or 'قانون الزام به ثبت رسمی معاملات اموال غیر منقول' in body)
            and (body.startswith('[') or body.startswith('به موجب') or len(body) < 250)
        )
        if is_notice:
            notices.setdefault(key, []).append(body)
        else:
            current[key] = body
    expected = {str(i) for i in range(1, 283)} | {
        '40bis', '41bis', '54bis', '138bis', '143bis', '146bis', '169bis', '251bis'
    }
    got = set(current) | set(notices)
    if got != expected:
        raise ValueError(f'direct-tax coverage mismatch; missing={sorted(expected-got)} extra={sorted(got-expected)}')
    return current, notices, headings


def markdown_articles(path: Path, wanted: set[int] | None = None) -> dict[str, str]:
    """Parse ordinary bold article headings in a Markdown source."""
    lines = path.read_text().splitlines()
    hits = []
    for i, line in enumerate(lines):
        x = norm_heading(line)
        m = re.match(r'^ماده\s*([۰-۹0-9]+)(?:\s*(مکرر))?\s*[-–]', x)
        if m and (line.lstrip().startswith('**') or path.name == 'direct_tax_bylaw_187.md'):
            n = int(m.group(1).translate(F2A))
            if wanted is None or n in wanted:
                hits.append((i, str(n) + ('bis' if m.group(2) else '')))
    out = {}
    for j, (start, key) in enumerate(hits):
        # Boundary is the next article heading, including an article outside wanted.
        end = len(lines)
        for k in range(start + 1, len(lines)):
            if re.match(r'^ماده\s*[۰-۹0-9]+(?:\s*مکرر)?\s*[-–]', norm_heading(lines[k])):
                end = k
                break
        body = strip_article_heading('\n'.join(lines[start:end]))
        body = re.split(r'\n\s*(?:قانون فوق|رئیس مجلس|انتهای پیام)', body, maxsplit=1)[0]
        out[key] = body.strip()
    return out


def tinn_pre1404() -> dict[str, str]:
    old = markdown_articles(CACHE / 'direct_tax_1394_snapshot.md', set(range(44, 52)) | {100, 101, 105, 119, 120, 126, 131})
    # Remove source footnotes accidentally placed at the end of article 46.
    if '46' in old:
        old['46'] = re.split(r'\n\s*۱۲\.\s*به موجب بند ۹', old['46'], maxsplit=1)[0].strip()
    for k in ('45', '48'):
        if k in old:
            old[k] = old[k].replace('نیم در هزار۱حق', 'نیم در هزار حق')
    return old


def solh_occurrences(number: int, bis: bool = False) -> list[str]:
    """Return authentic historical occurrences from the mixed historical Solh compilation."""
    lines = (CACHE / 'direct_tax_solh.md').read_text().splitlines()
    all_heads = []
    for i, line in enumerate(lines):
        x = line.strip().replace('‌', '')
        m = re.match(r'^ماده\s*([۰-۹0-9]+)(?:\s*(مکرر))?\s*[-ـ]', x)
        if m:
            all_heads.append((i, int(m.group(1).translate(F2A)), bool(m.group(2))))
    out = []
    for j, (start, no, is_bis) in enumerate(all_heads):
        if no != number or is_bis != bis:
            continue
        end = all_heads[j + 1][0] if j + 1 < len(all_heads) else len(lines)
        text = strip_article_heading('\n'.join(lines[start:end]))
        text = re.split(r'\n(?:باب|فصل)\s', text, maxsplit=1)[0].strip()
        if text:
            out.append(text)
    return out


def former_187() -> str:
    s = (CACHE / 'direct_tax_article187_former.md').read_text()
    s = s.split('– متن سابق ماده 187 به شرح زیر می باشد:', 1)[1]
    s = s.split('[منبع: سازمان امور مالیاتی کشور]', 1)[0]
    return strip_article_heading(s)


def parse_seq(path: Path, start: int, end: int, *, special2: bool = False) -> tuple[tuple[str, str], ...]:
    lines = path.read_text().splitlines()
    hits = []
    for n in range(start, end + 1):
        fa, asc = str(n).translate(A2F), str(n)
        pat = re.compile(r'^\s*(?:\*+)?ماده(?:\*+)?\s*(?:' + re.escape(fa) + '|' + asc + r')(?![۰-۹0-9])\s*[-–ـ]?', re.I)
        found = next((i for i, line in enumerate(lines) if pat.match(line)), None)
        if found is None and special2 and n == 2:
            found = next((i for i, line in enumerate(lines) if re.match(r'^\s*ماه\s*۲\s*[-–ـ]', line)), None)
        if found is None:
            raise ValueError(f'missing article {n} in {path.name}')
        hits.append((n, found))
    out = []
    for j, (n, begin) in enumerate(hits):
        finish = hits[j + 1][1] if j + 1 < len(hits) else len(lines)
        body = clean('\n'.join(lines[begin:finish]))
        body = re.sub(r'^(?:\*+)?(?:ماده|ماه)(?:\*+)?\s*[۰-۹0-9]+\s*[-–ـ]?\s*', '', body, count=1)
        body = re.split(r'\n(?:این آیین نامه|این آییـن|علی طیب|صادق آملی|سید احسان|انتهای پیام|دریافت فایل|اجتمام|تنظیم:|منبع:|\* \*)', body, maxsplit=1)[0].strip()
        if special2 and n == 2 and '\nالف- حجم فعالیت:' in body:
            # The Mizan page appends an obsolete earlier grouping after the current 1398 text.
            body = body.split('\nالف- حجم فعالیت:', 1)[0].strip()
        if not body:
            raise ValueError(f'empty article {n} in {path.name}')
        out.append((str(n), body))
    return tuple(out)


def amendment_1394() -> tuple[tuple[str, str], ...]:
    lines = (CACHE / 'direct_tax_1394_amendment.md').read_text().splitlines()
    hits = []
    for i, line in enumerate(lines):
        m = re.match(r'^\s*بند\s*([۰-۹0-9]+)\s*[-–]', line)
        if m:
            hits.append((int(m.group(1).translate(F2A)), i))
    if [n for n, _ in hits] != list(range(1, 61)):
        raise ValueError('1394 amendment clauses are not 1..60')
    out = []
    for j, (n, begin) in enumerate(hits):
        finish = hits[j + 1][1] if j + 1 < len(hits) else len(lines)
        body = clean('\n'.join(lines[begin:finish]))
        body = re.sub(r'^بند\s*[۰-۹]+\s*[-–]\s*', '', body, count=1)
        body = body.split('قانون فوق مشتمل', 1)[0].strip()
        out.append((str(n), body))
    return tuple(out)


def main() -> None:
    current, notices, headings = direct_law()
    old1404 = tinn_pre1404()
    histories: dict[str, list[dict]] = {}

    def hist(key: str, text: str, eff: str, exp: str, note: str, rank: int) -> None:
        text = clean(text)
        if not text or any(x['text'] == text for x in histories.setdefault(key, [])):
            return
        histories[key].append({'text': text, 'effective_date': eff, 'expiry_date': exp, 'notes': note, 'rank': rank})

    d1366 = '1988-02-22'; d1381 = '2002-03-21'; d1395 = '2016-03-20'; d1400 = '2021-05-23'
    d1403_repeal = '2024-06-22'; d1404 = '2025-08-16'

    # Historical editorial status notices for provisions with no current text.
    for key, values in notices.items():
        for value in values:
            if '۱۳۸۰/۱۱/۲۷' in value:
                dt = d1381
            elif '۱۴۰۳' in value or key == '187':
                dt = d1403_repeal
            else:
                dt = d1395
            hist(key, value, dt, dt, 'یادداشت تنقیحی منبع درباره نسخ؛ متن سابق ماده نیست.', 90)

    # Pre-1404 numbering and substantive text of articles affected by speculation-tax law.
    for n in range(44, 52):
        hist(str(n), old1404[str(n)], d1395, d1404, 'نسخه معتبر پیش از تغییر شماره‌گذاری/الحاق مالیات بر عایدی سرمایه در ۱۴۰۴.', 50)
    # Reconstruct pre-1404 text only by reversing express additions/replacements in the amending act.
    hist('76', 'در مواردی که نقل و انتقال موضوع ماده (۵۲) این قانون حسب مورد مشمول مواد (۵۹) یا (۷۷) باشد، وجه دیگری بابت مالیات بر درآمد نقل و انتقال مزبور مطالبه نخواهد شد.', d1395, d1404, 'متن اصلاحی ۱۳۹۴ پیش از جایگزینی سال ۱۴۰۴.', 50)
    hist('93', current['93'].split('\nتبصره ۲', 1)[0], d1395, d1404, 'نسخه پیش از الحاق تبصره‌های ۲ تا ۹ در سال ۱۴۰۴.', 50)
    hist('105', old1404['105'], d1395, d1404, 'نسخه پیش از الحاق تبصره‌های مالیات عایدی سرمایه در سال ۱۴۰۴.', 50)
    for key in ('119', '120', '126'):
        hist(key, old1404[key], d1395, d1404, 'نسخه پیش از اصلاح قانون مالیات بر سوداگری و سفته‌بازی ۱۴۰۴.', 50)
    hist('132', current['132'].split('\nتبصره ۳', 1)[0], d1395, '2022-08-15', 'نسخه پیش از تعدیل نصاب ۱۴۰۱ و الحاق تبصره‌های ۳ و ۴ در سال ۱۴۰۴.', 50)
    hist('169bis', current['169bis'].split('\nتبصره ۱۰', 1)[0], d1395, d1404, 'نسخه پیش از الحاق تبصره‌های ۱۰ و ۱۱ در سال ۱۴۰۴.', 50)

    # Authentic older generations for business and tax-procedure provisions.
    selections = {
        '84': (84, False, 0, '1992-04-27', d1395, 'نسخه تاریخی با مبلغ ثابت معافیت حقوق.'),
        '95-old': (95, False, 2, d1366, d1381, 'متن مصوب اولیه درباره دفاتر قانونی.'),
        '95-mid': (95, False, 0, d1381, d1395, 'نسخه اصلاحی پیش از جایگزینی ماده ۹۵ در سال ۱۳۹۴.'),
        '100': (100, False, 0, d1366, d1395, 'نسخه تاریخی پیش از اصلاح موعد و تبصره سال ۱۳۹۴.'),
        '101': (101, False, 0, d1366, d1395, 'نسخه تاریخی معافیت درآمد مشاغل.'),
        '105-old': (105, False, 1, d1366, d1381, 'نسخه تاریخی پیش از نرخ واحد ۲۵ درصد.'),
        '131': (131, False, 0, d1366, d1395, 'نسخه تاریخی نرخ‌های پلکانی مصوب اولیه.'),
        '147': (147, False, 0, d1366, d1395, 'نسخه تاریخی هزینه‌های قابل قبول پیش از تبصره‌های ۱۳۹۴.'),
        '148': (148, False, 0, d1366, d1395, 'نسخه تاریخی فهرست هزینه‌های قابل قبول.'),
        '169': (169, False, 0, d1366, d1395, 'نسخه تاریخی تکالیف صورتحساب و نگهداری اطلاعات.'),
        '186': (186, False, 0, d1366, d1381, 'نسخه تاریخی گواهی مالیاتی تسهیلات و مجوزها.'),
        '187-old': (187, False, 0, d1366, d1395, 'نسخه تاریخی ماده ۱۸۷ پیش از تبصره‌های ۱۳۹۴.'),
        '219': (219, False, 0, d1366, d1381, 'نسخه تاریخی ساختار تشخیص مالیات.'),
        '238': (238, False, 0, d1366, d1400, 'نسخه تاریخی سازوکار رفع اختلاف پیش از اصلاح ۱۴۰۰.'),
        '239': (239, False, 0, d1366, d1381, 'نسخه تاریخی قطعیت برگ تشخیص.'),
        '251bis': (251, True, 0, '1992-04-27', d1381, 'نسخه تاریخی ماده ۲۵۱ مکرر با تبصره‌ای که در ۱۳۸۰ نسخ شد.'),
    }
    for name, (no, bis, index, eff, exp, note) in selections.items():
        vals = solh_occurrences(no, bis)
        if index >= len(vals):
            raise ValueError(f'missing historical selection {name}: {len(vals)} occurrences')
        text = vals[index]
        if name == '169':
            text = text.split('\nتبصره۲', 1)[0].strip()
        hist(name.split('-')[0], text, eff, exp, note, 10 if 'old' in name or name in {'84','100','101','131','147','148','169','186','219','238','239','251bis'} else 20)

    # Intermediate/current-before-1404 versions available in the 1394 snapshot.
    hist('131', old1404['131'], d1395, '2022-08-15', 'نسخه نرخ‌های پلکانی اصلاحی ۱۳۹۴ پیش از تعدیل نصاب‌های ۱۴۰۱.', 55)
    hist('147', current['147'], d1395, '2022-08-15', 'نسخه تبصره ۳ با نصاب پنجاه میلیون ریال پیش از تعدیل ۱۴۰۱.', 55)
    hist('202', current['202'], d1395, '2022-08-15', 'نسخه نصاب‌های ممنوع‌الخروجی پیش از تصویب‌نامه تعدیل ۱۴۰۱.', 55)
    hist('187', former_187(), d1395, d1403_repeal, 'آخرین متن معتبر ماده ۱۸۷ با تبصره‌های ۳ و ۴، پیش از نسخ در ۱۴۰۳.', 60)

    # Apply Cabinet Decision 77899/T59727H of 1401/05/09 under article 175.
    adjusted131 = old1404['131'].replace('پانصد میلیون (۵۰۰،۰۰۰،۰۰۰) ریال', 'دو میلیارد (۲٫۰۰۰٫۰۰۰٫۰۰۰) ریال').replace('یک میلیارد (۱،۰۰۰،۰۰۰،۰۰۰) ریال', 'چهار میلیارد (۴٫۰۰۰٫۰۰۰٫۰۰۰) ریال')
    # Tinn uses Arabic comma separators in this historical transcription.
    adjusted131 = adjusted131.replace('پانصد میلیون (۵۰۰٫۰۰۰٫۰۰۰) ریال', 'دو میلیارد (۲٫۰۰۰٫۰۰۰٫۰۰۰) ریال').replace('یک میلیارد (۱٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'چهار میلیارد (۴٫۰۰۰٫۰۰۰٫۰۰۰) ریال')
    hist('131', adjusted131, '2022-08-15', '2024-05-20', 'نسخه پس از تعدیل نصاب‌های ۱۴۰۱ و پیش از اصلاح تبصره در ۱۴۰۳.', 60)
    old132_adjusted = current['132'].split('\nتبصره ۳', 1)[0]
    old132_adjusted = old132_adjusted.replace('پنج میلیارد (۵٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'ده میلیارد (۱۰٫۰۰۰٫۰۰۰٫۰۰۰) ریال')
    hist('132', old132_adjusted, '2022-08-15', d1404, 'نسخه پس از تعدیل نصاب بند «س» و پیش از تبصره‌های عایدی سرمایه ۱۴۰۴.', 60)
    replacements = {
        '131': (
            ('پانصد میلیون (۵۰۰٫۰۰۰٫۰۰۰) ریال', 'دو میلیارد (۲٫۰۰۰٫۰۰۰٫۰۰۰) ریال'),
            ('یک میلیارد (۱٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'چهار میلیارد (۴٫۰۰۰٫۰۰۰٫۰۰۰) ریال'),
        ),
        '132': (('پنج میلیارد (۵٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'ده میلیارد (۱۰٫۰۰۰٫۰۰۰٫۰۰۰) ریال'),),
        '147': (('پنجاه میلیون (۵۰٫۰۰۰٫۰۰۰) ریال', 'دویست میلیون (۲۰۰٫۰۰۰٫۰۰۰) ریال'),),
        '202': (
            ('پنج میلیارد (۵٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'بیست میلیارد (۲۰٫۰۰۰٫۰۰۰٫۰۰۰) ریال'),
            ('دو میلیارد (۲٫۰۰۰٫۰۰۰٫۰۰۰) ریال', 'هشت میلیارد (۸٫۰۰۰٫۰۰۰٫۰۰۰) ریال'),
            ('یک‌صد میلیون (۱۰۰٫۰۰۰٫۰۰۰) ریال', 'چهارصد میلیون (۴۰۰٫۰۰۰٫۰۰۰) ریال'),
        ),
    }
    for key, pairs in replacements.items():
        before = current[key]
        for old, new in pairs:
            current[key] = current[key].replace(old, new)
        if current[key] == before:
            raise ValueError(f'1401 threshold replacement failed for article {key}')

    src_current = 'متن تنقیحی قانون مالیات‌های مستقیم از پایگاه اختبار، با اصلاحات ۱۴۰۴ و تطبیق نصاب‌های تصویب‌نامه ۷۷۸۹۹/ت۵۹۷۲۷هـ سال ۱۴۰۱.'
    rows = []
    all_keys = sorted(set(current) | set(notices), key=lambda k: (int(k.removesuffix('bis')), k.endswith('bis')))
    for key in all_keys:
        hs = sorted(histories.get(key, []), key=lambda x: (x['rank'], x['effective_date'], x['text']))
        # Repeal status notes come last; substantive historical versions precede them.
        for version, item in enumerate(hs, 1):
            rows.append({
                'key': key, 'article_no': str(int(key.removesuffix('bis'))).translate(A2F) + (' مکرر' if key.endswith('bis') else ''),
                'text': item['text'], 'version_no': version, 'is_current': False,
                'effective_date': item['effective_date'], 'expiry_date': item['expiry_date'],
                'source_note': src_current if item['rank'] >= 90 else 'منابع تاریخی قانون، قانون اصلاحی ۱۳۹۴ و متن‌های مقابله‌ای محفوظ در source_cache.',
                'notes': item['notes'],
            })
        if key in current:
            eff = d1404 if key in {'3','40','40bis','41','41bis','42','43','44','45','46','47','48','49','50','51','76','93','105','119','120','124','126','132','169bis'} else d1366
            # Use the heading's latest express amendment date for notable later versions.
            h = headings.get(key, '')
            if '۱۴۰۳' in h: eff = '2024-04-29'
            elif '۱۴۰۲' in h: eff = '2024-03-20'
            elif '۱۴۰۱' in h: eff = '2022-07-31'
            elif '۱۴۰۰' in h: eff = d1400
            elif '۱۳۹۴' in h and key not in {'105','169bis'}: eff = d1395
            elif '۱۳۸۰' in h: eff = d1381
            elif '۱۳۷۱' in h: eff = '1992-04-27'
            if key in {'3','40','40bis','41','41bis','42','43','44','45','46','47','48','49','50','51','76','93','105','119','120','124','126','132','169bis'}:
                eff = d1404
            if key == '131': eff = '2024-05-20'
            elif key in {'147','148','202'}: eff = '2022-08-15'
            elif key in {'84','95','100','101','169','219'}: eff = d1395
            elif key in {'186','239','251bis'}: eff = d1381
            elif key == '238': eff = d1400
            rows.append({
                'key': key, 'article_no': str(int(key.removesuffix('bis'))).translate(A2F) + (' مکرر' if key.endswith('bis') else ''),
                'text': current[key], 'version_no': len(hs) + 1, 'is_current': True,
                'effective_date': eff, 'expiry_date': None, 'source_note': src_current,
                'notes': 'نسخه جاری تنقیحی تا اصلاحات ۱۴۰۴.' if key in {'3','40','40bis','41','41bis','42','43','44','45','46','47','48','49','50','51','76','93','105','119','120','124','126','132','169bis'} else None,
            })

    by95 = parse_seq(CACHE / 'direct_tax_bylaw_95.md', 1, 17, special2=True)
    by219 = parse_seq(CACHE / 'direct_tax_bylaw_219.md', 1, 51)
    by187 = parse_seq(CACHE / 'direct_tax_bylaw_187.md', 1, 14)
    ins251 = parse_seq(CACHE / 'direct_tax_instruction_251bis.md', 1, 40)
    amend = amendment_1394()

    vals = {
        'DIRECT_TAX_ROWS': tuple(rows),
        'DIRECT_TAX_AMENDMENT_1394': amend,
        'DIRECT_TAX_BYLAW_95': by95,
        'DIRECT_TAX_BYLAW_219': by219,
        'DIRECT_TAX_BYLAW_187': by187,
        'DIRECT_TAX_INSTRUCTION_251BIS': ins251,
    }
    head = '# -*- coding: utf-8 -*-\n"""Generated direct-tax law, amendment and implementing rules."""\n# Generated by scripts/build_direct_tax_seeds.py.\n\n'
    OUT.write_text(head + ''.join(f'{k} = {pprint.pformat(v, width=120, sort_dicts=False)}\n\n' for k, v in vals.items()))
    current_count = sum(1 for r in rows if r['is_current'])
    hist_count = len(rows) - current_count
    print(f'[OK] Direct tax: 290 keys; {current_count} current rows; {hist_count} historical rows; total={len(rows)}')
    print('[OK] 1394 amendment=60 clauses; regulations=17+51+14; directive=40')
    print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
