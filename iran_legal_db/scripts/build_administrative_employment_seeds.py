# -*- coding: utf-8 -*-
"""Extract sourced administrative/employment texts cached for this project."""
from __future__ import annotations
import pprint, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'data'/'source_cache'; OUT=ROOT/'data'/'seed'/'administrative_employment.py'
D2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')
A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def clean(s):
 # Some crawled pages contain empty Markdown footnote links like [](url) or *[](url).
 # Remove those before preserving labelled Markdown links.
 s=re.sub(r'!?\[\]\([^)]+\)','',s)
 s=re.sub(r'!\[[^]]*\]\([^)]+\)','',s); s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('\ufeff','').replace('\u200e','').replace('\u200f','')
 s=s.replace('ي','ی').replace('ى','ی').replace('ك','ک').replace('‌','\u200c')
 s=re.sub(r'(?m)^\s*#{1,6}\s*','',s); s=re.sub(r'[ \t]+',' ',s); s=re.sub(r' *\n *','\n',s); s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip(' \n-ـ')

def heads(lines):
 out=[]
 for i,line in enumerate(lines):
  x=line.replace('*','').replace('#','').replace('\u200c',' ').strip()
  m=re.match(r'^(?:[-–—]\s*)?ماده\s*([۰-۹٠-٩0-9]+)\s*(?:\([^)]*\))?\s*[-ـ.،:]?',x)
  if m: out.append((int(m.group(1).translate(D2A)),i))
 return out

def parse(fn,count, occurrence=0, start=0):
 lines=(CACHE/fn).read_text(encoding='utf-8').splitlines(); hs=[x for x in heads(lines) if x[1]>=start]; ans=[]
 for n in range(1,count+1):
  hits=[(j,p) for j,(no,p) in enumerate(hs) if no==n]
  if len(hits)<=occurrence: raise ValueError(f'{fn}: missing {n}; got {[x[0] for x in hs]}')
  j,b=hits[occurrence]; e=hs[j+1][1] if j+1<len(hs) else len(lines)
  t=clean('\n'.join(lines[b:e])); t=re.sub(r'^ماده\s*[۰-۹]+\s*(?:\([^)]*\))?\s*[-ـ.،:]?\s*','',t,1)
  for marker in ('منبع:', 'منبع :', 'مطالب مرتبط', 'نوشته های مشابه', 'نوشته‌های مشابه', 'دیدگاهتان را', 'تمامی حقوق مادی', 'برچسب ها:', 'برچسب‌ها:'):
   if marker in t: t=t.split(marker,1)[0].strip()
  if not t: raise ValueError(f'{fn}: empty {n}')
  ans.append((str(n),t))
 return tuple(ans)

CIVIL_SERVICE=parse('civil_service_current.md',128)
ADMIN_VIOLATIONS=parse('admin_violations_law.md',27)
ADMIN_VIOLATIONS_BYLAW=parse('admin_violations_bylaw.md',47)
DIVAN_CURRENT=parse('divan_law_current.md',124)
DIVAN_ORIGINAL=parse('divan_law_original_1392.md',124)
DIVAN_AMENDMENT=parse('divan_amendment_1402.md',62)
ART46_BYLAW=parse('civil_service_article46_bylaw.md',6)
ART46_DIRECTIVE=parse('civil_service_article46_directive.md',12)
CONTRACT_EMPLOYMENT=parse('contract_employment_bylaw_1368.md',30)
CS84_BYLAW=parse('civil_service_84_100_bylaw.md',5)
# Historical text for article 44 is preserved from current text only where source cache supplies amendment act;
# original current-law cache is used for full source provenance.
def single_act(filename):
 raw=(CACHE/filename).read_text(encoding='utf-8')
 start=raw.index('ماده واحده-')
 end=raw.index('قانون فوق مشتمل',start)
 return clean(raw[start:end])
ARTICLE44_AMENDMENT=single_act('civil_service_article44_amendment_1399.md')
PERMANENT_1397=single_act('civil_service_permanent_1397.md')
OUT.write_text('# -*- coding: utf-8 -*-\n"""Generated from locally cached, cited public legal texts."""\n\n'+
 '\n\n'.join(f'{name} = {pprint.pformat(value,width=120,sort_dicts=False)}' for name,value in globals().copy().items() if name in {'CIVIL_SERVICE','ADMIN_VIOLATIONS','ADMIN_VIOLATIONS_BYLAW','DIVAN_CURRENT','DIVAN_ORIGINAL','DIVAN_AMENDMENT','ART46_BYLAW','ART46_DIRECTIVE','CONTRACT_EMPLOYMENT','CS84_BYLAW','ARTICLE44_AMENDMENT','PERMANENT_1397'})+'\n',encoding='utf-8')
print('written',OUT)
for n in ('CIVIL_SERVICE','ADMIN_VIOLATIONS','ADMIN_VIOLATIONS_BYLAW','DIVAN_CURRENT','DIVAN_AMENDMENT','ART46_BYLAW','ART46_DIRECTIVE','CONTRACT_EMPLOYMENT','CS84_BYLAW'): print(n,len(globals()[n]))
