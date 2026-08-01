# -*- coding: utf-8 -*-
"""Idempotently load the sourced administrative and public-employment package."""
from __future__ import annotations
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__)); sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from administrative_employment import *
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
TOPIC='حقوق اداری و استخدامی'
SOURCES={
'QCSM-1386':'https://www.ekhtebar.ir/قانون-مديريت-خدمات-كشوري-مصوب-1376/ (مقابله با میزان آنلاین؛ متن جاری ۱۲۸ ماده).',
'PCSM-1397':'https://shenasname.ir/laws/5322-daemi-modiriat', 'ECSM44-1399':'https://shenasname.ir/laws/modiriat/5986-eslah-boomi',
'AICSM46-1396':'https://www.ekhtebar.ir/آيين‌نامه-اجرايی-ماده-۴۶-قانون-مديري/', 'DICSM46-1397':'https://snn.ir/fa/news/692291/',
'AIEP-1368':'https://www.solh.ir/regulation/7/81', 'AICSM84-1389':'https://shenasname.ir/laws/modiriat/1264-77683',
'QTAK-1372':'https://www.ekhtebar.ir/قانون-رسیدگی-به-تخلفات-اداری-مصوب-۱۳۷۲/', 'AITAK-1373':'https://goums.ac.ir/content/34106/',
'QDA-1392':'https://www.ekhtebar.ir/قانون-تشکیلات-و-آیین-دادرسی-دیوان-عدال/', 'EQDAD-1402':'https://www.ekhtebar.ir/قانون-اصلاح-قانون-تشکیلات-و-آیین-دادرسی/' }
def idof(c,t,col,v):
 r=c.execute(f'SELECT id FROM {t} WHERE {col}=?',(v,)).fetchone();return r['id'] if r else None
