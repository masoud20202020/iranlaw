# -*- coding: utf-8 -*-
"""Build static seeds for municipal law, urban renewal, finance and leading rulings."""
from __future__ import annotations
import pprint,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data'/'source_cache'
OUT=ROOT/'data'/'seed'/'municipal_law.py'
FA2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
A2FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def strip_md(s:str)->str:
    s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
    return s.replace('**','').replace('__','').replace('\\-','-').strip()

def clean(s:str)->str:
    repl={
        'ي':'ی','ك':'ک','ة':'ه','\ufeff':'','\u00ad':'','\u200e':'‌','\u200f':'‌','‎':'‌','‏':'‌','�':'ـ',
        'آئین':'آیین','هیات':'هیأت','مسوول':'مسئول','موسسات':'مؤسسات','میباشد':'می‌باشد','میشود':'می‌شود',
        'میشوند':'می‌شوند','میگردد':'می‌گردد','میکند':'می‌کند','میتواند':'می‌تواند','می نماید':'می‌نماید',
        'می شود':'می‌شود','می گردد':'می‌گردد','می باشد':'می‌باشد','نمی باشد':'نمی‌باشد','بموجب':'به موجب',
        'بعهده':'به عهده','بمنظور':'به منظور','بترتیب':'به ترتیب','بموقع':'به موقع','بمیزان':'به میزان',
        'بنام':'به نام','بوسیله':'به وسیله','بمالک':'به مالک','بشهرداری':'به شهرداری','بوصول':'به وصول',
        'باخذ':'به اخذ','بصدور':'به صدور','بموقع':'به موقع','لازم الاجرا':'لازم‌الاجرا','غیر منقول':'غیرمنقول',
        'قائم مقام':'قائم‌مقام','صورت مجلس':'صورت‌مجلس','ذی ربط':'ذی‌ربط','یکماه':'یک ماه','یکسال':'یک سال',
        'یکبار':'یک بار','پنجسال':'پنج سال','ششماه':'شش ماه','شورایعالی':'شورای عالی','رئیس جمهور':'رئیس‌جمهور',
    }
    for a,b in repl.items(): s=s.replace(a,b)
    s=re.sub(r'‌+','‌',s)
    s=re.sub(r'[ \t]*‌[ \t]*','‌',s)
    s=re.sub(r'(^|\n)‌',r'\1',s)
    s=re.sub(r'([)\]،؛:.])‌',r'\1 ',s)
    s=re.sub(r'[ \t]+',' ',s)
    s=re.sub(r' *\n *','\n',s)
    s=re.sub(r'\n{3,}','\n\n',s)
    return s.translate(A2FA).strip()

def expiry_from_marker(marker:str)->str|None:
    for key,date in (
        ('۱۰ˏ۱۱ˏ۱۴۰۰','2022-01-30'),('۳۰ˏ۰۱ˏ۱۳۹۶','2017-04-19'),('۲۴ˏ۰۴ˏ۱۳۵۹','1980-07-15'),
        ('۲۲ˏ۱۲ˏ۱۳۵۱','1973-03-13'),('۲۷ˏ۱۱ˏ۱۳۴۵','1967-02-16'),('۱۳ˏ۰۲ˏ۱۳۴۴','1965-05-03'),
    ):
        if key in marker:return date
    return None

def parse_municipality():
    path=CACHE/'municipality_law_current.md'
    lines=path.read_text().splitlines()
    pat=re.compile(r'^[‌\s]*(?:\*\*)?ماده[\s‌]*(?:\*\*)?([۰-۹0-9]+)\s*\)?\s*(.*)$')
    arts={};meta={};cur=None
    for raw in lines:
        line=strip_md(raw)
        m=pat.match(line)
        if m:
            n=int(m.group(1).translate(FA2A))
            if not 1<=n<=119 or n in arts:
                cur=None;continue
            cur=n;marker=m.group(2).strip();meta[n]=(marker,'منسوخ' in marker,expiry_from_marker(marker))
            first=re.sub(r'^\s*(?:\((?:اصلاحی|الحاقی|منسوخه?|منسوخ)[^)]*\)\s*)?[ـ–-]?\s*','',marker)
            arts[n]=[first] if first else []
            continue
        if cur is None or not line:continue
        if line.startswith(('#','* * *','انتهای پیام')):continue
        if 'https://' in line:continue
        # In a surviving article, omit a wholly repealed paragraph/band from the current text.
        if not meta[cur][1] and 'منسوخ' in line:continue
        arts[cur].append(line)
    if set(arts)!=set(range(1,120)):
        raise ValueError(f'municipality coverage: missing={sorted(set(range(1,120))-set(arts))}')
    result=[]
    for n in range(1,120):
        text=clean('\n'.join(arts[n]));marker,repealed,expiry=meta[n]
        if not text:raise ValueError(f'empty municipality article {n}')
        result.append((n,text,repealed,expiry))
    return tuple(result)

