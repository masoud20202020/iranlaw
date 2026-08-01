# -*- coding: utf-8 -*-
"""Build static seeds for narcotics legislation, treatment rules and leading rulings."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'drug_law.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def sm(s):
 s=re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',s);return s.replace('**','').replace('__','').replace('\\-','-').strip()
def clean(s):
 d={'ي':'ی','ك':'ک','ة':'ه','\ufeff':'','\u00ad':'‌','\u200e':'‌','\u200f':'‌','‎':'‌','‏':'‌','�':'ـ','آئین':'آیین','هیات':'هیأت','مسوول':'مسئول','موسسات':'مؤسسات','میباشد':'می‌باشد','میشود':'می‌شود','میشوند':'می‌شوند','میگردد':'می‌گردد','میکند':'می‌کند','میتواند':'می‌تواند','می نماید':'می‌نماید','می شود':'می‌شود','می گردد':'می‌گردد','می باشد':'می‌باشد','نمی باشد':'نمی‌باشد','بموجب':'به موجب','بعهده':'به عهده','بمنظور':'به منظور','بترتیب':'به ترتیب','بموقع':'به موقع','بمیزان':'به میزان','بنام':'به نام','بوسیله':'به وسیله','لازم الاجرا':'لازم‌الاجرا','غیر منقول':'غیرمنقول','قائم مقام':'قائم‌مقام','صورت جلسه':'صورت‌جلسه','صورت مجلس':'صورت‌مجلس','ذی ربط':'ذی‌ربط','یکماه':'یک ماه','یکسال':'یک سال','یکبار':'یک بار','ششماه':'شش ماه','بهشرح':'به شرح','مواد مخدر':'مواد مخدر','اینکهقانون':'اینکه قانون','۱۳۴قانون':'۱۳۴ قانون','قانونگذاردر':'قانونگذار در'}
 for a,b in d.items():s=s.replace(a,b)
 s=re.sub(r'\[پاورقی\s*[۰-۹0-9]+\]','',s)
 s=re.sub(r'‌+','‌',s);s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'(^|\n)‌',r'\1',s);s=re.sub(r'([)\]،؛:.])‌',r'\1 ',s);s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip()

def parse_seq(path,start,end,bylaw=False):
 expected=[str(i) for i in range(start,end+1)];idx=0;cur=None;arts={};foot=False
 pat=re.compile(r'^ماده[\s‌]*(?:\()?([۰-۹0-9]+)(?:\))?\s*(.*)$')
 for raw in path.read_text().splitlines():
  if re.match(r'^\s*\[[^]]+\]\([^)]+\)\s*$',raw):continue
  line=sm(raw).lstrip('‌ ');m=pat.match(line)
  if m:
   k=str(int(m.group(1).translate(F2A)));rest=m.group(2)
   if idx<len(expected) and k==expected[idx]:
    cur=k;idx+=1;foot=False;rest=re.sub(r'^\s*\((?:اصلاحی|الحاقی|منسوخه?|منسوخ)[^)]*\)\s*[ـ–:]?\s*','',rest).lstrip('ـ–:- ');arts[k]=[rest] if rest else []
   elif not foot and cur is not None and idx<len(expected):arts[cur].append(line)
   continue
  if cur is None or not line:continue
  if bylaw and line.startswith('[پاورقی]'):foot=True;continue
  if foot:continue
  if line.startswith('* * *'):
   cur=None;continue
  if line.startswith(('#','### نوشته','#### بیشتر','رئیس مجلس','علی لاریجانی','انتهای پیام')):continue
  if line.startswith(('قانون فوق مشتمل','این آیین‌نامه در','این آئین نامه در','برای دریافت فایل')):continue
  if 'https://' in line:continue
  arts[cur].append(line)
 if idx!=len(expected):raise ValueError(f'{path.name}: missing from {expected[idx:idx+6]}')
 out={k:clean('\n'.join(arts[k])) for k in expected}
 return out

def amendment45():
 txt=(CACHE/'drug_article45_amendment_1396.md').read_text();part=txt.split('ماده‌واحده',1)[1].split('قانون فوق مشتمل',1)[0]
 return clean('ماده‌واحده ـ '+sm(part).lstrip('ـ- '))
def ruling(path,start,end):
 txt=path.read_text();return clean(sm(txt.split(start,1)[1].split(end,1)[0]))

def main():
 law=parse_seq(CACHE/'drug_law_current.md',1,46)
 law['46']=law['46'].split('اصلاحیه قانون اصلاح قانون مبارزه با مواد مخدر',1)[0].strip()
 fine={k for k,v in law.items() if 'جزای نقدی مندرج' in v}
 oldfine={k:'\n'.join(x for x in law[k].splitlines() if 'جزای نقدی مندرج' not in x).strip() for k in fine}
 # Article 10 was deleted in the 1376 reform; preserve its substantive former text instead of a filler marker.
 old10='معتادان به مواد مخدر مذکور در ماده ۸ که تا یک گرم از آن‌ها را حمل یا نگهداری کنند به مجازات‌های مواد ۸ و ۹ محکوم نخواهند شد.'
 bylaw=parse_seq(CACHE/'drug_law_bylaw_1377_solh.md',1,34,bylaw=True)
 bylaw4_old=bylaw['4'];bylaw4_current='\n'.join(x for x in bylaw4_old.splitlines() if not (x.startswith('الف') and 'منسوخه' in x)).strip()
 treatment=parse_seq(CACHE/'drug_treatment_bylaw_1391.md',1,15)
 r738=ruling(CACHE/'ruling_738_drugs.md','#### **د: رای وحدت رویه شماره ۷۳۸- ۱۳۹۳/۱۰/۳۰ هیئت عمومی دیوان عالی کشور**','#### **مواد قانونی مرتبط:**')
 r743=ruling(CACHE/'ruling_743_drugs.md','#### **ج)**رای وحدت‌ رویه شماره ۷۴۳ – ۱۳۹۴/۸/۵ هیئت‌ عمومی دیوان ‌عالی ‌کشور','\n\nهیئت عمومی دیوان عالی کشور')
 r814=ruling(CACHE/'ruling_814_drugs.md','ج) رای وحدت‌ رویه شماره 814 - 1400/07/20 هیات‌ عمومی دیوان ‌عالی ‌کشور','هیات‌ عمومی دیوان‌ عالی‌ کشور')
 r826=ruling(CACHE/'ruling_826_drugs.md','با توجه به اینکه قانونگذار','[هیات عمومی دیوان عالی کشور]')
 r826=clean('با توجه به اینکه قانونگذار '+r826)
 r846=ruling(CACHE/'ruling_846_drugs.md','#### **ج)**رای وحدت‌ رویه شماره ۸۴۶ – ۱۴۰۳/۰۱/۲۸ هیئت‌ عمومی دیوان ‌عالی ‌کشور','رئیس هیئت‌ عمومی دیوان‌ عالی‌ کشور')
 vals={'DRUG_LAW':tuple(law.items()),'FINE_ARTICLES':tuple(sorted(fine,key=int)),'DRUG_FINE_OLD':tuple((k,oldfine[k]) for k in sorted(fine,key=int)),'DRUG_ART10_OLD':old10,'ARTICLE45_AMENDMENT':amendment45(),'DRUG_BYLAW':tuple(bylaw.items()),'DRUG_BYLAW_ART4_OLD':bylaw4_old,'DRUG_BYLAW_ART4_CURRENT':bylaw4_current,'TREATMENT_BYLAW':tuple(treatment.items()),'RULING_738':r738,'RULING_743':r743,'RULING_814':r814,'RULING_826':r826,'RULING_846':r846}
 head='# -*- coding: utf-8 -*-\n"""Generated narcotics law, treatment regulations and leading rulings."""\n# Generated by scripts/build_drug_law_seeds.py.\n\n';OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print(f'[OK] narcotics law=46 numbers; adjusted-fine histories={len(fine)}; general bylaw=34; treatment bylaw=15; rulings=5')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
