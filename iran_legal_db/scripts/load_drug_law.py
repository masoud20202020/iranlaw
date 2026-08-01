# -*- coding: utf-8 -*-
"""Load narcotics law, executive/treatment rules and leading unified rulings."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from drug_law import *
RL='QMM-1367';RA='E45MM-1396';RB='AIMM-1377';RT='AIDM-1391';R738='RVR-738-1393';R743='RVR-743-1394';R814='RVR-814-1400';R826='RVR-826-1401';R846='RVR-846-1403';REFS=(RL,RA,RB,RT,R738,R743,R814,R826,R846)
DL='1988-10-25';D76='1997-11-08';D79='2001-03-05';D89='2010-07-31';DT='2012-05-06';D94='2015-06-22';D96='2017-10-04';D1403='2024-06-24';D738='2015-01-20';D743='2015-10-27';D814='2021-10-12';D826='2022-11-15';D846='2024-04-16'
SRC_L='قانون مبارزه با مواد مخدر مصوب ۱۳۶۷/۰۸/۰۳ با اصلاحات ۱۳۷۶، ۱۳۸۹ و ۱۳۹۶ و تعدیل مبالغ جزای نقدی ۱۴۰۳؛ متن تلفیقی اختبار و مقابله با شناسنامه قانون.'
SRC_A='قانون الحاق یک ماده به قانون مبارزه با مواد مخدر مصوب ۱۳۹۶/۰۷/۱۲؛ متن کامل ماده‌واحده و ماده ۴۵.'
SRC_B='آیین‌نامه اجرایی قانون اصلاح قانون مبارزه با مواد مخدر مصوب ۱۳۷۷ با اصلاحات و نسخ‌های ۱۳۷۹؛ متن مقابله‌ای صلح.'
SRC_T='آیین‌نامه اجرایی مراکز مجاز درمان و کاهش آسیب اعتیاد مصوب ۱۳۹۱/۰۲/۱۷ ستاد مبارزه با مواد مخدر؛ متن کامل ۱۵ ماده.'
SRC738='قسمت لازم‌الاتباع رأی وحدت رویه ۷۳۸ مورخ ۱۳۹۳/۱۰/۳۰ هیأت عمومی دیوان عالی کشور.';SRC743='قسمت لازم‌الاتباع رأی وحدت رویه ۷۴۳ مورخ ۱۳۹۴/۰۸/۰۵ هیأت عمومی دیوان عالی کشور.';SRC814='قسمت لازم‌الاتباع رأی وحدت رویه ۸۱۴ مورخ ۱۴۰۰/۰۷/۲۰ هیأت عمومی دیوان عالی کشور.';SRC826='قسمت لازم‌الاتباع رأی وحدت رویه ۸۲۶ مورخ ۱۴۰۱/۰۸/۲۴ هیأت عمومی دیوان عالی کشور.';SRC846='قسمت لازم‌الاتباع رأی وحدت رویه ۸۴۶ مورخ ۱۴۰۳/۰۱/۲۸ هیأت عمومی دیوان عالی کشور.'
REPEALED_BYLAW={2,3,5,7,9,12}
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
def deco(c,d,tags,topics=('حقوق کیفری','آیین دادرسی کیفری')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,key,no,text,v,cur,eff,exp,src,note=None):return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def rows(c,d,ref,data,date,src):
 o={}
 for k,t in data:o[k]=av(c,d,ref,k,pn(k),t,1,True,date,None,src)
 return o

def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[RL]=up(c,RL,'قانون مبارزه با مواد مخدر با اصلاحات و تعدیل مبالغ ۱۴۰۳','قانون مبارزه با مواد مخدر','law','مجمع تشخیص مصلحت نظام','legislative','amended',DL,DL,'پوشش شماره‌های ۱ تا ۴۶؛ مواد ۱۰ و ۳۲ فقط تاریخی‌اند. ده ماده دارای جزای نقدی در دو نسخه پیش و پس از تعدیل ۱۴۰۳ و ماده ۴۶ دارای تاریخچه تغییر شماره است.')
  docs[RA]=up(c,RA,'قانون الحاق یک ماده به قانون مبارزه با مواد مخدر مصوب ۱۳۹۶','الحاق ماده ۴۵ مواد مخدر','amendment','مجلس شورای اسلامی','legislative','in_force',D96,D96,'متن کامل ماده‌واحده الحاق ماده ۴۵ درباره تحدید مجازات اعدام و تغییر شماره ماده ۴۵ سابق به ۴۶.')
  docs[RB]=up(c,RB,'آیین‌نامه اجرایی قانون اصلاح قانون مبارزه با مواد مخدر','آیین‌نامه اجرایی مواد مخدر','regulation','ستاد مبارزه با مواد مخدر','executive','amended',D76,D76,'پوشش کامل ۳۴ ماده؛ شش ماده کاملاً منسوخ و بند الف ماده ۴ تاریخی است؛ ۲۸ ماده جاری و هفت ردیف تاریخی.')
  docs[RT]=up(c,RT,'آیین‌نامه اجرایی مراکز مجاز درمان و کاهش آسیب اعتیاد به مواد مخدر و روانگردان‌ها','آیین‌نامه مراکز درمان اعتیاد','regulation','ستاد مبارزه با مواد مخدر','executive','in_force',DT,DT,'متن کامل ۱۵ ماده و ۱۱ تبصره درباره انواع مراکز درمان، صدور مجوز، نظارت و سامانه ملی اطلاعات.')
  for ref,num,date,title,short,note in ((R738,'۷۳۸',D738,'رأی وحدت رویه شماره ۷۳۸ درباره تعدد جرائم مواد مخدر','رأی ۷۳۸ ـ تعدد جرم','حاکمیت ماده ۱۳۴ قانون مجازات اسلامی در تعدد جرائم مواد مخدر.'),(R743,'۷۴۳',D743,'رأی وحدت رویه شماره ۷۴۳ درباره فرجام‌خواهی احکام اعدام مواد مخدر','رأی ۷۴۳ ـ فرجام اعدام','قابلیت فرجام‌خواهی احکام اعدام مواد مخدر پس از نسخ ماده ۳۲.'),(R814,'۸۱۴',D814,'رأی وحدت رویه شماره ۸۱۴ درباره مفهوم ارسال مواد مخدر','رأی ۸۱۴ ـ ارسال مواد مخدر','ارسال موضوع ماده ۴ صرفاً ارسال به خارج از کشور است.'),(R826,'۸۲۶',D826,'رأی وحدت رویه شماره ۸۲۶ درباره تأثیر عفو در سابقه محکومیت مواد مخدر','رأی ۸۲۶ ـ سابقه و عفو','مبنای سابقه قطعی بند پ ماده ۴۵، محکومیت قابل اجرا پس از عفو یا تخفیف است.'),(R846,'۸۴۶',D846,'رأی وحدت رویه شماره ۸۴۶ درباره تخفیف مجازات جرائم مواد مخدر','رأی ۸۴۶ ـ تخفیف مجازات','ممنوعیت نهادهای ارفاقی در تبصره ماده ۴۵ مانع تخفیف هنگام صدور حکم نیست.')):
   docs[ref]=up(c,ref,title,short,'unified_ruling','دیوان عالی کشور','judicial','in_force',date,date,note)
  for d in docs.values():clear(c,d)
  deco(c,docs[RL],('مواد مخدر','روانگردان صنعتی','اعتیاد','تریاک','هروئین','شیشه','مجازات اعدام'))
  deco(c,docs[RA],('ماده ۴۵','مفسد فی‌الارض','کاهش مجازات اعدام','نهادهای ارفاقی'))
  deco(c,docs[RB],('مصادره اموال','کشف مواد مخدر','اجرای احکام مواد مخدر'))
  deco(c,docs[RT],('درمان اعتیاد','کاهش آسیب','مرکز اقامتی','داروی آگونیست'),('حقوق کیفری','حقوق اداری'))
  for ref,tags in ((R738,('تعدد جرم','ماده ۱۳۴')),(R743,('فرجام‌خواهی','حکم اعدام')),(R814,('ارسال مواد مخدر','تفسیر مضیق')),(R826,('عفو رهبری','سابقه محکومیت')),(R846,('تخفیف مجازات','نهاد ارفاقی'))):deco(c,docs[ref],tags)
  law=dict(DRUG_LAW);oldfine=dict(DRUG_FINE_OLD);lids={};lold={}
  for n in range(1,47):
   k=str(n);no=pn(n)
   if n==10:
    lold[k]=av(c,docs[RL],RL,k,no,DRUG_ART10_OLD,1,False,DL,D76,SRC_L,'متن مصوب پیشین؛ ماده ۱۰ در اصلاحات ۱۳۷۶ حذف شد.');continue
   if n==32:
    lold[k]=av(c,docs[RL],RL,k,no,law[k],1,False,D76,D94,SRC_L,'نسخ صریح به موجب ماده ۵۷۰ قانون آیین دادرسی کیفری؛ فقط تاریخی.');continue
   if k in FINE_ARTICLES:
    lold[k]=av(c,docs[RL],RL,k,no,oldfine[k],1,False,D76,D1403,SRC_L,'متن پیش از تعدیل مبالغ ۱۴۰۳؛ همه نسل‌های تعدیل میانی جداگانه ثبت نشده‌اند.')
    lids[k]=av(c,docs[RL],RL,k,no,law[k],2,True,D1403,None,SRC_L,'نسخه جاری همراه توضیح صریح مبالغ تعدیل‌شده ۱۴۰۳.')
   elif n==46:
    lold[k]=av(c,docs[RL],RL,k,'۴۵',law[k],1,False,D89,D96,SRC_L,'این حکم پیش از الحاق ۱۳۹۶ با شماره ماده ۴۵ شناخته می‌شد.')
    lids[k]=av(c,docs[RL],RL,k,no,law[k],2,True,D96,None,SRC_L,'پس از الحاق ماده جدید ۴۵، شماره این حکم به ۴۶ تغییر یافت.')
   else:
    eff=D96 if n==45 else D89 if n in (43,44) else D76;lids[k]=av(c,docs[RL],RL,k,no,law[k],1,True,eff,None,SRC_L)
  aid=av(c,docs[RA],RA,'single','ماده‌واحده',ARTICLE45_AMENDMENT,1,True,D96,None,SRC_A)
  by=dict(DRUG_BYLAW);bids={};bold={}
  for n in range(1,35):
   k=str(n);no=pn(n)
   if n in REPEALED_BYLAW:bold[k]=av(c,docs[RB],RB,k,no,by[k],1,False,D76,D79,SRC_B,'نسخ صریح در اصلاحات ۱۳۷۹.')
   elif n==4:
    bold[k]=av(c,docs[RB],RB,k,no,DRUG_BYLAW_ART4_OLD,1,False,D76,D79,SRC_B,'نسخه پیش از نسخ بند الف.')
    bids[k]=av(c,docs[RB],RB,k,no,DRUG_BYLAW_ART4_CURRENT,2,True,D79,None,SRC_B,'نسخه جاری بدون بند الف منسوخ.')
   else:bids[k]=av(c,docs[RB],RB,k,no,by[k],1,True,D76,None,SRC_B)
  tids=rows(c,docs[RT],RT,TREATMENT_BYLAW,DT,SRC_T)
  rid={}
  for ref,text,date,src in ((R738,RULING_738,D738,SRC738),(R743,RULING_743,D743,SRC743),(R814,RULING_814,D814,SRC814),(R826,RULING_826,D826,SRC826),(R846,RULING_846,D846,SRC846)):
   rid[ref]=av(c,docs[ref],ref,'decision','رأی',text,1,True,date,None,src)
  add_relation(c,docs[RA],'amends',docs[RL],from_article_id=aid,to_article_id=lids['45'],description='الحاق ماده ۴۵ درباره شرایط اعدام و مجازات‌های جایگزین.')
  add_relation(c,docs[RA],'amends',docs[RL],from_article_id=aid,to_article_id=lold['46'],description='تغییر شماره ماده ۴۵ سابق به ماده ۴۶.')
  add_relation(c,docs[RB],'implements',docs[RL],from_article_id=bids['1'],to_article_id=lids['34'],description='آیین‌نامه اجرایی موضوع ماده ۳۴ قانون.')
  add_relation(c,docs[RB],'cites',docs[RL],from_article_id=bids['4'],to_article_id=lids['15'],description='اجرای مقررات درمان و ترک اعتیاد.')
  add_relation(c,docs[RT],'implements',docs[RL],from_article_id=tids['1'],to_article_id=lids['15'],description='مراکز مجاز درمان و کاهش آسیب موضوع تبصره ۱ ماده ۱۵.')
  for target in ('4','5','8'):add_relation(c,docs[R738],'interprets',docs[RL],from_article_id=rid[R738],to_article_id=lids[target],description='اعمال قواعد تعدد جرم ماده ۱۳۴ قانون مجازات اسلامی.')
  add_relation(c,docs[R743],'interprets',docs[RL],from_article_id=rid[R743],to_article_id=lold['32'],description='فرجام‌خواهی احکام اعدام پس از نسخ ماده ۳۲.')
  add_relation(c,docs[R814],'interprets',docs[RL],from_article_id=rid[R814],to_article_id=lids['4'],description='ارسال در ماده ۴ ناظر به ارسال مواد به خارج از کشور است.')
  add_relation(c,docs[R826],'interprets',docs[RL],from_article_id=rid[R826],to_article_id=lids['45'],description='اثر عفو یا تخفیف بر سابقه محکومیت قطعی بند پ ماده ۴۵.')
  add_relation(c,docs[R846],'interprets',docs[RL],from_article_id=rid[R846],to_article_id=lids['38'],description='امکان اعمال کیفیات مخففه در مرحله صدور حکم.')
  add_relation(c,docs[R846],'interprets',docs[RL],from_article_id=rid[R846],to_article_id=lids['45'],description='محدودیت تبصره ماده ۴۵ ناظر به نهادهای ارفاقی مرحله اجراست.')
  for target,desc in (('QMA-1392','قواعد تعدد، تخفیف و درجات مجازات.'),('QADK-1392','فرجام‌خواهی و تشریفات دادرسی کیفری.'),('AIZ-1400','اردوگاه کاردرمانی و نگهداری محکومان مواد مخدر.')):
   x=c.execute('select id from documents where reference_code=?',(target,)).fetchone()
   if x:add_relation(c,docs[RL],'cites',x['id'],description=desc)
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] قانون مواد مخدر: ۴۶ شماره / ۵۷ نسخه / ۴۴ جاری / ۱۳ تاریخی | الحاق ماده ۴۵=۱')
  print('[OK] آیین‌نامه عمومی=۳۴ شماره/۳۵ نسخه/۲۸ جاری | درمان و کاهش آسیب=۱۵ | آرای وحدت رویه=۵')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
