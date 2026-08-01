# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'data','seed')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
from environment import ENV,AIR,WASTE,WASTE_BYLAW,FORESTS
F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');S={'QHBE-1353':'https://www.mizanonline.ir/fa/news/4761325/','QHP-1396':'https://www.ekhtebar.ir/قانون-هوای-پاک/','QMP-1383':'https://www.ekhtebar.ir/قانون-مدیریت-پسماندها/','AIMP-1384':'https://www.ekhtebar.ir/آیین‌نامه-اجرایی-قانون-مدیریت-پسماند/','QHBJM-1346':'https://www.ekhtebar.ir/قانون-حفاظت-و-بهره-برداري-از-جنگلها-و-مر/'}
def one(c,q,x):
 r=c.execute(q,(x,)).fetchone();return r['id'] if r else None
def doc(c,r,t,s,date,note):
 d=one(c,'select id from documents where reference_code=?',r);typ='regulation' if r=='AIMP-1384' else 'law';auth='هیئت وزیران' if typ=='regulation' else ('مجلس شورای ملی (پیش از انقلاب)' if r in ('QHBE-1353','QHBJM-1346') else 'مجلس شورای اسلامی')
 if not d:d=get_or_create_document(c,title=t,short_title=s,type_code=typ,issuing_authority=auth,status_code='amended',ratification_date=date,effective_date=date,reference_code=r,notes=note)
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?',typ),one(c,'select id from authorities where name_fa=?',auth),one(c,'select id from statuses where code=?','amended'),date,date,note,d));return d
def clear(c,d):
 for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
def rows(c,d,r,x,date,note):
 z={}
 for n,t in x:z[n]=add_article(c,d,article_no=n.translate(F),article_key=f'{r}:{n}',version_no=1,is_current=1,effective_date=date,text=t,source_note=S[r],notes=note)
 return z
def main():
 c=get_connection()
 try:
  c.execute('begin');sp=[('QHBE-1353','قانون حفاظت و بهسازی محیط زیست با اصلاحات و الحاقات','حفاظت محیط زیست','1974-06-18','متن تلفیقی ۲۱ ماده‌ای، با اصلاحات منعکس در منبع.'),('QHP-1396','قانون هوای پاک','هوای پاک','2017-07-16','متن کامل ۳۴ ماده.'),('QMP-1383','قانون مدیریت پسماندها','مدیریت پسماند','2004-05-09','متن کامل ۲۳ ماده.'),('AIMP-1384','آیین‌نامه اجرایی قانون مدیریت پسماندها','آیین‌نامه پسماند','2005-07-25','متن کامل ۳۹ ماده.'),('QHBJM-1346','قانون حفاظت و بهره‌برداری از جنگل‌ها و مراتع با اصلاحات','جنگل‌ها و مراتع','1967-08-16','متن تلفیقی ۶۷ ماده شماره‌دار؛ تکرار فنی ماده ۶۴ در منبع یک‌بار ثبت شد.')]
  ds={x[0]:doc(c,*x) for x in sp}
  for r,d in ds.items():
   clear(c,d);link_document_topic(c,d,'حقوق عمومی')
   for tag in ('محیط زیست','منابع طبیعی','آلودگی','پسماند'):link_document_tag(c,d,add_tag(c,tag))
  ids={}
  for r,x,date,note in [('QHBE-1353',ENV,'1974-06-18','متن تلفیقی جاری.'),('QHP-1396',AIR,'2017-07-16','متن کامل.'),('QMP-1383',WASTE,'2004-05-09','متن کامل.'),('AIMP-1384',WASTE_BYLAW,'2005-07-25','متن کامل.'),('QHBJM-1346',FORESTS,'1967-08-16','متن تلفیقی منبع‌دار.')]:ids[r]=rows(c,ds[r],r,x,date,note)
  add_relation(c,ds['AIMP-1384'],'implements',ds['QMP-1383'],description='آیین‌نامه اجرایی قانون مدیریت پسماندها.')
  add_relation(c,ds['QHP-1396'],'cites',ds['QHBE-1353'],description='حمایت از محیط زیست و جلوگیری از آلودگی هوا.')
  add_relation(c,ds['QHBJM-1346'],'cites',ds['QHBE-1353'],description='ارتباط حفاظت منابع طبیعی و محیط زیست.')
  c.commit();print('loaded environment',sum(len(x) for x in (ENV,AIR,WASTE,WASTE_BYLAW,FORESTS)))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
