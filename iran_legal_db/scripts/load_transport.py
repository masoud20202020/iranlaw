# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from transport import MARITIME,TRANSIT,ROAD
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');S={'QDR-1343':'https://www.ekhtebar.ir/قانون-دريایی-مصوب-1343/','QTAK-1374':'https://www.ekhtebar.ir/قانون-حمل-و-نقل-و-عبور-کالاهای-خارجی-از/','AIRT-1391':'https://www.ekhtebar.ir/آیین-نامه-اجرایی-تبصره-یک-ماده-۳۱-و-ماده/'}
def one(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def doc(c,r,t,s,typ,date,note):
 d=one(c,'select id from documents where reference_code=?',r);a='هیئت وزیران' if typ=='regulation' else ('مجلس شورای ملی (پیش از انقلاب)' if r=='QDR-1343' else 'مجلس شورای اسلامی')
 if not d:d=get_or_create_document(c,title=t,short_title=s,type_code=typ,issuing_authority=a,status_code='amended' if r=='QDR-1343' else 'in_force',ratification_date=date,effective_date=date,reference_code=r,notes=note)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?',typ),one(c,'select id from authorities where name_fa=?',a),one(c,'select id from statuses where code=?','amended' if r=='QDR-1343' else 'in_force'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def rows(c,d,r,x,date,note):
 z={}
 for n,t in x:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{r}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[r],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QDR-1343','قانون دریایی با اصلاحات و الحاقات','قانون دریایی','law','1964-09-20','متن تلفیقی ۱۹۴ ماده‌ای با اصلاحات منعکس در منبع.'),('QTAK-1374','قانون حمل و نقل و عبور کالاهای خارجی از قلمرو جمهوری اسلامی ایران','ترانزیت خارجی کالا','law','1996-03-11','متن کامل ۲۶ ماده.'),('AIRT-1391','آیین‌نامه اجرایی تبصره یک ماده ۳۱ و ماده ۳۲ قانون رسیدگی به تخلفات رانندگی','آیین‌نامه حمل‌ونقل برون‌شهری','regulation','2012-09-16','متن کامل ۲۱ ماده آیین‌نامه؛ مواد ۳۱ و ۳۲ قانون مرجع که در صفحه بازنشر شده‌اند وارد این سند نشده‌اند.')]
  ds={x[0]:doc(c,*x) for x in sp}
  for r,d in ds.items():
   clear(c,d);link_document_topic(c,d,'حقوق تجارت')
   for tag in ('حمل‌ونقل','ترانزیت','کشتیرانی','بارنامه'):link_document_tag(c,d,add_tag(c,tag))
  ids={}
  for r,x,date,note in [('QDR-1343',MARITIME,'1964-09-20','متن تلفیقی جاری.'),('QTAK-1374',TRANSIT,'1996-03-11','متن کامل.'),('AIRT-1391',ROAD,'2012-09-16','متن کامل آیین‌نامه.')]:ids[r]=rows(c,ds[r],r,x,date,note)
  c.commit();print('loaded transport',sum(len(x) for x in (MARITIME,TRANSIT,ROAD)))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
