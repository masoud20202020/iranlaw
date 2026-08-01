# -*- coding: utf-8 -*-
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';O=R/'data/seed/intellectual_property.py';D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def clean(x):
 x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('__','').replace('ي','ی').replace('ك','ک').replace('\u200c','‌');x=re.sub(r'[ \t]+',' ',x);x=re.sub(r' *\n *','\n',x);return x.strip(' \n-')
def parse(fn,n):
 ls=(C/fn).read_text().splitlines();h=[]
 for i,l in enumerate(ls):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])',l.replace('*','').replace('#','').replace('\u200c',' '))
  if m:h.append((int(m.group(1).translate(D)),i))
 a=[]
 for k in range(1,n+1):
  j=next((j for j,(no,_) in enumerate(h) if no==k),None)
  if j is None:raise ValueError((fn,k))
  b=h[j][1];e=h[j+1][1] if j+1<len(h) else len(ls);x=clean('\n'.join(ls[b:e]));x=re.sub(r'^ماده\s*[۰-۹]+\s*[-ـ–:]?\s*','',x,1)
  for z in ('مطالب مرتبط','برچسب ها','دیدگاهتان را بنویسید','قانون فوق مشتمل'):
   if z in x:x=x.split(z,1)[0].strip()
  a.append((str(k),x))
 return tuple(a)
COPYRIGHT=parse('copyright_current.md',33); SOFTWARE=parse('software_law.md',17); TRANSLATION=parse('translation_law.md',12); INDUSTRIAL=parse('industrial_property_1403.md',150)
O.write_text('# -*- coding: utf-8 -*-\n'+'\n\n'.join(f'{k} = {pprint.pformat(v,width=120)}' for k,v in {'COPYRIGHT':COPYRIGHT,'SOFTWARE':SOFTWARE,'TRANSLATION':TRANSLATION,'INDUSTRIAL':INDUSTRIAL}.items())+'\n')
print('written',O,'counts',len(COPYRIGHT),len(SOFTWARE),len(TRANSLATION),len(INDUSTRIAL))
