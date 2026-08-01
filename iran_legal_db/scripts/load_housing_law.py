# -*- coding: utf-8 -*-
"""Load tenancy, apartment ownership, building presale and registration package."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from housing_law import *
R56='QRM-1356';R62='QRM-1362';R76='QRM-1376';RB='AIRM-1378';RA='QTAP-1343';RAB='AITAP-1347';RP='QPFS-1389';RPB='AIPFS-1393';RR='QERF-1403';REFS=(R56,R62,R76,RB,RA,RAB,RP,RPB,RR)
D56='1977-07-24';D62='1983-05-03';D76='1997-08-17';D78='1999-05-09';D43='1965-03-07';D47='1968-04-28';D71='1992-04-19';D89='2011-01-02';D93='2014-05-28';D1403A='2024-04-29';D1403='2024-06-23'
SRC56='قانون روابط موجر و مستأجر مصوب ۱۳۵۶/۰۵/۰۲؛ متن کامل با اصلاحات تا ۱۳۵۸، پایگاه اختبار.';SRC62='قانون روابط موجر و مستأجر مصوب ۱۳۶۲/۰۲/۱۳ با اصلاحات تا ۱۳۷۴.';SRC76='قانون روابط موجر و مستأجر مصوب ۱۳۷۶/۰۵/۲۶ با اصلاح ماده ۲ در ۱۴۰۳.';SRCB='آیین‌نامه اجرایی قانون روابط موجر و مستأجر ۱۳۷۶، مصوب ۱۳۷۸/۰۲/۱۹.';SRCA='قانون تملک آپارتمان‌ها مصوب ۱۳۴۳/۱۲/۱۶ با اصلاحات بعدی.';SRCAB='آیین‌نامه اجرایی قانون تملک آپارتمان‌ها مصوب ۱۳۴۷/۰۲/۰۸ با اصلاحات تا ۱۳۷۱.';SRCP='قانون پیش‌فروش ساختمان مصوب ۱۳۸۹/۱۰/۱۲ با اصلاحات قانون الزام به ثبت رسمی معاملات اموال غیرمنقول.';SRCPB='آیین‌نامه اجرایی قانون پیش‌فروش ساختمان، تصویب‌نامه شماره ۲۹۸۱۱/ت۴۷۷۴۱هـ مصوب ۱۳۹۳/۰۳/۰۷.';SRCR='قانون الزام به ثبت رسمی معاملات اموال غیرمنقول، مصوب مجلس ۱۴۰۱/۰۹/۰۶ و مجمع تشخیص مصلحت نظام ۱۴۰۳/۰۲/۲۶.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,status,rat,eff,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute("insert into authorities(name_fa,authority_type)values(?,'legislative')",(auth,)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 for topic in ('حقوق مدنی','حقوق ثبت اسناد و املاک'):link_document_topic(c,d,topic)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,key,no,text,v,cur,eff,exp,src,note=None):return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def rows(c,d,ref,data,date,src):
 o={}
 for n,t in data:o[n]=av(c,d,ref,n,pn(n),t,1,True,date,None,src)
 return o
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[R56]=up(c,R56,'قانون روابط موجر و مستأجر مصوب ۱۳۵۶','موجر و مستأجر ۱۳۵۶','law','مجلس شورای ملی (پیش از انقلاب)','amended',D56,D56,'متن کامل ۳۲ ماده؛ همچنان درباره روابط تجاری و قراردادهای مشمول زمان خود کاربرد دارد.')
  docs[R62]=up(c,R62,'قانون روابط موجر و مستأجر مصوب ۱۳۶۲','موجر و مستأجر ۱۳۶۲','law','مجلس شورای اسلامی','amended',D62,D62,'متن کامل ۱۵ ماده درباره اماکن مسکونی و روابط استیجاری پیش از قانون ۱۳۷۶.')
  docs[R76]=up(c,R76,'قانون روابط موجر و مستأجر مصوب ۱۳۷۶ با اصلاح ماده ۲','موجر و مستأجر ۱۳۷۶','law','مجلس شورای اسلامی','amended',D76,D76,'متن کامل ۱۳ ماده؛ ماده ۲ در سال ۱۴۰۳ برای ثبت سامانه‌ای قرارداد و اخذ کد رهگیری نسخه‌بندی شده است.')
  docs[RB]=up(c,RB,'آیین‌نامه اجرایی قانون روابط موجر و مستأجر ۱۳۷۶','آیین‌نامه اجاره ۱۳۷۶','regulation','هیئت وزیران','amended',D78,D78,'پوشش شماره‌های ۱ تا ۲۰؛ ماده ۱۶ سابق در اصلاح ساختاری به ماده ۱۵ تغییر شماره یافته و تاریخی است.')
  docs[RA]=up(c,RA,'قانون تملک آپارتمان‌ها با اصلاحات','قانون تملک آپارتمان‌ها','law','مجلس شورای ملی (پیش از انقلاب)','amended',D43,D43,'پانزده ماده و ماده ۱۰ مکرر درباره قسمت‌های اختصاصی و مشترک، اداره ساختمان و هزینه‌های مشترک.')
  docs[RAB]=up(c,RAB,'آیین‌نامه اجرایی قانون تملک آپارتمان‌ها','آیین‌نامه آپارتمان‌ها','regulation','هیئت وزیران','amended',D47,D47,'متن ۲۷ ماده‌ای؛ تاریخچه تبصره ۲ ماده ۱۶ که در سال ۱۳۷۱ منسوخ شد نگهداری شده است.')
  docs[RP]=up(c,RP,'قانون پیش‌فروش ساختمان با اصلاحات ۱۴۰۳','قانون پیش‌فروش ساختمان','law','مجلس شورای اسلامی','amended',D89,D89,'پوشش ۲۵ شماره ماده؛ مواد ۲۰ و ۲۱ تاریخی و مواد ۱، ۲ و ۴ با نسخه پیش از اصلاحات ثبت رسمی ۱۴۰۳ نگهداری شده‌اند.')
  docs[RPB]=up(c,RPB,'آیین‌نامه اجرایی قانون پیش‌فروش ساختمان','آیین‌نامه پیش‌فروش ساختمان','regulation','هیئت وزیران','in_force',D93,D93,'متن کامل ۲۲ ماده درباره سند رسمی، ثبت، مهندس ناظر، بیمه و انتقال حقوق پیش‌فروش.')
  docs[RR]=up(c,RR,'قانون الزام به ثبت رسمی معاملات اموال غیرمنقول','الزام ثبت رسمی املاک','law','مجلس شورای اسلامی و مجمع تشخیص مصلحت نظام','in_force',D1403,D1403,'متن کامل ۱۵ ماده؛ ثبت رسمی معاملات، سامانه اسناد غیررسمی و اصلاحات قانون پیش‌فروش ساختمان.')
  for d in docs.values():clear(c,d)
  for ref,tags in ((R56,('حق کسب و پیشه','تخلیه','اجاره‌بها')),(R62,('اجاره مسکونی','عسر و حرج')),(R76,('سرقفلی','کد رهگیری','ودیعه')),(RB,('دستور تخلیه','اجرای ثبت')),(RA,('قسمت مشترک','هزینه مشترک','مجمع عمومی مالکان')),(RAB,('مدیر ساختمان','هزینه مشترک')),(RP,('پیش‌فروش ساختمان','پیش‌خریدار','سند رسمی')),(RPB,('شناسنامه فنی','مهندس ناظر')),(RR,('ثبت رسمی','سامانه اسناد غیررسمی','اموال غیرمنقول'))):deco(c,docs[ref],tags)
  ids56=rows(c,docs[R56],R56,LANDLORD_1356,D56,SRC56);ids62=rows(c,docs[R62],R62,LANDLORD_1362,D62,SRC62)
  ids76={}
  for n,t in LANDLORD_1376_CURRENT:
   if n==2:
    av(c,docs[R76],R76,n,pn(n),LANDLORD_1376_ART2_OLD,1,False,D76,D1403A,SRC76,'متن مصوب ۱۳۷۶.')
    ids76[n]=av(c,docs[R76],R76,n,pn(n),t,2,True,D1403A,None,SRC76,'نسخه جاری با الزام ثبت سامانه‌ای و کد رهگیری.')
   else:ids76[n]=av(c,docs[R76],R76,n,pn(n),t,1,True,D76,None,SRC76)
  idsb={}
  for n,t in sorted(LANDLORD_BYLAW_1378):
   if n==16:av(c,docs[RB],RB,n,pn(n),t,1,False,D78,D78,SRCB,'یادداشت ساختاری: ماده ۱۶ سابق به ماده ۱۵ تغییر شماره یافت.');continue
   idsb[n]=av(c,docs[RB],RB,n,pn(n),t,1,True,D78,None,SRCB)
  aptids={}
  for key,t in APARTMENT_LAW:
   no='۱۰ مکرر' if key=='10bis' else pn(key);aptids[key]=av(c,docs[RA],RA,key,no,t,1,True,D43,None,SRCA)
  abids={}
  for n,t in APARTMENT_BYLAW_CURRENT:
   if n==16:
    av(c,docs[RAB],RAB,n,pn(n),APARTMENT_BYLAW_ART16_OLD,1,False,D47,D71,SRCAB,'نسخه پیش از نسخ تبصره ۲.')
    abids[n]=av(c,docs[RAB],RAB,n,pn(n),t,2,True,D71,None,SRCAB,'نسخه جاری بدون تبصره ۲ منسوخ.')
   else:abids[n]=av(c,docs[RAB],RAB,n,pn(n),t,1,True,D47,None,SRCAB)
  pre=dict(PRESALE_PRE1403);pcur=dict(PRESALE_CURRENT);pids={};pold={}
  for n in range(1,26):
   if n in (1,2,4):
    old=PRESALE_ART1_OLD if n==1 else PRESALE_ART2_OLD if n==2 else pre[n]
    pold[n]=av(c,docs[RP],RP,n,pn(n),old,1,False,D89,D1403,SRCP,'متن پیش از اصلاحات قانون الزام ثبت رسمی.')
    pids[n]=av(c,docs[RP],RP,n,pn(n),pcur[n],2,True,D1403,None,SRCR,'نسخه جاری پس از اصلاح ۱۴۰۳.')
   elif n in (20,21):pold[n]=av(c,docs[RP],RP,n,pn(n),pre[n],1,False,D89,D1403,SRCP,'حذف به موجب ماده ۱۵ قانون الزام به ثبت رسمی معاملات اموال غیرمنقول.')
   else:pids[n]=av(c,docs[RP],RP,n,pn(n),pcur[n],1,True,D89,None,SRCP)
  pbids=rows(c,docs[RPB],RPB,PRESALE_BYLAW,D93,SRCPB);rids=rows(c,docs[RR],RR,MANDATORY_REGISTRATION_1403,D1403,SRCR)
  add_relation(c,docs[RB],'implements',docs[R76],from_article_id=idsb[1],to_article_id=ids76[12],description='آیین‌نامه اجرایی موضوع ماده ۱۲ قانون ۱۳۷۶.')
  add_relation(c,docs[RAB],'implements',docs[RA],from_article_id=abids[1],description='آیین‌نامه اداره قسمت‌های مشترک و ساختمان.')
  add_relation(c,docs[RPB],'implements',docs[RP],from_article_id=pbids[1],to_article_id=pids[25],description='آیین‌نامه اجرایی موضوع ماده ۲۵ قانون پیش‌فروش.')
  for n in (1,2,4):add_relation(c,docs[RR],'amends',docs[RP],from_article_id=rids[15],to_article_id=pold[n],description=f'اصلاح ماده {pn(n)} قانون پیش‌فروش در ۱۴۰۳.')
  for n in (20,21):add_relation(c,docs[RR],'abrogates',docs[RP],from_article_id=rids[15],to_article_id=pold[n],description=f'حذف ماده {pn(n)} قانون پیش‌فروش در ۱۴۰۳.')
  add_relation(c,docs[RR],'amends',docs[RP],from_article_id=rids[15],description='اصلاحات تکمیلی مواد ۱۴ و ۲۳ قانون پیش‌فروش ساختمان.')
  add_relation(c,docs[R76],'cites',docs[R56],description='روابط استیجاری پیش از قانون ۱۳۷۶ حسب تاریخ و نوع محل تابع مقررات سابق است.')
  add_relation(c,docs[R76],'cites',docs[R62],description='قراردادهای مسکونی پیشین حسب مورد تابع قانون ۱۳۶۲ باقی می‌مانند.')
  for src,targets in ((R76,('QM-1307','QEA-1356')),(RA,('QM-1307',)),(RP,('QRS-1310',)),(RR,('QRS-1310','QAH-1319'))):
   for target in targets:
    d=c.execute('select id from documents where reference_code=?',(target,)).fetchone()
    if d:add_relation(c,docs[src],'cites',d['id'],description='ارتباط با قواعد مدنی، ثبتی یا اجرایی مرتبط با املاک.')
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] موجر و مستأجر: ۱۳۵۶=۳۲، ۱۳۶۲=۱۵، ۱۳۷۶=۱۳/۱۴ نسخه، آیین‌نامه=۲۰ شماره/۱۹ جاری')
  print('[OK] آپارتمان‌ها=۱۶، آیین‌نامه=۲۷/۲۸ نسخه | پیش‌فروش=۲۵/۲۸ نسخه، آیین‌نامه=۲۲ | الزام ثبت رسمی=۱۵')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
