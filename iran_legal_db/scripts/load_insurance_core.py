# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import *
from insurance_core import *
INS='QBI-1316';CI='QBMC-1350';ECI='EQBMC-1353';TP='QST-1395';TP87='QST-1387';TP47='QST-1347';REFS=(INS,CI,ECI,TP,TP87,TP47)
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,status,rat,eff,note):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();d=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=note)
 aid=gi(c,'authorities','name_fa',auth) or c.execute("insert into authorities(name_fa,authority_type)values(?,'legislative')",(auth,)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,note,d));return d
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 for t in ('حقوق بیمه','حقوق مدنی'):link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def rows(c,d,ref,data,date,src,cur=True,exp=None):
 o={}
 for k,t in data:o[k]=add_article(c,d,article_no=str(k).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')),article_key=f'{ref}:{k}',version_no=1,is_current=int(cur),effective_date=date,expiry_date=exp,text=t,source_note=src)
 return o
def main():
 c=get_connection()
 try:
  c.execute('begin');D={}
  specs=((INS,'قانون بیمه مصوب ۱۳۱۶','قانون بیمه','law','مجلس شورای ملی (پیش از انقلاب)','in_force','1937-04-27','1937-04-27','متن کامل ۳۶ ماده درباره عقد بیمه، بطلان، خسارت، جانشینی و مرور زمان.'),(CI,'قانون تأسیس بیمه مرکزی ایران و بیمه‌گری با اصلاحات','قانون تأسیس بیمه مرکزی','law','مجلس شورای ملی (پیش از انقلاب)','amended','1971-06-20','1971-06-20','متن کامل ۷۷ ماده درباره ارکان بیمه مرکزی، نظارت، پروانه، تصفیه و بیمه اتکایی.'),(ECI,'قانون اصلاح قانون تأسیس بیمه مرکزی ایران و بیمه‌گری','اصلاحیه بیمه مرکزی ۱۳۵۳','amendment','مجلس شورای ملی (پیش از انقلاب)','in_force','1974-06-18','1974-06-26','ماده‌واحده اصلاح مواد ۲۸ و ۳۵.'),(TP,'قانون بیمه اجباری خسارات واردشده به شخص ثالث در اثر حوادث ناشی از وسایل نقلیه','قانون شخص ثالث ۱۳۹۵','law','مجلس شورای اسلامی','in_force','2016-05-09','2016-06-21','متن کامل ۶۶ ماده درباره بیمه‌گر، صندوق، زیان‌دیده و پرداخت خسارت.'),(TP87,'قانون اصلاح قانون بیمه اجباری مسئولیت مدنی دارندگان وسایل نقلیه مصوب ۱۳۸۷ (منسوخ)','قانون شخص ثالث ۱۳۸۷','law','کمیسیون اقتصادی مجلس شورای اسلامی','abrogated','2008-07-06','2008-08-20','متن کامل ۳۰ ماده صرفاً تاریخی؛ منسوخ به موجب ماده ۶۶ قانون ۱۳۹۵.'),(TP47,'قانون بیمه اجباری مسئولیت مدنی دارندگان وسایل نقلیه مصوب ۱۳۴۷ (منسوخ)','قانون شخص ثالث ۱۳۴۷','law','مجلس شورای ملی (پیش از انقلاب)','abrogated','1969-01-13','1969-03-21','متن کامل ۱۴ ماده صرفاً تاریخی؛ منسوخ به موجب ماده ۳۰ قانون ۱۳۸۷.'))
  for x in specs:D[x[0]]=up(c,*x)
  for d in D.values():clear(c,d)
  deco(c,D[INS],('عقد بیمه','بیمه‌گر','بیمه‌گذار','خطر بیمه‌شده','جانشینی بیمه‌گر'));deco(c,D[CI],('بیمه مرکزی','شورای عالی بیمه','پروانه بیمه‌گری','بیمه اتکایی'));deco(c,D[ECI],('اصلاحیه ۱۳۵۳','سهام خارجی'));deco(c,D[TP],('بیمه شخص ثالث','خسارت بدنی','صندوق تأمین خسارت‌های بدنی','راننده مسبب'));deco(c,D[TP87],('قانون منسوخ','شخص ثالث ۱۳۸۷'));deco(c,D[TP47],('قانون منسوخ','شخص ثالث ۱۳۴۷'))
  ins=rows(c,D[INS],INS,INSURANCE_LAW,'1937-04-27','قانون بیمه مصوب ۱۳۱۶؛ متن کامل از منبع مقابله‌ای.')
  ci=rows(c,D[CI],CI,CENTRAL_INSURANCE_LAW,'1971-06-20','قانون تأسیس بیمه مرکزی؛ متن تلفیقی با اصلاحات.')
  eci=add_article(c,D[ECI],article_no='ماده واحده',article_key=f'{ECI}:single',version_no=1,is_current=1,effective_date='1974-06-26',text=CENTRAL_AMENDMENT_1353,source_note='قانون اصلاحی مصوب ۱۳۵۳/۰۳/۲۸.')
  tp=rows(c,D[TP],TP,THIRD_PARTY_1395,'2016-06-21','قانون شخص ثالث ۱۳۹۵؛ متن کامل ۶۶ ماده.')
  t87=rows(c,D[TP87],TP87,THIRD_PARTY_1387,'2008-08-20','قانون آزمایشی شخص ثالث ۱۳۸۷؛ متن کامل تاریخی.',False,'2016-06-21')
  t47=rows(c,D[TP47],TP47,THIRD_PARTY_1347,'1969-03-21','قانون شخص ثالث ۱۳۴۷؛ متن کامل تاریخی.',False,'2008-08-20')
  add_relation(c,D[ECI],'amends',D[CI],from_article_id=eci,to_article_id=ci['28'],description='اصلاح ماده ۲۸ درباره سرمایه‌گذاری منابع بیمه مرکزی.');add_relation(c,D[ECI],'amends',D[CI],from_article_id=eci,to_article_id=ci['35'],description='اصلاح ماده ۳۵ درباره سهامداران خارجی.')
  add_relation(c,D[CI],'cites',D[INS],from_article_id=ci['17'],description='صلاحیت شورای عالی بیمه در تعیین انواع معاملات و شرایط عمومی بیمه‌نامه‌ها.')
  add_relation(c,D[TP],'abrogates',D[TP87],from_article_id=tp['66'],description='نسخ قانون شخص ثالث ۱۳۸۷.')
  for n in range(1,31):add_relation(c,D[TP],'abrogates',D[TP87],from_article_id=tp['66'],to_article_id=t87[str(n)],description='نسخ با اجرای قانون ۱۳۹۵.')
  add_relation(c,D[TP87],'abrogates',D[TP47],from_article_id=t87['30'],description='نسخ قانون شخص ثالث ۱۳۴۷.')
  for n in range(1,15):add_relation(c,D[TP87],'abrogates',D[TP47],from_article_id=t87['30'],to_article_id=t47[str(n)],description='نسخ با اجرای قانون ۱۳۸۷.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone();print('[OK] بیمه=۳۶؛ بیمه مرکزی=۷۷؛ اصلاحیه=۱؛ شخص ثالث=۶۶؛ قوانین تاریخی=۳۰+۱۴');print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
