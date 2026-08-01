# -*- coding: utf-8 -*-
"""Load issuer disclosure and Tehran/Farabourse admission rules."""
from __future__ import annotations
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from issuer_rules import *
REF_D='DAFSH-1386';REF_T='DPT-1386';REF_TA='EPT-1402';REF_F='DPF-1388';REF_FA='EPF-1402';REFS=(REF_D,REF_T,REF_TA,REF_F,REF_FA)
D_D='2007-07-25';D_CUR='2025-05-21';D_T='2007-12-22';D_F='2009-04-14';D_A='2023-10-26'
SRC_D='دستورالعمل افشای اطلاعات ناشران؛ متن مصوب ۱۳۸۶ و نسخه تلفیقی رسمی با اصلاحات تا ۱۴۰۳/۱۰/۲۳؛ PDF رسمی سازمان بورس و نسخه مقابله‌ای پارس حقوق.'
SRC_T='دستورالعمل پذیرش اوراق بهادار در بورس تهران مصوب ۱۳۸۶، متن ۶۱ ماده با اصلاحات تلفیقی منتشرشده تا ۱۳۹۰؛ اصلاحات مؤثر ۱۴۰۲ در سند همراه ثبت شده است.'
SRC_TA='خلاصه رسمی اصلاحات ۱۴۰۲/۰۸/۰۴ بورس تهران بر پایه اطلاعیه مدیریت امور ناشران بورس تهران؛ این سند رونوشت کامل جدول اصلاحی نیست.'
SRC_F='دستورالعمل پذیرش و عرضه اوراق بهادار فرابورس مصوب ۱۳۸۸، متن کامل ۴۴ ماده اولیه.'
SRC_FA='متن کامل جدول تطبیقی مصوبه اصلاحی ۱۴۰۲/۰۸/۰۴ هیئت مدیره سازمان بورس درباره دستورالعمل فرابورس؛ منبع آرشیوی گلستان محاسب.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def lid(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,status,date,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
 did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code='directive',issuing_authority='هیئت مدیره سازمان بورس و اوراق بهادار',status_code=status,ratification_date=date,effective_date=date,reference_code=ref,notes=notes)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,lid(c,'document_types','code','directive'),lid(c,'authorities','name_fa','هیئت مدیره سازمان بورس و اوراق بهادار'),lid(c,'statuses','code',status),date,date,notes,did));return did
def clear(c,ids):
 marks=','.join('?' for _ in ids);c.execute(f'delete from relations where from_document_id in ({marks})',tuple(ids))
 for d in ids:
  c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 for topic in ('حقوق تجارت','حقوق بازار سرمایه'):link_document_topic(c,d,topic)
 for t in tags:link_document_tag(c,d,add_tag(c,t))
def ano(k):
 s=str(k)
 if 'bis' in s:
  a,b=s.split('bis',1);return pn(a)+' مکرر'+((' '+pn(b)) if b else '')
 return pn(s)
