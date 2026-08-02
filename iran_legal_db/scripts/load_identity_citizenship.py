# -*- coding: utf-8 -*-
"""Load civil registration, nationality, national ID, passport and leading precedents."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from identity_citizenship import *
QSA='QSA-1355';AISA='AISA-1385';QNM='QNM-1376';AINM='AINM-1378';AKNM='AKNM-1387';AISM='AISM-1391'
QTF='QTF-1385';EQTF='EQTF-1398';AITF='AITF-1399';QGO='QGO-1351';AIPZ='AIPZ-1363'
R748='RVR-748-1395';R732='RVR-732-1393';R726='RVR-726-1391';R658='RVR-658-1381';R617='RVR-617-1376';NM='NM-586-1403'
REFS=(QSA,AISA,QNM,AINM,AKNM,AISM,QTF,EQTF,AITF,QGO,AIPZ,R748,R732,R726,R658,R617,NM)
DREG='1976-07-07';DREG63='1985-01-08';DREG1401='2022-09-21';DFINE='2024-06-24';DREG_BY='2006-04-09'
DNID='1997-05-07';DNID_BY='2000-02-20';DAPPLIED='2008-05-04';DSMART='2012-11-11';DSMART_ADD='2021-05-12'
DCIT='2006-09-24';DCIT_NEW='2019-09-24';DCIT_BY='2020-05-20';DPASS='1973-03-01';DPASS62='1983-06-21';DPASS67='1988-10-06';DPASS70='1991-08-14';DPASS73='1994-09-25';DPASS80='2001-06-13';DPASS90='2011-11-24';DZI='1984-05-06'
DATES={R617:'1997-06-24',R658:'2002-04-09',R726:'2012-07-17',R732:'2014-04-08',R748:'2016-04-12',NM:'2024-05-11'}
SRC_REG='قانون ثبت احوال مصوب ۱۳۵۵/۰۴/۱۶، اصلاحات ۱۳۶۳ و اصلاح ماده ۳۴ در ۱۴۰۱؛ متن تلفیقی اختبار، میزان و سامانه ملی قوانین.'
SRC_REGBY='آیین‌نامه اجرایی تبصره ۲ اصلاحی ماده ۵ قانون ثبت احوال مصوب ۱۳۸۵/۰۱/۲۰ هیأت وزیران؛ متن کامل ۱۴ ماده.'
SRC_NID='قانون الزام اختصاص شماره ملی و کدپستی برای کلیه اتباع ایرانی مصوب ۱۳۷۶/۰۲/۱۷؛ متن کامل شش ماده.'
SRC_NIDBY='آیین‌نامه اجرایی قانون الزام اختصاص شماره ملی و کدپستی مصوب ۱۳۷۸/۱۲/۰۱ هیأت وزیران؛ متن کامل ۱۴ ماده.'
SRC_APPLIED='آیین‌نامه کاربردی شدن کارت شناسایی ملی مصوب ۱۳۸۷/۰۲/۱۵ هیأت وزیران؛ متن کامل ده ماده.'
SRC_SMART='آیین‌نامه اجرایی بند د ماده ۴۶ قانون برنامه پنجم مصوب ۱۳۹۱/۰۸/۲۱ با الحاق ماده ۱۳ در ۱۴۰۰؛ متن کامل کارت هوشمند ملی.'
SRC_NAT='کتاب دوم جلد دوم قانون مدنی، مواد ۹۷۶ تا ۹۹۱؛ متن جاری با اصلاح ماده ۹۸۹ به موجب قانون حمایت از ایرانیان خارج از کشور مصوب ۱۴۰۴ و مقابله با منبع تاریخی.'
SRC_CIT='قانون تعیین تکلیف تابعیت فرزندان حاصل از ازدواج زنان ایرانی با مردان غیرایرانی؛ متن ۱۳۸۵ و نسخه جاری اصلاحی ۱۳۹۸.'
SRC_CIT_AM='قانون اصلاح قانون تعیین تکلیف تابعیت فرزندان حاصل از ازدواج زنان ایرانی با مردان خارجی مصوب ۱۳۹۸/۰۷/۰۲؛ ماده‌واحده کامل.'
SRC_CIT_BY='آیین‌نامه اعطای تابعیت ایران به فرزندان حاصل از ازدواج زنان ایرانی با مردان خارجی مصوب ۱۳۹۹/۰۲/۳۱؛ متن کامل ۲۴ ماده.'
SRC_PASS='قانون گذرنامه مصوب ۱۳۵۱/۱۲/۱۰ با اصلاحات و تعدیل جزاهای نقدی ۱۴۰۳؛ مقابله متن مصوب، قوانین اصلاحی و منابع تنقیحی.'
SRC_ZI='آیین‌نامه اجرایی پروانه گذر زیارتی مصوب ۱۳۶۳/۰۲/۱۶؛ متن کامل یازده ماده.'
SRC_R='قسمت لازم‌الاتباع رأی وحدت رویه هیأت عمومی دیوان عالی کشور.'
SRC_NM='پاسخ کامل نظریه مشورتی شماره ۷/۱۴۰۲/۵۸۶ مورخ ۱۴۰۳/۰۲/۲۲ اداره کل حقوقی قوه قضائیه.'

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
def deco(c,d,tags,topics=('حقوق مدنی','حقوق اداری')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,key,no,text,v=1,cur=True,eff=None,exp=None,src=None,note=None):return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def rows(c,d,ref,data,date,src):
 o={}
 for k,t in data:o[k]=av(c,d,ref,k,pn(k),t,eff=date,src=src)
 return o

def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  specs=(
   (QSA,'قانون ثبت احوال با اصلاحات تا ۱۴۰۳','قانون ثبت احوال','law','مجلس شورای ملی','legislative','amended',DREG,'پوشش کامل ۵۵ ماده؛ تاریخچه ماده ۳۴ درباره محرمانگی و ماده ۴۸ با تعدیل جزای نقدی ۱۴۰۳.'),
   (AISA,'آیین‌نامه اجرایی تبصره ۲ اصلاحی ماده ۵ قانون ثبت احوال','آیین‌نامه همکاری در ثبت وقایع حیاتی','regulation','هیئت وزیران','executive','in_force',DREG_BY,'متن کامل ۱۴ ماده درباره اعلام ولادت و وفات، فاقدان شناسنامه، روستاها و تبادل الکترونیکی.'),
   (QNM,'قانون الزام اختصاص شماره ملی و کدپستی برای کلیه اتباع ایرانی','قانون شماره ملی و کدپستی','law','مجلس شورای اسلامی','legislative','in_force',DNID,'متن کامل شش ماده درباره شماره ملی، کدپستی و کارت شناسایی ملی.'),
   (AINM,'آیین‌نامه اجرایی قانون الزام اختصاص شماره ملی و کدپستی','آیین‌نامه شماره ملی و کدپستی','regulation','هیئت وزیران','executive','in_force',DNID_BY,'متن کامل ۱۴ ماده درباره کارت شناسایی، پایگاه جمعیت و کاربرد شماره ملی و کدپستی.'),
   (AKNM,'آیین‌نامه کاربردی شدن کارت شناسایی ملی','کاربرد کارت شناسایی ملی','regulation','هیئت وزیران','executive','in_force',DAPPLIED,'متن کامل ده ماده درباره احراز هویت و ارائه خدمات بر مبنای کارت ملی.'),
   (AISM,'آیین‌نامه اجرایی کارت هوشمند ملی چندمنظوره با اصلاحات','آیین‌نامه کارت هوشمند ملی','regulation','هیئت وزیران','executive','amended',DSMART,'سیزده ماده؛ ماده ۱۳ الحاقی ۱۴۰۰ درباره اعلام تمایل به اهدای عضو.'),
   (QTF,'قانون تعیین تکلیف تابعیت فرزندان حاصل از ازدواج زنان ایرانی با مردان غیرایرانی','تابعیت فرزندان مادران ایرانی','law','مجلس شورای اسلامی','legislative','amended',DCIT,'ماده‌واحده در دو نسخه: متن تاریخی ۱۳۸۵ و متن جاری اصلاحی ۱۳۹۸.'),
   (EQTF,'قانون اصلاح قانون تعیین تکلیف تابعیت فرزندان حاصل از ازدواج زنان ایرانی با مردان خارجی','اصلاح تابعیت فرزندان ۱۳۹۸','amendment','مجلس شورای اسلامی','legislative','in_force',DCIT_NEW,'متن کامل ماده‌واحده اصلاحی ۱۳۹۸.'),
   (AITF,'آیین‌نامه اعطای تابعیت ایران به فرزندان حاصل از ازدواج زنان ایرانی با مردان خارجی','آیین‌نامه تابعیت فرزندان','regulation','هیئت وزیران','executive','in_force',DCIT_BY,'متن کامل ۲۴ ماده درباره احراز نسب، استعلام امنیتی، شناسنامه، کارت ملی و رسیدگی داخل و خارج کشور.'),
   (QGO,'قانون گذرنامه با اصلاحات و تعدیل جزاهای نقدی ۱۴۰۳','قانون گذرنامه','law','مجلس شورای ملی','legislative','amended',DPASS,'پوشش ۱ تا ۴۲ و ماده ۳۵ مکرر؛ ماده ۲۶ فقط تاریخی و تاریخچه مهم فصل سوم، ماده ۱۸ و مواد کیفری.'),
   (AIPZ,'آیین‌نامه اجرایی پروانه گذر زیارتی','آیین‌نامه پروانه گذر زیارتی','regulation','هیئت وزیران','executive','in_force',DZI,'متن کامل یازده ماده موضوع بند ۱ ماده ۲۹ قانون گذرنامه.'),
  )
  for ref,title,short,typ,auth,atype,status,date,note in specs:docs[ref]=up(c,ref,title,short,typ,auth,atype,status,date,date,note)
  for ref,num,title,short,note in (
   (R617,'۶۱۷','رأی وحدت رویه شماره ۶۱۷ درباره شناسنامه طفل ناشی از رابطه نامشروع','رأی ۶۱۷ ـ شناسنامه طفل','تکلیف پدر عرفی به اخذ شناسنامه و انحصار نفی رابطه به توارث.'),
   (R658,'۶۵۸','رأی وحدت رویه شماره ۶۵۸ درباره تردید در تابعیت و ترتیب اعتراض','رأی ۶۵۸ ـ تردید در تابعیت','نقش شورای تأمین، هیأت حل اختلاف و دادگاه عمومی در موارد تردید تابعیت.'),
   (R726,'۷۲۶','رأی وحدت رویه شماره ۷۲۶ درباره صلاحیت محلی دعاوی اسناد ثبت احوال','رأی ۷۲۶ ـ صلاحیت محلی','صلاحیت دادگاه محل اقامت خواهان در دعاوی راجع به اسناد ثبت احوال.'),
   (R732,'۷۳۲','رأی وحدت رویه شماره ۷۳۲ درباره تعیین یا تغییر تاریخ فوت','رأی ۷۳۲ ـ تاریخ فوت','صلاحیت دادگاه عمومی حقوقی برای تعیین یا تغییر تاریخ فوت.'),
   (R748,'۷۴۸','رأی وحدت رویه شماره ۷۴۸ درباره دعوای الزام به صدور شناسنامه','رأی ۷۴۸ ـ صدور شناسنامه','قابلیت رسیدگی دادگاه به دعوای الزام ثبت احوال پس از احراز هویت و تابعیت.'),
  ):docs[ref]=up(c,ref,title,short,'unified_ruling','دیوان عالی کشور','judicial','in_force',DATES[ref],DATES[ref],note)
  docs[NM]=up(c,NM,'نظریه مشورتی شماره ۷/۱۴۰۲/۵۸۶ درباره دعوای الزام به صدور شناسنامه','نظریه ۵۸۶ ـ صدور شناسنامه','advisory_opinion','اداره کل حقوقی قوه قضائیه','judicial','in_force',DATES[NM],DATES[NM],'پاسخ کامل پنج‌بندی درباره رسیدگی مستقیم دادگاه، احراز هویت و تابعیت و ترتیب اعتراض به نظر شورای تأمین.')
  for d in docs.values():clear(c,d)
  # Refresh only the nationality book of the existing Civil Code; no other civil-code provision is touched.
  qm=c.execute("select id from documents where reference_code='QM-1307'").fetchone();
  if not qm:raise RuntimeError('missing QM-1307')
  qmid=qm['id'];keys=tuple(f'QM:{n}' for n in range(976,992));ph=','.join('?'*len(keys))
  oldids=[r['id'] for r in c.execute(f'select id from articles where article_key in ({ph})',keys)]
  if oldids:
   iph=','.join('?'*len(oldids));c.execute(f'delete from relations where from_article_id in ({iph}) or to_article_id in ({iph})',oldids*2);c.execute(f'delete from articles_fts where article_id in ({iph})',oldids)
  c.execute(f'delete from articles where article_key in ({ph})',keys)
  deco(c,docs[QSA],('ثبت احوال','شناسنامه','ولادت','وفات','نام خانوادگی','هیأت حل اختلاف','اسناد سجلی'))
  deco(c,docs[AISA],('وقایع حیاتی','فاقد شناسنامه','گواهی ولادت','گواهی فوت','دولت الکترونیک'))
  for ref,tags in ((QNM,('شماره ملی','کدپستی','کارت ملی')),(AINM,('پایگاه اطلاعات جمعیت','شماره ملی','کدپستی')),(AKNM,('احراز هویت','کارت شناسایی ملی')),(AISM,('کارت هوشمند ملی','زیست‌سنجی','امضای الکترونیکی','اهدای عضو'))):deco(c,docs[ref],tags)
  for ref,tags in ((QTF,('تابعیت','مادر ایرانی','پدر غیرایرانی','بی‌تابعیتی')),(EQTF,('تابعیت فرزندان','ازدواج شرعی','استعلام امنیتی')),(AITF,('احراز نسب','کمیسیون تابعیت','صدور شناسنامه'))):deco(c,docs[ref],tags,('حقوق مدنی','حقوق خانواده','حقوق اداری'))
  deco(c,docs[QGO],('گذرنامه','ممنوع‌الخروجی','خروج از کشور','برگ بازگشت','گذرنامه سیاسی'),('حقوق اداری','حقوق کیفری'))
  deco(c,docs[AIPZ],('پروانه گذر زیارتی','حج','عتبات مقدسه'))
  for ref,tags in ((R617,('طفل ناشی از زنا','اخذ شناسنامه')),(R658,('مشکوک‌التابعه','شورای تأمین')),(R726,('صلاحیت محلی','اسناد ثبت احوال')),(R732,('تاریخ فوت','اهلیت','وراثت')),(R748,('فاقد شناسنامه','الزام به صدور شناسنامه'))):deco(c,docs[ref],tags)
  deco(c,docs[NM],('فاقد سند سجلی','اثبات نسب','شورای تأمین','اعتراض'),('حقوق مدنی','آیین دادرسی مدنی'))
  # Civil registry law and its two material histories.
  reg=dict(CIVIL_REGISTRY_LAW);regids={};regh={}
  for n in range(1,56):
   k=str(n);eff=DREG63 if n in (1,3,5,7,8,9,10,11,13,14,15,16,17,20,22,23,25,29,30,31,32,35,36,37,38,39,40,41,42,43,44,45,46,47) else DREG
   if n==34:
    regh[k]=av(c,docs[QSA],QSA,k,pn(n),CIVIL_REGISTRY_ART34_OLD,1,False,DREG,DREG1401,SRC_REG,'متن پیش از اصلاح ۱۴۰۱ درباره دسترسی مقامات دولتی ذی‌صلاح.')
    regids[k]=av(c,docs[QSA],QSA,k,pn(n),reg[k],2,True,DREG1401,None,SRC_REG,'نسخه جاری با قید مصوبه کارگروه تعامل‌پذیری دولت الکترونیکی.')
   elif n==48:
    regh[k]=av(c,docs[QSA],QSA,k,pn(n),CIVIL_REGISTRY_ART48_OLD,1,False,DREG63,DFINE,SRC_REG,'متن پیش از تعدیل مبلغ جزای نقدی ۱۴۰۳.')
    regids[k]=av(c,docs[QSA],QSA,k,pn(n),reg[k],2,True,DFINE,None,SRC_REG,'نسخه جاری همراه مبلغ تعدیل‌شده ۱۴۰۳.')
   else:regids[k]=av(c,docs[QSA],QSA,k,pn(n),reg[k],eff=eff,src=SRC_REG)
  rbids=rows(c,docs[AISA],AISA,CIVIL_REGISTRY_BYLAW,DREG_BY,SRC_REGBY)
  nidids=rows(c,docs[QNM],QNM,NATIONAL_ID_LAW,DNID,SRC_NID);nibids=rows(c,docs[AINM],AINM,NATIONAL_ID_BYLAW,DNID_BY,SRC_NIDBY);akids=rows(c,docs[AKNM],AKNM,NATIONAL_ID_APPLICATION_BYLAW,DAPPLIED,SRC_APPLIED)
  smids={}
  for k,t in SMART_ID_BYLAW:smids[k]=av(c,docs[AISM],AISM,k,pn(k),t,eff=DSMART_ADD if k=='13' else DSMART,src=SRC_SMART,note='ماده الحاقی ۱۴۰۰.' if k=='13' else None)
  # Repair the complete nationality book in the existing Civil Code.
  nat=dict(NATIONALITY_CIVIL_CODE);natids={};nath={}
  neff={'977':'1970-02-16','980':'1991-11-05','982':'1991-11-05','987':'1991-11-05','988':'1970-02-16','991':'1991-11-05'}
  for n in range(976,992):
   k=str(n);no=pn(n)
   if n==981:nath[k]=av(c,qmid,'QM',k,no,nat[k],1,False,'1935-02-16','1991-11-05',SRC_NAT,'ماده ۹۸۱ به موجب قانون اصلاح موادی از قانون مدنی مصوب ۱۳۷۰ منسوخ است.')
   elif n==989:
    nath[k]=av(c,qmid,'QM',k,no,NATIONALITY_ART989_OLD,1,False,'1935-02-16','2025-10-15',SRC_NAT,'متن پیش از حذف حکم فروش اموال غیرمنقول در اصلاح ۱۴۰۴.')
    natids[k]=av(c,qmid,'QM',k,no,nat[k],2,True,'2025-10-15',None,SRC_NAT,'نسخه جاری اصلاحی ۱۴۰۴؛ لایحه عام اصلاح تابعیت ۱۴۰۳ در ۱۴۰۳/۱۱/۲۹ مسترد شد و مبنای متن جاری نیست.')
   else:natids[k]=av(c,qmid,'QM',k,no,nat[k],eff=neff.get(k,'1935-02-16'),src=SRC_NAT)
  # Citizenship special law: stable key with historical and current versions.
  oldcit=av(c,docs[QTF],QTF,'single','ماده‌واحده',CITIZENSHIP_CHILDREN_1385,1,False,DCIT,DCIT_NEW,SRC_CIT,'متن مصوب ۱۳۸۵؛ در ۱۳۹۸ به طور کامل جایگزین شد.')
  curcit=av(c,docs[QTF],QTF,'single','ماده‌واحده',CITIZENSHIP_CHILDREN_CURRENT,2,True,DCIT_NEW,None,SRC_CIT,'متن جاری اصلاحی ۱۳۹۸.')
  amcit=av(c,docs[EQTF],EQTF,'single','ماده‌واحده',CITIZENSHIP_AMENDMENT_1398,eff=DCIT_NEW,src=SRC_CIT_AM)
  cbids=rows(c,docs[AITF],AITF,CITIZENSHIP_CHILDREN_BYLAW,DCIT_BY,SRC_CIT_BY)
  # Passport: 42 current provisions including 35bis; article 26 is historical only.
  p=dict(PASSPORT_LAW);po=dict(PASSPORT_OLD);pids={};phist={}
  for n in range(1,43):
   k=str(n);no=pn(n)
   if n in (10,11,12,13):
    phist[k]=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS62,SRC_PASS,'فصل سوم مصوب ۱۳۵۱؛ در ۱۳۶۲ جایگزین شد.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],2,True,DPASS62,None,SRC_PASS,'نسخه جاری فصل سوم با اصلاحات بعدی.')
   elif n==18:
    phist['18-1']=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS70,SRC_PASS,'متن اولیه ۱۳۵۱.')
    phist['18-2']=av(c,docs[QGO],QGO,k,no,PASSPORT_ART18_1370,2,False,DPASS70,DPASS80,SRC_PASS,'نسخه محدودکننده ۱۳۷۰؛ به موجب قانون ۱۳۸۰ ملغی شد.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],3,True,DPASS80,None,SRC_PASS,'نسخه جاری پس از احیای بند ۱ مصوب ۱۳۵۱ در قانون ۱۳۸۰.')
   elif n==25:
    phist[k]=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS73,SRC_PASS,'اعتبار سه‌ساله مصوب ۱۳۵۱.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],2,True,DPASS73,None,SRC_PASS,'اعتبار پنج‌ساله اصلاحی ۱۳۷۳.')
   elif n==26:phist[k]=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS73,SRC_PASS,'حکم انتقالی؛ به موجب اصلاح ۱۳۷۳ حذف شد.')
   elif n==34:
    phist['34-1']=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS67,SRC_PASS,'متن اولیه ۱۳۵۱.')
    phist['34-2']=av(c,docs[QGO],QGO,k,no,PASSPORT_ART34_1367,2,False,DPASS67,DFINE,SRC_PASS,'نسخه اصلاحی ۱۳۶۷ پیش از تعدیل ۱۴۰۳.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],3,True,DFINE,None,SRC_PASS,'نسخه جاری با جزای نقدی تعدیل‌شده ۱۴۰۳.')
   elif n==35:
    phist['35-1']=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS67,SRC_PASS,'متن اولیه ۱۳۵۱.')
    phist['35-2']=av(c,docs[QGO],QGO,k,no,PASSPORT_ART35_1367,2,False,DPASS67,DFINE,SRC_PASS,'نسخه اصلاحی ۱۳۶۷ پیش از تعدیل ۱۴۰۳.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],3,True,DFINE,None,SRC_PASS,'نسخه جاری با جزای نقدی تعدیل‌شده ۱۴۰۳.')
   elif n==36:
    phist[k]=av(c,docs[QGO],QGO,k,no,po[k],1,False,DPASS,DPASS90,SRC_PASS,'متن کیفری اولیه ۱۳۵۱.')
    pids[k]=av(c,docs[QGO],QGO,k,no,p[k],2,True,DPASS90,None,SRC_PASS,'نسخه اصلاحی ۱۳۹۰ درباره سفر به کشور ممنوع یا محدود.')
   else:pids[k]=av(c,docs[QGO],QGO,k,no,p[k],eff=DPASS62 if n in (10,11,12,13) else DPASS,src=SRC_PASS)
  phist['35bis']=av(c,docs[QGO],QGO,'35bis','۳۵ مکرر',PASSPORT_ART35BIS_1367,1,False,DPASS67,DFINE,SRC_PASS,'متن الحاقی ۱۳۶۷ پیش از تعدیل ۱۴۰۳.')
  pids['35bis']=av(c,docs[QGO],QGO,'35bis','۳۵ مکرر',PASSPORT_ART35BIS_CURRENT,2,True,DFINE,None,SRC_PASS,'نسخه جاری با دو بازه جزای نقدی تعدیل‌شده ۱۴۰۳.')
  zids=rows(c,docs[AIPZ],AIPZ,PASSPORT_ZIARAT_BYLAW,DZI,SRC_ZI)
  rids={}
  for ref,num in ((R617,'617'),(R658,'658'),(R726,'726'),(R732,'732'),(R748,'748')):rids[ref]=av(c,docs[ref],ref,'decision','رأی',RULINGS[num],eff=DATES[ref],src=SRC_R)
  nmid=av(c,docs[NM],NM,'answer','پاسخ',ADVISORY_586,eff=DATES[NM],src=SRC_NM)
  # Relations.
  add_relation(c,docs[AISA],'implements',docs[QSA],from_article_id=rbids['1'],to_article_id=regids['5'],description='همکاری دستگاه‌ها و اشخاص در ثبت وقایع حیاتی موضوع تبصره ۲ ماده ۵.')
  add_relation(c,docs[AINM],'implements',docs[QNM],from_article_id=nibids['1'],to_article_id=nidids['6'],description='آیین‌نامه اجرایی قانون شماره ملی و کدپستی.')
  add_relation(c,docs[AKNM],'implements',docs[QNM],from_article_id=akids['1'],to_article_id=nidids['2'],description='کاربرد کارت ملی در احراز هویت و ارائه خدمات.')
  add_relation(c,docs[AISM],'implements',docs[QNM],from_article_id=smids['5'],to_article_id=nidids['3'],description='جایگزینی کارت هوشمند چندمنظوره با کارت شناسایی ملی.')
  add_relation(c,docs[AISM],'cites',docs[QSA],from_article_id=smids['2'],to_article_id=regids['34'],description='پایگاه الکترونیکی اطلاعات هویتی و رعایت محرمانگی داده‌های سجلی.')
  add_relation(c,docs[EQTF],'amends',docs[QTF],from_article_id=amcit,to_article_id=curcit,description='جایگزینی عنوان، ماده‌واحده و تبصره‌های قانون ۱۳۸۵.')
  add_relation(c,docs[AITF],'implements',docs[QTF],from_article_id=cbids['1'],to_article_id=curcit,description='تشریفات اعلام تابعیت فرزندان مادر ایرانی.')
  add_relation(c,docs[QTF],'cites',qmid,to_article_id=natids['976'],description='قانون خاص مکمل قواعد تابعیت قانون مدنی.')
  add_relation(c,docs[QTF],'cites',docs[QSA],to_article_id=regids['13'],description='صدور شناسنامه پس از تأیید تابعیت.')
  add_relation(c,docs[QGO],'cites',qmid,to_article_id=natids['976'],description='لزوم اثبات تابعیت ایرانی برای صدور گذرنامه و برگ بازگشت.')
  add_relation(c,docs[QGO],'cites',docs[QSA],to_article_id=regids['36'],description='اسناد هویتی مبنای احراز هویت متقاضی گذرنامه.')
  add_relation(c,docs[AIPZ],'implements',docs[QGO],from_article_id=zids['1'],to_article_id=pids['29'],description='پروانه گذر زیارتی موضوع بند ۱ ماده ۲۹.')
  for ref,target,desc in ((R617,'16','تکلیف پدر عرفی طفل به اعلام ولادت و اخذ شناسنامه.'),(R658,'45','ترتیب رسیدگی به تردید در تابعیت و اعتراض.'),(R726,'4','صلاحیت دادگاه محل اقامت خواهان.'),(R732,'3','خروج تعیین یا تغییر تاریخ فوت از صلاحیت هیأت حل اختلاف.'),(R748,'45','لزوم احراز هویت و تابعیت پیش از الزام به صدور شناسنامه.')):add_relation(c,docs[ref],'interprets',docs[QSA],from_article_id=rids[ref],to_article_id=regids[target],description=desc)
  add_relation(c,docs[R617],'interprets',qmid,from_article_id=rids[R617],description='اثر رابطه نامشروع بر تکالیف سجلی با استثنای توارث ماده ۸۸۴ قانون مدنی.')
  add_relation(c,docs[R732],'interprets',qmid,from_article_id=rids[R732],description='آثار فوت بر اهلیت و وراثت موضوع ماده ۹۵۶ قانون مدنی.')
  add_relation(c,docs[NM],'interprets',docs[QSA],from_article_id=nmid,to_article_id=regids['45'],description='احراز هویت و تابعیت، نظر شورای تأمین و ترتیب اعتراض.')
  add_relation(c,docs[NM],'interprets',docs[R748],from_article_id=nmid,to_article_id=rids[R748],description='تبیین امکان رسیدگی مستقیم دادگاه به دعوای صدور شناسنامه.')
  add_relation(c,docs[NM],'interprets',docs[R658],from_article_id=nmid,to_article_id=rids[R658],description='تعمیم ترتیب تردید در تابعیت به اشخاص دارای یا فاقد شناسنامه.')
  # Document-level links to avoid cascade loss when target packages rebuild articles.
  for ref,target,desc in ((QGO,'QMM-1367','ابطال گذرنامه و ممنوع‌الخروجی محکومان مواد مخدر.'),(QGO,'QADK-1392','قرارهای نظارت قضایی و ممنوعیت خروج.'),(QTF,'QHKH-1391','ثبت ازدواج و دعاوی نسب و خانواده.')):
   x=c.execute('select id from documents where reference_code=?',(target,)).fetchone()
   if x:add_relation(c,docs[ref],'cites',x['id'],description=desc)
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] ثبت احوال=۵۵ شماره/۵۷ نسخه | شماره ملی و کارت=۶+۱۴+۱۰+۱۳ | تابعیت مدنی=۱۶ شماره بازسازی شد')
  print('[OK] تابعیت فرزندان=۲ نسخه+اصلاحیه+۲۴ ماده | گذرنامه=۴۳ کلید/۵۶ نسخه (۴۲ جاری) | آرا=۵ | نظریه=۱')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
