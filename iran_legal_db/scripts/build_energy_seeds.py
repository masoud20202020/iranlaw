# -*- coding: utf-8 -*-
import re,pprint
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=R/'data/source_cache';O=R/'data/seed/energy.py';D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')
def parse(f,n):
 ls=(C/f).read_text().splitlines();h=[]
 for i,l in enumerate(ls):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)',l.replace('*','').replace('#','').replace('\u200c',' '));
  if m:h.append((int(m.group(1).translate(D)),i))
 o=[]
 for k in range(1,n+1):
  j=next(j for j,(x,_) in enumerate(h) if x==k);b=h[j][1];e=h[j+1][1] if j+1<len(h) else len(ls);x='\n'.join(ls[b:e]);x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('ي','ی').replace('ك','ک');x=re.sub(r'^ماده\s*[۰-۹]+\s*[-ـ–:]?\s*','',x.strip(),1);x=re.sub(r'[ \t]+',' ',x);x=re.sub(r' *\n *','\n',x);o.append((str(k),x.strip()))
 return tuple(o)
OIL=parse('oil.md',16);ENERGY=parse('energy_pattern.md',75)
O.write_text('# -*- coding: utf-8 -*-\nOIL='+pprint.pformat(OIL,width=120)+'\n\nENERGY='+pprint.pformat(ENERGY,width=120)+'\n');print('written',len(OIL),len(ENERGY))
