# -*- coding: utf-8 -*-
"""Load anti-smuggling law, customs legislation, executive rules and unified rulings."""
import os,sys,re
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from customs_smuggling import *

RL='QMK-1392';RA='EQMK-1400';RC='QAG-1390';RB='AIAG-1391';RS='AIQK-56-1395';RD='AIQK-5556-1401';R736='RVR-736-1393';R839='RVR-839-1402';R878='RVR-878-1405';REFS=(RL,RA,RC,RB,RS,RD,R736,R839,R878)
DL='2013-12-24';DA='2022-01-30';D94='2015-10-13';D1401='2022-05-01';DC='2011-11-13';DB='2013-02-24';DS='2016-06-26';DD='2023-01-29';D736='2014-11-25';D839='2023-12-05';D878='2026-06-16'
SRC_L='قانون مبارزه با قاچاق کالا و ارز مصوب ۱۳۹۲/۱۰/۰۳ با اصلاحات جامع ۱۴۰۰؛ متن تلفیقی اختبار و مقابله با شناسنامه قانون.'
SRC_PRE='آخرین متن تلفیقی قابل دسترس پیش از اصلاح جامع ۱۴۰۰ در پایگاه ستاد مبارزه با قاچاق کالا و ارز؛ برای تاریخچه مواد اصلاح‌شده.'
SRC_A='قانون اصلاح قانون مبارزه با قاچاق کالا و ارز مصوب ۱۴۰۰/۱۱/۱۰؛ متن کامل ۴۷ ماده.'
SRC_C='قانون امور گمرکی مصوب ۱۳۹۰/۰۸/۲۲ با اصلاحات تا ۱۴۰۱/۰۲/۱۱؛ متن اختبار و مقابله با شناسنامه قانون.'
SRC_B='آیین‌نامه اجرایی قانون امور گمرکی مصوب ۱۳۹۱/۱۲/۰۶ با اصلاحات بعدی؛ ۲۲۱ ماده و ماده ۱۸۹ مکرر.'
SRC_S='آیین‌نامه اجرایی مواد ۵ و ۶ قانون مبارزه با قاچاق کالا و ارز مصوب ۱۳۹۵/۰۴/۰۶ با اصلاحات تا ۱۳۹۸/۰۷/۲۸؛ متن ۴۶ ماده‌ای.'
SRC_D='آیین‌نامه اجرایی مواد ۵۵ و ۵۶ قانون مبارزه با قاچاق کالا و ارز، تصویب‌نامه شماره ۲۱۶۱۰۵/ت۶۰۱۷۸هـ مصوب ۱۴۰۱/۱۱/۰۹؛ متن ۲۵ ماده‌ای.'
SRC_736='قسمت لازم‌الاتباع رأی وحدت رویه شماره ۷۳۶ مورخ ۱۳۹۳/۰۹/۰۴ هیأت عمومی دیوان عالی کشور.'
SRC_839='قسمت لازم‌الاتباع رأی وحدت رویه شماره ۸۳۹ مورخ ۱۴۰۲/۰۹/۱۴ هیأت عمومی دیوان عالی کشور.'
SRC_878='قسمت لازم‌الاتباع رأی وحدت رویه شماره ۸۷۸ مورخ ۱۴۰۵/۰۳/۲۶ هیأت عمومی دیوان عالی کشور.'
HISTORY_KEYS=('1','2','3','5','6','7','11','18','20','21','27','37','41','42','47','48','49','50','52','53','55','56','59','60','63','65','66','68','69','73')
AMEND_MAP={'1':3,'2':6,'3':14,'4':15,'5':16,'6':17,'7':13,'11':19,'18':20,'20':21,'21':22,'27':24,'37':26,'41':28,'42':29,'47':31,'48':32,'49':33,'50':34,'52':36,'53':37,'55':38,'56':39,'59':40,'60':41,'63':42,'65':43,'66':44,'68':45,'69':46,'77':47,'78':47}
NEW_MAP={'2bis':12,'6bis1':17,'6bis2':18,'25bis':23,'33bis1':25,'33bis2':25,'42bis':30,'50bis1':35,'50bis2':35,'50bis3':35}

