# -*- coding: utf-8 -*-
"""Load the Bankruptcy Liquidation Administration Law and regulations."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from bankruptcy_law import *
REF='QATV-1318';REF_B='AATV-1318';REF_F='QSFB-1344'
D0='1939-07-15';D1373='1995-03-19';D1403='2025-03-16';DB='1939';DF='1965-04-22'
SRC='قانون اداره تصفیه امور ورشکستگی مصوب ۱۳۱۸/۴/۲۴؛ متن با منابع رسمی و https://www.ekhtebar.ir مقابله شده است.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def idof(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,status,date,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
 did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=date,effective_date=date,reference_code=ref,notes=notes)
 aid=idof(c,'authorities','name_fa',auth)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,idof(c,'document_types','code',typ),aid,idof(c,'statuses','code',status),date,date,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 for topic in ('حقوق تجارت','آیین دادرسی مدنی'):link_document_topic(c,d,topic)
 for t in tags:link_document_tag(c,d,add_tag(c,t))
def rows(c,d,ref,data,date,source):
 out={}
 for n,t in data:out[n]=add_article(c,d,article_no=pn(n),article_key=f'{ref}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=source)
 return out
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[REF]=up(c,REF,'قانون اداره تصفیه امور ورشکستگی (مصوب ۱۳۱۸، با وضعیت تنقیحی ۱۴۰۳)','ق.ا.ت.و.','law','مجلس شورای ملی (پیش از انقلاب)','amended',D0,'متن کامل ۶۰ ماده؛ مواد ۵۳ و ۵۶ و بند ۱ ماده ۵۴ در سال ۱۴۰۳ منسوخ اعلام شده‌اند.')
  docs[REF_B]=up(c,REF_B,'آیین‌نامه اداره تصفیه امور ورشکستگی','آیین‌نامه اداره تصفیه','regulation','وزارت دادگستری','in_force',DB,'متن کامل ۶۷ ماده آیین‌نامه موضوع ماده ۶۰ قانون.')
  docs[REF_F]=up(c,REF_F,'قانون طرز استفاده از درآمد صندوق‌های الف و ب اداره کل تصفیه امور ورشکستگی','قانون صندوق‌های تصفیه','law','مجلس شورای ملی (پیش از انقلاب)','amended',DF,'سه ماده درباره مصارف صندوق ب و نحوه اجرای آن؛ سازوکار مالی آن با قوانین بعدی تغییر یافته است.')
  for d in docs.values():clear(c,d)
  deco(c,docs[REF],['ورشکستگی','اداره تصفیه','طلبکاران','مزایده','قانون مادر'])
  deco(c,docs[REF_B],['ورشکستگی','حسابداری','طبقه‌بندی بستانکاران','صندوق الف','صندوق ب'])
  deco(c,docs[REF_F],['صندوق الف','صندوق ب','درآمد اختصاصی'])
  o=dict(BANKRUPTCY_ORIGINAL);cur=dict(BANKRUPTCY_CURRENT);ids={};oldids={};count=0
  for n in range(1,61):
   if n==54:
    stages=[(D0,o[n],'متن مصوب ۱۳۱۸'),(D1373,BANKRUPTCY_ART54_1373,'اصلاح سازوکار درآمد صندوق ب در ۱۳۷۳'),(D1403,cur[n],'نسخه جاری پس از نسخ بند ۱ در ۱۴۰۳')]
   elif n in (53,56):stages=[(D0,o[n],'منسوخ به موجب قانون فهرست احکام نامعتبر تجارت ۱۴۰۳')]
   else:stages=[(D0,o[n],'متن مصوب ۱۳۱۸')]
   for i,(date,text,note) in enumerate(stages,1):
    isc=int(i==len(stages) and n not in (53,56));exp=(stages[i][0] if i<len(stages) else (D1403 if n in (53,56) else None))
    aid=add_article(c,docs[REF],article_no=pn(n),article_key=f'{REF}:{n}',version_no=i,is_current=isc,effective_date=date,expiry_date=exp,text=text,source_note=SRC,notes=note)
    if isc:ids[n]=aid
    else:oldids[n]=aid
    count+=1
  bid=rows(c,docs[REF_B],REF_B,BANKRUPTCY_BYLAW,DB,'آیین‌نامه رسمی اداره تصفیه؛ https://qavanin.ir/Law/TreeText/192317')
  fid=rows(c,docs[REF_F],REF_F,BANKRUPTCY_FUNDS_LAW,DF,'قانون مصوب ۱۳۴۴/۲/۲')
  add_relation(c,docs[REF_B],'implements',docs[REF],from_article_id=bid[1],to_article_id=ids[60],description='آیین‌نامه اجرایی موضوع ماده ۶۰ قانون.')
  for n in range(51,58):
   target=ids.get(n) or oldids.get(n)
   add_relation(c,docs[REF_F],'amends',docs[REF],from_article_id=fid[1],to_article_id=target,description='مقررات تکمیلی مربوط به صندوق‌های الف و ب.')
  invalid=c.execute("select id from documents where reference_code='FNAT-1403'").fetchone()
  if invalid:
   ia=c.execute('select id from articles where document_id=? order by id limit 1',(invalid['id'],)).fetchone()
   for n,target in ((53,oldids[53]),(54,oldids[54]),(56,oldids[56])):
    add_relation(c,invalid['id'],'abrogates',docs[REF],from_article_id=(ia['id'] if ia else None),to_article_id=target,description=f'نسخ ماده/بند مرتبط {pn(n)} در قانون فهرست ۱۴۰۳.')
  for code,desc in [('QT-1311','تکمیل مقررات ورشکستگی مواد ۴۱۲ تا ۵۷۵ قانون تجارت'),('QADM-1379','ارتباط با قواعد دادرسی مدنی')]:
   d=c.execute('select id from documents where reference_code=?',(code,)).fetchone()
   if d:add_relation(c,docs[REF],'cites',d['id'],description=desc)
  c.commit();t=c.execute('select (select count(*) from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)cur,(select count(*)from articles where is_current=0)hist,(select count(*)from relations)r').fetchone()
  print(f'[OK] قانون اداره تصفیه: ۶۰ شماره ماده، {count} نسخه، ۵۸ ماده جاری')
  print('[OK] آیین‌نامه: ۶۷ ماده | قانون صندوق‌ها: ۳ ماده')
  print(f"[TOTAL] اسناد: {t['d']} | مواد/نسخه‌ها: {t['a']} | جاری: {t['cur']} | تاریخی: {t['hist']} | روابط: {t['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
