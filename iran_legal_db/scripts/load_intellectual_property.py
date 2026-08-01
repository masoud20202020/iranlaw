# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from intellectual_property import COPYRIGHT,SOFTWARE,TRANSLATION,INDUSTRIAL
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');SRC={'QHMMH-1348':'https://www.ekhtebar.ir/قانون-حمايت-حقوق-مولفان-و-مصنفان-و-هنرم/','QHPNR-1379':'https://www.ekhtebar.ir/قانون-حمايت-از-حقوق-پديد-آورندگان-نرم/','QTKA-1352':'https://www.ekhtebar.ir/قانون-ترجمه-و-تكثير-كتب-و-نشريات-و-آثار/','QMS-1403':'https://www.ekhtebar.ir/قانون-حمایت-از-مالکیت-صنعتی-مصوب-۱۴۰۳/'}
def get(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def doc(c,ref,title,short,date,note):
 d=get(c,'select id from documents where reference_code=?',ref)
 if not d:d=get_or_create_document(c,title=title,short_title=short,type_code='law',issuing_authority='مجلس شورای اسلامی',status_code='amended' if ref=='QHMMH-1348' else 'in_force',ratification_date=date,effective_date=date,reference_code=ref,notes=note)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(title,short,get(c,'select id from document_types where code=?','law'),get(c,'select id from authorities where name_fa=?','مجلس شورای اسلامی'),get(c,'select id from statuses where code=?','amended' if ref=='QHMMH-1348' else 'in_force'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def add(c,d,ref,rs,date,note):
 z={}
 for n,t in rs:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=SRC[ref],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QHMMH-1348','قانون حمایت حقوق مؤلفان و مصنفان و هنرمندان با اصلاح ماده ۱۲','حقوق مؤلفان','1970-01-01','متن جاری ۳۳ ماده‌ای با آخرین اصلاح ماده ۱۲ در ۱۳۸۹.'),('QHPNR-1379','قانون حمایت از حقوق پدیدآورندگان نرم‌افزارهای رایانه‌ای','حقوق نرم‌افزار','2000-12-24','متن کامل ۱۷ ماده و تبصره.'),('QTKA-1352','قانون ترجمه و تکثیر کتب و نشریات و آثار صوتی','ترجمه و تکثیر آثار','1973-12-27','متن کامل ۱۲ ماده.'),('QMS-1403','قانون حمایت از مالکیت صنعتی','مالکیت صنعتی','2024-05-21','متن کامل ۱۵۰ ماده؛ قانون جاری اختراع، طرح صنعتی، علامت، نام تجاری و اسرار تجاری.')]
  ds={x[0]:doc(c,*x) for x in sp}
  ids={}
  for ref,d in ds.items():
   clear(c,d);link_document_topic(c,d,'حقوق تجارت')
   for tag in ('مالکیت فکری','مالکیت صنعتی','حقوق پدیدآورنده'):link_document_tag(c,d,add_tag(c,tag))
  for ref,rs,date,note in [('QHMMH-1348',COPYRIGHT,'1970-01-01','متن تلفیقی جاری؛ تاریخچه ماده ۱۲ به‌طور مجزا در مرحله تکمیلی ثبت می‌شود.'),('QHPNR-1379',SOFTWARE,'2000-12-24','متن کامل.'),('QTKA-1352',TRANSLATION,'1973-12-27','متن کامل.'),('QMS-1403',INDUSTRIAL,'2024-05-21','متن کامل؛ قانون ۱۴۰۳ جایگزین نظام سابق ثبت اختراعات، طرح‌های صنعتی و علائم تجاری است.')]:ids[ref]=add(c,ds[ref],ref,rs,date,note)
  add_relation(c,ds['QHPNR-1379'],'cites',ds['QMS-1403'],description='ارجاع موضوعی نرم‌افزارِ واجد شرایط اختراع به نظام مالکیت صنعتی.')
  add_relation(c,ds['QTKA-1352'],'cites',ds['QHMMH-1348'],description='ارتباط موضوعی حمایت از حقوق پدیدآورندگان و تکثیر آثار.')
  c.commit();print('loaded intellectual property',sum(len(x) for x in (COPYRIGHT,SOFTWARE,TRANSLATION,INDUSTRIAL)))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