def upsert(c,ref,title,short,typ,auth,status,date,note):
 r=c.execute('SELECT id FROM documents WHERE reference_code=?',(ref,)).fetchone()
 if r: did=r['id']
 else: did=get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=date,effective_date=date,reference_code=ref,notes=note)
 aid=idof(c,'authorities','name_fa',auth)
 if not aid: aid=c.execute('INSERT INTO authorities(name_fa,authority_type) VALUES(?,?)',(auth,'legislative' if 'مجلس' in auth else 'executive')).lastrowid
 c.execute('UPDATE documents SET title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(title,short,idof(c,'document_types','code',typ),aid,idof(c,'statuses','code',status),date,date,note,did)); return did
def clear(c,did):
 c.execute('DELETE FROM relations WHERE from_document_id=?',(did,));c.execute('DELETE FROM articles_fts WHERE document_id=?',(did,));c.execute('DELETE FROM articles WHERE document_id=?',(did,));c.execute('DELETE FROM document_tags WHERE document_id=?',(did,));c.execute('DELETE FROM document_topics WHERE document_id=?',(did,))
def decor(c,did,tags):
 link_document_topic(c,did,TOPIC)
 for x in tags: link_document_tag(c,did,add_tag(c,x))
def addrows(c,did,ref,rows,date,note):
 out={}
 for n,text in rows: out[n]=add_article(c,did,article_no=n.translate(F),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=text,source_note=SOURCES[ref],notes=note)
 return out
def main():
 c=get_connection()
 try:
  c.execute('BEGIN')
  specs=[
 ('QCSM-1386','قانون مدیریت خدمات کشوری با اصلاحات و الحاقات','مدیریت خدمات کشوری','law','مجلس شورای اسلامی','amended','2007-10-08','متن جاری ۱۲۸ ماده؛ در این بارگذاری، ماده ۴۴ اصلاحی ۱۳۹۹ در متن تلفیقی جاری منعکس است.'),
 ('PCSM-1397','قانون دائمی شدن قانون مدیریت خدمات کشوری','دائمی شدن مدیریت خدمات','law','مجلس شورای اسلامی','in_force','2018-05-15','ماده‌واحده؛ پایان اعتبار آزمایشی و دائمی شدن قانون.'),
 ('ECSM44-1399','قانون اصلاح ماده ۴۴ قانون مدیریت خدمات کشوری','اصلاح ماده ۴۴ مدیریت خدمات','amendment','مجلس شورای اسلامی','in_force','2020-09-06','اصلاح استخدام و اولویت بومی شهرستانی.'),
 ('AICSM46-1396','آیین‌نامه اجرایی ماده ۴۶ قانون مدیریت خدمات کشوری','آیین‌نامه ماده ۴۶','regulation','هیئت وزیران','in_force','2017-02-18','متن کامل شش ماده.'),
 ('DICSM46-1397','دستورالعمل تبدیل وضعیت استخدامی کارمندان پیمانی به رسمی','تبدیل پیمانی به رسمی','directive','سازمان اداری و استخدامی کشور','in_force','2018-05-23','متن کامل ۱۲ ماده.'),
 ('AIEP-1368','آیین‌نامه استخدام پیمانی','استخدام پیمانی','regulation','هیئت وزیران','in_force','1989-07-16','متن کامل ۳۰ ماده؛ بازنشر منبع صلح.'),
 ('AICSM84-1389','آیین‌نامه اجرایی مواد ۸۴، ۸۶، ۸۷، ۹۰، ۹۱ و ۹۳ قانون مدیریت خدمات کشوری','آیین‌نامه مواد رفاهی خدمات کشوری','regulation','هیئت وزیران','in_force','2010-05-19','متن کامل پنج ماده.'),
 ('QTAK-1372','قانون رسیدگی به تخلفات اداری','تخلفات اداری','law','مجلس شورای اسلامی','in_force','1993-11-28','متن کامل ۲۷ ماده.'),
 ('AITAK-1373','آیین‌نامه اجرایی قانون رسیدگی به تخلفات اداری','آیین‌نامه تخلفات اداری','regulation','هیئت وزیران','in_force','1994-10-19','متن کامل ۴۷ ماده.'),
 ('QDA-1392','قانون دیوان عدالت اداری با اصلاحات و الحاقات تا ۱۴۰۲','قانون دیوان عدالت اداری','law','مجلس شورای اسلامی','amended','2013-06-15','متن جاری ۱۲۴ ماده. رکورد ناقص پیشین این مرجع با پوشش کامل بازسازی شده است؛ برای مواد متفاوت، نسخه ۱۳۹۲ نیز نگهداری می‌شود.'),
 ('EQDAD-1402','قانون اصلاح قانون تشکیلات و آیین دادرسی دیوان عدالت اداری','اصلاح قانون دیوان ۱۴۰۲','amendment','مجلس شورای اسلامی','in_force','2023-04-30','متن کامل ۶۲ ماده قانون اصلاحی.')]
  docs={s[0]:upsert(c,*s) for s in specs}
  for did in docs.values(): clear(c,did)
  for ref,did in docs.items(): decor(c,did,('حقوق اداری','استخدام دولتی','دیوان عدالت اداری') if ref.startswith('QD') else ('حقوق اداری','استخدام دولتی'))
  ids={}
  ids['QCSM-1386']=addrows(c,docs['QCSM-1386'],'QCSM-1386',CIVIL_SERVICE,'2007-10-08','متن تلفیقی جاری؛ مقابله‌شده با منبع دوم.')
  ids['PCSM-1397']=addrows(c,docs['PCSM-1397'],'PCSM-1397',(('1',PERMANENT_1397),),'2018-05-15','متن منبع شامل سربرگ بازنشر است؛ فقط ماده‌واحده را باید در استفاده حرفه‌ای با روزنامه رسمی مقابله کرد.')
  ids['ECSM44-1399']=addrows(c,docs['ECSM44-1399'],'ECSM44-1399',(('1',ARTICLE44_AMENDMENT),),'2020-09-06','متن منبع‌دار قانون اصلاحی؛ شامل بازنشر و فراداده منبع است.')
  for ref,rows,date,note in [('AICSM46-1396',ART46_BYLAW,'2017-02-18','متن کامل.'),('DICSM46-1397',ART46_DIRECTIVE,'2018-05-23','متن کامل.'),('AIEP-1368',CONTRACT_EMPLOYMENT,'1989-07-16','متن کامل.'),('AICSM84-1389',CS84_BYLAW,'2010-05-19','متن کامل.'),('QTAK-1372',ADMIN_VIOLATIONS,'1993-11-28','متن کامل.'),('AITAK-1373',ADMIN_VIOLATIONS_BYLAW,'1994-10-19','متن کامل.'),('EQDAD-1402',DIVAN_AMENDMENT,'2023-04-30','متن کامل قانون اصلاحی.')]: ids[ref]=addrows(c,docs[ref],ref,rows,date,note)
  old=dict(DIVAN_ORIGINAL); cur=dict(DIVAN_CURRENT); ids['QDA-1392']={}
  for n in map(str,range(1,125)):
   if old[n]!=cur[n]:
    add_article(c,docs['QDA-1392'],article_no=n.translate(F),article_key=f'QDA-1392:{n}',version_no=1,is_current=0,effective_date='2013-06-15',expiry_date='2023-04-30',text=old[n],source_note='https://www.isfahanbar.org/news/92/متن-کامل-قانون-تشکیلات-آیین-دادرسی-دیوان-عدالت-اداری',notes='نسخه تاریخی ۱۳۹۲، پیش از اصلاحات ۱۴۰۲.')
    ver=2; note='نسخه جاری پس از اصلاحات ۱۴۰۲؛ نسخه پیشین در بانک نگهداری شده است.'
   else: ver=1; note='متن جاری؛ در مقابله با متن ۱۳۹۲ تفاوتی مشاهده نشد.'
   ids['QDA-1392'][n]=add_article(c,docs['QDA-1392'],article_no=n.translate(F),article_key=f'QDA-1392:{n}',version_no=ver,is_current=1,effective_date='2023-04-30' if ver==2 else '2013-06-15',text=cur[n],source_note=SOURCES['QDA-1392'],notes=note)
  add_relation(c,docs['PCSM-1397'],'amends',docs['QCSM-1386'],description='دائمی شدن قانون مدیریت خدمات کشوری.')
  add_relation(c,docs['ECSM44-1399'],'amends',docs['QCSM-1386'],from_article_id=ids['ECSM44-1399']['1'],to_article_id=ids['QCSM-1386']['44'],description='اصلاح ماده ۴۴ درباره آزمون و اولویت بومی.')
  add_relation(c,docs['AICSM46-1396'],'implements',docs['QCSM-1386'],description='آیین‌نامه اجرایی ماده ۴۶.')
  add_relation(c,docs['DICSM46-1397'],'implements',docs['QCSM-1386'],description='دستورالعمل تبدیل وضعیت در اجرای ماده ۴۶.')
  add_relation(c,docs['AICSM84-1389'],'implements',docs['QCSM-1386'],description='اجرای مواد رفاهی قانون مدیریت خدمات کشوری.')
  add_relation(c,docs['AITAK-1373'],'implements',docs['QTAK-1372'],description='آیین‌نامه اجرایی قانون رسیدگی به تخلفات اداری.')
  add_relation(c,docs['EQDAD-1402'],'amends',docs['QDA-1392'],description='قانون اصلاحی ۱۴۰۲؛ رابطه در سطح سند برای پایداری بازبارگذاری.')
  c.commit(); print('loaded',len(docs),'documents; current articles',sum(c.execute('SELECT COUNT(*) FROM articles WHERE document_id=? AND is_current=1',(d,)).fetchone()[0] for d in docs.values()))
 except Exception: c.rollback(); raise
 finally: c.close()
if __name__=='__main__': main()
