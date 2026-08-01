# -*- coding: utf-8 -*-
"""Load criminal enforcement, prison, monitoring and decarceration regulations."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from criminal_enforcement import *
RE='QADK-1392-EXEC';RJ='AIEK-1398';RP='AIZ-1400';RM='AIME-1397';RA='AIN79-1393';RD='DSKZ-1398';RL='DMEL-1401';REFS=(RE,RJ,RP,RM,RA,RD,RL)
DE='2015-06-22';DJ='2019-06-17';DP='2021-05-10';DM='2018-07-01';DA='2014-08-27';DD='2019-08-22';DL='2022-08-24'
SRC_E='بخش پنجم قانون آیین دادرسی کیفری، مواد ۴۸۴ تا ۵۵۸، متن تنقیحی جاری با اصلاحات بعدی.';SRC_J='آیین‌نامه شماره ۹۰۰۰/۲۷۸۶۳/۲۰۰ مورخ ۱۳۹۸/۳/۲۷ رئیس قوه قضائیه درباره نحوه اجرای حدود، سلب حیات، قصاص، دیات، شلاق و مجازات‌های مکانی.';SRC_P='آیین‌نامه اجرایی سازمان زندان‌ها و اقدامات تأمینی و تربیتی کشور مصوب ۱۴۰۰/۲/۲۰ با اصلاحات ۱۴۰۰/۱۰/۲۹.';SRC_M='آیین‌نامه اجرایی مراقبت‌های الکترونیکی مصوب ۱۳۹۷/۴/۱۰ رئیس قوه قضائیه.';SRC_A='آیین‌نامه اجرایی ماده ۷۹ قانون مجازات اسلامی در تعیین مجازات‌های جایگزین حبس، تصویب‌نامه شماره ۶۶۸۶۲/ت۵۰۱۳۹هـ.';SRC_D='دستورالعمل ساماندهی زندانیان و کاهش جمعیت کیفری زندان‌ها مصوب ۱۳۹۸/۵/۳۱، ابلاغیه شماره ۹۰۰۰/۶۹۸۵۵/۱۰۰.';SRC_L='دستورالعمل تعیین محدوده مراقبتی محکومان تحت نظارت سامانه‌های الکترونیکی مصوب ۱۴۰۱.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,status,date,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=date,effective_date=date,reference_code=ref,notes=notes)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute("insert into authorities(name_fa,authority_type)values(?,'judicial')",(auth,)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),date,date,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 for topic in ('آیین دادرسی کیفری','حقوق کیفری'):link_document_topic(c,d,topic)
 for t in tags:link_document_tag(c,d,add_tag(c,t))
def rows(c,d,ref,data,date,src):
 o={}
 for n,t in data:o[n]=add_article(c,d,article_no=pn(n),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=src)
 return o
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[RE]=up(c,RE,'بخش اجرای احکام کیفری و اقدامات تأمینی و تربیتی قانون آیین دادرسی کیفری','اجرای احکام کیفری','law','مجلس شورای اسلامی','amended',DE,'رونوشت کامل مواد ۴۸۴ تا ۵۵۸ بخش پنجم قانون آیین دادرسی کیفری؛ این سند گزیده تخصصی است و جایگزین سند کامل قانون نیست.')
  docs[RJ]=up(c,RJ,'آیین‌نامه نحوه اجرای احکام حدود، سلب حیات، قصاص، دیات، شلاق و مجازات‌های مکانی','آیین‌نامه اجرای مجازات‌ها','regulation','رئیس قوه قضائیه','in_force',DJ,'متن کامل ۱۴۸ ماده و ۴۰ تبصره درباره تشریفات عمومی و اختصاصی اجرای مجازات‌ها.')
  docs[RP]=up(c,RP,'آیین‌نامه اجرایی سازمان زندان‌ها و اقدامات تأمینی و تربیتی کشور','آیین‌نامه سازمان زندان‌ها','regulation','رئیس قوه قضائیه','amended',DP,'متن کامل ۳۴۲ ماده با اصلاحات ۱۴۰۰/۱۰/۲۹؛ مقررات مؤسسات کیفری، حقوق زندانی، بهداشت، اشتغال، مرخصی، ملاقات و کانون اصلاح و تربیت.')
  docs[RM]=up(c,RM,'آیین‌نامه اجرایی مراقبت‌های الکترونیکی','آیین‌نامه پابند الکترونیکی','regulation','رئیس قوه قضائیه','in_force',DM,'متن کامل ۲۸ ماده درباره نصب تجهیزات، وثیقه، محدوده مراقبت، نظارت و گزارش تخلف.')
  docs[RA]=up(c,RA,'آیین‌نامه اجرایی ماده ۷۹ قانون مجازات اسلامی درباره مجازات‌های جایگزین حبس','آیین‌نامه جایگزین حبس','regulation','هیئت وزیران','in_force',DA,'متن کامل ۱۶ ماده درباره خدمات عمومی رایگان، نهادهای پذیرنده و نظارت قاضی اجرای احکام.')
  docs[RD]=up(c,RD,'دستورالعمل ساماندهی زندانیان و کاهش جمعیت کیفری زندان‌ها','دستورالعمل کاهش جمعیت کیفری','directive','رئیس قوه قضائیه','in_force',DD,'متن کامل ۲۹ ماده و ۲۳ تبصره درباره قرارهای تأمین، جایگزین حبس، اعسار، مرخصی و پایش جمعیت کیفری.')
  docs[RL]=up(c,RL,'دستورالعمل تعیین محدوده مراقبتی محکومان تحت نظارت سامانه‌های الکترونیکی','محدوده مراقبت الکترونیکی','directive','رئیس قوه قضائیه','in_force',DL,'چهار ماده درباره محدوده‌های مراقبتی ۲۰۰، ۵۰۰ و ۱۰۰۰ متر و معیار انتخاب آنها.')
  for d in docs.values():clear(c,d)
  for ref,tags in ((RE,('قاضی اجرای احکام','آزادی مشروط','نظام نیمه‌آزادی')),(RJ,('قصاص','اعدام','شلاق','دیه','تبعید')),(RP,('زندان','حقوق زندانی','مرخصی','کانون اصلاح و تربیت')),(RM,('پابند الکترونیکی','مراقبت الکترونیکی')),(RA,('مجازات جایگزین حبس','خدمات عمومی رایگان')),(RD,('حبس‌زدایی','کاهش جمعیت کیفری')),(RL,('محدوده مراقبتی','سامانه الکترونیکی'))):deco(c,docs[ref],tags)
  e=rows(c,docs[RE],RE,CRIMINAL_EXECUTION_SECTION,DE,SRC_E);j=rows(c,docs[RJ],RJ,CRIMINAL_JUDGMENTS_BYLAW,DJ,SRC_J);p=rows(c,docs[RP],RP,PRISONS_BYLAW,DP,SRC_P);m=rows(c,docs[RM],RM,ELECTRONIC_MONITORING_BYLAW,DM,SRC_M);a=rows(c,docs[RA],RA,ALTERNATIVE_PUNISHMENTS_BYLAW,DA,SRC_A);d=rows(c,docs[RD],RD,PRISON_POPULATION_DIRECTIVE,DD,SRC_D);l=rows(c,docs[RL],RL,ELECTRONIC_LIMITS_DIRECTIVE,DL,SRC_L)
  add_relation(c,docs[RJ],'implements',docs[RE],from_article_id=j[1],to_article_id=e[549],description='آیین‌نامه اجرایی نحوه اجرای مجازات‌های موضوع ماده ۵۴۹.')
  add_relation(c,docs[RP],'implements',docs[RE],from_article_id=p[1],to_article_id=e[489],description='نظام اداره زندان و اجرای وظایف قاضی اجرا درباره زندانیان.')
  add_relation(c,docs[RM],'implements',docs[RE],from_article_id=m[1],to_article_id=e[557],description='مراقبت الکترونیکی موضوع ماده ۵۵۷.')
  add_relation(c,docs[RA],'implements',docs[RE],from_article_id=a[1],to_article_id=e[557],description='اجرای خدمات عمومی رایگان و مجازات‌های جایگزین حبس.')
  add_relation(c,docs[RD],'implements',docs[RE],from_article_id=d[1],description='سیاست‌های اجرایی کاهش بازداشت و حبس در مراحل دادرسی و اجرا.')
  add_relation(c,docs[RD],'cites',docs[RP],from_article_id=d[13],description='نظارت بر زندان‌ها، شوراهای طبقه‌بندی و ارفاق‌های قانونی.')
  add_relation(c,docs[RL],'implements',docs[RM],from_article_id=l[1],to_article_id=m[27],description='تعیین درجات محدوده مراقبتی در اجرای آیین‌نامه مراقبت الکترونیکی.')
  for ref,desc in (('QADK-1392','این سند گزیده مواد ۴۸۴ تا ۵۵۸ قانون کامل آیین دادرسی کیفری است.'),('QMA-1392','ارتباط اجرای مجازات‌ها و جایگزین‌های حبس با قانون مجازات اسلامی.'),('QNEM-1394','اجرای محکومیت‌های مالی و جزای نقدی.')):
   x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
   if x:add_relation(c,docs[RE],'cites',x['id'],description=desc)
  x=c.execute("select id from documents where reference_code='QMA-1392'").fetchone()
  if x:
   add_relation(c,docs[RJ],'cites',x['id'],description='ماده ۲۱۶ قانون مجازات اسلامی و مقررات حدود، قصاص و دیات.')
   add_relation(c,docs[RA],'cites',x['id'],description='آیین‌نامه ماده ۷۹ قانون مجازات اسلامی.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] اجرای احکام کیفری: مواد ۴۸۴ تا ۵۵۸ = ۷۵ | آیین‌نامه اجرای مجازات‌ها = ۱۴۸')
  print('[OK] زندان‌ها=۳۴۲ | مراقبت الکترونیکی=۲۸ | جایگزین حبس=۱۶ | کاهش جمعیت=۲۹ | محدوده مراقبتی=۴')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
