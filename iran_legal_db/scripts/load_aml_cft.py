# -*- coding: utf-8 -*-
"""Load AML/CFT statutes, current/historical regulations and 1404-1405 reforms."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from aml_cft import *
AML='QAML-1386';EA='EAML-1397';AB='AICML-1398';EAB='EAICML-1404';AOLD='AIAML-1388';CFT='QCFT-1394';EC='ECFT-1397';COLD='AICFT-1396';TARGET='AITFT-1404';FIU='AIFIU-1398';ACCESS='QCFTC-1404';REFS=(AML,EA,AB,EAB,AOLD,CFT,EC,COLD,TARGET,FIU,ACCESS)
SRC_AML='قانون مبارزه با پولشویی مصوب ۱۳۸۶ با اصلاحات جامع ۱۳۹۷؛ متن جاری از اختبار و متن تاریخی از بازنشر مصوبه اولیه.'
SRC_EA='قانون اصلاح قانون مبارزه با پولشویی مصوب ۱۳۹۷؛ متن کامل ۱۳ ماده.'
SRC_AB='آیین‌نامه اجرایی مقابله و پیشگیری از جرایم پولشویی و تأمین مالی تروریسم؛ متن تلفیقی ۱۶۸ ماده/ماده مکرر با اصلاحات ۱۴۰۴.'
SRC_EAB='اصلاح آیین‌نامه اجرایی ماده ۱۴ الحاقی قانون مبارزه با پولشویی مصوب ۱۴۰۴؛ متن کامل ۵۷ بند.'
SRC_AOLD='آیین‌نامه اجرایی قانون مبارزه با پولشویی مصوب ۱۳۸۸؛ متن ۴۹ ماده‌ای منسوخ، با اصلاحات درج‌شده در منبع.'
SRC_CFT='قانون مبارزه با تأمین مالی تروریسم مصوب ۱۳۹۴ با اصلاحات ۱۳۹۷؛ متن جاری و تاریخی.'
SRC_EC='قانون اصلاح قانون مبارزه با تأمین مالی تروریسم مصوب ۱۳۹۷؛ متن کامل پنج ماده.'
SRC_COLD='آیین‌نامه اجرایی قانون مبارزه با تأمین مالی تروریسم مصوب ۱۳۹۶؛ متن کامل ۳۰ ماده و منسوخ از ۱۴۰۴.'
SRC_TARGET='آیین‌نامه اجرایی اقدام مالی هدفمند علیه تروریسم و تأمین مالی تروریسم مصوب ۱۴۰۴ با اصلاحات تا ۱۴۰۵/۰۳/۳۱.'
SRC_FIU='آیین‌نامه تشکیلات مرکز اطلاعات مالی مصوب ۱۳۹۸؛ مواد ۱ تا ۳ و ۵ تا ۸ متن مقرره و ماده ۴ خلاصه ساختاری منبع‌دار از فهرست ۲۶ وظیفه.'
SRC_ACCESS='قانون الحاق دولت جمهوری اسلامی ایران به کنوانسیون بین‌المللی مقابله با تأمین مالی تروریسم؛ ماده‌واحده و شروط مصوب/تأییدشده تا ۱۴۰۴.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,atype,status,rat,eff,note):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=note)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute('insert into authorities(name_fa,authority_type)values(?,?)',(auth,atype)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,note,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags,topics=('حقوق کیفری','حقوق پول و بانک')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def seq(c,d,ref,data,eff,src,current=True,expiry=None,special_notes=None):
 out={}
 for k,t in data:
  no=(pn(k[:-3])+' مکرر') if k.endswith('bis') else pn(k);note=(special_notes or {}).get(k)
  out[k]=add_article(c,d,article_no=no,article_key=f'{ref}:{k}',version_no=1,is_current=int(current),effective_date=eff,expiry_date=expiry if not current else None,text=t,source_note=src,notes=note)
 return out
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  specs=(
   (AML,'قانون مبارزه با پولشویی با اصلاحات ۱۳۹۷','قانون مبارزه با پولشویی','law','مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام','legislative','amended','2008-01-22','2008-02-20','۱۵ کلید ساختاری و ۲۵ ردیف؛ تاریخچه مواد اصلاح‌شده و ماده ۷ مکرر مرکز اطلاعات مالی.'),
   (EA,'قانون اصلاح قانون مبارزه با پولشویی','اصلاحیه پولشویی ۱۳۹۷','amendment','مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام','legislative','in_force','2018-09-25','2019-01-05','متن کامل ۱۳ ماده اصلاحی و الحاقی.'),
   (AB,'آیین‌نامه اجرایی مقابله و پیشگیری از جرایم پولشویی و تأمین مالی تروریسم با اصلاحات ۱۴۰۴','آیین‌نامه جامع AML/CFT','regulation','هیأت وزیران','executive','amended','2019-10-13','2019-10-14','متن جاری تلفیقی ۱۶۴ ماده و چهار ماده مکرر؛ عنوان و ساختار اصلاحی ۱۴۰۴.'),
   (EAB,'اصلاح آیین‌نامه اجرایی ماده ۱۴ الحاقی قانون مبارزه با پولشویی','اصلاحیه آیین‌نامه AML/CFT ۱۴۰۴','amendment','هیأت وزیران','executive','in_force','2025-10-19','2025-11-05','متن کامل ۵۷ بند اصلاحی؛ مبنای عنوان جدید و شماره‌گذاری جاری.'),
   (AOLD,'آیین‌نامه اجرایی قانون مبارزه با پولشویی مصوب ۱۳۸۸ (منسوخ)','آیین‌نامه قدیم پولشویی','regulation','هیأت وزیران','executive','abrogated','2009-02-11','2009-02-11','متن کامل ۴۹ ماده صرفاً تاریخی؛ آیین‌نامه جاری ۱۴۰۴ منسوخ بودن آن را تصریح می‌کند.'),
   (CFT,'قانون مبارزه با تأمین مالی تروریسم با اصلاحات ۱۳۹۷','قانون مبارزه با تأمین مالی تروریسم','law','مجلس شورای اسلامی','legislative','amended','2016-02-02','2016-03-05','۱۷ ماده و ۲۲ ردیف با تاریخچه پنج ماده اصلاح‌شده در ۱۳۹۷.'),
   (EC,'قانون اصلاح قانون مبارزه با تأمین مالی تروریسم','اصلاحیه تأمین مالی تروریسم ۱۳۹۷','amendment','مجلس شورای اسلامی','legislative','in_force','2018-07-22','2018-08-01','متن کامل پنج ماده اصلاحی.'),
   (COLD,'آیین‌نامه اجرایی قانون مبارزه با تأمین مالی تروریسم مصوب ۱۳۹۶ (منسوخ)','آیین‌نامه قدیم CFT','regulation','هیأت وزیران','executive','abrogated','2017-10-29','2017-10-29','متن کامل ۳۰ ماده؛ به موجب ماده ۳۰ آیین‌نامه اقدام مالی هدفمند منسوخ شد.'),
   (TARGET,'آیین‌نامه اجرایی اقدام مالی هدفمند علیه تروریسم و تأمین مالی تروریسم با اصلاحات ۱۴۰۵','آیین‌نامه اقدام مالی هدفمند','regulation','هیأت وزیران','executive','amended','2025-11-12','2025-11-12','۳۰ ماده جاری و ماده ۳۱ تاریخی؛ اصلاحات جاری تا ۱۴۰۵/۰۳/۳۱.'),
   (FIU,'آیین‌نامه تشکیلات مرکز اطلاعات مالی','آیین‌نامه مرکز اطلاعات مالی','regulation','هیأت وزیران','executive','amended','2019-09-04','2019-09-07','هشت ماده؛ ماده ۴ به علت محدودیت دسترسی مستقیم، خلاصه ساختاری منبع‌دار فهرست ۲۶ وظیفه است و رونوشت لفظ‌به‌لفظ محسوب نمی‌شود.'),
   (ACCESS,'قانون الحاق دولت جمهوری اسلامی ایران به کنوانسیون بین‌المللی مقابله با تأمین مالی تروریسم','قانون الحاق به کنوانسیون CFT','law','مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام','legislative','in_force','2018-12-05','2025-11-05','ماده‌واحده و هفت شرط؛ متن ۲۸ ماده کنوانسیون به علت دسترس نبودن رونوشت متنی کامل PDF در این رکورد وارد نشده است.'),)
  for x in specs:docs[x[0]]=up(c,*x)
  for d in docs.values():clear(c,d)
  deco(c,docs[AML],('پولشویی','جرم منشأ','عواید حاصل از جرم','مرکز اطلاعات مالی','معامله مشکوک'))
  deco(c,docs[EA],('اصلاحیه ۱۳۹۷','شورای عالی مقابله','ضابط خاص'))
  deco(c,docs[AB],('شناسایی ارباب‌رجوع','مالک واقعی','رویکرد مبتنی بر ریسک','دارایی مجازی','گزارش معامله مشکوک','سازمان غیرانتفاعی'))
  deco(c,docs[EAB],('اصلاحیه ۱۴۰۴','حرف و مشاغل غیرمالی','دارایی مجازی'))
  deco(c,docs[AOLD],('آیین‌نامه منسوخ','شناسایی مشتری','سقف مقرر'))
  deco(c,docs[CFT],('تأمین مالی تروریسم','سازمان تروریستی','مسدودسازی اموال','گزارش عملیات مشکوک'))
  deco(c,docs[EC],('اصلاحیه ۱۳۹۷','شورای عالی امنیت ملی','محاربه','افساد فی‌الارض'))
  deco(c,docs[COLD],('آیین‌نامه منسوخ CFT','فهرست تحریمی','بانک پوسته‌ای'))
  deco(c,docs[TARGET],('اقدام مالی هدفمند','فهرست اشخاص معین','انسداد دارایی','کارگروه ملی','قطعنامه ۱۲۶۷'))
  deco(c,docs[FIU],('مرکز اطلاعات مالی','تحلیل معامله مشکوک','ردیابی وجوه'))
  deco(c,docs[ACCESS],('کنوانسیون تأمین مالی تروریسم','قانون الحاق','شروط ایران'),('حقوق بین‌الملل','حقوق کیفری'))
  amlids={};amlcur={}
  for r in AML_LAW_ROWS:
   aid=add_article(c,docs[AML],article_no=r['article_no'],article_key=f"{AML}:{r['key']}",version_no=r['version_no'],is_current=int(r['is_current']),effective_date=r['effective_date'],expiry_date=r['expiry_date'],text=r['text'],source_note=SRC_AML,notes=r['notes']);amlids[(r['key'],r['version_no'])]=aid
   if r['is_current']:amlcur[r['key']]=aid
  eaids=seq(c,docs[EA],EA,AML_AMENDMENT_1397,'2019-01-05',SRC_EA)
  abids=seq(c,docs[AB],AB,AML_BYLAW_CURRENT,'2025-11-05',SRC_AB)
  eabids=seq(c,docs[EAB],EAB,AML_BYLAW_AMENDMENT_1404,'2025-11-05',SRC_EAB)
  oldids=seq(c,docs[AOLD],AOLD,AML_OLD_BYLAW,'2009-02-11',SRC_AOLD,False,None)
  cftids={};cftcur={}
  for r in CFT_LAW_ROWS:
   aid=add_article(c,docs[CFT],article_no=r['article_no'],article_key=f"{CFT}:{r['key']}",version_no=r['version_no'],is_current=int(r['is_current']),effective_date=r['effective_date'],expiry_date=r['expiry_date'],text=r['text'],source_note=SRC_CFT,notes=r['notes']);cftids[(r['key'],r['version_no'])]=aid
   if r['is_current']:cftcur[r['key']]=aid
  ecids=seq(c,docs[EC],EC,CFT_AMENDMENT_1397,'2018-08-01',SRC_EC)
  coldids=seq(c,docs[COLD],COLD,CFT_OLD_BYLAW,'2017-10-29',SRC_COLD,False,'2025-11-12')
  tids={};tcur={}
  for r in TARGETED_FINANCIAL_ROWS:
   aid=add_article(c,docs[TARGET],article_no=r['article_no'],article_key=f"{TARGET}:{r['key']}",version_no=r['version_no'],is_current=int(r['is_current']),effective_date=r['effective_date'],expiry_date=r['expiry_date'],text=r['text'],source_note=SRC_TARGET,notes=r['notes']);tids[(r['key'],r['version_no'])]=aid
   if r['is_current']:tcur[r['key']]=aid
  fiuids=seq(c,docs[FIU],FIU,FIU_BYLAW,'2019-09-07',SRC_FIU,special_notes={'4':'خلاصه ساختاری منبع‌دار ماده ۴؛ سایر مواد رونوشت کامل متن در دسترس‌اند.'})
  accid=add_article(c,docs[ACCESS],article_no='ماده واحده',article_key=f'{ACCESS}:single',version_no=1,is_current=1,effective_date='2025-11-05',text=CFT_ACCESSION_ACT,source_note=SRC_ACCESS)
  # Amendment network for the AML statute.
  links=(('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','7bis'),('9','8'),('10','9'),('11','11'),('12','13'),('13','14'))
  for ek,ak in links:add_relation(c,docs[EA],'amends',docs[AML],from_article_id=eaids[ek],to_article_id=amlcur[ak],description=f'اصلاح یا الحاق ماده {ak}.')
  add_relation(c,docs[AB],'implements',docs[AML],from_article_id=abids['1'],to_article_id=amlcur['14'],description='آیین‌نامه جامع اجرایی قانون مبارزه با پولشویی.')
  add_relation(c,docs[AB],'implements',docs[CFT],from_article_id=abids['135'],to_article_id=cftcur['14'],description='گزارش معاملات مشکوک به پولشویی و تأمین مالی تروریسم.')
  add_relation(c,docs[AB],'abrogates',docs[AOLD],from_article_id=abids['164'],description='تأیید منسوخ بودن آیین‌نامه اجرایی سال ۱۳۸۸ و لزوم اصلاح مقررات مبتنی بر آن.')
  add_relation(c,docs[EAB],'amends',docs[AB],description='اصلاح ۵۷ بندی، تغییر عنوان و شماره‌گذاری جاری آیین‌نامه.')
  for ek,ak in (('1','1'),('10','8'),('12','9bis'),('16','27bis'),('20','41'),('39','135'),('51','158'),('52','159')):add_relation(c,docs[EAB],'amends',docs[AB],from_article_id=eabids[ek],to_article_id=abids[ak],description='اعمال در متن تلفیقی جاری آیین‌نامه.')
  for ek,ck in (('1','1'),('2','2'),('3','5'),('4','10'),('5','14')):add_relation(c,docs[EC],'amends',docs[CFT],from_article_id=ecids[ek],to_article_id=cftcur[ck],description=f'اصلاح ماده {ck} قانون تأمین مالی تروریسم.')
  add_relation(c,docs[TARGET],'implements',docs[CFT],from_article_id=tcur['1'],to_article_id=cftcur['17'],description='سازوکار فهرست‌گذاری، انسداد و اقدام مالی هدفمند.')
  add_relation(c,docs[TARGET],'abrogates',docs[COLD],from_article_id=tcur['30'],description='نسخ صریح آیین‌نامه اجرایی تأمین مالی تروریسم مصوب ۱۳۹۶.')
  add_relation(c,docs[FIU],'implements',docs[AML],from_article_id=fiuids['1'],to_article_id=amlcur['7bis'],description='ساختار، استقلال و وظایف مرکز اطلاعات مالی.')
  add_relation(c,docs[ACCESS],'cites',docs[CFT],from_article_id=accid,to_article_id=cftcur['16'],description='الحاق مشروط به کنوانسیون بین‌المللی و همکاری در چهارچوب قوانین داخلی.')
  add_relation(c,docs[ACCESS],'cites',docs[TARGET],from_article_id=accid,to_article_id=tcur['1'],description='ارتباط شروط الحاق با اقدام مالی هدفمند و صلاحیت شورای عالی امنیت ملی.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] AML=۱۵ کلید/۲۵ ردیف؛ اصلاحیه=۱۳؛ آیین‌نامه جاری=۱۶۸؛ اصلاحیه آیین‌نامه=۵۷؛ قدیم=۴۹ تاریخی')
  print('[OK] CFT=۱۷/۲۲؛ اصلاحیه=۵؛ آیین‌نامه قدیم=۳۰ تاریخی؛ اقدام هدفمند=۳۱؛ مرکز اطلاعات مالی=۸؛ الحاق=۱')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
