# -*- coding: utf-8 -*-
"""Build static seeds for tenancy, apartments, presale and mandatory registration."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'housing_law.py'
FA2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def strip_md(s):
 s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s);return s.replace('**','').replace('__','').replace('\\-','-').strip()
def clean(s):
 repl={'ي':'ی','ك':'ک','ة':'ه','\ufeff':'','\u00ad':'','\u200e':'‌','\u200f':'‌','‎':'‌','‏':'‌','آئین':'آیین','هیات':'هیأت','مسوول':'مسئول','موسسات':'مؤسسات','میباشد':'می‌باشد','میشود':'می‌شود','میشوند':'می‌شوند','میگردد':'می‌گردد','میکند':'می‌کند','میتواند':'می‌تواند','می نماید':'می‌نماید','می شود':'می‌شود','می گردد':'می‌گردد','می باشد':'می‌باشد','نمی باشد':'نمی‌باشد','بموجب':'به موجب','بعهده':'به عهده','بمنظور':'به منظور','بترتیب':'به ترتیب','بموقع':'به موقع','بمیزان':'به میزان','بنام':'به نام','بوسیله':'به وسیله','بدادگاه':'به دادگاه','لازم الاجرا':'لازم‌الاجرا','غیر منقول':'غیرمنقول','قائم مقام':'قائم‌مقام','مال الاجاره':'مال‌الاجاره','اجاره بها':'اجاره‌بها','حق الزحمه':'حق‌الزحمه','پیش فروش':'پیش‌فروش','پیش خریدار':'پیش‌خریدار','پیش فروشنده':'پیش‌فروشنده','صورت مجلس':'صورت‌مجلس','ذی ربط':'ذی‌ربط','یکماه':'یک ماه','یکبار':'یک بار'}
 for a,b in repl.items():s=s.replace(a,b)
 s=re.sub(r'\s*\(\s*(?:اصلاحی|الحاقی|منسوخه?)[^)]*\)\s*[ـ–-]?','',s)
 s=re.sub(r'\s*\(این (?:ماده|بند|تبصره) به موجب[^)]*\)','',s)
 s=re.sub(r'‌+','‌',s);s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'(^|\n)‌',r'\1',s);s=re.sub(r'([)\]،؛:.])‌',r'\1 ',s)
 s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s);return s.translate(A2FA).strip()
def marker_line(line):return line.lstrip('‌ #').replace('ماده ‌','ماده ').replace('ماده‌','ماده ')
def parse(path,wanted):
 arts={};cur=None
 for raw in path.read_text().splitlines():
  line=strip_md(raw);m=re.match(r'^ماده[\s‌]*([۰-۹0-9]+)(?:[\s‌]*\([^)]*\))?[\s‌]*[ـ–-]\s*[‌ ]*(.*)$',marker_line(line))
  if m:
   n=int(m.group(1).translate(FA2A));cur=n if n in wanted and n not in arts else None
   if cur:arts[cur]=[m.group(2)] if m.group(2) else []
   continue
  if cur is None or not line:continue
  if line.startswith('#') or re.match(r'^(فصل|مبحث|بخش)\s',line):continue
  if line.startswith(('قانون فوق مشتمل','اسحاق جهانگیری','رئیس مجلس','* * *','انتهای پیام')):cur=None;continue
  if 'https://' in line or '](http' in line:continue
  arts[cur].append(line)
 miss=sorted(wanted-set(arts))
 if miss:raise ValueError(f'{path.name}: {miss}')
 return {n:clean('\n'.join(arts[n])) for n in sorted(wanted)}
def apartment_law():
 arts={};cur=None;key=None
 for raw in (CACHE/'apartment_ownership_law.md').read_text().splitlines():
  line=strip_md(raw);m=re.match(r'^ماده[\s‌]*([۰-۹0-9]+)([\s‌]+مکرر)?(?:[\s‌]*\([^)]*\))?[\s‌]*[ـ–-]\s*[‌ ]*(.*)$',marker_line(line))
  if m:
   n=int(m.group(1).translate(FA2A));key='10bis' if m.group(2) else str(n);cur=key if key not in arts else None
   if cur:arts[cur]=[m.group(3)] if m.group(3) else []
   continue
  if cur is None or not line:continue
  if line.startswith('#') or line.startswith(('قانون بالا مشتمل','* * *')):cur=None;continue
  if 'https://' in line:continue
  arts[cur].append(line)
 want={str(n) for n in range(1,16)}|{'10bis'}
 if set(arts)!=want:raise ValueError(('apartment',set(arts)))
 result={k:clean('\n'.join(v)) for k,v in arts.items()}
 result['15']=result['15'].split('قانون بالا مشتمل',1)[0].strip()
 return result
def drop_lines(text,prefixes):return '\n'.join(x for x in text.splitlines() if not x.startswith(prefixes)).strip()
def main():
 l56=parse(CACHE/'landlord_tenant_1356.md',set(range(1,33)));l62=parse(CACHE/'landlord_tenant_1362.md',set(range(1,16)));l76=parse(CACHE/'landlord_tenant_1376.md',set(range(1,14)));lb=parse(CACHE/'landlord_tenant_bylaw_1378.md',set(range(1,21))-{16});lb[16]='ماده ۱۶ سابق به موجب اصلاحیه آیین‌نامه به ماده ۱۵ تغییر شماره یافت و ماده ۱۵ سابق حذف شد.'
 old_l76_2='قراردادهای عادی اجاره باید با قید مدت اجاره در دو نسخه تنظیم شود و به امضای موجر و مستأجر برسد و به وسیله دو نفر افراد مورد اعتماد طرفین به عنوان شهود گواهی گردد.'
 apt=apartment_law();aptb=parse(CACHE/'apartment_ownership_bylaw.md',set(range(1,28)));aptb16_old=aptb[16];aptb[16]='\n'.join(x for x in aptb[16].splitlines() if not x.startswith('تبصره ۲')).strip()
 pre=parse(CACHE/'building_presale_law.md',set(range(1,26)));pre_current=dict(pre)
 old_pre1='هر قراردادی با هر عنوان که به موجب آن مالک رسمی زمین (پیش‌فروشنده) متعهد به احداث یا تکمیل واحد ساختمانی مشخص در آن زمین شود و واحد ساختمانی مذکور با هر نوع کاربری از ابتدا یا در حین احداث و تکمیل یا پس از اتمام عملیات ساختمانی به مالکیت طرف دیگر قرارداد (پیش‌خریدار) درآید، از نظر مقررات این قانون قرارداد پیش‌فروش ساختمان محسوب می‌شود.\nتبصره ـ اشخاص زیر نیز می‌توانند در چهارچوب این قانون و قراردادی که به موجب آن زمینی در اختیارشان قرار می‌گیرد اقدام به پیش‌فروش ساختمان نمایند:\n۱ـ سرمایه‌گذارانی که در ازای سرمایه‌گذاری از طریق احداث بنا بر روی زمین متعلق به دیگری، واحدهای ساختمانی مشخصی از بنای احداثی ضمن عقد و به موجب سند رسمی به آنان اختصاص می‌یابد.\n۲ـ مستأجران اراضی اعم از ملکی، دولتی یا موقوفه که به موجب سند رسمی حق احداث بنا بر روی عین مستأجره را دارند.'
 old_pre2=pre[2].replace('۳- متن پروانه ساختمانی صادر شده از مراجع ذی صلاح در صورت صدور، راجع به موضوع معامله به عنوان پیوست قرارداد.','۳- اوصاف و امکانات واحد ساختمانی مورد معامله مانند مساحت اعیانی، تعداد اتاق‌ها، شماره طبقه، شماره واحد، توقفگاه (پارکینگ) و انباری.').replace('۱۱ ـ احکام مذکور در مواد (۶)، (۷) و (۸) و تبصره آن، (۹)، (۱۱)، (۱۲)، (۱۴)، (۱۶) این قانون','۱۱ ـ احکام مذکور در مواد (۶)، (۷) و (۸) و تبصره آن، (۹)، (۱۱)، (۱۲)، (۱۴)، (۱۶) و (۲۰) این قانون')
 if '۱۰ـ معرفی داوران' not in old_pre2:old_pre2=old_pre2+'\n۱۰ـ معرفی داوران.'
 old_pre2='\n'.join((line[:-len('این قانون')].rstrip()+' و (۲۰) این قانون') if line.startswith('۱۱') and line.endswith('این قانون') and '(۲۰)' not in line else line for line in old_pre2.splitlines())
 pre_current[2]=drop_lines(pre[2],('۱۰ـ معرفی داوران','۱۰- معرفی داوران'))
 pre_current[4]=drop_lines(pre[4],('۲ـ پروانه ساخت','۲- پروانه ساخت','۴ـ تأییدیه','۴- تأییدیه','تبصره ـ در مجموعه‌های احداثی'))
 preb=parse(CACHE/'building_presale_bylaw.md',set(range(1,23)));mandatory=parse(CACHE/'mandatory_real_estate_registration_1403.md',set(range(1,16)))
 vals={'LANDLORD_1356':tuple(l56.items()),'LANDLORD_1362':tuple(l62.items()),'LANDLORD_1376_CURRENT':tuple(l76.items()),'LANDLORD_1376_ART2_OLD':old_l76_2,'LANDLORD_BYLAW_1378':tuple(lb.items()),'APARTMENT_LAW':tuple(apt.items()),'APARTMENT_BYLAW_CURRENT':tuple(aptb.items()),'APARTMENT_BYLAW_ART16_OLD':aptb16_old,'PRESALE_PRE1403':tuple(pre.items()),'PRESALE_CURRENT':tuple(pre_current.items()),'PRESALE_ART1_OLD':old_pre1,'PRESALE_ART2_OLD':old_pre2,'PRESALE_BYLAW':tuple(preb.items()),'MANDATORY_REGISTRATION_1403':tuple(mandatory.items())}
 head='# -*- coding: utf-8 -*-\n"""Generated housing, tenancy, apartment and presale texts."""\n# Generated by scripts/build_housing_seeds.py.\n\n';OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] tenancy=32/15/13 + bylaw20; apartment=16 + bylaw27; presale=25 + bylaw22; mandatory registration=15')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
