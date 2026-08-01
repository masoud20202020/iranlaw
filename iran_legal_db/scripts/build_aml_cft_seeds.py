# -*- coding: utf-8 -*-
"""Build anti-money-laundering and counter-terrorist-financing seeds."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'aml_cft.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def clean(s):
 s=re.sub(r'!\[[^]]*\]\([^)]+\)','',s);s=re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('_','').replace('\\-','-').replace('\ufeff','').replace('\u200e','‌').replace('\u200f','‌').replace('\u00ad','‌')
 for a,b in {'ي':'ی','ك':'ک','ة':'ه','هیات':'هیأت','مسوول':'مسئول','مسؤول':'مسئول','موسسات':'مؤسسات','موسسه':'مؤسسه','آئین':'آیین','می باشد':'می‌باشد','می شود':'می‌شود','می گردد':'می‌گردد','می نماید':'می‌نماید','لازم الاجرا':'لازم‌الاجرا','ذی ربط':'ذی‌ربط','پول شویی':'پولشویی','تامین':'تأمین','ارباب رجوع':'ارباب‌رجوع','به صورت':'به‌صورت','کسب وکار':'کسب‌وکار','ن‌هاد':'نهاد','ساز و کار':'سازوکار','رییس':'رئیس','جرائم':'جرایم'}.items():s=s.replace(a,b)
 s=re.sub(r'(?m)^>\s?','',s);s=re.sub(r'(?m)^#{1,6}\s*.*$','',s);s=re.sub(r'\[\]\([^)]*\)','',s);s=re.sub(r'(?m)^\s*\*\s*\*\s*\*\s*$','',s)
 s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip(' ‌\n-*')
def norm(l):return re.sub(r'\s+',' ',re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',l).replace('*','').replace('_','').replace('‌',' ').replace('ـ','-')).strip()
def all_heads(path):
 out=[]
 for i,l in enumerate(path.read_text().splitlines()):
  m=re.match(r'^ماده\s*([۰-۹0-9]+)(?:\s*(مکرر))?\s*(?:\([^)]*\))?\s*[-–]?',norm(l))
  if m:out.append((i,str(int(m.group(1).translate(F2A)))+('bis' if m.group(2) else '')))
 return out
def parse_keys(path,expected=None,first_only=False):
 lines=path.read_text().splitlines();heads=all_heads(path);out={};seen=set()
 for idx,(begin,key) in enumerate(heads):
  if first_only and key in seen:continue
  if key in seen and not first_only:raise ValueError(f'duplicate heading {path.name}:{key}')
  seen.add(key);finish=heads[idx+1][0] if idx+1<len(heads) else len(lines);body=clean('\n'.join(lines[begin:finish]))
  body=re.sub(r'^ماده[‌\s]*[۰-۹]+[‌\s]*(?:مکرر)?\s*(?:\([^\n]*?\))?\s*[-–ـ]?\s*','',body,count=1)
  for term in ('قانون فوق مشتمل','معاون اول رئیس جمهور','رئیس مجلس','انتهای پیام','### تازه','مطالب مرتبط'):
   if term in body:body=body.split(term,1)[0].strip()
  out[key]=body
 if expected is not None and set(out)!=set(expected):raise ValueError(f'coverage {path.name}: missing={set(expected)-set(out)} extra={set(out)-set(expected)}')
 return out
def parse_seq(path,end):return parse_keys(path,{str(i) for i in range(1,end+1)})
def parse_first_law(path,end):
 # Source may append an implementing bylaw with repeated article numbers; keep the first law occurrence.
 lines=path.read_text().splitlines();heads=all_heads(path);out={}
 for idx,(begin,key) in enumerate(heads):
  if key not in {str(i) for i in range(1,end+1)} or key in out:continue
  finish=heads[idx+1][0] if idx+1<len(heads) else len(lines);body=clean('\n'.join(lines[begin:finish]));body=re.sub(r'^ماده[‌\s]*[۰-۹]+\s*[-–ـ]?\s*','',body,count=1);body=body.split('قانون فوق مشتمل',1)[0].strip();out[key]=body
 if set(out)!={str(i) for i in range(1,end+1)}:raise ValueError('first law coverage '+path.name)
 return out
def top_clauses(path,end):
 lines=path.read_text().splitlines();hits=[];pos=0
 for n in range(1,end+1):
  found=None
  for i in range(pos,len(lines)):
   x=norm(lines[i]);m=re.match(r'^([۰-۹0-9]+)\s*[-–]\s*(?=(?:بند|ماده|مواد|تبصره|متن|متون|در\s|عنوان|شماره))',x)
   if m and int(m.group(1).translate(F2A))==n:found=i;break
  if found is None:raise ValueError(f'missing top clause {n} in {path.name}')
  hits.append((n,found));pos=found+1
 out=[]
 for j,(n,b) in enumerate(hits):
  e=hits[j+1][1] if j+1<len(hits) else len(lines);t=clean('\n'.join(lines[b:e]));t=re.sub(r'^[۰-۹]+\s*[-–]\s*','',t,count=1);t=t.split('محمدرضا عارف',1)[0].replace('\nمعاون اول رئیس جمهور-','').strip();out.append((str(n),t))
 return tuple(out)
def cft_amendment():
 lines=(CACHE/'cft_amendment_1397.md').read_text().splitlines();hits=[];pos=0
 starts={1:'ماده (۱) قانون',2:'ماده (۲) قانون',3:'متن ذیل',4:'ماده (۱۰) قانون',5:'تبصره (۱) ماده'}
 for n in range(1,6):
  for i in range(pos,len(lines)):
   x=norm(lines[i])
   if re.match(r'^ماده\s*'+str(n).translate(A2F)+r'\s*[-–]',x) and starts[n] in x:hits.append((n,i));pos=i+1;break
  else:raise ValueError('cft amendment '+str(n))
 out=[]
 for j,(n,b) in enumerate(hits):
  e=hits[j+1][1] if j+1<len(hits) else len(lines);t=clean('\n'.join(lines[b:e]));t=re.sub(r'^ماده[‌\s]*[۰-۹]+\s*[-–ـ]\s*','',t,count=1);t=t.split('قانون فوق مشتمل',1)[0].strip();out.append((str(n),t))
 return tuple(out)
def accession_act():
 s=(CACHE/'cft_convention_accession_1404.md').read_text();s=s.split('**ماده واحده-**',1)[1].split('بسم الله الرحمن الرحیم',1)[0];return clean(s)
FIU_BYLAW=(
 ('1','''در این آیین‌نامه، اصطلاحات زیر در معانی مشروح مربوط به کار می‌روند:\n۱- قانون: قانون مبارزه با پولشویی مصوب ۱۳۸۶ و اصلاحات بعدی آن.\n۲- شورای عالی: شورای عالی مقابله و پیشگیری از جرایم پولشویی و تأمین مالی تروریسم موضوع ماده (۴) قانون.\n۳- رئیس شورای عالی: وزیر امور اقتصادی و دارایی موضوع ماده (۴) قانون.\n۴- دبیرخانه: دبیرخانه شورای عالی.\n۵- مرکز: مرکز اطلاعات مالی موضوع قانون.'''),
 ('2','مرکز مؤسسه دولتی تابع وزارت امور اقتصادی و دارایی و دارای استقلال اداری و مالی است.'),
 ('3','''رئیس مرکز از میان افراد دارای حداقل مدرک کارشناسی ارشد و ده سال سابقه مدیریتی یا قضایی مرتبط و با رأی حداقل دو سوم اعضای شورای عالی و با حکم رئیس شورای عالی به این سمت منصوب می‌گردد. دوره ریاست چهار سال و تجدید آن برای یک‌بار مجاز است.\nتبصره ۱- رئیس مرکز مدیریت کلیه فعالیت‌های مرکز و دبیرخانه شورای عالی را بر عهده دارد. سطح سازمانی رئیس مرکز، معاون وزیر خواهد بود.\nتبصره ۲- کلیه کارکنان مرکز توسط رئیس مرکز تعیین می‌شوند.\nتبصره ۳- تشکیلات تفصیلی مرکز و اصلاحات آن در چهارچوب این آیین‌نامه به پیشنهاد رئیس مرکز به تصویب رئیس شورای عالی می‌رسد.\nتبصره ۴- در صورت نیاز، به پیشنهاد رئیس مرکز و تصویب رئیس شورای عالی، واحد اطلاعات مالی در مراکز استان‌ها تشکیل خواهد شد.'''),
 ('4','''با هدف پیشگیری و مقابله با پولشویی و تأمین مالی تروریسم در کشور، وظایف و اختیارات مرکز به شرح زیر است:\n۱- دریافت، گردآوری، نگهداری و تجزیه و تحلیل و ارزیابی اطلاعات و بررسی معاملات و عملیات مشکوک به پولشویی و تأمین مالی تروریسم.\n۲- ردیابی وجوه و انتقال اموال با رعایت ضوابط قانونی و گزارش معاملات و عملیات مشکوک به پولشویی و تأمین مالی تروریسم.\n۳- بررسی و ارزیابی نحوه تحصیل و مشروعیت دارایی‌ها و عملیات مشکوک اشخاص در گزارش‌های واصله و ارسال آنها به مراجع ذی‌صلاح قضایی در مواردی که به احتمال قوی صحت دارد و یا محتمل آن از اهمیت برخوردار است.\n۴- توقیف و جلوگیری از نقل و انتقال وجوه یا اموال مشکوک به پولشویی و تأمین مالی تروریسم به ترتیب مقرر در تبصره (۱) ماده (۷) مکرر قانون.\n۵- تدوین آیین‌نامه‌های مربوط به روش‌ها و مصادیق گزارش معاملات مشکوک و اعمال موضوع قانون و قانون مبارزه با تأمین مالی تروریسم مصوب ۱۳۹۵ و اصلاحات بعدی آن و ارجاع به مراجع ذی‌ربط جهت تصویب در هیأت وزیران.\n۶- همکاری با اشخاص، سازمان‌ها، نهادها یا دستگاه‌های دولتی و سازمان‌های مردم‌نهاد که در زمینه مبارزه با پولشویی و تأمین مالی تروریسم فعالیت می‌کنند.\n۷- تهیه برنامه‌های آموزشی در زمینه آثار زیانبار پولشویی و تأمین مالی تروریسم، شیوه‌های متداول در انجام جرایم مذکور و ابزارهای پیشگیری از آن.\n۸- پیگیری ایجاد کارگروه ملی ارزیابی خطرپذیری و تهیه برنامه اقدام مبتنی بر آن.\n۹- نظارت، ارزیابی و رتبه‌بندی اشخاص مشمول.\n۱۰- بررسی صلاحیت حرفه‌ای مسئولان واحدهای مبارزه با پولشویی.\n۱۱- همکاری و تبادل اطلاعات با مراکز مشابه خارجی و مجامع بین‌المللی طبق قانون.\n۱۲- تهیه اصول راهنما و ارائه مشاوره به اشخاص مشمول.\n۱۳- تهیه گزارش اقدامات و پیشنهادهای مربوط به شورای عالی و شورای عالی پیشگیری از وقوع جرم.\n۱۴- نظارت و پیگیری مصوبات شورای عالی تا حصول نتیجه.\n۱۵- ردیابی اشخاص حقیقی یا حقوقی مرتبط با جرایم پولشویی و تأمین مالی تروریسم در خارج از کشور.\n۱۶- اعمال نظارت لازم بر کلیه اشخاص مشمول و تهیه گزارش‌های نظارتی.\n۱۷- درخواست و اخذ اطلاعات مورد نیاز از اشخاص موضوع مواد (۵) و (۶) قانون.\n۱۸- استعلام برخط اطلاعات تکمیلی مرتبط با معاملات و تراکنش‌های مالی مشکوک.\n۱۹- دسترسی به سامانه‌های جامع اطلاعات هویتی و اقتصادی اشخاص.\n۲۰- برنامه‌ریزی و تمهید مالی، حقوقی، اداری و استخدامی برای حمایت از کارکنان مرکز.\n۲۱- طراحی و استقرار نظام جامع آمار و اطلاعات درخصوص آرای قضایی، سوابق اشخاص و اموال مسدود یا توقیف‌شده.\n۲۲- انجام اقدامات مقتضی جهت انعقاد یادداشت تفاهم با سایر کشورها.\n۲۳- امکان استفاده از کمک‌های فنی سازمان‌های بین‌المللی مرتبط.\n۲۴- حضور فعال در مجامع بین‌المللی و دفاع از مواضع جمهوری اسلامی ایران.\n۲۵- اجرای سیاست‌ها و تصمیمات شورای عالی و اداره امور دبیرخانه‌ای آن.\n۲۶- انجام سایر وظایف محوله از سوی شورای عالی در چهارچوب قانون و قانون مبارزه با تأمین مالی تروریسم.'''),
 ('5','''در استخدام و به‌کارگیری نیروی انسانی در مرکز، رعایت شرایط عمومی قوانین ذی‌ربط و تبصره (۲) ماده (۷) مکرر قانون الزامی است.\nتبصره ۱- تمام مشاغل سازمانی مرکز و واحدهای زیرمجموعه آن در زمره مشاغل حساس است.\nتبصره ۲- مرکز مشمول افزایش امتیازات و فوق‌العاده‌های مواد مرتبط قانون مدیریت خدمات کشوری است.'''),
 ('6','''دبیرخانه در مرکز مستقر خواهد بود و صرفاً انجام وظایف دبیرخانه‌ای زیر را تحت نظر دبیر شورای عالی بر عهده خواهد داشت:\n۱- برنامه‌ریزی و انجام کلیه امور اداری دبیرخانه‌ای و کارشناسی مورد نیاز شورای عالی از جمله برنامه‌ریزی برای برگزاری جلسات، تهیه و تنظیم دستور جلسات، تنظیم و ابلاغ مصوبات و ارائه گزارش نتایج به شورای عالی.\n۲- تهیه گزارش از نحوه اقدامات اشخاص مشمول نسبت به مصوبات شورای عالی جهت ارائه به مسئولان ذی‌ربط.\n۳- تهیه آیین‌نامه‌ها، دستورالعمل‌ها و ضوابط اجرایی لازم جهت هماهنگی و هدایت دستگاه‌های ذی‌ربط در امر مبارزه با پولشویی و تأمین مالی تروریسم و پیگیری اجرای کامل قانون.\n۴- تدوین و پیشنهاد راهبردهای مقتضی درخصوص اجرای قانون برای بررسی و تصویب به شورا.\n۵- تهیه و پیشنهاد پیش‌نویس آیین‌نامه‌های لازم درخصوص اجرای قانون با همکاری کارگروهی متشکل از نمایندگان سازمان‌های عضو شورا برای تصویب به هیأت وزیران.\nتبصره ۱- رئیس مرکز، دبیر شورای عالی است.\nتبصره ۲- ساختار داخلی دبیرخانه متناسب با حجم فعالیت‌ها در تشکیلات تفصیلی مرکز پیش‌بینی می‌گردد.\nتبصره ۳- گزارش‌های موضوع این ماده جهت ارائه به شورای عالی از طریق رئیس مرکز و به وسیله واحدهای ذی‌ربط اجرایی مرکز تهیه می‌شود.\nتبصره ۴- پرداخت حق جلسه برای اعضای شورای عالی و کارگروه‌های کارشناسی در چهارچوب قوانین و مقررات مربوط خواهد بود.'''),
 ('7','کلیه دستگاه‌های اجرایی، قوای سه‌گانه و نیروهای نظامی و انتظامی در صورت درخواست مرکز مکلفند در راستای تأمین کارکنان مرکز همکاری لازم را داشته باشند.'),
 ('8','سازمان برنامه و بودجه کشور مکلف است بودجه مورد نیاز مرکز را در لوایح بودجه سنواتی به‌صورت ردیف مستقل منظور نماید.'),)
def main():
 curaml=parse_keys(CACHE/'aml_law_current.md',{*map(str,range(1,15)),'7bis'});origaml=parse_first_law(CACHE/'aml_law_original_1386.md',12)
 amlrows=[];changed={*map(str,range(1,10)),'11'}
 for key in sorted(curaml,key=lambda k:(int(k.removesuffix('bis')),k.endswith('bis'))):
  no=str(int(key.removesuffix('bis'))).translate(A2F)+(' مکرر' if key.endswith('bis') else '')
  if key in changed:amlrows.append({'key':key,'article_no':no,'version_no':1,'is_current':False,'effective_date':'2008-01-22','expiry_date':'2019-01-05','text':origaml[key],'notes':'متن پیش از اصلاح جامع ۱۳۹۷.'});v=2
  else:v=1
  amlrows.append({'key':key,'article_no':no,'version_no':v,'is_current':True,'effective_date':'2019-01-05' if key in changed or key in {'7bis','13','14'} else '2008-01-22','expiry_date':None,'text':curaml[key],'notes':'نسخه جاری اصلاحی ۱۳۹۷.' if v==2 or key in {'7bis','13','14'} else None})
 amlby=parse_keys(CACHE/'aml_bylaw_current_1404.md',{*map(str,range(1,165)),'9bis','27bis','150bis','152bis'})
 oldby=parse_seq(CACHE/'aml_old_bylaw_1388.md',49)
 cftcur=parse_seq(CACHE/'cft_law_current.md',17);cftold=parse_seq(CACHE/'cft_law_original_1394.md',17);cftchanged={'1','2','5','10','14'};cftrows=[]
 for key in map(str,range(1,18)):
  if key in cftchanged:cftrows.append({'key':key,'article_no':key.translate(A2F),'version_no':1,'is_current':False,'effective_date':'2016-02-02','expiry_date':'2018-08-01','text':cftold[key],'notes':'متن پیش از اصلاح ۱۳۹۷.'});v=2
  else:v=1
  cftrows.append({'key':key,'article_no':key.translate(A2F),'version_no':v,'is_current':True,'effective_date':'2018-08-01' if key in cftchanged else '2016-02-02','expiry_date':None,'text':cftcur[key],'notes':'نسخه جاری اصلاحی ۱۳۹۷.' if v==2 else None})
 oldcft=parse_seq(CACHE/'cft_old_bylaw_1396.md',30)
 targeted=parse_keys(CACHE/'cft_targeted_bylaw_1404.md',{*map(str,range(1,32))},first_only=True)
 # Remove the embedded editorial quotation of former item 8 from current article 1.
 targeted['1']=re.sub(r'\nمتن سابق بند ۸-.*?(?=\n۹-)','',targeted['1'],flags=re.S)
 # Article 31 is repealed; keep its former substantive text only.
 former31=targeted['31'];m=re.search(r'متن ماده ۳۱ سابق[^-]*-\s*(.*)',former31,re.S);former31=clean(m.group(1) if m else former31)
 targetrows=[]
 for key in map(str,range(1,31)):
  targetrows.append({'key':key,'article_no':key.translate(A2F),'version_no':1,'is_current':True,'effective_date':'2026-06-21' if key in {'1','2'} else '2025-11-12','expiry_date':None,'text':targeted[key],'notes':'نسخه جاری پس از اصلاح ۱۴۰۵/۰۳/۳۱.' if key in {'1','2'} else None})
 targetrows.append({'key':'31','article_no':'۳۱','version_no':1,'is_current':False,'effective_date':'2026-02-22','expiry_date':'2026-06-21','text':former31,'notes':'ماده الحاقی ۱۴۰۴/۱۲/۰۳ که در اصلاح ۱۴۰۵/۰۳/۳۱ نسخ شد.'})
 vals={'AML_LAW_ROWS':tuple(amlrows),'AML_AMENDMENT_1397':tuple(parse_seq(CACHE/'aml_amendment_1397.md',13).items()),'AML_BYLAW_CURRENT':tuple(amlby.items()),'AML_BYLAW_AMENDMENT_1404':top_clauses(CACHE/'aml_bylaw_amendment_1404.md',57),'AML_OLD_BYLAW':tuple(oldby.items()),'CFT_LAW_ROWS':tuple(cftrows),'CFT_AMENDMENT_1397':cft_amendment(),'CFT_OLD_BYLAW':tuple(oldcft.items()),'TARGETED_FINANCIAL_ROWS':tuple(targetrows),'FIU_BYLAW':tuple((k,clean(t)) for k,t in FIU_BYLAW),'CFT_ACCESSION_ACT':accession_act()}
 head='# -*- coding: utf-8 -*-\n"""Generated AML/CFT law and regulation package."""\n# Generated by scripts/build_aml_cft_seeds.py.\n\n';OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] AML law=15 keys/25 rows; amendment=13; current bylaw=168; amendment=57; old bylaw=49 historical')
 print('[OK] CFT law=17 keys/22 rows; amendment=5; old bylaw=30 historical; targeted bylaw=31 rows; FIU=8; accession=1')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