def parse_numbered_bold(path:Path,start:int,end:int):
    """Parse pages whose main article headings are bold; ignore embedded unbolded quoted laws."""
    arts={};cur=None
    pat=re.compile(r'^ماده[\s‌]*([۰-۹0-9]+)(?:[\s‌]*\([^)]*\))?[\s‌]*[ـ–-]\s*(.*)$')
    for raw in path.read_text().splitlines():
        # Main headings are bold in these sources; quoted amending texts inside an article are not.
        m=pat.match(strip_md(raw)) if raw.strip().startswith('**ماده') else None
        if m:
            n=int(m.group(1).translate(FA2A));cur=n if start<=n<=end and n not in arts else None
            if cur:arts[cur]=[m.group(2)] if m.group(2).strip() else []
            continue
        if cur is None or not raw.strip():continue
        if raw.lstrip().startswith(('>','#','* * *')):continue
        line=strip_md(raw)
        if not line or 'https://' in line:continue
        if line.startswith(('قانون فوق مشتمل','قانون بالا مشتمل','محمدباقر قالیباف','رئیس مجلس','معاون اول رئیس جمهور')):
            cur=None;continue
        arts[cur].append(line)
    want=set(range(start,end+1))
    if set(arts)!=want:raise ValueError(f'{path.name}: missing={sorted(want-set(arts))}; extra={sorted(set(arts)-want)}')
    return {n:clean('\n'.join(arts[n])) for n in range(start,end+1)}

def parse_urban_renewal():
    path=CACHE/'urban_renewal_law.md';arts={};cur=None
    pat=re.compile(r'^ماده[\s‌]*([۰-۹0-9]+)(?:[\s‌]*\([^)]*\))?[\s‌]*[ـ–-]\s*(.*)$')
    for raw in path.read_text().splitlines():
        m=pat.match(strip_md(raw)) if raw.strip().startswith('**ماده') else None
        if m:
            n=int(m.group(1).translate(FA2A));cur=n if 1<=n<=36 and n not in arts else None
            if cur:arts[cur]=[m.group(2)] if m.group(2).strip() else []
            continue
        if cur is None or not raw.strip():continue
        if raw.lstrip().startswith(('>','#','* * *')):continue
        line=strip_md(raw)
        if not line or 'https://' in line:continue
        if line.startswith(('قانون بالا مشتمل','رئیس مجلس')):cur=None;continue
        arts[cur].append(line)
    if set(arts)!=set(range(1,37)):raise ValueError(f'urban renewal coverage: {sorted(set(range(1,37))-set(arts))}')
    return {n:clean('\n'.join(arts[n])) for n in range(1,37)}

def parse_financial_1346():
    path=CACHE/'municipal_financial_bylaw_1346.md';arts={};cur=None
    pat=re.compile(r'^[‌\s]*ماده[\s‌]*([۰-۹0-9]+)\s*[ـ–-]\s*(.*)$')
    for raw in path.read_text().splitlines():
        line=strip_md(raw);m=pat.match(line)
        if m:
            n=int(m.group(1).translate(FA2A));cur=n if 1<=n<=48 and n not in arts else None
            if cur:arts[cur]=[m.group(2)] if m.group(2) else []
            continue
        if cur is None or not line:continue
        if line.startswith(('#','آیین‌نامه فوق مشتمل','رییس مجلس')):cur=None;continue
        if 'https://' in line:continue
        arts[cur].append(line)
    if set(arts)!=set(range(1,49)):raise ValueError(f'financial 1346: {sorted(set(range(1,49))-set(arts))}')
    result={n:clean('\n'.join(arts[n])) for n in range(1,49)}
    # The source appends the parliamentary approval formula to article 48 on the same wrapped paragraph.
    result[48]=result[48].split('آیین‌نامه فوق مشتمل',1)[0].strip()
    return result

def article100_old_1345():
    lines=(CACHE/'municipality_amendment_1345.md').read_text().splitlines();collect=[];on=False
    for raw in lines:
        line=strip_md(raw)
        if re.match(r'^[‌\s]*ماده 100\s*[ـ–-]',line):
            on=True;collect=[re.sub(r'^[‌\s]*ماده 100\s*[ـ–-]\s*','',line)];continue
        if on and re.match(r'^[‌\s]*ماده 101\s*[ـ–-]',line):break
        if on and line:collect.append(line)
    if not collect:raise ValueError('old article 100')
    return clean('\n'.join(collect))

def article101_current():
    txt=(CACHE/'municipality_article101_1390.md').read_text()
    m=re.search(r'ماده 101\s*-\s*(.*?)(?=\n\nقانون فوق مشتمل)',txt,re.S)
    if not m:raise ValueError('current article 101')
    return clean(strip_md(m.group(1)))

def drop_prefixed_lines(text:str,prefixes:tuple[str,...])->str:
    return '\n'.join(x for x in text.splitlines() if not x.startswith(prefixes)).strip()

def extract_ruling(path:Path,marker:str,end_marker:str)->str:
    txt=path.read_text();part=txt.split(marker,1)[1].split(end_marker,1)[0]
    return clean(strip_md(part))

