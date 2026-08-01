# -*- coding: utf-8 -*-
"""Build static seeds for the Bankruptcy Liquidation Administration package."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'data'/'source_cache'; SEED=ROOT/'data'/'seed'
TR=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789')

def clean(s):
 s=s.replace('\xa0',' ').replace('\u200f','').replace('\u200e','').replace('��','د').replace('�','ی')
 s=re.sub(r'!\[[^]]*\]\([^)]*\)','',s);s=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',s);s=s.replace('**','').replace('__','')
 s=re.sub(r'(?m)^\s*#{1,6}.*$','',s);return re.sub(r'\s+',' ',s).strip(' -–ـ')

def parse(path,start,count):
 t=path.read_text('utf8').replace('��','د').replace('�','ی');t=t[t.index(start):]
 pat=re.compile(r'(?m)^\s*‌?(?:\*\*)?‌?ماده\s*([۰-۹0-9]+)\s*(?:[-ـ]\*\*|\*\*|[-ـ])?\s*')
 ms=[];expected=1
 for m in pat.finditer(t):
  n=int(m.group(1).translate(TR))
  if n==expected:ms.append(m);expected+=1
  if expected==count+1:break
 if len(ms)!=count:raise RuntimeError((path.name,[int(m.group(1).translate(TR)) for m in ms]))
 rows=[]
 for i,m in enumerate(ms):
  e=ms[i+1].start() if i+1<len(ms) else len(t);b=t[m.end():e]
  # stop before unrelated page/navigation after final article
  if i+1==len(ms):
   for x in ('قانون فوق مشتمل','این قانون که مشتمل','قانون بالا که مشتمل','* * *','*   مجموعه قوانین','### نوشته','### بیشتر'):
    if x in b:b=b.split(x,1)[0]
  rows.append((i+1,clean(b)))
 return rows

def main():
 law=parse(CACHE/'bankruptcy_law.md','**ماده ۱-',60)
 m=dict(law)
 # Restore provisions displayed only as historical annotations.
 for n in (53,56):
  mm=re.search(r'متن ماده\s*'+str(n).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))+r' سابق:\s*«([^»]+)',m[n])
  if mm:m[n]=clean(mm.group(1))
 # Original and current versions of article 54.
 clause2='۲- از مبلغ موضوع اعتراض‌نامه که به موجب ماده ۲۹۳ قانون تجارت تنظیم می‌شود از قرار هر ۱۰ ریالی ده دینار گرفته شده که نصف آن جزء درآمد عمومی کشور منظور و نصف دیگر آن متعلق به صندوق (ب) خواهد بود.'
 orig54='درآمد صندوق (ب): ۱- بیست و پنج درصد (۲۵٪) به حقوقی که به موجب قانون ثبت شرکت‌ها مصوب ۲ خرداد ۱۳۱۰ و ماده ۱۱ قانون تجارت برای امضای دفاتر تجاری تعلق می‌گیرد اضافه شده و این اضافه به صندوق (ب) متعلق است. '+clause2
 v1373='درآمد صندوق (ب): ۱- درآمد صندوق (ب) به ازای هر یکصد صفحه دفتر تجارتی یک‌هزار و پانصد (۱۵۰۰) ریال است که به حساب اداره کل تصفیه امور ورشکستگی واریز می‌شود. '+clause2
 current54='درآمد صندوق (ب): '+clause2
 original=[(n,(orig54 if n==54 else m[n])) for n in range(1,61)]
 current=[(n,(current54 if n==54 else m[n])) for n in range(1,61)]
 bylaw=parse(CACHE/'bankruptcy_bylaw.md','**ماده ۱**',67)
 fund=parse(CACHE/'bankruptcy_fund.md','**‌ماده ۱**',3)
 out=SEED/'bankruptcy_law.py'
 with out.open('w',encoding='utf8') as f:
  f.write('# -*- coding: utf-8 -*-\n"""قانون و آیین‌نامه اداره تصفیه امور ورشکستگی."""\n\n')
  for name,val in [('BANKRUPTCY_ORIGINAL',original),('BANKRUPTCY_CURRENT',current),('BANKRUPTCY_ART54_1373',v1373),('BANKRUPTCY_BYLAW',bylaw),('BANKRUPTCY_FUNDS_LAW',fund)]:
   f.write(name+' = '+pprint.pformat(val,width=116,sort_dicts=False)+'\n\n')
 print('[OK] law=60, bylaw=67, funds law=3')
if __name__=='__main__':main()
