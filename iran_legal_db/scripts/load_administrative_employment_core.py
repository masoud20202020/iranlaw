# -*- coding: utf-8 -*-
"""Idempotently load phase-three core statutes: veterans and selection."""
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from administrative_employment_core import ISARGARAN,GOZINESH,JANBAZAN,TASRI
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
S={'QCSE-1391':'https://www.ekhtebar.ir/قانون-جامع-خدمات‌رسانی-به-ایثارگران-م/','QGMO-1374':'https://www.ekhtebar.ir/قانون-گزینش-معلمان-و-کارکنان-آموزش-و-پر/','QTG-1375':'https://www.ekhtebar.ir/?p=43853','QTSAJ-1374':'https://shenasname.ir/isaar/224-3131374'}
def one(c,q,v):
 r=c.execute(q,(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,date,note):
 d=one(c,'select id from documents where reference_code=?',ref)
 if not d:d=get_or_create_document(c,title=title,short_title=short,type_code='law',issuing_authority='مجلس شورای اسلامی',status_code='amended',ratification_date=date,effective_date=date,reference_code=ref,notes=note)
 a=one(c,'select id from authorities where name_fa=?','مجلس شورای اسلامی');c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(title,short,one(c,'select id from document_types where code=?','law'),a,one(c,'select id from statuses where code=?','amended'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def rows(c,d,ref,x,date,note):
 z={}
 for n,t in x:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[ref],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QCSE-1391','قانون جامع خدمات‌رسانی به ایثارگران با اصلاحات تا ۱۳۹۷','خدمات‌رسانی به ایثارگران','2013-01-17','متن تلفیقی ۷۶ ماده‌ای با آخرین اصلاحات درج‌شده در منبع تا ۱۳۹۷؛ متن‌های سابقِ بازنشرشده در کروشه، در مرحله بعد تاریخچه‌گذاری دقیق می‌شوند.'),('QGMO-1374','قانون گزینش معلمان و کارکنان آموزش و پرورش','قانون گزینش','1995-09-05','متن کامل ۱۸ ماده و تبصره‌ها؛ قانون تسری ۱۳۷۵ دامنه آن را به دیگر دستگاه‌ها گسترش می‌دهد.'),('QTG-1375','قانون تسری قانون گزینش به کارکنان سایر دستگاه‌های دولتی','قانون تسری گزینش','1996-04-28','متن ماده‌واحده و تبصره‌ها.'),('QTSAJ-1374','قانون تسهیلات استخدامی و اجتماعی جانبازان انقلاب اسلامی با اصلاحات','تسهیلات استخدامی جانبازان','1995-05-21','متن ۲۰ ماده‌ای بازنشرشده با اصلاحات و الحاقات بعدی.')]
  d={x[0]:up(c,*x) for x in sp}
  for ref,v in d.items():
   clear(c,v);link_document_topic(c,v,'حقوق اداری و استخدامی')
   for tag in ('ایثارگران','استخدام دولتی','حقوق اداری'):link_document_tag(c,v,add_tag(c,tag))
  ids={'QCSE-1391':rows(c,d['QCSE-1391'],'QCSE-1391',ISARGARAN,'2013-01-17','متن تلفیقی جاری با اصلاحات منعکس در منبع.'),'QGMO-1374':rows(c,d['QGMO-1374'],'QGMO-1374',GOZINESH,'1995-09-05','متن کامل منبع‌دار.'),'QTSAJ-1374':rows(c,d['QTSAJ-1374'],'QTSAJ-1374',JANBAZAN,'1995-05-21','متن بازنشرشده با اصلاحات منعکس در منبع.')}
  ids['QTG-1375']={'single':add_article(c,d['QTG-1375'],article_no='ماده‌واحده',article_key='QTG-1375:single',version_no=1,is_current=1,effective_date='1996-04-28',text=TASRI,source_note=S['QTG-1375'],notes='متن کامل ماده‌واحده و تبصره‌ها.')}
  qc=one(c,'select id from documents where reference_code=?','QCSM-1386');qd=one(c,'select id from documents where reference_code=?','QDA-1392')
  add_relation(c,d['QTG-1375'],'amends',d['QGMO-1374'],from_article_id=ids['QTG-1375']['single'],description='تسری احکام قانون گزینش به سایر دستگاه‌های مشمول.')
  add_relation(c,d['QCSE-1391'],'implements',qc,description='ارتباط موضوعی احکام استخدام و تبدیل وضعیت ایثارگران با نظام استخدامی دولت.')
  add_relation(c,d['QTSAJ-1374'],'implements',qc,description='تسهیلات استخدامی جانبازان در دستگاه‌های مشمول.')
  add_relation(c,d['QGMO-1374'],'cites',qd,description='مرجع رسیدگی به اعتراض‌های گزینشی طبق تبصره ۳ ماده ۱۴.')
  c.commit();print('loaded 4 core statutes; current',sum(c.execute('select count(*) from articles where document_id=? and is_current=1',(x,)).fetchone()[0] for x in d.values()))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
