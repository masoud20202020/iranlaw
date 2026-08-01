# -*- coding: utf-8 -*-
"""Build seeds for VAT, taxpayer terminal system, regulations and leading Divan rulings."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'vat_taxpayer.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def clean(s):
 s=re.sub(r'!\[[^]]*\]\([^)]+\)','',s);s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('\\-','-').replace('\ufeff','').replace('\u00ad','‌').replace('\u200e','‌').replace('\u200f','‌')
 # Frequent OCR defects in the original 1398 PDF and uniform Persian orthography.
 for a,b in {'ي':'ی','ك':'ک','ة':'ه','اطالعات':'اطلاعات','اصطالحات':'اصطلاحات','اصالحات':'اصلاحات','اصالح':'اصلاح','اسالمی':'اسلامی','اعالم':'اعلام','ابالغ':'ابلاغ','اقالم':'اقلام','معامالت':'معاملات','استعالم':'استعلام','الزم':'لازم','االجراء':'الاجرا','مشمو ل':'مشمول','صورتحساب':'صورت‌حساب','مودیان':'مؤدیان','مودی':'مؤدی','هیات':'هیأت','مسوول':'مسئول','موسسات':'مؤسسات','آئین':'آیین','ذی ربط':'ذی‌ربط','می باشد':'می‌باشد','می شود':'می‌شود','می گردد':'می‌گردد','می نماید':'می‌نماید','بموجب':'به موجب','بعهده':'به عهده','ما به التفاوت':'مابه‌التفاوت','لازم الاجرا':'لازم‌الاجرا','غیر تجاری':'غیرتجاری','کسب و کار':'کسب‌وکار','به صورت':'به‌صورت','می باشد':'می‌باشد'}.items():s=s.replace(a,b)
 s=s.replace('اطلاعات کارپوشه اطلاعات کارپوشه غیرتجاری','اطلاعات کارپوشه غیرتجاری').replace('کلیه اشخاص کلیه اشخاص غیرتجاری','کلیه اشخاص غیرتجاری').replace('را را ','را ')
 s=re.sub(r'(?m)^>\s?','',s);s=re.sub(r'(?m)^#{1,6}\s*.*$','',s);s=re.sub(r'\[ویرایش\][^\n]*','',s);s=re.sub(r'\[\]\([^)]*\)','',s)
 s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip(' \n-*')

def parse_seq(text,start,end,anchor=None,stop=None):
 if anchor:text=text.split(anchor,1)[1]
 if stop and stop in text:text=text.split(stop,1)[0]
 hits=[];pos=0
 for n in range(start,end+1):
  f=str(n).translate(A2F);a=str(n)
  # Handles «ماده۱»، «**ماده**۱» and ordinary headings, while excluding «ماده (۱)» references.
  pat=re.compile(r'(?<![\w(])(?:\*+)?[‌\s]*ماده(?:\*+)?[‌\s]*(?:'+re.escape(f)+'|'+a+r')(?![۰-۹0-9])[‌\s]*(?:\*+)?[‌\s]*(?:[-–ـ:)]+\s*)?',re.M)
  m=pat.search(text,pos)
  if not m:raise ValueError(f'missing article {n}')
  hits.append((str(n),m.start(),m.end()));pos=m.end()
 out={}
 for i,(k,st,en) in enumerate(hits):
  tail=hits[i+1][1] if i+1<len(hits) else len(text);body=text[en:tail]
  body=re.split(r'\n(?:قانون فوق|رئیس مجلس|معاون اول رئیس|### تازه|برچسب ها|انتهای پیام|منبع:)',body,maxsplit=1)[0]
  out[k]=clean(body)
  if not out[k]:raise ValueError('empty '+k)
 return out

def between(text,a,b):return clean(text.split(a,1)[1].split(b,1)[0])

def main():
 vat=parse_seq((CACHE/'vat_law_1400.md').read_text(),1,57,anchor='# قانون مالیات بر ارزش افزوده')
 vat['57']=vat['57'].split('محمدباقر قالیباف',1)[0].strip()
 vat7_base=vat['7'];vat26_base=vat['26']
 annual={
  '1403':vat7_base+'\n\nحکم نرخ سال ۱۴۰۳- به موجب قانون بودجه سال ۱۴۰۳، نرخ موضوع این ماده یک واحد درصد افزایش یافت و نرخ استاندارد ده درصد (۱۰٪) شد.',
  '1404':vat7_base+'\n\nحکم نرخ سال ۱۴۰۴- به موجب بند «خ» تبصره (۱) قانون بودجه سال ۱۴۰۴، نرخ موضوع این ماده یک واحد درصد افزایش یافت و نرخ استاندارد ده درصد (۱۰٪) شد.',
  '1405':vat7_base+'\n\nحکم نرخ سال ۱۴۰۵- به موجب ردیف (۳-۱-۶) الزامات منابع قانون بودجه سال ۱۴۰۵، نرخ موضوع این ماده یک واحد درصد افزایش یافت و نرخ استاندارد جاری ده درصد (۱۰٪) است.'}
 annual26={y:vat26_base+'\n\nحکم نرخ سال '+y+'- نرخ مالیات و جریمه موضوع بند «ب» این ماده به موجب قانون بودجه همان سال یک واحد درصد افزایش یافته و برای اجرت ساخت، حق‌العمل و سود فروشنده طلا، جواهر و پلاتین ده درصد (۱۰٪) است.' for y in ('۱۴۰۳','۱۴۰۴','۱۴۰۵')}
 oldvat=parse_seq((CACHE/'vat_law_1387.md').read_text(),1,53,anchor='مصوب 1387,02,17')
 oldvat['53']=oldvat['53'].split('قانون فوق مشتمل',1)[0].strip()

 curtxt=(CACHE/'tax_terminals_current_1404.md').read_text();origtext=(CACHE/'tax_terminals_original_1398.md').read_text()
 terminal=parse_seq(curtxt,1,29,anchor='## قانون پایانه‌های فروشگاهی')
 original=parse_seq(origtext,1,29,anchor='# قانون پااینه های فروشگاهی')
 # Bis provisions sit between base article headings and must have stable independent keys.
 terminal['14bis']=between(curtxt,'**ماده****۱۴****مکرر**','**ماده****۱۵')
 terminal['14']=between(curtxt,'**ماده****۱۴**','**ماده****۱۴****مکرر**').split('#### فصل',1)[0].strip()
 terminal['16bis']=between(curtxt,'**ماده ۱۶ مکرر**','**ماده****۱۷')
 terminal['16']=between(curtxt,'**ماده****۱۶****–**','**ماده ۱۶ مکرر**')
 terminal['29']=terminal['29'].split('قانون فوق مشتمل',1)[0].strip()
 # The direct PDF has OCR spacing but is the enacted 1398 text; obvious OCR defects are normalized by clean().
 original['29']=original['29'].split('قانون فوق مشتمل',1)[0].strip()

 facil=parse_seq((CACHE/'tax_facilitation_1402.md').read_text(),1,10,anchor='### قانون تسهیل تکالیف')
 facil['10']=facil['10'].split('قانون فوق مشتمل',1)[0].strip()
 spec=parse_seq((CACHE/'tax_speculation_1404.md').read_text(),1,28,anchor='## **قانون مالیات بر سوداگری')
 spec['28']=spec['28'].split('قانون فوق مشتمل',1)[0].strip()

 b14=parse_seq((CACHE/'terminal_bylaw_14bis_1403.md').read_text(),1,12,anchor='آیین‌نامه اجرایی ماده (۱۴) مکرر')
 b14['12']=b14['12'].split('محمدرضا عارف',1)[0].strip()
 b26=parse_seq((CACHE/'terminal_bylaw_26.md').read_text(),1,42,anchor='## **آیین‌ نامه موضوع ماده 26')
 b26['42']=b26['42'].split('سید احسان خاندوزی',1)[0].replace('[۲]','').strip()
 edu=parse_seq((CACHE/'vat_bylaw_education_1400.md').read_text(),1,3,anchor='## مصوب: 1400/10/28')
 edu['3']=edu['3'].split('معاون اول رئیس',1)[0].strip()
 inactive=parse_seq((CACHE/'vat_bylaw_inactive_1401.md').read_text(),1,6,anchor='## مصوبه شماره')
 inactive['6']=inactive['6'].split('معاون اول رئیس',1)[0].strip()

 r348='''مطابق بند (۱۰) ماده (۱۲) قانون مالیات بر ارزش افزوده مصوب ۱۳۸۷، خدمات مشمول مالیات بر درآمد حقوق موضوع قانون مالیات‌های مستقیم از پرداخت مالیات معاف است. با توجه به این حکم، ارائه خدمات مشمول مالیات بر حقوق به‌طور مطلق از مالیات معاف بوده و مقید نمودن آن به پرداخت‌کنندگان مستقیم و بی‌واسطه مغایر هدف و اراده مقنن است؛ لذا بند (۱۱) بخشنامه شماره ۲۸۰۰۴ مورخ ۱۳۸۸/۱۱/۱۲ معاونت مالیات بر ارزش افزوده سازمان امور مالیاتی کشور که برخلاف اطلاق حکم قانونی وضع شده، ابطال می‌شود.'''
 r2558='''الف- اطلاق مثال ذیل بند (۳) دستورالعمل شماره ۲۳۰/۱۰۰۱/د مورخ ۱۳۹۹/۱/۲۰ که به محض انجام هر پرداخت توسط کارفرما به پیمانکار، ولو آنکه بابت مالیات بر ارزش افزوده نباشد، برای اداره امور مالیاتی حق مطالبه مالیات بر ارزش افزوده در نظر گرفته بود، با بند «م» تبصره (۶) قانون بودجه سال ۱۳۹۹ مغایرت دارد و از تاریخ تصویب ابطال می‌شود.\nب- تا زمانی که کارفرما مالیات بر ارزش افزوده را به پیمانکار پرداخت نکرده باشد، سازمان امور مالیاتی حق اخذ جریمه دیرکرد ندارد؛ بنابراین اطلاق بند (۴) دستورالعمل در پیش‌بینی تعلق و مطالبه جرائم از پیمانکار از تاریخ تصویب ابطال می‌شود.\nج- تذکر (۲) بند (۴) دستورالعمل که سهم شهرداری‌ها از مالیات و عوارض ارزش افزوده را بدون دلیل قانونی از حکم بند «م» تبصره (۶) قانون بودجه سال ۱۳۹۹ مستثنی کرده بود، خلاف قانون و خارج از حدود اختیار است و از تاریخ تصویب ابطال می‌شود.'''
 rtapsi='''براساس ماده (۲) قانون مالیات بر ارزش افزوده مصوب ۱۴۰۰، اصل بر شمول عرضه کالاها و خدمات است و استثناهای آن در ماده (۹) مشخص شده است؛ اتخاذ اطلاق از موارد استثنا برخلاف اصول حقوقی است. خدمات متصدی حمل‌ونقل از خدمات مباشر حمل‌ونقل مجزاست و معافیت صرفاً به مباشر و درآمد حاصل از حمل تعلق می‌گیرد. در تاکسی‌های اینترنتی، بخش اصلی کرایه که در برابر جابه‌جایی مسافر به راننده تعلق می‌گیرد مشمول معافیت جزء (۱۳) بند «ب» ماده (۹) است، ولی سهم و کمیسیون دریافتی شرکت بابت خدمتی که به راننده ارائه می‌دهد مشمول مالیات است. بنابراین عبارت مورد اعتراض بخشنامه‌های سازمان امور مالیاتی در حدود قانون صادر شده و ابطال نشد. این رأی براساس ماده (۹۳) قانون دیوان عدالت اداری در رسیدگی و تصمیم‌گیری مراجع قضایی و اداری معتبر و ملاک عمل است.'''
 vals={'VAT_LAW':tuple((str(i),vat[str(i)]) for i in range(1,58)),'VAT_ART7_BASE':vat7_base,'VAT_ART7_ANNUAL':annual,'VAT_ART26_BASE':vat26_base,'VAT_ART26_ANNUAL':annual26,
       'VAT_OLD_1387':tuple((str(i),oldvat[str(i)]) for i in range(1,54)),
       'TERMINAL_LAW':tuple((k,terminal[k]) for k in [*map(str,range(1,15)),'14bis','15','16','16bis',*map(str,range(17,30))]),
       'TERMINAL_ORIGINAL':tuple((str(i),original[str(i)]) for i in range(1,30)),
       'FACILITATION_LAW':tuple((str(i),facil[str(i)]) for i in range(1,11)),
       'SPECULATION_TAX_LAW':tuple((str(i),spec[str(i)]) for i in range(1,29)),
       'TERMINAL_14BIS_BYLAW':tuple((str(i),b14[str(i)]) for i in range(1,13)),
       'TRUSTED_COMPANIES_BYLAW':tuple((str(i),b26[str(i)]) for i in range(1,43)),
       'VAT_EDUCATION_BYLAW':tuple((str(i),edu[str(i)]) for i in range(1,4)),
       'VAT_INACTIVE_WORKSPACE_BYLAW':tuple((str(i),inactive[str(i)]) for i in range(1,7)),
       'DIVAN_348':clean(r348),'DIVAN_2558':clean(r2558),'DIVAN_TAPSI':clean(rtapsi)}
 head='# -*- coding: utf-8 -*-\n"""Generated VAT, taxpayer terminal, regulations and Divan rulings."""\n# Generated by scripts/build_vat_taxpayer_seeds.py.\n\n'
 OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] VAT current=57; former VAT=53; terminals=31 keys; facilitation=10; speculation tax=28')
 print('[OK] regulations=12+42+3+6; Divan rulings=3')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
