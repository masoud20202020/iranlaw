# -*- coding: utf-8 -*-
"""Load complete Family Protection Law, its bylaw, and Non-Contentious Matters Law."""
from __future__ import annotations
import os, sys

SCRIPT_DIR=os.path.dirname(__file__); ROOT=os.path.dirname(SCRIPT_DIR)
sys.path[:0]=[SCRIPT_DIR,os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from family_law import *

REF_F='QHKH-1391'; REF_B='AQHKH-1392'; REF_H='QAH-1319'; REFS=(REF_F,REF_B,REF_H)
D_F='2013-02-19'; D_B='2015-02-16'; D_1400='2021-08-29'; D_1402='2023-09-30'
D_H='1940-06-23'; D_1342='1963-12-11'
SRC_F='قانون حمایت خانواده مصوب ۱۳۹۱/۱۲/۰۱ مجلس شورای اسلامی؛ متن ۵۸ ماده‌ای با نسخه روزنامه رسمی و پایگاه اختبار مقابله شده است.'
SRC_B='آیین‌نامه اجرایی قانون حمایت خانواده مصوب ۱۳۹۳/۱۱/۲۷ رئیس قوه قضائیه؛ متن با اصلاحات ۱۴۰۰ و ۱۴۰۲ خبرگزاری میزان و شناسنامه قانون مقابله شده است.'
SRC_H='قانون امور حسبی مصوب ۱۳۱۹/۰۴/۰۲ مجلس شورای ملی؛ متن کامل ۳۷۸ ماده با اصلاحات تا ۱۳۷۴ از نسخه شناسنامه قانون.'

def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gid(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None

def up(c,ref,title,short,typ,auth,status,rat,eff,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
 did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
 aid=gid(c,'authorities','name_fa',auth)
 if aid is None: aid=c.execute("insert into authorities(name_fa,authority_type) values(?,'legislative')",(auth,)).lastrowid
 c.execute('''update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?''',(title,short,gid(c,'document_types','code',typ),aid,gid(c,'statuses','code',status),rat,eff,notes,did));return did

def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))

def deco(c,d,topics,tags):
 for x in topics:link_document_topic(c,d,x)
 for x in tags:link_document_tag(c,d,add_tag(c,x))

def av(c,d,ref,n,text,v,cur,eff,exp,src,note=None):
 return add_article(c,d,article_no=pn(n),article_key=f'{ref}:{n}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)

def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[REF_F]=up(c,REF_F,'قانون حمایت خانواده (متن کامل مصوب ۱۳۹۱)','قانون حمایت خانواده','law','مجلس شورای اسلامی','in_force',D_F,D_F,'متن کامل ۵۸ ماده درباره دادگاه خانواده، مراکز مشاوره، ازدواج، طلاق، مهریه، حضانت، مستمری بازماندگان و ضمانت اجراها.')
  docs[REF_B]=up(c,REF_B,'آیین‌نامه اجرایی قانون حمایت خانواده با اصلاحات ۱۴۰۰ و ۱۴۰۲','آیین‌نامه حمایت خانواده','regulation','رئیس قوه قضائیه','amended',D_B,D_B,'پوشش ۶۹ شماره ماده؛ ۶۷ ماده جاری، مواد ۱۴ و ۱۵ منسوخ و تاریخچه اصلاح مواد ۱۰، ۳۲، ۳۳، ۳۴، ۳۶ و ۴۷ در سال ۱۴۰۲.')
  docs[REF_H]=up(c,REF_H,'قانون امور حسبی (متن کامل با اصلاحات)','قانون امور حسبی','law','مجلس شورای ملی (پیش از انقلاب)','amended',D_H,D_H,'متن کامل ۳۷۸ ماده درباره امور حسبی، قیمومت، غایب مفقودالاثر، ترکه، وصیت و تصدیق انحصار وراثت؛ تاریخچه هزینه ماده ۳۷۵ ثبت شده است.')
  for d in docs.values():clear(c,d)
  deco(c,docs[REF_F],('حقوق خانواده','آیین دادرسی مدنی'),('دادگاه خانواده','طلاق','مهریه','نفقه','حضانت','مراکز مشاوره خانواده'))
  deco(c,docs[REF_B],('حقوق خانواده','آیین دادرسی مدنی'),('طلاق توافقی','داوری خانواده','مشاور خانواده','ثبت ازدواج و طلاق','ملاقات طفل'))
  deco(c,docs[REF_H],('حقوق خانواده','آیین دادرسی مدنی'),('امور حسبی','قیمومت','غایب مفقودالاثر','ترکه','وصیت','انحصار وراثت'))

  fids={}
  for n,text in FAMILY_PROTECTION_LAW:
   fids[n]=av(c,docs[REF_F],REF_F,n,text,1,True,D_F,None,SRC_F)

  base=dict(FAMILY_BYLAW_BASE);cur=dict(FAMILY_BYLAW_CURRENT);amended=set(FAMILY_BYLAW_AMENDED);repealed=set(FAMILY_BYLAW_REPEALED);bids={};b_old={};bcount=0
  for n in range(1,70):
   if n in repealed:
    b_old[n]=av(c,docs[REF_B],REF_B,n,base[n],1,False,D_B,D_1400,SRC_B,'منسوخ به موجب اصلاحات آیین‌نامه در ۱۴۰۰.');bcount+=1
   elif n in amended:
    b_old[n]=av(c,docs[REF_B],REF_B,n,base[n],1,False,D_B,D_1402,SRC_B,'متن مصوب ۱۳۹۳ پیش از اصلاح ۱۴۰۲.')
    bids[n]=av(c,docs[REF_B],REF_B,n,cur[n],2,True,D_1402,None,SRC_B,'نسخه جاری مطابق اصلاحیه ۱۴۰۲/۰۷/۰۸.');bcount+=2
   else:
    bids[n]=av(c,docs[REF_B],REF_B,n,cur[n],1,True,D_B,None,SRC_B);bcount+=1

  hids={};hcount=0
  for n,text in HASBI_CURRENT:
   if n==375:
    av(c,docs[REF_H],REF_H,n,HASBI_ART375_OLD,1,False,D_H,D_1342,SRC_H,'هزینه مقرر در متن اولیه.')
    hids[n]=av(c,docs[REF_H],REF_H,n,text,2,True,D_1342,None,SRC_H,'اصلاح مبلغ هزینه به موجب قانون افزایش هزینه دادرسی ۱۳۴۲.');hcount+=2
   else:
    hids[n]=av(c,docs[REF_H],REF_H,n,text,1,True,D_H,None,SRC_H);hcount+=1

  for own,target,desc in ((1,17,'تشکیل و فعالیت مراکز مشاوره خانواده.'),(57,21,'ثبت وقایع ازدواج و طلاق.'),(66,41,'نظارت بر ملاقات والدین با طفل.'),(69,57,'آیین‌نامه اجرایی موضوع ماده ۵۷ قانون.')):
   add_relation(c,docs[REF_B],'implements',docs[REF_F],from_article_id=bids[own],to_article_id=fids[target],description=desc)
  add_relation(c,docs[REF_F],'cites',docs[REF_H],from_article_id=fids[4],description='صلاحیت دادگاه خانواده در قیمومت، غایب مفقودالاثر و سایر امور حسبی.')
  add_relation(c,docs[REF_H],'cites',docs[REF_F],description='قواعد خاص و مؤخر دادگاه خانواده در امور حسبی و احوال شخصیه.')
  for ref,desc in (('QM-1307','تکمیل قواعد نکاح، طلاق، نفقه، حضانت، حجر و ارث قانون مدنی.'),('QADM-1379','تشریفات عمومی رسیدگی و اجرای احکام خانواده.')):
   d=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
   if d:add_relation(c,docs[REF_F],'cites',d['id'],description=desc)
  d=c.execute("select id from documents where reference_code='QM-1307'").fetchone()
  if d:add_relation(c,docs[REF_H],'cites',d['id'],description='قواعد ماهوی حجر، ولایت، وصیت و ارث در قانون مدنی.')

  c.commit();t=c.execute('''select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r''').fetchone()
  print('[OK] قانون حمایت خانواده: ۵۸ ماده جاری')
  print(f'[OK] آیین‌نامه خانواده: ۶۹ شماره، {bcount} نسخه، ۶۷ جاری، ۸ تاریخی | امور حسبی: ۳۷۸ ماده، {hcount} نسخه')
  print(f"[TOTAL] اسناد: {t['d']} | مواد/نسخه‌ها: {t['a']} | جاری: {t['c']} | تاریخی: {t['h']} | روابط: {t['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
