# -*- coding: utf-8 -*-
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';O=R/'data/seed/cooperative_law.py';D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def clean(x):
 x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('__','').replace('ي','ی').replace('ك','ک');x=re.sub(r'[ \t]+',' ',x);x=re.sub(r' *\n *','\n',x);return x.strip(' \n-')
def parse(f):
 ls=(C/f).read_text().splitlines();h=[]
 for i,l in enumerate(ls):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])',l.replace('*','').replace('#','').replace('\u200c',' '))
  if m:h.append((int(m.group(1).translate(D)),i))
 out=[]
 for j,(n,b) in enumerate(h):
  e=h[j+1][1] if j+1<len(h) else len(ls);x=clean('\n'.join(ls[b:e]));x=re.sub(r'^ماده\s*[۰-۹]+\s*[-ـ–:]?\s*','',x,1)
  for z in ('مطالب مرتبط','برچسب ها','دیدگاهتان را بنویسید','قانون فوق مشتمل'):
   if z in x:x=x.split(z,1)[0].strip()
  if x and n not in {int(no) for no,_ in out}:out.append((str(n),x))
 return tuple(out)
SECTOR=parse('cooperative_sector.md');COMPANIES=parse('cooperative_companies.md');AMENDMENT=parse('cooperative_amendment_1393.md')
assert len(SECTOR)==77 and len(COMPANIES)==147 and len(AMENDMENT)==27
O.write_text('# -*- coding: utf-8 -*-\n'+'\n\n'.join(f'{k} = {pprint.pformat(v,width=120)}' for k,v in {'SECTOR':SECTOR,'COMPANIES':COMPANIES,'AMENDMENT':AMENDMENT}.items())+'\n')
print('written',O,len(SECTOR),len(COMPANIES),len(AMENDMENT))
