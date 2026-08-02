# -*- coding: utf-8 -*-
"""Build explicitly-labelled sourced summaries for administrative employment rulings."""
from pathlib import Path
import pprint
R=Path(__file__).resolve().parents[1]; src=(R/'data/source_cache/admin_employment_rulings_phase2.md').read_text()
def part(a,b=None):
 s=src.index(a); e=src.index(b,s) if b else len(src); return src[s:e].strip()
def clean_text(x):
    # The URL is stored in source_note by the loader; keep article text free of raw links.
    return '\n'.join(line for line in x.splitlines() if not line.strip().startswith('منبع:')).strip()

def summary(x): return 'خلاصه ساختاری منبع‌دار ـ این رکورد رونوشت لفظ‌به‌لفظ دادنامه نیست.\n\n'+clean_text(x)
rows=(
 ('DAD-669-1398','رأی وحدت رویه شماره ۶۶۹ درباره تبدیل وضعیت ایثارگران','۶۶۹','2019-07-02',part('## رأی وحدت رویه ۶۶۹','## دادنامه ۱۰۴۳')),
 ('DAD-1043-1400','رأی هیأت عمومی شماره ۱۰۴۳ درباره گزینش و کارمند پیمانی','۱۰۴۳','2021-06-12',part('## دادنامه ۱۰۴۳','## دادنامه ۱۴۲۰')),
 ('DAD-2120727-1402','دادنامه ابطال شرط تمام‌وقت در تبدیل وضعیت ایثارگران','۱۴۲۰۳۱۳۹۰۰۰۲۱۲۰۷۲۷','2023-11-07',part('## دادنامه ۱۴۲۰','## دادنامه ۱۴۰۳')),
 ('DAD-383671-1403','دادنامه اثر ترمیم حقوق بر اقلام پرداختی','۱۴۰۳۳۱۳۹۰۰۰۰۳۸۳۶۷۱','2024-05-07',part('## دادنامه ۱۴۰۳')),
)
rows=tuple((ref,title,no,date,summary(text)) for ref,title,no,date,text in rows)
out=R/'data/seed/administrative_employment_rulings.py'
out.write_text('# -*- coding: utf-8 -*-\nRULING_SUMMARIES = '+pprint.pformat(rows,width=140,sort_dicts=False)+'\n',encoding='utf-8')
print('written',out,'rulings',len(rows))
