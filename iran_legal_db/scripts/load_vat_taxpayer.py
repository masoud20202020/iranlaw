# -*- coding: utf-8 -*-
"""Load VAT, taxpayer terminal system, key regulations and Divan rulings."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from vat_taxpayer import *
QV='QMAF-1400';QVO='QMAF-1387';QT='QPSM-1398';QF='QTTM-1402';QS='QMS-1404';B14='AIM14-1403';B26='AIM26-1401';BE='AIM9-1400';BI='AIKP-1401';D348='DAD-348-1397';D2558='DAD-2558-1400';DTAP='DAD-2432139-1403'
REFS=(QV,QVO,QT,QF,QS,B14,B26,BE,BI,D348,D2558,DTAP)
DV='2021-05-23';DVE='2022-01-03';DVO='2008-05-06';DVOE='2008-09-22';DT='2019-10-13';DTE='2019-11-02';DF='2023-11-14';DFE='2023-12-21';DS='2025-06-29';DSE='2025-08-16';D1401='2022-09-21';D1402='2023-11-14';D1403='2024-03-20';D1404='2025-03-21';D1405='2026-03-21'
SRC_V='قانون مالیات بر ارزش افزوده مصوب ۱۴۰۰/۰۳/۰۲؛ متن کامل ۵۷ ماده از شناسنامه قانون و روزنامه رسمی، همراه احکام نرخ سالانه تا بودجه ۱۴۰۵.'
SRC_VO='قانون آزمایشی مالیات بر ارزش افزوده مصوب ۱۳۸۷/۰۲/۱۷؛ متن کامل ۵۳ ماده؛ از ۱۴۰۰/۱۰/۱۳ منسوخ و صرفاً تاریخی.'
SRC_T='قانون پایانه‌های فروشگاهی و سامانه مؤدیان مصوب ۱۳۹۸/۰۷/۲۱، متن تلفیقی با اصلاحات ۱۴۰۱، ۱۴۰۲ و قانون مالیات بر سوداگری و سفته‌بازی ۱۴۰۴؛ مقابله با PDF متن اولیه ۱۳۹۸.'
SRC_F='قانون تسهیل تکالیف مؤدیان جهت اجرای قانون پایانه‌های فروشگاهی و سامانه مؤدیان مصوب ۱۴۰۲/۰۸/۲۳؛ متن کامل ده ماده.'
SRC_S='قانون مالیات بر سوداگری و سفته‌بازی مصوب ۱۴۰۴/۰۴/۰۸؛ متن کامل ۲۸ ماده؛ اجرای مالیات عایدی سرمایه تابع استقرار بستر ماده ۱۶ مکرر است.'
SRC_B14='آیین‌نامه اجرایی ماده ۱۴ مکرر قانون پایانه‌های فروشگاهی و سامانه مؤدیان مصوب ۱۴۰۳/۱۰/۱۲؛ متن کامل ۱۲ ماده.'
SRC_B26='آیین‌نامه موضوع ماده ۲۶ قانون پایانه‌های فروشگاهی و سامانه مؤدیان، شماره ۵۱۰۹۱ مورخ ۱۴۰۱/۰۳/۲۲ با الحاق تبصره ماده ۱۶؛ متن کامل ۴۲ ماده.'
SRC_BE='آیین‌نامه اجرایی جزء ۱۴ بند ب ماده ۹ قانون مالیات بر ارزش افزوده مصوب ۱۴۰۰/۱۰/۲۸؛ متن کامل سه ماده.'
SRC_BI='آیین‌نامه غیرفعال نمودن کارپوشه مؤدیان موضوع تبصره ماده ۲۴ قانون مالیات بر ارزش افزوده مصوب ۱۴۰۱/۰۶/۱۳؛ متن کامل شش ماده.'
SRC_D='قسمت رأی دادنامه هیأت عمومی دیوان عدالت اداری.'

def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,atype,status,rat,eff,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute('insert into authorities(name_fa,authority_type)values(?,?)',(auth,atype)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags,topics=('حقوق مالیاتی','حقوق تجاری')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,key,no,text,v=1,cur=True,eff=None,exp=None,src=None,note=None):return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def rows(c,d,ref,data,date,src,current=True):
 o={}
 for k,t in data:o[k]=av(c,d,ref,k,pn(k),t,cur=current,eff=date,exp=None if current else DVE,src=src)
 return o

def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  specs=(
   (QV,'قانون مالیات بر ارزش افزوده با نرخ جاری سال ۱۴۰۵','قانون دائمی مالیات بر ارزش افزوده','law','مجلس شورای اسلامی','legislative','amended',DV,DVE,'متن کامل ۵۷ ماده؛ مواد ۷ و ۲۶ دارای چهار نسل نرخ پایه و احکام بودجه ۱۴۰۳ تا ۱۴۰۵؛ نرخ استاندارد جاری ۱۰٪.'),
   (QVO,'قانون مالیات بر ارزش افزوده مصوب ۱۳۸۷ (منسوخ)','قانون آزمایشی ارزش افزوده ۱۳۸۷','law','کمیسیون اقتصادی مجلس شورای اسلامی','legislative','abrogated',DVO,DVOE,'متن کامل ۵۳ ماده، همگی تاریخی؛ با اجرای قانون دائمی در ۱۴۰۰/۱۰/۱۳ منسوخ شد.'),
   (QT,'قانون پایانه‌های فروشگاهی و سامانه مؤدیان با اصلاحات تا ۱۴۰۴','قانون سامانه مؤدیان','law','مجلس شورای اسلامی','legislative','amended',DT,DTE,'۳۱ کلید ساختاری: مواد ۱ تا ۲۹، ماده ۱۴ مکرر و ماده ۱۶ مکرر؛ ۱۷ ماده دارای تاریخچه پیش از اصلاحات ۱۴۰۱ تا ۱۴۰۴.'),
   (QF,'قانون تسهیل تکالیف مؤدیان جهت اجرای قانون پایانه‌های فروشگاهی و سامانه مؤدیان','قانون تسهیل تکالیف مؤدیان','amendment','مجلس شورای اسلامی','legislative','amended',DF,DFE,'متن کامل ده ماده؛ برخی احکام گذار آن تا پایان ۱۴۰۳ یا ۱۴۰۵ محدود شده‌اند.'),
   (QS,'قانون مالیات بر سوداگری و سفته‌بازی','قانون مالیات بر سوداگری','amendment','مجلس شورای اسلامی','legislative','in_force',DS,DSE,'متن کامل ۲۸ ماده اصلاحی قانون پایانه‌ها و قانون مالیات‌های مستقیم؛ وصول مالیات عایدی سرمایه منوط به استقرار بستر اجرایی است.'),
   (B14,'آیین‌نامه اجرایی ماده ۱۴ مکرر قانون پایانه‌های فروشگاهی و سامانه مؤدیان','آیین‌نامه مؤدیان معاف از صورتحساب','regulation','هیأت وزیران','executive','in_force','2025-01-01','2025-01-01','متن کامل ۱۲ ماده درباره تعیین مالیات مؤدیان معاف از صدور صورتحساب الکترونیکی.'),
   (B26,'آیین‌نامه موضوع ماده ۲۶ قانون پایانه‌های فروشگاهی و سامانه مؤدیان','آیین‌نامه شرکت‌های معتمد مالیاتی','regulation','وزیر امور اقتصادی و دارایی','executive','amended','2022-06-12','2022-06-12','متن کامل ۴۲ ماده درباره مجوز، تعهدات، نظارت و لغو مجوز شرکت‌های معتمد؛ جایگزین آیین‌نامه ۱۳۹۹.'),
   (BE,'آیین‌نامه اجرایی جزء ۱۴ بند ب ماده ۹ قانون مالیات بر ارزش افزوده','آیین‌نامه معافیت خدمات آموزشی و ورزشی','regulation','هیأت وزیران','executive','in_force','2022-01-18','2022-01-18','متن کامل سه ماده درباره معافیت خدمات آموزشی، پژوهشی و ورزشی دارای مجوز.'),
   (BI,'آیین‌نامه غیرفعال نمودن کارپوشه مؤدیان','آیین‌نامه غیرفعال‌سازی کارپوشه','regulation','هیأت وزیران','executive','in_force','2022-09-04','2022-09-04','متن کامل شش ماده موضوع تبصره ماده ۲۴ قانون ارزش افزوده.'),
   (D348,'دادنامه شماره ۳۴۸ هیأت عمومی دیوان عدالت اداری درباره مالیات قراردادهای تأمین نیروی انسانی','دادنامه ۳۴۸ ـ حقوق و دستمزد','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force','2018-05-22','2018-05-22','ابطال قید پرداخت مستقیم در معافیت بخش حقوق و دستمزد قراردادهای تأمین نیروی انسانی.'),
   (D2558,'دادنامه شماره ۲۵۵۸ هیأت عمومی دیوان عدالت اداری درباره ارزش افزوده پیمانکاران دولتی','دادنامه ۲۵۵۸ ـ پیمانکاران','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force','2021-12-21','2021-12-21','ابطال سه بخش دستورالعمل مطالبه اصل و جرایم پیش از پرداخت مالیات ارزش افزوده توسط کارفرمای دولتی.'),
   (DTAP,'دادنامه شماره ۱۴۰۳۳۱۳۹۰۰۰۲۴۳۲۱۳۹ درباره مالیات بر ارزش افزوده تاکسی‌های اینترنتی','دادنامه تاکسی اینترنتی و ارزش افزوده','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force','2024-12-31','2024-12-31','عدم ابطال مقررات؛ تفکیک کرایه معاف راننده از کمیسیون مشمول مالیات شرکت تاکسی اینترنتی.'),
  )
  for ref,title,short,typ,auth,atype,status,rat,eff,note in specs:docs[ref]=up(c,ref,title,short,typ,auth,atype,status,rat,eff,note)
  for d in docs.values():clear(c,d)
  deco(c,docs[QV],('مالیات بر ارزش افزوده','اعتبار مالیاتی','معافیت مالیاتی','نرخ ده درصد','طلا','عوارض سبز','صادرات'))
  deco(c,docs[QVO],('قانون منسوخ','ارزش افزوده آزمایشی','تاریخچه مالیاتی'))
  deco(c,docs[QT],('سامانه مؤدیان','پایانه فروشگاهی','صورتحساب الکترونیکی','کارپوشه تجاری','حساب تجاری','حافظه مالیاتی'))
  deco(c,docs[QF],('تسهیل تکالیف','حد مجاز فروش','مؤدیان معاف','بخشودگی جرایم'))
  deco(c,docs[QS],('مالیات بر عایدی سرمایه','سوداگری','سفته‌بازی','رمزارز','طلا','املاک','خودرو'))
  deco(c,docs[B14],('ماده ۱۴ مکرر','کاربرگ مالیات','معافیت صورتحساب'))
  deco(c,docs[B26],('شرکت معتمد مالیاتی','مجوز فعالیت','محرمانگی اطلاعات'))
  deco(c,docs[BE],('خدمات آموزشی','خدمات پژوهشی','خدمات ورزشی','معافیت'))
  deco(c,docs[BI],('غیرفعال‌سازی کارپوشه','مسدودسازی کارتخوان','تعطیلی کسب‌وکار'))
  for ref,tags in ((D348,('تأمین نیروی انسانی','حقوق و دستمزد')),(D2558,('پیمانکار دولتی','اسناد خزانه','جریمه دیرکرد')),(DTAP,('تاکسی اینترنتی','کمیسیون','حمل‌ونقل'))):deco(c,docs[ref],tags,('حقوق مالیاتی','حقوق اداری'))
  # Permanent VAT law; annual budget rates are versions, not a silent rewrite of the permanent 9% base.
  vat=dict(VAT_LAW);vid={};vh={}
  for n in range(1,58):
   k=str(n);no=pn(n)
   if n==7:
    vh['7-1']=av(c,docs[QV],QV,k,no,VAT_ART7_BASE,1,False,DVE,D1403,SRC_V,'نرخ پایه دائمی ۹٪ پیش از حکم بودجه ۱۴۰۳.')
    vh['7-2']=av(c,docs[QV],QV,k,no,VAT_ART7_ANNUAL['1403'],2,False,D1403,D1404,SRC_V,'نرخ ۱۰٪ برای سال ۱۴۰۳.')
    vh['7-3']=av(c,docs[QV],QV,k,no,VAT_ART7_ANNUAL['1404'],3,False,D1404,D1405,SRC_V,'نرخ ۱۰٪ برای سال ۱۴۰۴.')
    vid[k]=av(c,docs[QV],QV,k,no,VAT_ART7_ANNUAL['1405'],4,True,D1405,None,SRC_V,'نرخ استاندارد جاری سال ۱۴۰۵ برابر ۱۰٪؛ حکم بودجه‌ای و نه اصلاح دائمی عدد ۹٪ ماده.')
   elif n==26:
    vh['26-1']=av(c,docs[QV],QV,k,no,VAT_ART26_BASE,1,False,DVE,D1403,SRC_V,'نرخ پایه ۹٪ بند ب پیش از احکام بودجه‌ای.')
    vh['26-2']=av(c,docs[QV],QV,k,no,VAT_ART26_ANNUAL['۱۴۰۳'],2,False,D1403,D1404,SRC_V,'نرخ ۱۰٪ بند ب برای سال ۱۴۰۳.')
    vh['26-3']=av(c,docs[QV],QV,k,no,VAT_ART26_ANNUAL['۱۴۰۴'],3,False,D1404,D1405,SRC_V,'نرخ ۱۰٪ بند ب برای سال ۱۴۰۴.')
    vid[k]=av(c,docs[QV],QV,k,no,VAT_ART26_ANNUAL['۱۴۰۵'],4,True,D1405,None,SRC_V,'نرخ جاری ۱۰٪ اجرت، حق‌العمل و سود فروش طلا در سال ۱۴۰۵؛ اصل طلا معاف است.')
   else:vid[k]=av(c,docs[QV],QV,k,no,vat[k],eff=DVE,src=SRC_V)
  oldids=rows(c,docs[QVO],QVO,VAT_OLD_1387,DVOE,SRC_VO,current=False)
  # Taxpayer terminal law with material pre-amendment history.
  term=dict(TERMINAL_LAW);orig=dict(TERMINAL_ORIGINAL);tids={};th={}
  changed={1:DSE,2:DSE,3:DSE,5:DSE,6:D1402,10:DSE,11:DSE,12:DSE,13:DSE,14:DSE,15:D1401,19:DSE,20:DSE,22:DSE,25:DSE,26:D1402,29:DSE}
  keys=[*map(str,range(1,15)),'14bis','15','16','16bis',*map(str,range(17,30))]
  for k in keys:
   no=(pn(k[:-3])+' مکرر') if k.endswith('bis') else pn(k);eff=D1402 if k=='14bis' else DSE if k=='16bis' else DTE
   if k.isdigit() and int(k) in changed:
    th[k]=av(c,docs[QT],QT,k,no,orig[k],1,False,DTE,changed[int(k)],SRC_T,'متن مصوب ۱۳۹۸ پیش از اصلاح؛ نسل میانی برخی اصلاحات ۱۴۰۲ جداگانه materialize نشده است.')
    tids[k]=av(c,docs[QT],QT,k,no,term[k],2,True,changed[int(k)],None,SRC_T,'نسخه جاری تلفیقی تا اصلاحات ۱۴۰۴.')
   else:tids[k]=av(c,docs[QT],QT,k,no,term[k],eff=eff,src=SRC_T,note='حکم جدید ۱۴۰۴؛ آغاز برخی تکالیف و وصول مالیات عایدی سرمایه منوط به انقضای مهلت و استقرار بستر اجرایی است.' if k=='16bis' else None)
  fids=rows(c,docs[QF],QF,FACILITATION_LAW,DFE,SRC_F);sids=rows(c,docs[QS],QS,SPECULATION_TAX_LAW,DSE,SRC_S)
  b14ids=rows(c,docs[B14],B14,TERMINAL_14BIS_BYLAW,'2025-01-01',SRC_B14);b26ids=rows(c,docs[B26],B26,TRUSTED_COMPANIES_BYLAW,'2022-06-12',SRC_B26);beids=rows(c,docs[BE],BE,VAT_EDUCATION_BYLAW,'2022-01-18',SRC_BE);biids=rows(c,docs[BI],BI,VAT_INACTIVE_WORKSPACE_BYLAW,'2022-09-04',SRC_BI)
  dr={D348:DIVAN_348,D2558:DIVAN_2558,DTAP:DIVAN_TAPSI};dids={ref:av(c,docs[ref],ref,'decision','رأی',txt,eff=next(x[7] for x in specs if x[0]==ref),src=SRC_D) for ref,txt in dr.items()}
  # Relations.
  add_relation(c,docs[QV],'abrogates',docs[QVO],description='نسخ قانون آزمایشی ۱۳۸۷ از تاریخ اجرای قانون دائمی.')
  add_relation(c,docs[QV],'cites',docs[QT],from_article_id=vid['13'],to_article_id=tids['1'],description='اجرای نظام ارزش افزوده بر بستر سامانه مؤدیان و صورتحساب الکترونیکی.')
  add_relation(c,docs[QF],'cites',docs[QV],from_article_id=fids['3'],to_article_id=vid['4'],description='اظهارنامه و مهلت پرداخت مالیات ارزش افزوده در دوره‌های گذار.')
  for fk,tk,desc in (('5','2','ثبت‌نام و تخصیص کارپوشه توسط سازمان.'),('6','5','الحاق تبصره‌های تبادل داده کارتخوان و سامانه‌های دولتی.'),('7','6','افزایش حد مجاز از سه برابر به پنج برابر.'),('8','14bis','الحاق ماده ۱۴ مکرر درباره معافیت از صدور صورتحساب.'),('9','22','بخشودگی اجباری در موارد خارج از اختیار مؤدی.'),('10','26','تعرفه خدمات صدور صورتحساب توسط شرکت‌های معتمد.')):add_relation(c,docs[QF],'amends',docs[QT],from_article_id=fids[fk],to_article_id=tids[tk],description=desc)
  for sk,tk,desc in (('3','1','بازتعریف اشخاص تجاری و غیرتجاری و انواع کارپوشه و حساب.'),('4','2','اصلاح تبصره‌ها و ثبت وجوه غیرمرتبط با فروش.'),('5','3','فعالیت‌های خارج از ایران.'),('6','10','حساب تجاری و تناظر تراکنش‌ها.'),('7','11','داده‌های بانکی و اسناد تجاری.'),('8','16bis','الحاق بستر اجرایی صورتحساب دارایی‌ها و اشخاص غیرتجاری.'),('9','12','تبدیل اصطلاح اشخاص مشمول به اشخاص تجاری در مواد متعدد.'),('10','25','پذیرش هزینه‌های دارای صورتحساب و استثناها.'),('24','22','جریمه عدم صدور صورتحساب در بستر ماده ۱۶ مکرر.')):add_relation(c,docs[QS],'amends',docs[QT],from_article_id=sids[sk],to_article_id=tids[tk],description=desc)
  direct=c.execute("select id from documents where reference_code='QMMAL-1366'").fetchone()
  if direct:add_relation(c,docs[QS],'amends',direct['id'],description='اصلاح و الحاق احکام متعدد مالیات‌های مستقیم، از جمله مواد ۳ و ۴۶ تا ۵۱؛ نسخه تلفیقی کامل قانون مالیات‌های مستقیم در بسته مستقلی تکمیل خواهد شد.')
  add_relation(c,docs[B14],'implements',docs[QT],from_article_id=b14ids['1'],to_article_id=tids['14bis'],description='نحوه تعیین مالیات مؤدیان معاف از صدور صورتحساب الکترونیکی.')
  add_relation(c,docs[B14],'implements',docs[QV],from_article_id=b14ids['5'],to_article_id=vid['4'],description='محاسبه و مطالبه مالیات و عوارض هر دوره.')
  add_relation(c,docs[B26],'implements',docs[QT],from_article_id=b26ids['1'],to_article_id=tids['26'],description='شرایط انتخاب و نظارت بر شرکت‌های معتمد مالیاتی.')
  add_relation(c,docs[BE],'implements',docs[QV],from_article_id=beids['2'],to_article_id=vid['9'],description='مصادیق معافیت خدمات آموزشی، پژوهشی و ورزشی دارای مجوز.')
  add_relation(c,docs[BI],'implements',docs[QV],from_article_id=biids['1'],to_article_id=vid['24'],description='موارد و آثار غیرفعال شدن کارپوشه مؤدی.')
  add_relation(c,docs[BI],'cites',docs[QT],from_article_id=biids['2'],to_article_id=tids['13'],description='تعطیلی موقت یا دائم واحد کسب‌وکار در سامانه مؤدیان.')
  add_relation(c,docs[D348],'overrules',docs[QVO],from_article_id=dids[D348],to_article_id=oldids['12'],description='ابطال قید محدودکننده معافیت حقوق و دستمزد در بخشنامه اجرایی قانون ۱۳۸۷.')
  add_relation(c,docs[D348],'interprets',docs[QV],from_article_id=dids[D348],to_article_id=vid['9'],description='در قانون دائمی نیز بخش حقوق و دستمزد قراردادهای حجمی با تأیید بیمه‌گر معاف است.')
  add_relation(c,docs[D2558],'overrules',docs[QVO],from_article_id=dids[D2558],to_article_id=oldids['21'],description='منع مطالبه اصل و جرایم از پیمانکار پیش از پرداخت مالیات توسط کارفرمای دولتی در حکم بودجه ۱۳۹۹.')
  add_relation(c,docs[DTAP],'interprets',docs[QV],from_article_id=dids[DTAP],to_article_id=vid['9'],description='تفکیک کرایه حمل معاف راننده از کمیسیون مشمول مالیات شرکت تاکسی اینترنتی.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] ارزش افزوده دائمی=۵۷ شماره/۶۳ نسخه؛ قانون ۱۳۸۷=۵۳ ماده تاریخی')
  print('[OK] سامانه مؤدیان=۳۱ کلید/۴۸ نسخه؛ تسهیل=۱۰؛ سوداگری=۲۸؛ آیین‌نامه‌ها=۱۲+۴۲+۳+۶؛ آرای دیوان=۳')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
