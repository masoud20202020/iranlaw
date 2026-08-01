# -*- coding: utf-8 -*-
"""Load core Iranian banking and monetary legislation."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from banking_law import *
CB='QBC-1402';PB='QPB-1351';UF='QOBR-1362';BR='AITMP-1362';BF='AITAB-1362';FL='QTSB-1386';R794='RVR-794-1399'
REFS=(CB,PB,UF,BR,BF,FL,R794)
SRC_CB='قانون بانک مرکزی جمهوری اسلامی ایران مصوب ۱۴۰۲؛ متن کامل ۶۷ ماده از اختبار و مقابله با ابلاغ بانک مرکزی.'
SRC_PB='قانون پولی و بانکی کشور مصوب ۱۳۵۱؛ متن کامل ۴۵ ماده و وضعیت نسخ صریح ماده ۶۷ قانون بانک مرکزی.'
SRC_UF='قانون عملیات بانکی بدون ربا مصوب ۱۳۶۲؛ متن کامل ۲۷ ماده با اصلاحات بعدی.'
SRC_BR='آیین‌نامه تجهیز منابع پولی، موضوع فصل دوم قانون عملیات بانکی بدون ربا؛ متن کامل ۱۲ ماده.'
SRC_BF='آیین‌نامه تسهیلات اعطایی بانکی، موضوع فصل سوم قانون عملیات بانکی بدون ربا؛ متن تلفیقی ۹۰ ماده با اصلاحات تا ۱۴۰۱.'
SRC_FL='قانون تسهیل اعطای تسهیلات بانکی و کاهش هزینه‌های طرح مصوب ۱۳۸۶؛ متن کامل ۹ ماده.'
SRC_R='قسمت لازم‌الاتباع رأی وحدت رویه شماره ۷۹۴ هیأت عمومی دیوان عالی کشور.'
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
def deco(c,d,tags,topics=('حقوق پول و بانک','حقوق تجارت')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def seq(c,d,ref,data,eff,src):
 out={}
 for k,t in data:out[k]=add_article(c,d,article_no=pn(k),article_key=f'{ref}:{k}',version_no=1,is_current=1,effective_date=eff,text=t,source_note=src)
 return out
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  specs=(
   (CB,'قانون بانک مرکزی جمهوری اسلامی ایران','قانون بانک مرکزی','law','مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام','legislative','in_force','2023-06-20','2024-05-27','متن کامل ۶۷ ماده؛ لازم‌الاجرا از ۱۴۰۳/۰۳/۰۷؛ جایگزین بخش مهمی از قانون پولی و بانکی ۱۳۵۱.'),
   (PB,'قانون پولی و بانکی کشور با وضعیت تنقیحی پس از قانون بانک مرکزی','قانون پولی و بانکی','law','مجلس شورای ملی (پیش از انقلاب)','legislative','amended','1972-07-09','1972-07-09','۴۵ کلید و ۴۶ ردیف؛ ۱۵ ماده/بند جاری و ۳۱ ردیف تاریخی پس از نسخ‌های صریح قانون بانک مرکزی.'),
   (UF,'قانون عملیات بانکی بدون ربا (بهره) با اصلاحات','قانون عملیات بانکی بدون ربا','law','مجلس شورای اسلامی','legislative','amended','1983-08-30','1984-03-21','۲۷ ماده؛ ماده ۹ با تاریخچه پیش و پس از الحاق استصناع، مرابحه و خرید دین.'),
   (BR,'آیین‌نامه تجهیز منابع پولی موضوع فصل دوم قانون عملیات بانکی بدون ربا','آیین‌نامه تجهیز منابع پولی','regulation','هیأت وزیران','executive','in_force','1983-12-18','1984-03-21','متن کامل ۱۲ ماده درباره سپرده قرض‌الحسنه و سپرده سرمایه‌گذاری مدت‌دار.'),
   (BF,'آیین‌نامه تسهیلات اعطایی بانکی موضوع فصل سوم قانون عملیات بانکی بدون ربا','آیین‌نامه تسهیلات بانکی','regulation','هیأت وزیران','executive','amended','1984-01-04','1984-03-21','متن تلفیقی ۹۰ ماده؛ عقود قرض‌الحسنه، مشارکت، مضاربه، سلف، فروش اقساطی، اجاره به شرط تملیک، جعاله، مزارعه، مساقات، استصناع، مرابحه و خرید دین.'),
   (FL,'قانون تسهیل اعطای تسهیلات بانکی و کاهش هزینه‌های طرح','قانون تسهیل تسهیلات بانکی','law','مجلس شورای اسلامی','legislative','in_force','2007-06-26','2007-07-18','متن کامل ۹ ماده درباره وثیقه طرح، مهلت بررسی، اعتبارسنجی و قراردادهای بانکی.'),
   (R794,'رأی وحدت رویه شماره ۷۹۴ درباره بطلان شرط سود مازاد بر مصوبات بانکی','رأی وحدت رویه ۷۹۴','unified_ruling','دیوان عالی کشور','judicial','in_force','2020-08-11','2020-08-11','لازم‌الاتباع بودن نرخ‌های مصوب بانک مرکزی و بطلان شرط سود مازاد در قرارداد تسهیلات.'),)
  for x in specs:docs[x[0]]=up(c,*x)
  for d in docs.values():clear(c,d)
  deco(c,docs[CB],('بانک مرکزی','هیأت‌عالی','گزیر','مؤسسه اعتباری','رمزپول','نظام پرداخت','ناترازی بانک'))
  deco(c,docs[PB],('پول رایج','بانکداری','ورشکستگی بانک','قانون منسوخ جزئی','نظارت بانکی'))
  deco(c,docs[UF],('بانکداری بدون ربا','قرض‌الحسنه','مضاربه','مرابحه','اجاره به شرط تملیک','خرید دین'))
  deco(c,docs[BR],('سپرده بانکی','سپرده سرمایه‌گذاری','حق‌الوکاله','قرض‌الحسنه'))
  deco(c,docs[BF],('تسهیلات بانکی','وثیقه','مشارکت مدنی','مرابحه','استصناع','خرید دین'))
  deco(c,docs[FL],('وثیقه طرح','اعتبارسنجی','اتحادیه بانکی','تسهیلات تولید'))
  deco(c,docs[R794],('سود بانکی','نرخ سود','شرط باطل','نظم عمومی اقتصادی'),('حقوق پول و بانک','آیین دادرسی مدنی'))
  cbids=seq(c,docs[CB],CB,CENTRAL_BANK_LAW,'2024-05-27',SRC_CB)
  pbids={};pbcurrent={}
  for r in MONETARY_BANKING_ROWS:
   aid=add_article(c,docs[PB],article_no=r['article_no'],article_key=f"{PB}:{r['key']}",version_no=r['version_no'],is_current=int(r['is_current']),effective_date=r['effective_date'],expiry_date=r['expiry_date'],text=r['text'],source_note=SRC_PB,notes=r['notes']);pbids[(r['key'],r['version_no'])]=aid
   if r['is_current']:pbcurrent[r['key']]=aid
  ufids={};ufcurrent={}
  for r in USURY_FREE_ROWS:
   aid=add_article(c,docs[UF],article_no=r['article_no'],article_key=f"{UF}:{r['key']}",version_no=r['version_no'],is_current=int(r['is_current']),effective_date=r['effective_date'],expiry_date=r['expiry_date'],text=r['text'],source_note=SRC_UF,notes=r['notes']);ufids[(r['key'],r['version_no'])]=aid
   if r['is_current']:ufcurrent[r['key']]=aid
  brids=seq(c,docs[BR],BR,BANK_RESOURCES_BYLAW,'1984-03-21',SRC_BR);bfids=seq(c,docs[BF],BF,BANK_FACILITIES_BYLAW,'1984-03-21',SRC_BF);flids=seq(c,docs[FL],FL,BANK_FACILITATION_LAW,'2007-07-18',SRC_FL)
  rid=add_article(c,docs[R794],article_no='رأی',article_key=f'{R794}:decision',version_no=1,is_current=1,effective_date='2020-08-11',text=RULING_794,source_note=SRC_R)
  # Express repeal network under article 67.
  add_relation(c,docs[CB],'amends',docs[PB],from_article_id=cbids['67'],description='اصلاح ساختار قانون پولی و بانکی و انتقال وظایف شورای پول و اعتبار به هیأت‌عالی.')
  repealed=list(range(1,18))+list(range(19,27))+[39,40,42,43,44]
  for n in repealed:add_relation(c,docs[CB],'abrogates',docs[PB],from_article_id=cbids['67'],to_article_id=pbids[(str(n),1)],description=f'نسخ صریح ماده {pn(n)} قانون پولی و بانکی از ۱۴۰۳/۰۳/۰۷.')
  add_relation(c,docs[CB],'amends',docs[PB],from_article_id=cbids['67'],to_article_id=pbcurrent['18'],description='نسخ بندهای ب، ج و د ماده ۱۸ و انتقال وظایف شورا به هیأت‌عالی.')
  add_relation(c,docs[UF],'amends',docs[PB],description='تطبیق عملیات بانکی با موازین بدون ربا و سلب وظایف واگذارشده از مراجع پیشین.')
  add_relation(c,docs[BR],'implements',docs[UF],from_article_id=brids['1'],to_article_id=ufcurrent['3'],description='انواع سپرده و تجهیز منابع پولی.')
  add_relation(c,docs[BR],'implements',docs[UF],from_article_id=brids['9'],to_article_id=ufcurrent['5'],description='وکالت در به‌کارگیری سپرده و تقسیم منافع.')
  add_relation(c,docs[BF],'implements',docs[UF],from_article_id=bfids['1'],to_article_id=ufcurrent['7'],description='ضوابط عمومی تسهیلات اعطایی و بازگشت منابع.')
  add_relation(c,docs[BF],'implements',docs[UF],from_article_id=bfids['81'],to_article_id=ufcurrent['9'],description='ضوابط عقد مرابحه در تسهیلات بانکی.')
  add_relation(c,docs[BF],'implements',docs[UF],from_article_id=bfids['86'],to_article_id=ufcurrent['9'],description='ضوابط خرید دین در تسهیلات بانکی.')
  add_relation(c,docs[FL],'cites',docs[UF],from_article_id=flids['7'],to_article_id=ufcurrent['15'],description='اعتبار اجرایی قراردادهای منعقدشده در اجرای قانون عملیات بانکی بدون ربا.')
  for n in (10,11,14):add_relation(c,docs[R794],'interprets',docs[PB],from_article_id=rid,to_article_id=pbids[(str(n),1)],description='مبنای تاریخی آمره بودن نرخ‌های مصوب؛ مواد مزبور بعداً در ۱۴۰۳ نسخ شدند.')
  add_relation(c,docs[R794],'interprets',docs[PB],from_article_id=rid,to_article_id=pbcurrent['37'],description='الزام بانک‌ها به رعایت قانون، آیین‌نامه و دستورات بانک مرکزی.')
  add_relation(c,docs[R794],'interprets',docs[UF],from_article_id=rid,to_article_id=ufcurrent['20'],description='بطلان شرط سود مازاد بر نرخ‌های مصوب بانک مرکزی.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] بانک مرکزی=۶۷؛ پولی و بانکی=۴۵ کلید/۴۶ ردیف؛ عملیات بدون ربا=۲۷ کلید/۲۸ ردیف')
  print('[OK] آیین‌نامه‌ها=۱۲+۹۰؛ تسهیل تسهیلات=۹؛ رأی وحدت رویه=۱')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