def main():
    municipality=parse_municipality()
    muni={n:t for n,t,_,_ in municipality}
    m100_old=article100_old_1345()
    m101_old=muni[101]
    m101_current=article101_current()

    renewal=parse_urban_renewal()
    renewal2_old=renewal[2]
    renewal2_mid=renewal2_old.replace('پنج در هزار','یک درصد (۱٪)')
    first,rest=(renewal2_old.split('\n',1)+[''])[:2]
    first_current=('در شهر تهران و سایر شهرهایی که اجرای این قانون در آن‌ها اعلام شده است، بر کلیه اراضی و ساختمان‌ها و '
                   'مستحدثات واقع در محدوده قانونی شهر، عوارض خاص سالانه به میزان دو و نیم درصد (۲٫۵٪) ارزش معاملاتی '
                   'آخرین تقویم موضوع صدر و تبصره (۳) ماده (۶۴) قانون مالیات‌های مستقیم برقرار می‌شود. شهرداری‌ها مکلفند '
                   'عوارض مذکور را وصول کرده و منحصراً به مصرف نوسازی و عمران شهری برسانند. مصرف وجوه حاصل از اجرای این '
                   'قانون در غیر موارد مصرح در این قانون در حکم تصرف غیرقانونی در اموال دولت خواهد بود.')
    renewal2_current=clean(first_current+('\n'+rest if rest else ''))
    renewal10_old=renewal[10]
    renewal10_current=drop_prefixed_lines(renewal10_old,('تبصره ۲','تبصره۲'))
    renewal16_old=renewal[16]
    renewal16_current=drop_prefixed_lines(renewal16_old,('تبصره ۲','تبصره۲','تبصره ۳','تبصره۳'))

    revenue=parse_numbered_bold(CACHE/'sustainable_municipal_revenue_1401.md',1,17)
    finance_new=parse_numbered_bold(CACHE/'sustainable_municipal_financial_bylaw_1401.md',1,18)
    finance_old=parse_financial_1346()

    ruling1509=extract_ruling(CACHE/'divan_1509_1399.md','رای هیات عمومی\n','\nمحمدکاظم بهرامی')
    ruling227=extract_ruling(CACHE/'divan_227_1395_delay.md','رای هیئت عمومی دیوان عدالت اداری\n','\nمحمد کاظم بهرامی')
    ruling1310=extract_ruling(CACHE/'divan_1310_1397.md','**رأی هیأت عمومی**\n','\nرئیس هیأت عمومی')
    ruling577=('خلاصه نتیجه لازم‌الاتباع رأی: رأی کمیسیون ماده ۱۰۰ قانون شهرداری مبنی بر قلع تأسیسات احداثی باید '
               'متضمن اعلام عدم رعایت اصول شهرسازی، فنی یا بهداشتی و ذکر مصداق آن در بنای احداثی باشد. صرف بیان مجمل '
               'ضرورت قلع، بدون احراز و استناد به عدم رعایت اصول سه‌گانه، برای صدور حکم تخریب کافی نیست.')

    vals={
        'MUNICIPALITY_ARTICLES':municipality,
        'MUNICIPALITY_ART100_OLD_1345':m100_old,
        'MUNICIPALITY_ART101_OLD_1345':m101_old,
        'MUNICIPALITY_ART101_CURRENT_1390':m101_current,
        'URBAN_RENEWAL_BASE':tuple(renewal.items()),
        'URBAN_RENEWAL_ART2_OLD':renewal2_old,
        'URBAN_RENEWAL_ART2_MID':renewal2_mid,
        'URBAN_RENEWAL_ART2_CURRENT':renewal2_current,
        'URBAN_RENEWAL_ART10_OLD':renewal10_old,
        'URBAN_RENEWAL_ART10_CURRENT':renewal10_current,
        'URBAN_RENEWAL_ART16_OLD':renewal16_old,
        'URBAN_RENEWAL_ART16_CURRENT':renewal16_current,
        'SUSTAINABLE_REVENUE_LAW':tuple(revenue.items()),
        'SUSTAINABLE_FINANCIAL_BYLAW':tuple(finance_new.items()),
        'MUNICIPAL_FINANCIAL_BYLAW_1346':tuple(finance_old.items()),
        'DIVAN_RULING_577_SUMMARY':ruling577,
        'DIVAN_RULING_1509':ruling1509,
        'DIVAN_RULING_227':ruling227,
        'DIVAN_RULING_1310':ruling1310,
    }
    head=('# -*- coding: utf-8 -*-\n'
          '"""Generated municipal law, urban renewal, finance and leading-ruling texts."""\n'
          '# Generated by scripts/build_municipal_seeds.py.\n\n')
    OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
    rep=sum(1 for _,_,r,_ in municipality if r)
    print(f'[OK] municipality=119 numbers ({119-rep} current, {rep} fully repealed) + history of arts 100/101')
    print('[OK] urban renewal=36 numbers with 1400 repeals and 3 rate versions; sustainable revenue=17; new finance bylaw=18; old finance bylaw=48')
    print('[OK] leading Divan rulings=4 (ruling 577 explicitly stored as a source-limited summary)')
    print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')

if __name__=='__main__':main()
