# -*- coding: utf-8 -*-
"""Load civil enforcement, financial-conviction laws, and estate bylaws."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from enforcement_law import *
REF_E='QEA-1356';REF_F='QNEM-1394';REF_FB='AINEM-1399';REF_OLD='QNEM-1377';REF_W='AIW-1322';REF_299='AIH299-1322';REFS=(REF_E,REF_F,REF_FB,REF_OLD,REF_W,REF_299)
D_E='1977-10-23';D_E_AM='2016-02-01';D_F='2015-06-13';D_OLD='1998-11-01';D_FB='2020-09-08';D_1322='1943'
SRC_E='قانون اجرای احکام مدنی مصوب ۱۳۵۶/۰۸/۰۱؛ متن کامل ۱۸۰ ماده با آخرین اصلاحات تا ۱۳۹۴/۱۱/۱۲، مقابله‌شده با پایگاه اختبار.'
SRC_F='قانون نحوه اجرای محکومیت‌های مالی مصوب ۱۳۹۳/۰۷/۱۵ مجلس و تأیید مجمع تشخیص مصلحت نظام در ۱۳۹۴/۰۳/۲۳.'
SRC_FB='آیین‌نامه نحوه اجرای محکومیت‌های مالی مصوب ۱۳۹۹/۰۶/۱۸ رئیس قوه قضائیه؛ ۲۸ ماده و ۶ تبصره.'
SRC_OLD='قانون نحوه اجرای محکومیت‌های مالی مصوب ۱۳۷۷/۰۸/۱۰؛ منسوخ به موجب ماده ۲۹ قانون سال ۱۳۹۴.'
SRC_W='آیین‌نامه راجع به مواد ۲۷۹ و ۲۸۸ قانون امور حسبی مصوب ۱۳۲۲ وزارت دادگستری.'
SRC_299='آیین‌نامه راجع به ماده ۲۹۹ قانون امور حسبی مصوب ۱۳۲۲ وزارت دادگستری.'
def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,status,rat,eff,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute("insert into authorities(name_fa,authority_type)values(?,'legislative')",(auth,)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags):
 link_document_topic(c,d,'آیین دادرسی مدنی')
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,n,text,v,cur,eff,exp,src,note=None):return add_article(c,d,article_no=pn(n),article_key=f'{ref}:{n}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[REF_E]=up(c,REF_E,'قانون اجرای احکام مدنی (متن کامل با اصلاحات)','قانون اجرای احکام مدنی','law','مجلس شورای ملی (پیش از انقلاب)','amended',D_E,D_E,'متن کامل ۱۸۰ ماده درباره اجراییه، توقیف اموال، مزایده، اعتراض ثالث اجرایی، اجرای احکام خارجی و هزینه اجرا؛ تاریخچه ماده ۹۶ ثبت شده است.')
  docs[REF_F]=up(c,REF_F,'قانون نحوه اجرای محکومیت‌های مالی','اجرای محکومیت‌های مالی','law','مجمع تشخیص مصلحت نظام','in_force',D_F,D_F,'متن کامل ۲۹ ماده درباره شناسایی اموال، حبس محکوم‌علیه، اعسار، تقسیط، مستثنیات دین و فرار از ادای دین.')
  docs[REF_FB]=up(c,REF_FB,'آیین‌نامه نحوه اجرای محکومیت‌های مالی','آیین‌نامه محکومیت‌های مالی','regulation','رئیس قوه قضائیه','in_force',D_FB,D_FB,'متن کامل ۲۸ ماده و ۶ تبصره درباره حبس، اعسار، کسر حقوق، استعلام اموال و مستثنیات دین.')
  docs[REF_OLD]=up(c,REF_OLD,'قانون نحوه اجرای محکومیت‌های مالی مصوب ۱۳۷۷ (منسوخ)','قانون مالی ۱۳۷۷','law','مجلس شورای اسلامی','abrogated',D_OLD,D_OLD,'متن کامل هفت ماده؛ از ۱۳۹۴/۰۳/۲۳ به موجب ماده ۲۹ قانون جدید منسوخ است.')
  docs[REF_W]=up(c,REF_W,'آیین‌نامه راجع به مواد ۲۷۹ و ۲۸۸ قانون امور حسبی (وصیت‌نامه سری)','آیین‌نامه وصیت‌نامه سری','regulation','وزارت دادگستری','in_force',D_1322,D_1322,'پنج ماده درباره محل و ترتیب امانت‌گذاری و ارسال وصیت‌نامه سری پس از فوت موصی.')
  docs[REF_299]=up(c,REF_299,'آیین‌نامه راجع به ماده ۲۹۹ قانون امور حسبی','آیین‌نامه ثبت ارث و وصیت','regulation','وزارت دادگستری','in_force',D_1322,D_1322,'چهارده ماده درباره ثبت ملک مورث به نام ورثه یا موصی‌له و آثار اختلاف یا اعتراض نسبت به وصیت.')
  for d in docs.values():clear(c,d)
  deco(c,docs[REF_E],('اجرای احکام مدنی','توقیف اموال','مزایده','محکوم‌له','اعتراض ثالث اجرایی'))
  deco(c,docs[REF_F],('محکومیت مالی','اعسار','مستثنیات دین','فرار از ادای دین','ممنوع‌الخروجی'))
  deco(c,docs[REF_FB],('اعسار','تقسیط','کسر حقوق','استعلام اموال'))
  deco(c,docs[REF_OLD],('قانون منسوخ','محکومیت مالی'))
  deco(c,docs[REF_W],('وصیت‌نامه سری','امانت اسناد'))
  deco(c,docs[REF_299],('ثبت ارث','موصی‌له','گواهی انحصار وراثت'))
  eids={};ecount=0
  for n,text in CIVIL_EXECUTION_CURRENT:
   if n==96:
    av(c,docs[REF_E],REF_E,n,CIVIL_EXECUTION_ART96_OLD,1,False,D_E,D_E_AM,SRC_E,'متن پیش از اصلاح تبصره ۲ در سال ۱۳۹۴.')
    eids[n]=av(c,docs[REF_E],REF_E,n,text,2,True,D_E_AM,None,SRC_E,'نسخه جاری با حمایت از مستمری مددجویان کمیته امداد و بهزیستی.');ecount+=2
   else:eids[n]=av(c,docs[REF_E],REF_E,n,text,1,True,D_E,None,SRC_E);ecount+=1
  fids={n:av(c,docs[REF_F],REF_F,n,t,1,True,D_F,None,SRC_F) for n,t in FINANCIAL_CONVICTIONS_1394}
  bids={n:av(c,docs[REF_FB],REF_FB,n,t,1,True,D_FB,None,SRC_FB) for n,t in FINANCIAL_BYLAW_1399}
  oldids={n:av(c,docs[REF_OLD],REF_OLD,n,t,1,False,D_OLD,D_F,SRC_OLD,'منسوخ از تاریخ لازم‌الاجرا شدن قانون جدید.') for n,t in FINANCIAL_CONVICTIONS_1377}
  wids={n:av(c,docs[REF_W],REF_W,n,t,1,True,D_1322,None,SRC_W) for n,t in SECRET_WILL_BYLAW}
  xids={n:av(c,docs[REF_299],REF_299,n,t,1,True,D_1322,None,SRC_299) for n,t in HASBI_299_BYLAW}
  for n in range(1,8):add_relation(c,docs[REF_F],'abrogates',docs[REF_OLD],from_article_id=fids[29],to_article_id=oldids[n],description=f'نسخ ماده {pn(n)} قانون ۱۳۷۷ به موجب ماده ۲۹ قانون جدید.')
  add_relation(c,docs[REF_F],'cites',docs[REF_E],from_article_id=fids[1],to_article_id=eids[1],description='توقیف و استیفای محکوم‌به مطابق قانون اجرای احکام مدنی.')
  add_relation(c,docs[REF_FB],'implements',docs[REF_F],from_article_id=bids[1],to_article_id=fids[28],description='آیین‌نامه اجرایی موضوع ماده ۲۸ قانون.')
  add_relation(c,docs[REF_FB],'cites',docs[REF_E],from_article_id=bids[3],to_article_id=eids[46],description='تقویم محکوم‌به عین معین بر پایه ماده ۴۶.')
  add_relation(c,docs[REF_FB],'cites',docs[REF_E],from_article_id=bids[9],to_article_id=eids[96],description='کسر حقوق و مزایای محکوم‌علیه.')
  h=c.execute("select id from documents where reference_code='QAH-1319'").fetchone()
  if h:
   add_relation(c,docs[REF_W],'implements',h['id'],description='آیین‌نامه مواد ۲۷۹ و ۲۸۸ قانون امور حسبی درباره وصیت‌نامه سری.')
   add_relation(c,docs[REF_299],'implements',h['id'],description='آیین‌نامه موضوع ماده ۲۹۹ قانون امور حسبی درباره ثبت ملک ورثه و موصی‌له.')
  for ref,desc in (('QADM-1379','ارتباط با تشریفات عمومی آیین دادرسی مدنی.'),('QATV-1318','اعلام ورشکستگی محکوم‌علیه تاجر به اداره یا مدیر تصفیه.')):
   d=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
   if d:add_relation(c,docs[REF_E],'cites',d['id'],description=desc)
  c.commit();z=c.execute('''select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r''').fetchone()
  print(f'[OK] اجرای احکام مدنی: ۱۸۰ ماده جاری، {ecount} نسخه')
  print('[OK] محکومیت‌های مالی: ۲۹ | آیین‌نامه: ۲۸ | قانون منسوخ ۱۳۷۷: ۷ تاریخی | آیین‌نامه‌های وصیت/ارث: ۵/۱۴')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
