# -*- coding: utf-8 -*-
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';O=R/'data/seed/consumer_competition.py';D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def clean(x):
 x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('__','').replace('ي','ی').replace('ك','ک').replace('\u200c','‌');x=re.sub(r'[ \t]+',' ',x);x=re.sub(r' *\n *','\n',x);return x.strip(' \n-')
def parse(fn,want=None, markdown_heads=False):
 ls=(C/fn).read_text().splitlines();h=[]
 for i,l in enumerate(ls):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])',l.replace('*','').replace('#','').replace('\u200c',' '))
  if m and 'متن سابق' not in l and 'مکرر' not in l and (not markdown_heads or '**' in l):h.append((int(m.group(1).translate(D)),i))
 # Sources with material headings have no duplicate numbered articles in selected texts.
 out=[]
 for j,(n,b) in enumerate(h):
  if want and n not in want:continue
  e=h[j+1][1] if j+1<len(h) else len(ls);x=clean('\n'.join(ls[b:e]));x=re.sub(r'^ماده\s*[۰-۹]+\s*[-ـ–:]?\s*','',x,1)
  for z in ('مطالب مرتبط','برچسب ها','دیدگاهتان را بنویسید','قانون فوق مشتمل'):
   if z in x:x=x.split(z,1)[0].strip()
  if x:out.append((str(n),x))
 return tuple(out)
CONSUMER=parse('consumer_law.md',set(range(1,23)))
CONSUMER_BYLAW=parse('consumer_bylaw.md')
AUTO=parse('auto_consumer_law.md',set(range(1,12)))
ARTICLE44=parse('article44_current.md',set(range(1,93)),markdown_heads=True)
# The source's current executive bylaw jumps from 38 to 40; article 39 is not present in this version.
assert [int(x[0]) for x in CONSUMER_BYLAW]==list(range(1,39))+list(range(40,44)),[x[0] for x in CONSUMER_BYLAW]
O.write_text('# -*- coding: utf-8 -*-\n'+'\n\n'.join(f'{k} = {pprint.pformat(v,width=120)}' for k,v in {'CONSUMER':CONSUMER,'CONSUMER_BYLAW':CONSUMER_BYLAW,'AUTO':AUTO,'ARTICLE44':ARTICLE44}.items())+'\n')
print('written',O,'counts',len(CONSUMER),len(CONSUMER_BYLAW),len(AUTO),len(ARTICLE44))
