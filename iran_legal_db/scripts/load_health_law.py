# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_tag,get_or_create_document,link_document_tag,link_document_topic
from health_law import MED,PEN,FOOD
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');U={'QMDA-1334':'https://www.ekhtebar.ir/قانون-مربوط-به-مقررات-امور-پزشکی-و-دارو/','QTAHD-1367':'https://www.ekhtebar.ir/قانون-تعزیرات-حکومتی-امور-بهداشتی-و-در/','QMKAB-1346':'https://www.ekhtebar.ir/قانون-مواد-خوردنی-و-آشامیدنی-و-آرایشی-و/'}
def one(c,q,v):
 r=c.execute(q,(v,)).fetchone();return r['id'] if r else None
def main():
 c=get_connection()
 try:
  c.execute('begin')
  for r,t,s,a,date,x in [('QMDA-1334','قانون مربوط به مقررات امور پزشکی و دارویی و مواد خوردنی و آشامیدنی','مقررات امور پزشکی و دارویی','مجلس شورای ملی (پیش از انقلاب)','1955-06-19',MED),('QTAHD-1367','قانون تعزیرات حکومتی امور بهداشتی و درمانی','تعزیرات بهداشتی و درمانی','مجمع تشخیص مصلحت نظام','1989-03-14',PEN),('QMKAB-1346','قانون مواد خوردنی و آشامیدنی و آرایشی و بهداشتی','مواد خوردنی و آرایشی و بهداشتی','مجلس شورای ملی (پیش از انقلاب)','1967-07-13',FOOD)]:
   d=one(c,'select id from documents where reference_code=?',r)
   if not d:d=get_or_create_document(c,title=t,short_title=s,type_code='law',issuing_authority=a,status_code='amended',ratification_date=date,effective_date=date,reference_code=r,notes=f'متن منبع‌دار {len(x)} ماده‌ای با اصلاحات منعکس در منبع.')
   c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?','law'),one(c,'select id from authorities where name_fa=?',a),one(c,'select id from statuses where code=?','amended'),date,date,f'متن منبع‌دار {len(x)} ماده‌ای با اصلاحات منعکس در منبع.',d))
   for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
   link_document_topic(c,d,'حقوق کیفری')
   for z in ('حقوق سلامت','امور پزشکی','دارو','بهداشت عمومی'):link_document_tag(c,d,add_tag(c,z))
   for n,text in x:add_article(c,d,article_no=n.translate(F),article_key=f'{r}:{n}',version_no=1,is_current=1,effective_date=date,text=text,source_note=U[r])
  c.commit();print('loaded',len(MED)+len(PEN)+len(FOOD))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
