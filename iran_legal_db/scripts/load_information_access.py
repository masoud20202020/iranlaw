# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from information_access import LAW,BYLAW
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');U={'QDDA-1388':'https://www.ekhtebar.ir/قانون-انتشار-و-دسترسي-آزاد-به-اطلاعات-2/','AIDDA-1393':'https://www.ekhtebar.ir/آیین‌نامه-اجرایی-قانون-انتشار-و-دسترسی/'}
def one(c,q,v):
 r=c.execute(q,(v,)).fetchone();return r['id'] if r else None
def main():
 c=get_connection()
 try:
  c.execute('begin');ds={}
  for r,t,s,typ,date,note in [('QDDA-1388','قانون انتشار و دسترسی آزاد به اطلاعات','دسترسی آزاد به اطلاعات','law','2009-08-22','متن کامل ۲۳ ماده.'),('AIDDA-1393','آیین‌نامه اجرایی قانون انتشار و دسترسی آزاد به اطلاعات','آیین‌نامه دسترسی به اطلاعات','regulation','2014-05-21','متن کامل ۱۱ ماده.')]:
   a='مجلس شورای اسلامی' if typ=='law' else 'هیئت وزیران';d=one(c,'select id from documents where reference_code=?',r)
   if not d:d=get_or_create_document(c,title=t,short_title=s,type_code=typ,issuing_authority=a,status_code='in_force',ratification_date=date,effective_date=date,reference_code=r,notes=note)
   c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?',typ),one(c,'select id from authorities where name_fa=?',a),one(c,'select id from statuses where code=?','in_force'),date,date,note,d));ds[r]=d
   for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
   link_document_topic(c,d,'حقوق عمومی')
   for x in ('دسترسی آزاد به اطلاعات','اطلاعات شخصی','حریم خصوصی','دولت الکترونیک'):link_document_tag(c,d,add_tag(c,x))
  for r,x,date in [('QDDA-1388',LAW,'2009-08-22'),('AIDDA-1393',BYLAW,'2014-05-21')]:
   for n,t in x:add_article(c,ds[r],article_no=n.translate(F),article_key=f'{r}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=U[r])
  add_relation(c,ds['AIDDA-1393'],'implements',ds['QDDA-1388'],description='آیین‌نامه اجرایی قانون انتشار و دسترسی آزاد به اطلاعات.')
  c.commit();print('loaded',len(LAW)+len(BYLAW))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
