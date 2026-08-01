# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from cooperative_law import SECTOR,COMPANIES,AMENDMENT
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');S={'QBC-1370':'https://www.ekhtebar.ir/قانون-بخش-تعاوني-اقتصاد-جمهوري-اسلامي/','QSC-1350':'https://www.ekhtebar.ir/قانون-شرکت-های-تعاونی/','EQBC-1393':'https://www.ekhtebar.com/قانون-اصلاح-موادی-از-قانون-بخش-تعاونی-ا/'}
def one(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def doc(c,ref,title,short,typ,date,note):
 d=one(c,'select id from documents where reference_code=?',ref);auth='مجلس شورای اسلامی'
 if not d:d=get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code='amended' if ref!='EQBC-1393' else 'in_force',ratification_date=date,effective_date=date,reference_code=ref,notes=note)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(title,short,one(c,'select id from document_types where code=?',typ),one(c,'select id from authorities where name_fa=?',auth),one(c,'select id from statuses where code=?','amended' if ref!='EQBC-1393' else 'in_force'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def rows(c,d,ref,rs,date,note):
 z={}
 for n,t in rs:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[ref],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QBC-1370','قانون بخش تعاونی اقتصاد جمهوری اسلامی ایران با اصلاحات تا ۱۳۹۳','قانون بخش تعاونی','law','1991-09-04','متن تلفیقی جاری ۷۷ ماده‌ای با اصلاحات تا ۱۳۹۳.'),('QSC-1350','قانون شرکت‌های تعاونی با اصلاحات و الحاقات','قانون شرکت‌های تعاونی','law','1971-06-06','متن جاری بازنشرشده ۱۴۸ ماده شماره‌دار؛ شماره‌های ۶۵ و ۷۲ در منبع جاری موجود نیست و شماره ۷۱ دو متن دارد که در مرحله تکمیلی نسخه‌بندی می‌شود.'),('EQBC-1393','قانون اصلاح موادی از قانون بخش تعاونی اقتصاد جمهوری اسلامی ایران','اصلاح قانون بخش تعاونی ۱۳۹۳','amendment','2014-05-07','متن کامل ۲۷ ماده اصلاحی/الحاقی.')]
  ds={x[0]:doc(c,*x) for x in sp};ids={}
  for ref,d in ds.items():
   clear(c,d);link_document_topic(c,d,'حقوق تجارت')
   for tag in ('تعاونی','شرکت تعاونی','اتاق تعاون','اقتصاد تعاونی'):link_document_tag(c,d,add_tag(c,tag))
  for ref,rs,date,note in [('QBC-1370',SECTOR,'1991-09-04','متن تلفیقی جاری.'),('QSC-1350',COMPANIES,'1971-06-06','بازنشر دارای وضعیت‌های اصلاح و نسخ در متن.'),('EQBC-1393',AMENDMENT,'2014-05-07','متن کامل قانون اصلاحی.')]:ids[ref]=rows(c,ds[ref],ref,rs,date,note)
  add_relation(c,ds['EQBC-1393'],'amends',ds['QBC-1370'],description='اصلاح و الحاق مواد قانون بخش تعاونی در ۱۳۹۳.')
  e44=one(c,'select id from documents where reference_code=?','QE44-1386');add_relation(c,ds['QBC-1370'],'cites',e44,description='ارتباط احکام بخش تعاونی با اجرای سیاست‌های کلی اصل ۴۴.')
  c.commit();print('loaded cooperative',sum(len(x) for x in (SECTOR,COMPANIES,AMENDMENT)))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