def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
 r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None
def up(c,ref,title,short,typ,auth,atype,status,rat,eff,notes):
 r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
 aid=gi(c,'authorities','name_fa',auth)
 if aid is None:aid=c.execute('insert into authorities(name_fa,authority_type)values(?,?)',(auth,atype)).lastrowid
 c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',(title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,notes,did));return did
def clear(c,d):
 c.execute('delete from relations where from_document_id=?',(d,));c.execute('delete from articles_fts where document_id=?',(d,));c.execute('delete from articles where document_id=?',(d,));c.execute('delete from document_tags where document_id=?',(d,));c.execute('delete from document_topics where document_id=?',(d,))
def deco(c,d,tags,topics=('حقوق کیفری','حقوق اداری','حقوق تجارت')):
 for t in topics:link_document_topic(c,d,t)
 for x in tags:link_document_tag(c,d,add_tag(c,x))
def av(c,d,ref,key,no,text,v,cur,eff,exp,src,note=None):return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)
def rows(c,d,ref,data,date,src,keyed=False):
 out={}
 for item in data:
  if keyed:key,no,text=item
  else:key,text=item;no=pn(key)
  out[key]=av(c,d,ref,key,no,text,1,True,date,None,src)
 return out

def main():
 c=get_connection()
 try:
  c.execute('begin');docs={}
  docs[RL]=up(c,RL,'قانون مبارزه با قاچاق کالا و ارز با اصلاحات ۱۴۰۰ و ۱۴۰۱','مبارزه با قاچاق کالا و ارز','law','مجلس شورای اسلامی','legislative','amended',DL,DL,'پوشش ۷۸ شماره و ۱۱ ماده مکرر؛ مواد ۴ و ۷۶ تاریخی‌اند. ۳۰ ماده اصلاح‌شده، ماده ۷۳ و تفکیک مواد ۷۷ و ۷۸ نسخه‌بندی شده‌اند.')
  docs[RA]=up(c,RA,'قانون اصلاح قانون مبارزه با قاچاق کالا و ارز مصوب ۱۴۰۰','اصلاح قانون قاچاق ۱۴۰۰','amendment','مجلس شورای اسلامی','legislative','in_force',DA,DA,'متن کامل ۴۷ ماده اصلاحی و الحاقی؛ مرجع تاریخچه جامع اصلاحات قانون قاچاق کالا و ارز.')
  docs[RC]=up(c,RC,'قانون امور گمرکی با اصلاحات تا ۱۴۰۱','قانون امور گمرکی','law','مجلس شورای اسلامی','legislative','amended',DC,DC,'متن کامل ۱۶۵ ماده؛ تاریخچه تعریف تضمین در ماده ۱ و حذف بند «غ» ماده ۱۱۹ نگهداری شده است.')
  docs[RB]=up(c,RB,'آیین‌نامه اجرایی قانون امور گمرکی با اصلاحات بعدی','آیین‌نامه امور گمرکی','regulation','هیئت وزیران','executive','amended',DB,DB,'پوشش کامل مواد ۱ تا ۲۲۱ و ماده ۱۸۹ مکرر؛ متن جاری تلفیقی شامل اصلاحات شناسایی‌شده تا ۱۴۰۱ است، اما همه نسل‌های پیشین مواد جداگانه ثبت نشده‌اند.')
  docs[RS]=up(c,RS,'آیین‌نامه اجرایی مواد ۵ و ۶ قانون مبارزه با قاچاق کالا و ارز','آیین‌نامه سامانه‌های مبارزه با قاچاق','regulation','هیئت وزیران','executive','amended',DS,DS,'متن کامل ۴۶ ماده درباره سامانه جامع تجارت، سامانه ارزی، حمل‌ونقل، پنجره واحد و تبادل اطلاعات؛ اصلاحات تا ۱۳۹۸ در متن جاری اعمال شده است.')
  docs[RD]=up(c,RD,'آیین‌نامه اجرایی مواد ۵۵ و ۵۶ قانون مبارزه با قاچاق کالا و ارز','آیین‌نامه فروش و امحای کالای قاچاق','regulation','هیئت وزیران','executive','in_force',DD,DD,'متن کامل ۲۵ ماده درباره فروش، صادرات، امحا، استرداد و سامانه اموال تملیکی؛ جایگزین آیین‌نامه ۱۳۹۵ است.')
  docs[R736]=up(c,R736,'رأی وحدت رویه شماره ۷۳۶ درباره صلاحیت رسیدگی به قاچاق کالای ممنوع','رأی وحدت رویه ۷۳۶','unified_ruling','دیوان عالی کشور','judicial','in_force',D736,D736,'قسمت لازم‌الاتباع رأی درباره صلاحیت دادسرا و دادگاه انقلاب در قاچاق کالای ممنوع.')
  docs[R839]=up(c,R839,'رأی وحدت رویه شماره ۸۳۹ درباره صلاحیت نگهداری جزئی کالای ممنوع قاچاق','رأی وحدت رویه ۸۳۹','unified_ruling','دیوان عالی کشور','judicial','in_force',D839,D839,'قسمت لازم‌الاتباع رأی: نگهداری جزئی مشروبات الکلی خارجی که مصداق قاچاق نیست در صلاحیت دادگاه کیفری دو است.')
  docs[R878]=up(c,R878,'رأی وحدت رویه شماره ۸۷۸ درباره تأخیر در تعهدات ارزی واردکنندگان','رأی وحدت رویه ۸۷۸','unified_ruling','دیوان عالی کشور','judicial','in_force',D878,D878,'قسمت لازم‌الاتباع تازه‌ترین رأی شناسایی‌شده درباره مابه‌التفاوت نرخ ارز و صلاحیت سازمان تعزیرات حکومتی.')
  for d in docs.values():clear(c,d)
  deco(c,docs[RL],('قاچاق کالا','قاچاق ارز','کالای ممنوع','تعزیرات حکومتی','دادگاه انقلاب','کالای قاچاق'))
  deco(c,docs[RA],('اصلاح قانون قاچاق','تعهد ارزی','کارت بازرگانی','اموال تملیکی'))
  deco(c,docs[RC],('گمرک','حقوق ورودی','ترخیص کالا','ارزش گمرکی','قاچاق گمرکی'))
  deco(c,docs[RB],('تشریفات گمرکی','ورود موقت','عبور خارجی','کارگزار گمرکی','اختلاف گمرکی'))
  deco(c,docs[RS],('سامانه جامع تجارت','سامانه ارزی','پنجره واحد تجارت','شناسه کالا'))
  deco(c,docs[RD],('اموال تملیکی','فروش کالای قاچاق','امحای کالا','فروش به شرط صادرات'))
  deco(c,docs[R736],('صلاحیت دادگاه انقلاب','قاچاق کالای ممنوع'),('حقوق کیفری','آیین دادرسی کیفری'))
  deco(c,docs[R839],('نگهداری کالای ممنوع','صلاحیت دادگاه کیفری دو'),('حقوق کیفری','آیین دادرسی کیفری'))
  deco(c,docs[R878],('تعهد ارزی واردکننده','مابه‌التفاوت نرخ ارز','صلاحیت تعزیرات'),('حقوق کیفری','حقوق پول و بانک'))

  current={k:(no,t) for k,no,t in SMUGGLING_CURRENT};pre={k:(no,t) for k,no,t in SMUGGLING_PRE1400}
  lids={};lold={}
  for key,(no,text) in current.items():
   if key=='4':lold[key]=av(c,docs[RL],RL,key,no,SMUGGLING_ART4_HISTORICAL,1,False,DL,DA,SRC_PRE,'ماده ۴ به موجب ماده ۱۵ اصلاحیه ۱۴۰۰ حذف شده است.');continue
   if key=='76':lold[key]=av(c,docs[RL],RL,key,no,SMUGGLING_ART76_HISTORICAL,1,False,DL,D94,SRC_L,'ماده ۷۶ به موجب اصلاحات ۱۳۹۴ منسوخ است؛ نمایش آن در یک منبع تلفیقی به معنی احیای حکم نیست.');continue
   if key in HISTORY_KEYS:
    old=pre[key][1];exp=D1401 if key=='73' else DA;eff=D1401 if key=='73' else DA
    lold[key]=av(c,docs[RL],RL,key,no,old,1,False,DL,exp,SRC_PRE,'نسخه پیش از اصلاح مؤثر بعدی.')
    lids[key]=av(c,docs[RL],RL,key,no,text,2,True,eff,None,SRC_L,'نسخه جاری تلفیقی.')
   elif key=='77':
    lold[key]=av(c,docs[RL],RL,key,no,SMUGGLING_OLD_ART77_FINANCE,1,False,DL,DA,SRC_PRE,'تبصره مالی ماده ۷۷ پیش از تبدیل به ماده مستقل در اصلاحیه ۱۴۰۰.')
    lids[key]=av(c,docs[RL],RL,key,no,text,2,True,DA,None,SRC_L,'ماده ۷۷ جاری درباره وجوه حاصل از اجرای قانون.')
   elif key=='78':
    lold[key]=av(c,docs[RL],RL,key,no,SMUGGLING_OLD_ART78_BASE,1,False,DL,DA,SRC_PRE,'متن ناسخ سابق ماده ۷۷ که در اصلاحیه ۱۴۰۰ به ماده ۷۸ تغییر شماره یافت.')
    lids[key]=av(c,docs[RL],RL,key,no,text,2,True,DA,None,SRC_L,'متن جاری ماده ۷۸ پس از تغییر شماره.')
   else:
    eff=DA if key in NEW_MAP else DL;lids[key]=av(c,docs[RL],RL,key,no,text,1,True,eff,None,SRC_L)

  aids=rows(c,docs[RA],RA,SMUGGLING_AMENDMENT_1400,DA,SRC_A)
  cc=dict(CUSTOMS_LAW_CURRENT);co=dict(CUSTOMS_LAW_ORIGINAL);cids={};cold={}
  for n in range(1,166):
   k=str(n);no=pn(n)
   if n==1:
    cold[k]=av(c,docs[RC],RC,k,no,co[k],1,False,DC,D1401,SRC_C,'تعریف اولیه تضمین پیش از قانون جهش تولید دانش‌بنیان.')
    cids[k]=av(c,docs[RC],RC,k,no,cc[k],2,True,D1401,None,SRC_C,'نسخه جاری با توسعه انواع تضمین گمرکی.')
   elif n==119:
    cold[k]=av(c,docs[RC],RC,k,no,CUSTOMS_ART119_OLD,1,False,DC,D1401,SRC_C,'نسخه پیش از نسخ بند «غ» معافیت ماشین‌آلات خط تولید.')
    cids[k]=av(c,docs[RC],RC,k,no,CUSTOMS_ART119_CURRENT,2,True,D1401,None,SRC_C,'نسخه جاری بدون بند «غ» منسوخ.')
   else:cids[k]=av(c,docs[RC],RC,k,no,cc[k],1,True,DC,None,SRC_C)
  bids=rows(c,docs[RB],RB,CUSTOMS_BYLAW,DB,SRC_B,keyed=True)
  sids=rows(c,docs[RS],RS,SMUGGLING_SYSTEMS_BYLAW,DS,SRC_S)
  dids=rows(c,docs[RD],RD,SMUGGLING_DISPOSAL_BYLAW,DD,SRC_D)
  r736=av(c,docs[R736],R736,'decision','رأی',RULING_736,1,True,D736,None,SRC_736)
  r839=av(c,docs[R839],R839,'decision','رأی',RULING_839,1,True,D839,None,SRC_839)
  r878=av(c,docs[R878],R878,'decision','رأی',RULING_878,1,True,D878,None,SRC_878)

  # Material links from the 47-article reform act to old versions and new inserted provisions.
  for key,oldid in lold.items():
   art=AMEND_MAP.get(key)
   if art:add_relation(c,docs[RA],'amends',docs[RL],from_article_id=aids[str(art)],to_article_id=oldid,description=f'اصلاح، حذف یا تجدید ساختار ماده {current.get(key,pre.get(key))[0]} قانون قاچاق.')
  for key,art in NEW_MAP.items():
   add_relation(c,docs[RA],'amends',docs[RL],from_article_id=aids[str(art)],to_article_id=lids[key],description=f'الحاق ماده {current[key][0]} به قانون قاچاق.')
  add_relation(c,docs[RA],'cites',docs[RC],description='اصلاحیه ۱۴۰۰ در تعریف اسناد خلاف واقع و مصادیق گمرکی به قانون امور گمرکی استناد می‌کند.')
  add_relation(c,docs[RL],'cites',docs[RC],from_article_id=lids['2'],to_article_id=cids['113'],description='مصادیق قاچاق گمرکی و نسبت قانون خاص قاچاق با ماده ۱۱۳ قانون امور گمرکی.')
  add_relation(c,docs[RB],'implements',docs[RC],from_article_id=bids['1'],to_article_id=cids['164'],description='آیین‌نامه اجرایی موضوع ماده ۱۶۴ قانون امور گمرکی.')
  add_relation(c,docs[RS],'implements',docs[RL],from_article_id=sids['1'],to_article_id=lids['5'],description='سامانه‌های پیشگیری و شناسایی موضوع مواد ۵ و ۶ قانون.')
  add_relation(c,docs[RS],'implements',docs[RL],from_article_id=sids['1'],to_article_id=lids['6'],description='یکپارچه‌سازی سامانه جامع تجارت، ارزی و پنجره واحد.')
  add_relation(c,docs[RD],'implements',docs[RL],from_article_id=dids['1'],to_article_id=lids['55'],description='فروش کالای قاچاق با رعایت مجوزها و ضوابط قانونی.')
  add_relation(c,docs[RD],'implements',docs[RL],from_article_id=dids['1'],to_article_id=lids['56'],description='صادرات، امحا، استرداد و تعیین تکلیف کالای قاچاق.')
  for target in ('22','44'):
   add_relation(c,docs[R736],'interprets',docs[RL],from_article_id=r736,to_article_id=lids[target],description='صلاحیت مطلق دادسرا و دادگاه انقلاب در رسیدگی به خودِ قاچاق کالای ممنوع.')
  for target in ('22','44','63'):
   add_relation(c,docs[R839],'interprets',docs[RL],from_article_id=r839,to_article_id=lids[target],description='تفکیک نگهداری جزئی کالای ممنوع از عنوان قاچاق و صلاحیت دادگاه کیفری دو.')
  add_relation(c,docs[R839],'cites',docs[R736],from_article_id=r839,description='رأی ۸۳۹ قلمرو رأی ۷۳۶ را در فرض نگهداری جزئی از خود قاچاق تفکیک می‌کند.')
  add_relation(c,docs[R878],'interprets',docs[RL],from_article_id=r878,to_article_id=lids['2bis'],description='عدم پرداخت مابه‌التفاوت نرخ ارز، تخلف موضوع تبصره ۵ ماده ۲ مکرر و در صلاحیت تعزیرات است.')
  for src,target,desc in ((RL,'QMA-1392','قواعد عمومی جرایم و مجازات‌های اشخاص حقیقی و حقوقی.'),(RL,'QADK-1392','تشریفات رسیدگی کیفری در موارد سکوت قانون خاص.'),(RC,'QTE-1382','اعتبار اسناد و اظهار الکترونیکی در تشریفات گمرکی.')):
   x=c.execute('select id from documents where reference_code=?',(target,)).fetchone()
   if x:add_relation(c,docs[src],'cites',x['id'],description=desc)
  c.commit();z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
  print('[OK] قانون قاچاق: ۸۹ کلید ساختاری / ۱۲۱ نسخه / ۸۷ جاری / ۳۴ تاریخی | اصلاحیه ۱۴۰۰=۴۷')
  print('[OK] قانون گمرکی=۱۶۵/۱۶۷ نسخه | آیین‌نامه گمرکی=۲۲۲ | سامانه‌های قاچاق=۴۶ | فروش و امحا=۲۵ | آراء=۳')
  print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
