# -*- coding: utf-8 -*-
"""Load phase-two administrative employment rulings as sourced summaries."""
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from administrative_employment_rulings import RULING_SUMMARIES
URLS={
'DAD-669-1398':'https://www.ekhtebar.ir/رأی-وحدت-رویه-شماره-۶۶۹-هیأت-عمومی-دیوا/',
'DAD-1043-1400':'https://www.ekhtebar.ir/دیوان-عدالت-اداری-قطع-رابطه-استخدامی-ب/',
'DAD-2120727-1402':'https://www.ekhtebar.ir/ابطال-شرط-لزوم-خدمت-تمام-وقت-نیروهای-غی/',
'DAD-383671-1403':'https://www.ekhtebar.ir/رای-هیات-عمومی-دیوان-عدالت-اداری-مبنی-ب/'}
def ident(c,t,col,v):
 r=c.execute(f'SELECT id FROM {t} WHERE {col}=?',(v,)).fetchone();return r['id'] if r else None
def upsert(c,ref,title,date):
 r=c.execute('SELECT id FROM documents WHERE reference_code=?',(ref,)).fetchone()
 if r: did=r['id']
 else: did=get_or_create_document(c,title=title,short_title=title,type_code='divan_ruling',issuing_authority='هیأت عمومی دیوان عدالت اداری',status_code='in_force',ratification_date=date,effective_date=date,reference_code=ref,notes='خلاصه ساختاری منبع‌دار؛ متن کامل دادنامه نیست.')
 aid=ident(c,'authorities','name_fa','هیأت عمومی دیوان عدالت اداری')
 c.execute('UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? WHERE id=?',(title,title,ident(c,'document_types','code','divan_ruling'),aid,ident(c,'statuses','code','in_force'),date,date,'خلاصه ساختاری منبع‌دار؛ متن کامل دادنامه نیست.',did));return did
def clear(c,d):
 c.execute('DELETE FROM relations WHERE from_document_id=?',(d,));c.execute('DELETE FROM articles_fts WHERE document_id=?',(d,));c.execute('DELETE FROM articles WHERE document_id=?',(d,));c.execute('DELETE FROM document_tags WHERE document_id=?',(d,));c.execute('DELETE FROM document_topics WHERE document_id=?',(d,))
def docid(c,ref):
 r=c.execute('SELECT id FROM documents WHERE reference_code=?',(ref,)).fetchone();return r['id']
def main():
 c=get_connection()
 try:
  c.execute('BEGIN'); docs={}
  for ref,title,no,date,text in RULING_SUMMARIES:
   d=docs[ref]=upsert(c,ref,title,date);clear(c,d);link_document_topic(c,d,'حقوق اداری و استخدامی')
   for tag in ('رأی دیوان عدالت اداری','حقوق اداری','استخدام دولتی','خلاصه ساختاری') : link_document_tag(c,d,add_tag(c,tag))
   add_article(c,d,article_no='رأی',article_key=f'{ref}:ruling',version_no=1,is_current=1,effective_date=date,text=text,source_note=URLS[ref],notes='خلاصه ساختاری منبع‌دار؛ رونوشت لفظ‌به‌لفظ دادنامه نیست.')
  qd=docid(c,'QDA-1392');qc=docid(c,'QCSM-1386');qt=docid(c,'QTAK-1372')
  for ref in ('DAD-669-1398','DAD-2120727-1402','DAD-383671-1403'):add_relation(c,docs[ref],'interprets',qc,description='رابطه موضوعی با حقوق و استخدام عمومی و قانون مدیریت خدمات کشوری.')
  add_relation(c,docs['DAD-1043-1400'],'interprets',qt,description='صلاحیت هیأت تخلفات اداری درباره کارمند پیمانی.')
  for ref,d in docs.items():add_relation(c,d,'cites',qd,description='رأی صادره از هیأت عمومی دیوان عدالت اداری.')
  c.commit();print('loaded',len(docs),'sourced ruling summaries')
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
