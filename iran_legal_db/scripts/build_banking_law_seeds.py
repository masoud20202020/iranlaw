# -*- coding: utf-8 -*-
"""Build banking-law seeds: Central Bank, monetary/banking, usury-free operations and core rules."""
from __future__ import annotations
import pprint, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'banking_law.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def clean(s):
 s=re.sub(r'!\[[^]]*\]\([^)]+\)','',s);s=re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('\\-','-').replace('\ufeff','').replace('\u200e','‌').replace('\u200f','‌').replace('\u00ad','‌')
 for a,b in {'ي':'ی','ك':'ک','ة':'ه','هیات':'هیأت','مسوول':'مسئول','مسؤول':'مسئول','موسسات':'مؤسسات','موسسه':'مؤسسه','آئین':'آیین','بانکها':'بانک‌ها','آنها':'آن‌ها','می باشد':'می‌باشد','می شود':'می‌شود','می گردد':'می‌گردد','می نماید':'می‌نماید','لازم الاجرا':'لازم‌الاجرا','حق الوکاله':'حق‌الوکاله','قرض الحسنه':'قرض‌الحسنه','سرمایه گذاری':'سرمایه‌گذاری','سپرده گذار':'سپرده‌گذار','تامین':'تأمین','تسهیلات اعطائی':'تسهیلات اعطایی','سپرده های':'سپرده‌های','مدت دار':'مدت‌دار','می باشند':'می‌باشند','می باشد':'می‌باشد','بعنوان':'به‌عنوان','بکار':'به‌کار','بشرط':'به شرط','جعالف':'جعاله'}.items():s=s.replace(a,b)
 s=re.sub(r'(?m)^>\s?','',s);s=re.sub(r'(?m)^#{1,6}\s*.*$','',s);s=re.sub(r'\[\]\([^)]*\)','',s)
 s=re.sub(r'(?m)^\s*\*\s*\*\s*\*\s*$','',s);s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip(' ‌\n-*')

