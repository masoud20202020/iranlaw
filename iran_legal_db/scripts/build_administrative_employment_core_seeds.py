# -*- coding: utf-8 -*-
"""Build core statutes for administrative employment phase three from cached sources."""
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';O=R/'data/seed/administrative_employment_core.py'
T=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def clean(t):
 t=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',t).replace('**','').replace('‌','\u200c').replace('ي','ی').replace('ك','ک')
 t=re.sub(r'[ \t]+',' ',t);t=re.sub(r' *\n *','\n',t);return t.strip(' \n-')
def parse(fn,n):
 ls=(C/fn).read_text().splitlines();h=[]
 for i,l in enumerate(ls):
  x=l.replace('*','').replace('#','').replace('\u200c',' ')
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])',x)
  if m:h.append((int(m.group(1).translate(T)),i))
 out=[]
 for k in range(1,n+1):
  j=next((q for q,(no,_) in enumerate(h) if no==k),None)
  if j is None:raise ValueError((fn,k))
  b=h[j][1];e=h[j+1][1] if j+1<len(h) else len(ls);x=clean('\n'.join(ls[b:e]));x=re.sub(r'^ماده\s*[۰-۹]+\s*(?:[-ـ–:]|مکرر)?\s*','',x,1)
  for z in ('مطالب مرتبط','برچسب ها','دیدگاهتان را بنویسید','قانون فوق مشتمل'):
   if z in x:x=x.split(z,1)[0].strip()
  out.append((str(k),x))
 return tuple(out)
ISARGARAN=parse('isaar_current.md',76)
GOZINESH=parse('gozinesh_current.md',18)
JANBAZAN=parse('janbazan_facilities.md',20)
raw=(C/'gozinesh_tasri.md').read_text();a=raw.index('**ماده واحده-**');b=raw.index('قانون فوق مشتمل',a);TASRI=clean(raw[a:b])
O.write_text('# -*- coding: utf-8 -*-\n'+ '\n\n'.join(f'{k} = {pprint.pformat(v,width=120)}' for k,v in {'ISARGARAN':ISARGARAN,'GOZINESH':GOZINESH,'JANBAZAN':JANBAZAN,'TASRI':TASRI}.items())+'\n')
print('written',O,'counts',len(ISARGARAN),len(GOZINESH),len(JANBAZAN))