def rows(c,d,ref,data,date,source):
 out={}
 for n,t in data:out[n]=add_article(c,d,article_no=pn(n),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=source)
 return out
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[REF_D]=up(c,REF_D,'دستورالعمل اجرایی افشای اطلاعات ناشران ثبت‌شده نزد سازمان بورس و اوراق بهادار (متن تلفیقی)','دستورالعمل افشای ناشران','amended',D_D,'متن مصوب ۱۳۸۶ و ساختار تلفیقی ۲۳ مفاد جاری؛ نسخه‌های مصوب اولیه و مفاد حذف‌شده نیز تاریخی نگهداری شده‌اند.')
  docs[REF_T]=up(c,REF_T,'دستورالعمل پذیرش اوراق بهادار در بورس اوراق بهادار تهران','پذیرش بورس تهران','amended',D_T,'متن پایه ۶۱ ماده‌ای؛ اصلاحات طبقه‌بندی بازارها و تابلوها در مصوبه همراه ۱۴۰۲ ثبت شده است.')
  docs[REF_TA]=up(c,REF_TA,'خلاصه رسمی اصلاحات ۱۴۰۲ دستورالعمل پذیرش بورس اوراق بهادار تهران','اصلاح پذیرش تهران ۱۴۰۲','in_force',D_A,'سه محور رسمی اصلاحات؛ خلاصه تنقیحی است و رونوشت کامل جدول مصوبه محسوب نمی‌شود.')
  docs[REF_F]=up(c,REF_F,'دستورالعمل پذیرش و عرضه اوراق بهادار در فرابورس ایران (متن پایه مصوب ۱۳۸۸)','پذیرش فرابورس','amended',D_F,'متن کامل ۴۴ ماده اولیه؛ اصلاحیه‌های بعدی از جمله مصوبه جامع ۱۴۰۲ در سند همراه ثبت شده‌اند.')
  docs[REF_FA]=up(c,REF_FA,'مصوبه اصلاحی ۱۴۰۲ دستورالعمل پذیرش، عرضه و نقل و انتقال اوراق بهادار در فرابورس ایران','اصلاح پذیرش فرابورس ۱۴۰۲','in_force',D_A,'متن کامل جدول تطبیقی اصلاحات و پیوست‌های مصوب ۱۴۰۲/۰۸/۰۴.')
  clear(c,list(docs.values()))
  deco(c,docs[REF_D],['افشای اطلاعات','کدال','اطلاعات بااهمیت','اطلاعات نهانی','صورت مالی'])
  deco(c,docs[REF_T],['پذیرش اوراق بهادار','بورس تهران','هیئت پذیرش','لغو پذیرش'])
  deco(c,docs[REF_TA],['بازار اول','بازار دوم','طبقه‌بندی ناشران','اصلاحیه'])
  deco(c,docs[REF_F],['فرابورس','پذیرش اوراق بهادار','بازار اول','بازار دوم'])
  deco(c,docs[REF_FA],['فرابورس','بازار نوآفرین','دانش‌بنیان','اصلاحیه'])
  # Original disclosure provisions are retained as one historical generation.
  d_old={}
  for n,t in DISCLOSURE_ORIGINAL:
   d_old[str(n)]=add_article(c,docs[REF_D],article_no=pn(n),article_key=f'{REF_D}:{n}',version_no=1,is_current=0,effective_date=D_D,expiry_date=D_CUR,text=t,source_note=SRC_D,notes='نسخه مصوب اولیه')
  # Two provisions added by intervening amendments and removed in the 1403 consolidation.
  for k in ('2bis1','2bis2'):
   t=DISCLOSURE_INTERMEDIATE_DELETED[k]
   d_old[k]=add_article(c,docs[REF_D],article_no=ano(k),article_key=f'{REF_D}:{k}',version_no=1,is_current=0,effective_date='2016-09-13',expiry_date=D_CUR,text=t,source_note=SRC_D,notes='حذف‌شده در متن تلفیقی ۱۴۰۳')
  dcur={}
  for k,t in DISCLOSURE_CURRENT.items():
   ver=2 if k.isdigit() and int(k)<=21 else 1
   dcur[k]=add_article(c,docs[REF_D],article_no=ano(k),article_key=f'{REF_D}:{k}',version_no=ver,is_current=1,effective_date=D_CUR,text=t,source_note=SRC_D,notes='نسخه تلفیقی جاری')
  tids=rows(c,docs[REF_T],REF_T,TEHRAN_ADMISSION_BASE,D_T,SRC_T)
  taids=rows(c,docs[REF_TA],REF_TA,TEHRAN_AMENDMENT_1402_SUMMARY,D_A,SRC_TA)
  fids=rows(c,docs[REF_F],REF_F,FARABOURSE_ADMISSION_ORIGINAL,D_F,SRC_F)
  faid=add_article(c,docs[REF_FA],article_no='ماده واحده',article_key=f'{REF_FA}:MU',version_no=1,is_current=1,effective_date=D_A,text=FARABOURSE_AMENDMENT_1402,source_note=SRC_FA,notes='جدول تطبیقی کامل اصلاحات')
  # Network links to the market-law package and between base/amendment instruments.
  market=c.execute("select id from documents where reference_code='QBOV-1384'").fetchone();bylaw=c.execute("select id from documents where reference_code='AIBOV-1386'").fetchone();gov=c.execute("select id from documents where reference_code='DHSH-1401'").fetchone()
  if market:
   for own,target,desc in [('2','7','الزام افشا توسط ناشران'),('13','45','افشای فوری اطلاعات بااهمیت'),('17','46','حفاظت از اطلاعات نهانی')]:
    if own in dcur:add_relation(c,docs[REF_D],'implements',market['id'],from_article_id=dcur[own],description=desc+' (ماده '+pn(target)+' قانون بازار)')
   add_relation(c,docs[REF_T],'implements',market['id'],from_article_id=tids[1],description='پذیرش اوراق بهادار در بورس تهران (موضوع ماده ۳۰ قانون بازار)')
   add_relation(c,docs[REF_F],'implements',market['id'],from_article_id=fids[1],description='پذیرش و عرضه اوراق بهادار در فرابورس (موضوع ماده ۳۰ قانون بازار)')
  if bylaw:
   add_relation(c,docs[REF_T],'implements',bylaw['id'],description='اجرای ماده ۱۶ آیین‌نامه قانون بازار')
   add_relation(c,docs[REF_F],'implements',bylaw['id'],description='اجرای ماده ۱۶ آیین‌نامه قانون بازار')
  add_relation(c,docs[REF_TA],'amends',docs[REF_T],from_article_id=taids[1],description='اصلاح معیارها و طبقه‌بندی بازارها در ۱۴۰۲')
  add_relation(c,docs[REF_FA],'amends',docs[REF_F],from_article_id=faid,description='جدول تطبیقی کامل اصلاحات ۱۴۰۲')
  add_relation(c,docs[REF_T],'cites',docs[REF_D],description='رعایت الزامات افشای ناشران پذیرفته‌شده')
  add_relation(c,docs[REF_F],'cites',docs[REF_D],description='رعایت الزامات افشای ناشران فرابورسی')
  if gov:add_relation(c,docs[REF_D],'cites',gov['id'],from_article_id=dcur.get('1'),description='تعریف دستورالعمل حاکمیت شرکتی در متن تلفیقی افشا')
  c.commit();s=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)cur,(select count(*)from articles where is_current=0)hist,(select count(*)from relations)r').fetchone()
  print('[OK] افشای ناشران: ۲۳ مفاد جاری + ۲۳ تاریخی')
  print('[OK] پذیرش تهران: ۶۱ ماده | خلاصه اصلاحات ۱۴۰۲: ۳ مفاد')
  print('[OK] پذیرش فرابورس: ۴۴ ماده | جدول اصلاحات ۱۴۰۲: ۱ مفاد')
  print(f"[TOTAL] اسناد: {s['d']} | مواد/نسخه‌ها: {s['a']} | جاری: {s['cur']} | تاریخی: {s['hist']} | روابط: {s['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