def norm(l):return re.sub(r'\s+',' ',re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',l).replace('*','').replace('‌',' ').replace('ـ','-')).strip()

def parse_seq(path,start,end,stop_terms=()):
 lines=path.read_text().splitlines();heads=[]
 for i,l in enumerate(lines):
  m=re.match(r'^ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])\s*[-–]?',norm(l))
  if m:heads.append((int(m.group(1).translate(F2A)),i))
 byno={n:i for n,i in heads}
 if any(n not in byno for n in range(start,end+1)):raise ValueError(f'coverage {path.name}: missing {[n for n in range(start,end+1) if n not in byno]}')
 allpos=sorted((i,n) for n,i in heads);out=[]
 for n in range(start,end+1):
  begin=byno[n];finish=next((i for i,_ in allpos if i>begin),len(lines));body=clean('\n'.join(lines[begin:finish]))
  body=re.sub(r'^ماده\s*[۰-۹]+\s*[-–ـ]?\s*','',body,count=1)
  for term in ('قانون فوق مشتمل','رئیس مجلس','### تازه','مطالب مرتبط',*stop_terms):
   if term in body:body=body.split(term,1)[0].strip()
  if not body:raise ValueError(f'empty {path.name}:{n}')
  out.append((str(n),body))
 return tuple(out)

def ruling794():
 s=(CACHE/'ruling_794_banking.md').read_text();s=s.split('#### **ج) رای وحدت‌ رویه شماره ۷۹۴',1)[1];s=s.split('#### مواد قانونی مرتبط',1)[0]
 s=re.sub(r'^.*?کشور\*\*','',s,flags=re.S);return clean(s).replace('هیئت‌ عمومی دیوان‌ عالی‌ کشور','').strip()

def main():
 cb=parse_seq(CACHE/'central_bank_law_1402.md',1,67)
 pb=dict(parse_seq(CACHE/'monetary_banking_law_1351.md',1,45))
 uf=dict(parse_seq(CACHE/'usury_free_banking_1362.md',1,27))
 resources=parse_seq(CACHE/'bank_resources_bylaw_1362.md',1,12,stop_terms=('رسول رضایی',))
 facilities=parse_seq(CACHE/'bank_facilities_bylaw_1362.md',1,90)
 facilitation=parse_seq(CACHE/'bank_facilitation_law_1386.md',1,9)
 # The 1402 Central Bank Act expressly repealed these provisions of the 1351 Act.
 repealed=set(range(1,18))|set(range(19,27))|{39,40,42,43,44}
 pbrows=[]
 for n in range(1,46):
  k=str(n);no=str(n).translate(A2F)
  if n in repealed:pbrows.append({'key':k,'article_no':no,'version_no':1,'is_current':False,'effective_date':'1972-07-09','expiry_date':'2024-05-27','text':pb[k],'notes':'نسخ صریح به موجب بند الف ماده ۶۷ قانون بانک مرکزی ۱۴۰۲.'})
  elif n==18:
   pbrows.append({'key':k,'article_no':no,'version_no':1,'is_current':False,'effective_date':'1972-07-09','expiry_date':'2024-05-27','text':pb[k],'notes':'نسخه کامل پیش از نسخ بندهای ب، ج و د ماده ۱۸.'})
   a=pb[k].split('\nب-',1)[0].strip();a+='\n\nیادداشت تنقیحی- کلیه وظایف و اختیارات شورای پول و اعتبار به موجب ماده ۶۷ قانون بانک مرکزی جمهوری اسلامی ایران به هیأت‌عالی منتقل شده است.'
   pbrows.append({'key':k,'article_no':no,'version_no':2,'is_current':True,'effective_date':'2024-05-27','expiry_date':None,'text':a,'notes':'فقط بند الف باقی است؛ مرجع اعمال وظایف، هیأت‌عالی بانک مرکزی است.'})
  else:pbrows.append({'key':k,'article_no':no,'version_no':1,'is_current':True,'effective_date':'1972-07-09','expiry_date':None,'text':pb[k],'notes':'بقای ماده پس از قانون بانک مرکزی ۱۴۰۲؛ وظایف شورای پول و اعتبار به هیأت‌عالی منتقل شده است.' if n in range(27,39) else None})
 # Article 9: preserve pre-1390 text before adding istisna, murabaha and debt purchase.
 old9='''بانک‌ها می‌توانند به منظور ایجاد تسهیلات لازم جهت گسترش امور بازرگانی در چهارچوب سیاست‌های بازرگانی دولت، منابع مالی لازم را بر اساس قرارداد مضاربه در اختیار مشتریان با اولویت دادن به تعاونی‌های قانونی قرار دهند.\n\nتبصره- بانک‌ها در امر واردات مجاز به مضاربه با بخش خصوصی نمی‌باشند.'''
 ufrows=[]
 for n in range(1,28):
  k=str(n);no=str(n).translate(A2F)
  if n==9:
   ufrows.append({'key':k,'article_no':no,'version_no':1,'is_current':False,'effective_date':'1983-08-30','expiry_date':'2011-07-16','text':clean(old9),'notes':'متن پیش از الحاق استصناع، مرابحه و خرید دین.'})
   ufrows.append({'key':k,'article_no':no,'version_no':2,'is_current':True,'effective_date':'2011-07-16','expiry_date':None,'text':uf[k],'notes':'نسخه جاری با عقود الحاقی.'})
  else:ufrows.append({'key':k,'article_no':no,'version_no':1,'is_current':True,'effective_date':'1983-08-30','expiry_date':None,'text':uf[k],'notes':None})
 vals={'CENTRAL_BANK_LAW':cb,'MONETARY_BANKING_ROWS':tuple(pbrows),'USURY_FREE_ROWS':tuple(ufrows),'BANK_RESOURCES_BYLAW':resources,'BANK_FACILITIES_BYLAW':facilities,'BANK_FACILITATION_LAW':facilitation,'RULING_794':ruling794()}
 head='# -*- coding: utf-8 -*-\n"""Generated banking law package."""\n# Generated by scripts/build_banking_law_seeds.py.\n\n'
 OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] Central Bank=67; monetary/banking=45 keys/46 rows (15 current); usury-free=27 keys/28 rows')
 print('[OK] resources bylaw=12; facilities bylaw=90; facilitation law=9; unified ruling=1')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
