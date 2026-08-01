# -*- coding: utf-8 -*-
"""Load the 81-article Electronic Commerce Law and its principal regulations."""
from __future__ import annotations
import os, sys

SCRIPT_DIR=os.path.dirname(__file__); ROOT=os.path.dirname(SCRIPT_DIR)
sys.path[:0]=[SCRIPT_DIR, os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import add_article, add_relation, add_tag, get_or_create_document, link_document_tag, link_document_topic
from ecommerce_law import *

REF='QTE-1382'; REF32='AIN32-1386'; REF3842='AIN3842-1383'; REF48='AIN48-1384'; REF_KHT='KHT-1399'
MANAGED=(REF,REF32,REF3842,REF48,REF_KHT)
D1382='2004-01-07'; D1383='2004-12-30'; D1383B='2005-02-16'; D1384='2005-07-24'; D1386='2007-09-02'
D1390='2011-06-29'; D1393='2014-06-25'; D1394='2015-11-08'; D1399='2020-05-12'; D1399F='2021-01-27'; D1400='2021-07-25'; D1403='2024-06-19'
SRC='قانون تجارت الکترونیکی مصوب ۱۳۸۲/۱۰/۱۷؛ تطبیق رسمی: https://qavanin.ir/Law/PrintText/86054'


def pnum(x): return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def lid(c,t,col,v):
 r=c.execute(f'SELECT id FROM {t} WHERE {col}=?',(v,)).fetchone()
 if not r: raise ValueError(v)
 return r['id']

def upsert(c,ref,title,short,type_code,auth,status,date,notes,official=None):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
 if r: did=r['id']
 else: did=get_or_create_document(c,title=title,short_title=short,type_code=type_code,issuing_authority=auth,status_code=status,ratification_date=date,effective_date=date,official_newspaper_no=official,reference_code=ref,notes=notes)
 a=c.execute('select id from authorities where name_fa=?',(auth,)).fetchone()
 if not a: aid=c.execute("insert into authorities(name_fa,authority_type) values(?,'administrative')",(auth,)).lastrowid
 else: aid=a['id']
 c.execute('''update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,official_newspaper_no=?,notes=?,updated_at=current_timestamp where id=?''',(title,short,lid(c,'document_types','code',type_code),aid,lid(c,'statuses','code',status),date,date,official,notes,did))
 return did

def clear(c,did):
 c.execute('delete from relations where from_document_id=?',(did,)); c.execute('delete from articles_fts where document_id=?',(did,)); c.execute('delete from articles where document_id=?',(did,)); c.execute('delete from document_tags where document_id=?',(did,)); c.execute('delete from document_topics where document_id=?',(did,))
def deco(c,did,tags):
 for topic in ('حقوق تجارت','حقوق تجارت الکترونیک'): link_document_topic(c,did,topic)
 for t in tags: link_document_tag(c,did,add_tag(c,t))
def addv(c,did,key,no,text,v,cur,eff,exp,src,note=None):
 return add_article(c,did,article_no=pnum(no),article_key=f'{REF}:{key}',version_no=v,is_current=cur,effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def addrows(c,did,ref,rows,date,src):
 ids={}
 for n,t in rows: ids[n]=add_article(c,did,article_no=pnum(n),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=src)
 return ids

def main():
 c=get_connection()
 try:
  c.execute('begin')
  docs={}
  docs[REF]=upsert(c,REF,'قانون تجارت الکترونیکی (مصوب ۱۳۸۲، با تعدیلات و اصلاحات بعدی)','ق.ت.ا.','law','مجلس شورای اسلامی','amended',D1382,'متن کامل ۸۱ ماده؛ شامل داده‌پیام، امضای الکترونیکی، ادله، قراردادهای از راه دور، حمایت مصرف‌کننده، داده‌های شخصی، مالکیت فکری و جرایم؛ با تاریخچه جزای نقدی ۱۳۹۹ و ۱۴۰۳.')
  docs[REF32]=upsert(c,REF32,'آیین‌نامه اجرایی ماده ۳۲ قانون تجارت الکترونیکی','آیین‌نامه گواهی الکترونیکی','regulation','هیئت وزیران','amended',D1386,'بیست ماده درباره شورای سیاست‌گذاری، مرکز ریشه، مراکز میانی، دفاتر ثبت‌نام و زیرساخت کلید عمومی.',official='۹۸۹۸۶/ت۳۱۸۱۹هـ')
  docs[REF3842]=upsert(c,REF3842,'آیین‌نامه اجرایی مواد ۳۸ و ۴۲ قانون تجارت الکترونیکی','آیین‌نامه حق انصراف','regulation','هیئت وزیران','amended',D1383,'دو ماده درباره موارد فقدان حق انصراف و خدمات مالی خارج از حمایت مصرف‌کننده.')
  docs[REF48]=upsert(c,REF48,'آیین‌نامه اجرایی ماده ۴۸ قانون تجارت الکترونیکی','آیین‌نامه شکایت مصرف‌کننده','regulation','هیئت وزیران','in_force',D1384,'پنج ماده درباره اقامه دعوا توسط سازمان‌های حمایت از مصرف‌کننده.')
  docs[REF_KHT]=upsert(c,REF_KHT,'حکم مرتبط قانون کاهش مجازات حبس تعزیری درباره شروع به جرم در تجارت الکترونیکی','نسخ تبصره شروع به جرم','amendment','مجلس شورای اسلامی','in_force',D1399,'ثبت اثر ماده ۱۵ قانون کاهش مجازات حبس تعزیری بر تبصره‌های شروع به جرم مواد ۶۷ و ۶۸ قانون تجارت الکترونیکی.')
  for d in docs.values(): clear(c,d)
  deco(c,docs[REF],['تجارت الکترونیکی','داده‌پیام','امضای الکترونیکی','حقوق مصرف‌کننده','حریم خصوصی'])
  deco(c,docs[REF32],['گواهی الکترونیکی','مرکز ریشه','زیرساخت کلید عمومی'])
  deco(c,docs[REF3842],['حق انصراف','مصرف‌کننده','خدمات مالی'])
  deco(c,docs[REF48],['حمایت مصرف‌کننده','اقامه دعوا'])
  deco(c,docs[REF_KHT],['کاهش مجازات حبس','شروع به جرم'])

  orig=dict(ECOMMERCE_ORIGINAL_1382); cur=dict(ECOMMERCE_CURRENT); f99=ECOMMERCE_FINE_TEXTS_1399
  schedules={n:[(D1382,orig[n],SRC,'متن مصوب ۱۳۸۲')] for n in range(1,82)}
  for n in (32,48): schedules[n].append((D1390,cur[n],SRC,'اصلاح عنوان وزارتخانه در ۱۳۹۰'))
  schedules[67].append((D1399,cur[67],SRC,'حذف تبصره شروع به جرم در ۱۳۹۹'))
  schedules[68].append((D1399,f99[68],SRC,'حذف تبصره شروع به جرم و تعدیل جزای نقدی در ۱۳۹۹'))
  for n in ECOMMERCE_FINE_ARTICLES:
   if n!=68: schedules[n].append((D1399F,f99[n],SRC,'تعدیل جزای نقدی مصوب ۱۳۹۹'))
   schedules[n].append((D1403,cur[n],SRC,'تعدیل جزای نقدی مصوب ۱۴۰۳'))
  current_ids={}; count=0
  for n in range(1,82):
   stages=schedules[n]
   for i,(date,text,src,note) in enumerate(stages,1):
    iscur=int(i==len(stages)); exp=stages[i][0] if i<len(stages) else None
    aid=addv(c,docs[REF],str(n),n,text,i,iscur,date,exp,src,note)
    if iscur: current_ids[n]=aid
    count+=1

  # Bylaw 32, including the complete article-2 membership history.
  b32o=dict(ECOMMERCE_BYLAW32_ORIGINAL); b32c=dict(ECOMMERCE_BYLAW32_CURRENT); b32ids={}
  for n in range(1,21):
   stages=[(D1386,b32o[n])]
   if n==2:
    stages += [(D1393,ECOMMERCE_BYLAW32_ART2_INTERMEDIATE[1393]),(D1394,ECOMMERCE_BYLAW32_ART2_INTERMEDIATE[1394]),(D1400,b32c[2])]
   for i,(date,text) in enumerate(stages,1):
    aid=add_article(c,docs[REF32],article_no=pnum(n),article_key=f'{REF32}:{n}',version_no=i,is_current=int(i==len(stages)),effective_date=date,expiry_date=(stages[i][0] if i<len(stages) else None),text=text,source_note='آیین‌نامه ماده ۳۲ مصوب ۱۳۸۶ با اصلاحات بعدی؛ https://qavanin.ir/Law/PrintText/117839')
    if i==len(stages): b32ids[n]=aid

  # Bylaw 38/42, article 1 amendment history.
  b38o=dict(ECOMMERCE_BYLAW3842_ORIGINAL); b38c=dict(ECOMMERCE_BYLAW3842_CURRENT); b38ids={}
  a=add_article(c,docs[REF3842],article_no='۱',article_key=f'{REF3842}:1',version_no=1,is_current=0,effective_date=D1383,expiry_date=D1383B,text=b38o[1],source_note='تصویب‌نامه ۱۳۸۳/۱۰/۹')
  b38ids[1]=add_article(c,docs[REF3842],article_no='۱',article_key=f'{REF3842}:1',version_no=2,is_current=1,effective_date=D1383B,text=b38c[1],source_note='اصلاحی ۱۳۸۳/۱۱/۲۸')
  b38ids[2]=add_article(c,docs[REF3842],article_no='۲',article_key=f'{REF3842}:2',version_no=1,is_current=1,effective_date=D1383,text=b38c[2],source_note='تصویب‌نامه ۱۳۸۳/۱۰/۹')
  b48ids=addrows(c,docs[REF48],REF48,ECOMMERCE_BYLAW48,D1384,'آیین‌نامه ماده ۴۸ مصوب ۱۳۸۴/۵/۲؛ https://nezamat.ir/post-35422/')
  khtid=add_article(c,docs[REF_KHT],article_no='ماده ۱۵ (اثر مرتبط)',article_key=f'{REF_KHT}:15',version_no=1,is_current=1,effective_date=D1399,text='مصادیق خاص قانونی که در آنها برای شروع به جرمِ مشخص تحت همین عنوان مجازات تعیین شده است نسخ می‌گردد؛ این حکم موجب حذف تبصره‌های شروع به جرم مواد ۶۷ و ۶۸ قانون تجارت الکترونیکی شده است.',source_note='قانون کاهش مجازات حبس تعزیری مصوب ۱۳۹۹/۲/۲۳')

  add_relation(c,docs[REF32],'implements',docs[REF],from_article_id=b32ids[1],to_article_id=current_ids[32],description='آیین‌نامه دفاتر و مراکز صدور گواهی الکترونیکی.')
  for target in (38,42): add_relation(c,docs[REF3842],'implements',docs[REF],from_article_id=b38ids[1],to_article_id=current_ids[target],description='موارد استثنای حق انصراف و خدمات مالی.')
  add_relation(c,docs[REF48],'implements',docs[REF],from_article_id=b48ids[1],to_article_id=current_ids[48],description='نحوه اقامه دعوا توسط سازمان‌های حمایت مصرف‌کننده.')
  for target in (67,68): add_relation(c,docs[REF_KHT],'abrogates',docs[REF],from_article_id=khtid,to_article_id=current_ids[target],description='حذف تبصره خاص شروع به جرم در سال ۱۳۹۹.')
  for fine_ref in ('TMJN-1399','TMJN-1403'):
   d=c.execute('select id from documents where reference_code=?',(fine_ref,)).fetchone()
   if d:
    fa=c.execute('select id from articles where document_id=? order by id limit 1',(d['id'],)).fetchone()
    for n in ECOMMERCE_FINE_ARTICLES: add_relation(c,d['id'],'amends',docs[REF],from_article_id=(fa['id'] if fa else None),to_article_id=current_ids[n],description=f'تعدیل جزای نقدی ماده {pnum(n)}.')
  for rcode,desc in [('QT-1311','ارتباط با قواعد عمومی تجارت'),('QM-1307','اعتبار قراردادها و قواعد عمومی مدنی'),('QSC-1355','چک و امضای الکترونیکی')]:
   d=c.execute('select id from documents where reference_code=?',(rcode,)).fetchone()
   if d: add_relation(c,docs[REF],'cites',d['id'],description=desc)
  # Link existing electronic-cheque instruction to this law.
  d=c.execute("select id from documents where reference_code='CHKE-1402'").fetchone()
  if d:
   fa=c.execute('select id from articles where document_id=? order by id limit 1',(d['id'],)).fetchone()
   add_relation(c,d['id'],'implements',docs[REF],from_article_id=(fa['id'] if fa else None),to_article_id=current_ids[7],description='دستورالعمل چک الکترونیکی بر مبنای اعتبار امضای الکترونیکی و داده‌پیام.')
  c.commit()
  t=c.execute('''select (select count(*) from documents) d,(select count(*) from articles) a,(select count(*) from articles where is_current=1) cur,(select count(*) from articles where is_current=0) hist,(select count(*) from relations) r''').fetchone()
  print(f'[OK] قانون تجارت الکترونیکی: ۸۱ ماده جاری، {count} نسخه کل')
  print('[OK] آیین‌نامه‌ها: ماده ۳۲ (۲۰ ماده)، مواد ۳۸/۴۲ (۲ ماده)، ماده ۴۸ (۵ ماده)')
  print(f"[TOTAL] اسناد: {t['d']} | مواد/نسخه‌ها: {t['a']} | جاری: {t['cur']} | تاریخی: {t['hist']} | روابط: {t['r']}")
 except Exception:
  c.rollback(); raise
 finally: c.close()
if __name__=='__main__': main()
