# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from energy import OIL,ENERGY
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');S={'QN-1366':'https://www.ekhtebar.ir/قانون-نفت-مصوب-1366/','QAEM-1389':'https://www.ekhtebar.ir/قانون-اصلاح-الگوی-مصرف-انرژی-مصوب-۱۳۸۹/'}
def one(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def main():
 c=get_connection()
 try:
  c.execute('begin');ds={}
  for r,t,s,date,note in [('QN-1366','قانون نفت','قانون نفت','1987-09-06','متن ۱۶ ماده‌ای منبع‌دار.'),('QAEM-1389','قانون اصلاح الگوی مصرف انرژی','اصلاح الگوی مصرف انرژی','2011-02-23','متن کامل ۷۵ ماده.')]:
   d=one(c,'select id from documents where reference_code=?',r)
   if not d:d=get_or_create_document(c,title=t,short_title=s,type_code='law',issuing_authority='مجلس شورای اسلامی',status_code='in_force',ratification_date=date,effective_date=date,reference_code=r,notes=note)
   c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?','law'),one(c,'select id from authorities where name_fa=?','مجلس شورای اسلامی'),one(c,'select id from statuses where code=?','in_force'),date,date,note,d));ds[r]=d
   for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
   link_document_topic(c,d,'حقوق تجارت')
   for tag in ('انرژی','نفت و گاز','بهره‌وری انرژی'):link_document_tag(c,d,add_tag(c,tag))
  for r,x,date in [('QN-1366',OIL,'1987-09-06'),('QAEM-1389',ENERGY,'2011-02-23')]:
   for n,t in x:add_article(c,ds[r],article_no=n.translate(F),article_key=f'{r}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[r])
  add_relation(c,ds['QAEM-1389'],'cites',ds['QN-1366'],description='تکالیف بهینه‌سازی و مصرف حامل‌های انرژی و وظایف وزارت نفت.')
  c.commit();print('loaded energy',len(OIL)+len(ENERGY))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
