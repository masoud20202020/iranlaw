# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from consumer_competition import CONSUMER,CONSUMER_BYLAW,AUTO,ARTICLE44
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');S={'QE44-1386':'https://www.ekhtebar.ir/قانون-اجرای-سیاستهای-کلی-اصل-چهل-و-چهار/','QHMC-1388':'https://www.ekhtebar.ir/قانون-حمایت-از-حقوق-مصرف-کنندگان-مصوب-۱/','AIHMC-1390':'https://www.ekhtebar.ir/آیین‌نامه-اجرایی-قانون-حمایت-از-حقوق/','QHMCA-1386':'https://www.ekhtebar.ir/قانون-حمایت-از-حقوق-مصرف‌کنندگان-خودر/'}
def one(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def doc(c,ref,title,short,typ,date,note):
 d=one(c,'select id from documents where reference_code=?',ref)
 if not d:d=get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority='مجلس شورای اسلامی' if typ=='law' else 'هیئت وزیران',status_code='amended' if ref=='QE44-1386' else 'in_force',ratification_date=date,effective_date=date,reference_code=ref,notes=note)
 auth='مجلس شورای اسلامی' if typ=='law' else 'هیئت وزیران';c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(title,short,one(c,'select id from document_types where code=?',typ),one(c,'select id from authorities where name_fa=?',auth),one(c,'select id from statuses where code=?','amended' if ref=='QE44-1386' else 'in_force'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def rows(c,d,ref,rs,date,note):
 z={}
 for n,t in rs:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[ref],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QE44-1386','قانون اجرای سیاست‌های کلی اصل چهل و چهارم قانون اساسی با اصلاحات تا ۱۴۰۲','اجرای سیاست‌های کلی اصل ۴۴','law','2008-01-28','متن جاری ۹۲ ماده‌ای؛ پوشش کامل قانون و بخش رقابت و شورای رقابت.'),('QHMC-1388','قانون حمایت از حقوق مصرف‌کنندگان','حمایت از مصرف‌کنندگان','law','2009-10-07','متن کامل ۲۲ ماده.'),('AIHMC-1390','آیین‌نامه اجرایی قانون حمایت از حقوق مصرف‌کنندگان','آیین‌نامه حمایت از مصرف‌کنندگان','regulation','2011-10-09','متن جاری منبع شامل ۴۲ ماده شماره‌دار: ۱ تا ۳۸ و ۴۰ تا ۴۳؛ ماده ۳۹ در منبع جاری موجود نیست و از آن ساخته نشده است.'),('QHMCA-1386','قانون حمایت از حقوق مصرف‌کنندگان خودرو','حمایت از مصرف‌کنندگان خودرو','law','2007-06-13','متن کامل ۱۱ ماده.')]
  ds={x[0]:doc(c,*x) for x in sp};ids={}
  for ref,d in ds.items():
   clear(c,d);link_document_topic(c,d,'حقوق تجارت')
   for tag in ('حقوق مصرف‌کننده','رقابت','ضمانت کالا','خدمات پس از فروش'):link_document_tag(c,d,add_tag(c,tag))
  for ref,rs,date,note in [('QE44-1386',ARTICLE44,'2008-01-28','متن تلفیقی جاری با اصلاحات تا ۱۴۰۲.'),('QHMC-1388',CONSUMER,'2009-10-07','متن کامل.'),('AIHMC-1390',CONSUMER_BYLAW,'2011-10-09','متن منبع‌دار؛ نبود ماده ۳۹ در نسخه منبع مستند شده.'),('QHMCA-1386',AUTO,'2007-06-13','متن کامل.')]:ids[ref]=rows(c,ds[ref],ref,rs,date,note)
  add_relation(c,ds['AIHMC-1390'],'implements',ds['QHMC-1388'],description='آیین‌نامه اجرایی قانون حمایت از حقوق مصرف‌کنندگان.')
  add_relation(c,ds['QHMCA-1386'],'cites',ds['QHMC-1388'],description='حمایت تخصصی خودرو در امتداد نظام عمومی حقوق مصرف‌کننده.')
  add_relation(c,ds['QHMC-1388'],'cites',ds['QE44-1386'],description='ارتباط موضوعی تبانی و شرایط غیرعادلانه با رقابت.')
  c.commit();print('loaded consumer competition',sum(len(x) for x in (ARTICLE44,CONSUMER,CONSUMER_BYLAW,AUTO)))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
