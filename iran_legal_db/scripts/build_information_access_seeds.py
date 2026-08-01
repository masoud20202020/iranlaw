# -*- coding: utf-8 -*-
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def p(f,n):
 l=(C/f).read_text().splitlines();h=[]
 for i,x in enumerate(l):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)',x.replace('*','').replace('#','').replace('\u200c',' '));
  if m:h.append((int(m.group(1).translate(D)),i))
 o=[]
 for k in range(1,n+1):
  j=next(j for j,(a,_) in enumerate(h) if a==k);b=h[j][1];e=h[j+1][1] if j+1<len(h) else len(l);x='\n'.join(l[b:e]);x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('ي','ی').replace('ك','ک');x=re.sub(r'^ماده\s*[۰-۹]+\s*[-ـ–:]?\s*','',x.strip(),1);o.append((str(k),re.sub(r'[ \t]+',' ',x).strip()))
 return tuple(o)
LAW=p('free_information.md',23);BYLAW=p('free_information_bylaw.md',11);(R/'data/seed/information_access.py').write_text('# -*- coding: utf-8 -*-\nLAW='+pprint.pformat(LAW,width=120)+'\nBYLAW='+pprint.pformat(BYLAW,width=120)+'\n');print(len(LAW),len(BYLAW))
