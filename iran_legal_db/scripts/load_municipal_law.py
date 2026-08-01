# -*- coding: utf-8 -*-
"""Load municipal law, urban renewal, municipal finance and leading Divan rulings."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__))
sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'data','seed')]
from schema import get_connection
from importer import *
from municipal_law import *

RM='QSH-1334';RN='QNO-1347';RS='QDPSH-1401';RF='AIM1-1401';RO='AISH-1346'
R577='DAD-577-1393';R1509='DAD-1509-1399';R227='DAD-227-1395';R1310='DAD-1310-1397'
REFS=(RM,RN,RS,RF,RO,R577,R1509,R227,R1310)
D_M='1955-07-03';D_M45='1967-02-16';D_M58='1979-09-18';D_M90='2011-04-17';D_M1400='2022-01-30'
D_N='1968-11-28';D_N82='2003-03-21';D_S='2022-06-22';D_F='2023-03-01';D_O='1967-07-03'
D_577='2014-06-13';D_1509='2021-01-12';D_227='2016-06-14';D_1310='2018-07-31'
SRC_M='قانون شهرداری مصوب ۱۳۳۴/۰۴/۱۱ با اصلاحات و الحاقات؛ متن تنقیحی میزان و مقابله با داودآبادی و قانون اصلاحی ۱۳۴۵.'
SRC_N='قانون نوسازی و عمران شهری مصوب ۱۳۴۷/۰۹/۰۷؛ متن اختبار با اعمال نسخ‌های صریح ۱۴۰۰ و نرخ جاری قانون درآمد پایدار ۱۴۰۱.'
SRC_S='قانون درآمد پایدار و هزینه شهرداری‌ها و دهیاری‌ها مصوب ۱۴۰۱/۰۴/۰۱؛ متن کامل ۱۷ ماده.'
SRC_F='آیین‌نامه مالی موضوع ماده ۱ قانون درآمد پایدار، تصویب‌نامه شماره ۲۳۵۴۷۲/ت۶۰۷۰۲هـ مصوب ۱۴۰۱/۱۲/۱۰.'
SRC_O='آیین‌نامه مالی شهرداری‌ها مصوب ۱۳۴۶/۰۴/۱۲؛ متن پایه ۴۸ ماده‌ای شناسنامه قانون؛ نصاب‌های ریالی نیازمند کنترل مقررات تعدیل مؤخر است.'
SRC_577='دادنامه ۵۷۷ هیأت عمومی دیوان عدالت اداری؛ منبع در دسترس فقط گردش کار و پیام رأی را بازنشر کرده است؛ رکورد صریحاً خلاصه است.'
SRC_1509='قسمت لازم‌الاتباع دادنامه ۱۵۰۹ مورخ ۱۳۹۹/۱۰/۲۳ هیأت عمومی دیوان عدالت اداری.'
SRC_227='قسمت رأی دادنامه ۲۲۷ مورخ ۱۳۹۵/۰۳/۲۵ هیأت عمومی دیوان عدالت اداری با ارجاع به آراء ۶۲۸ تا ۶۳۳.'
SRC_1310='قسمت رأی دادنامه ۱۳۱۰ مورخ ۱۳۹۷/۰۵/۰۹ هیأت عمومی دیوان عدالت اداری.'

def pn(x):return str(x).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
def gi(c,t,col,v):
    r=c.execute(f'select id from {t} where {col}=?',(v,)).fetchone();return r['id'] if r else None

def up(c,ref,title,short,typ,auth,atype,status,rat,eff,notes):
    r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone()
    did=r['id'] if r else get_or_create_document(c,title=title,short_title=short,type_code=typ,issuing_authority=auth,status_code=status,ratification_date=rat,effective_date=eff,reference_code=ref,notes=notes)
    aid=gi(c,'authorities','name_fa',auth)
    if aid is None:aid=c.execute('insert into authorities(name_fa,authority_type)values(?,?)',(auth,atype)).lastrowid
    c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=?,updated_at=current_timestamp where id=?',
              (title,short,gi(c,'document_types','code',typ),aid,gi(c,'statuses','code',status),rat,eff,notes,did))
    return did

def clear(c,d):
    c.execute('delete from relations where from_document_id=?',(d,))
    c.execute('delete from articles_fts where document_id=?',(d,))
    c.execute('delete from articles where document_id=?',(d,))
    c.execute('delete from document_tags where document_id=?',(d,))
    c.execute('delete from document_topics where document_id=?',(d,))

def deco(c,d,tags,topics=('حقوق شهرداری‌ها','حقوق اداری')):
    for topic in topics:link_document_topic(c,d,topic)
    for tag in tags:link_document_tag(c,d,add_tag(c,tag))

def av(c,d,ref,key,no,text,v,cur,eff,exp,src,note=None):
    return add_article(c,d,article_no=no,article_key=f'{ref}:{key}',version_no=v,is_current=int(cur),effective_date=eff,expiry_date=exp,text=text,source_note=src,notes=note)

def rows(c,d,ref,data,date,src):
    ids={}
    for n,t in data:ids[n]=av(c,d,ref,n,pn(n),t,1,True,date,None,src)
    return ids

def main():
    c=get_connection()
    try:
        c.execute('begin');docs={}
        docs[RM]=up(c,RM,'قانون شهرداری مصوب ۱۳۳۴ با اصلاحات و الحاقات','قانون شهرداری','law','کمیسیون مشترک مجلسین (پیش از انقلاب)','legislative','amended',D_M,D_M,
                    'پوشش کامل شماره‌های ۱ تا ۱۱۹: ۴۷ ماده جاری و ۷۲ ماده کاملاً منسوخ. مواد ۱۰۰ و ۱۰۱ دو نسخه‌ای‌اند. در مواد جاری، اجزای منسوخ صریح از متن جاری حذف شده‌اند؛ متن منبع خام در source_cache محفوظ است.')
        docs[RN]=up(c,RN,'قانون نوسازی و عمران شهری با اصلاحات و نسخ‌های ۱۴۰۰ و نرخ ۱۴۰۱','نوسازی و عمران شهری','law','مجلس شورای ملی (پیش از انقلاب)','legislative','amended',D_N,D_N,
                    'پوشش کامل ۳۶ ماده؛ مواد ۱۸، ۲۵ و ۲۶ از ۱۴۰۰ تاریخی‌اند. ماده ۲ در سه نسل نرخ و مواد ۱۰ و ۱۶ پیش و پس از نسخ اجزای ۱۴۰۰ ثبت شده‌اند. متن ماده ۲ جاری، تلفیق صریح حکم نرخ ۱۴۰۱ با اجزای باقی‌مانده ماده است.')
        docs[RS]=up(c,RS,'قانون درآمد پایدار و هزینه شهرداری‌ها و دهیاری‌ها','قانون درآمد پایدار شهرداری‌ها','law','مجلس شورای اسلامی','legislative','in_force',D_S,D_S,
                    'متن کامل ۱۷ ماده درباره عوارض محلی، بهای خدمات، عوارض نوسازی، وصول مطالبات، شفافیت مالی و رعایت طرح تفصیلی.')
        docs[RF]=up(c,RF,'آیین‌نامه مالی موضوع ماده ۱ قانون درآمد پایدار و هزینه شهرداری‌ها و دهیاری‌ها','آیین‌نامه تأمین مالی شهرداری‌ها','regulation','هیئت وزیران','executive','in_force',D_F,D_F,
                    'متن کامل ۱۸ ماده درباره ابزارهای تأمین مالی، اوراق مالی اسلامی، مشارکت و انتخاب سرمایه‌گذار.')
        docs[RO]=up(c,RO,'آیین‌نامه مالی شهرداری‌ها مصوب ۱۳۴۶','آیین‌نامه مالی شهرداری‌ها','regulation','کمیسیون مشترک کشور مجلسین (پیش از انقلاب)','legislative','amended',D_O,D_O,
                    'متن پایه کامل ۴۸ ماده درباره معاملات، بودجه، درآمد، هزینه و اموال. نصاب‌های ریالی معاملات در مواد پایه، برای کاربرد روز باید همراه مصوبات تعدیل نصاب معاملات شهرداری‌ها و قوانین مؤخر کنترل شود.')
        docs[R577]=up(c,R577,'رأی شماره ۵۷۷ هیأت عمومی دیوان عدالت اداری درباره لزوم تصریح عدم رعایت اصول سه‌گانه در رأی قلع','رأی ۵۷۷ ـ اصول سه‌گانه','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force',D_577,D_577,
                      'خلاصه منبع‌دار نتیجه لازم‌الاتباع رأی درباره استدلال حکم قلع؛ رونوشت کامل قسمت رأی در منبع قابل دسترس نبود و این رکورد صریحاً خلاصه است.')
        docs[R1509]=up(c,R1509,'رأی وحدت رویه شماره ۱۵۰۹ هیأت عمومی دیوان عدالت اداری درباره دیوارکشی و صلاحیت کمیسیون ماده ۱۰۰','رأی ۱۵۰۹ ـ دیوارکشی','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force',D_1509,D_1509,
                       'قسمت لازم‌الاتباع رأی: دیوارکشی عملیات ساختمانی است و در محدوده و حریم شهر اخذ جواز لازم دارد.')
        docs[R227]=up(c,R227,'رأی شماره ۲۲۷ هیأت عمومی دیوان عدالت اداری درباره خسارت تأخیر جرایم ماده ۱۰۰','رأی ۲۲۷ ـ دیرکرد جریمه','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force',D_227,D_227,
                      'قسمت رأی درباره ابطال مجدد مصوبه شورای شهر کرج و ممنوعیت افزایش جریمه قطعی ماده ۱۰۰ به عنوان خسارت تأخیر.')
        docs[R1310]=up(c,R1310,'رأی شماره ۱۳۱۰ هیأت عمومی دیوان عدالت اداری درباره عوارض شهری و تغییر کاربری','رأی ۱۳۱۰ ـ عوارض شهری','divan_ruling','هیأت عمومی دیوان عدالت اداری','judicial','in_force',D_1310,D_1310,
                       'قسمت کامل رأی سه‌بندی درباره عوارض حق بیمه و قراردادها، تفکیک و نقل‌وانتقال، و ارزش افزوده ناشی از تغییر کاربری پس از تصمیم کمیسیون ماده ۵.')
        for d in docs.values():clear(c,d)

        deco(c,docs[RM],('کمیسیون ماده ۱۰۰','کمیسیون ماده ۷۷','تخلفات ساختمانی','پروانه ساختمان','تفکیک اراضی','وظایف شهرداری'))
        deco(c,docs[RN],('عوارض نوسازی','ممیزی املاک','نوسازی شهری','طرح توسعه شهری','حق مرغوبیت'))
        deco(c,docs[RS],('درآمد پایدار','عوارض محلی','بهای خدمات','شفافیت مالی','طرح تفصیلی'),('حقوق شهرداری‌ها','حقوق اداری','حقوق مالیاتی'))
        deco(c,docs[RF],('تأمین مالی شهری','اوراق مالی اسلامی','مشارکت عمومی خصوصی','سرمایه‌گذاری شهری'),('حقوق شهرداری‌ها','حقوق اداری','حقوق پول و بانک'))
        deco(c,docs[RO],('مناقصه شهرداری','مزایده شهرداری','بودجه شهرداری','اموال عمومی','معاملات شهرداری'))
        for ref,tags in ((R577,('قلع بنا','اصول شهرسازی','اصول فنی','اصول بهداشتی')),(R1509,('دیوارکشی','حریم شهر','عملیات ساختمانی')),(R227,('خسارت تأخیر','جریمه ماده ۱۰۰')),(R1310,('عوارض تغییر کاربری','عوارض تفکیک','کمیسیون ماده ۵'))):
            deco(c,docs[ref],tags)

        # Municipality law: 119 stable article keys; fully repealed provisions are historical only.
        mids={};mold={}
        for n,text,repealed,expiry in MUNICIPALITY_ARTICLES:
            base_eff=D_M45 if n>=100 else D_M
            if n==100:
                mold[n]=av(c,docs[RM],RM,n,pn(n),MUNICIPALITY_ART100_OLD_1345,1,False,D_M45,D_M58,SRC_M,'نسخه الحاقی ۱۳۴۵ با دو تبصره؛ نسل‌های میانی ۱۳۵۲ و ۱۳۵۵ جداگانه materialize نشده‌اند.')
                mids[n]=av(c,docs[RM],RM,n,pn(n),text,2,True,D_M58,None,SRC_M,'نسخه جاری تلفیقی با یازده تبصره و اصلاحات تا ۱۳۵۸.')
            elif n==101:
                mold[n]=av(c,docs[RM],RM,n,pn(n),MUNICIPALITY_ART101_OLD_1345,1,False,D_M45,D_M90,SRC_M,'متن الحاقی ۱۳۴۵ پیش از اصلاح جامع ۱۳۹۰.')
                mids[n]=av(c,docs[RM],RM,n,pn(n),MUNICIPALITY_ART101_CURRENT_1390,2,True,D_M90,None,'قانون اصلاح ماده ۱۰۱ قانون شهرداری مصوب ۱۳۹۰/۰۱/۲۸؛ متن رسمی مقابله‌ای.','نسخه جاری درباره تفکیک، افراز و قدرالسهم خدمات عمومی و معابر.')
            elif repealed:
                mold[n]=av(c,docs[RM],RM,n,pn(n),text,1,False,base_eff,expiry,SRC_M,'ماده کاملاً منسوخ؛ تاریخ نسخ مطابق عنوان منبع تنقیحی.')
            else:
                mids[n]=av(c,docs[RM],RM,n,pn(n),text,1,True,base_eff,None,SRC_M,'رسم‌الخط نوسازی شده؛ اجزای صریحاً منسوخ داخل ماده جاری حذف شده‌اند.')

        # Urban renewal: explicit 2022 invalid-list effects and three generations of the renovation rate.
        nbase=dict(URBAN_RENEWAL_BASE);nids={};nold={}
        for n in range(1,37):
            if n==2:
                nold[(n,1)]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART2_OLD,1,False,D_N,D_N82,SRC_N,'نرخ پنج در هزار متن مصوب ۱۳۴۷.')
                nold[(n,2)]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART2_MID,2,False,D_N82,D_S,SRC_N,'نرخ یک درصد به موجب قوانین تجمیع عوارض/مالیات بر ارزش افزوده؛ تعدیل بودجه‌ای ۱۳۸۹ جداگانه materialize نشده است.')
                nids[n]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART2_CURRENT,3,True,D_S,None,SRC_N,'متن تلفیقی جاری با نرخ ۲٫۵٪ موضوع ماده ۳ قانون درآمد پایدار ۱۴۰۱.')
            elif n==10:
                nold[(n,1)]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART10_OLD,1,False,D_N,D_M1400,SRC_N,'نسخه پیش از نسخ تبصره ۲ در قانون فهرست احکام نامعتبر ۱۴۰۰.')
                nids[n]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART10_CURRENT,2,True,D_M1400,None,SRC_N,'نسخه جاری بدون تبصره ۲ منسوخ.')
            elif n==16:
                nold[(n,1)]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART16_OLD,1,False,D_N,D_M1400,SRC_N,'نسخه پیش از نسخ تبصره‌های ۲ و ۳ در ۱۴۰۰.')
                nids[n]=av(c,docs[RN],RN,n,pn(n),URBAN_RENEWAL_ART16_CURRENT,2,True,D_M1400,None,SRC_N,'نسخه جاری بدون تبصره‌های ۲ و ۳ منسوخ.')
            elif n in (18,25,26):
                nold[(n,1)]=av(c,docs[RN],RN,n,pn(n),nbase[n],1,False,D_N,D_M1400,SRC_N,'نسخ صریح به موجب ماده ۱۱۴ قانون فهرست قوانین و احکام نامعتبر در حوزه شوراها و شهرداری‌ها مصوب ۱۴۰۰.')
            else:nids[n]=av(c,docs[RN],RN,n,pn(n),nbase[n],1,True,D_N,None,SRC_N,'متن جاری با نوسازی رسم‌الخط، بدون افزودن حکم جدید.')

        sids=rows(c,docs[RS],RS,SUSTAINABLE_REVENUE_LAW,D_S,SRC_S)
        fids=rows(c,docs[RF],RF,SUSTAINABLE_FINANCIAL_BYLAW,D_F,SRC_F)
        oids=rows(c,docs[RO],RO,MUNICIPAL_FINANCIAL_BYLAW_1346,D_O,SRC_O)
        rid577=av(c,docs[R577],R577,'decision','خلاصه رأی',DIVAN_RULING_577_SUMMARY,1,True,D_577,None,SRC_577,'خلاصه نتیجه لازم‌الاتباع؛ نه رونوشت کامل گردش کار و رأی.')
        rid1509=av(c,docs[R1509],R1509,'decision','رأی',DIVAN_RULING_1509,1,True,D_1509,None,SRC_1509)
        rid227=av(c,docs[R227],R227,'decision','رأی',DIVAN_RULING_227,1,True,D_227,None,SRC_227)
        rid1310=av(c,docs[R1310],R1310,'decision','رأی',DIVAN_RULING_1310,1,True,D_1310,None,SRC_1310)

        add_relation(c,docs[RN],'cites',docs[RM],from_article_id=nids[3],to_article_id=mids[77],description='اختلاف در اصل عوارض نوسازی تابع کمیسیون ماده ۷۷ قانون شهرداری است.')
        add_relation(c,docs[RN],'cites',docs[RM],from_article_id=nids[26] if 26 in nids else None,to_article_id=mids[100],description='الزام اخذ پروانه و رعایت ماده ۱۰۰ در ایجاد ساختمان.')
        add_relation(c,docs[RS],'amends',docs[RN],from_article_id=sids[3],to_article_id=nold[(2,2)],description='تعیین نرخ جاری عوارض نوسازی به میزان ۲٫۵٪ ارزش معاملاتی.')
        add_relation(c,docs[RS],'cites',docs[RM],from_article_id=sids[10],to_article_id=mids[77],description='اختلاف و اعتراض درباره عوارض و بهای خدمات شهرداری مشمول ماده ۷۷ است.')
        add_relation(c,docs[RS],'cites',docs[RM],from_article_id=sids[17],to_article_id=mids[100],description='صدور پروانه باید مطابق طرح تفصیلی و تغییر کاربری یا تراکم مازاد با تصویب کمیسیون ماده ۵ باشد.')
        add_relation(c,docs[RF],'implements',docs[RS],from_article_id=fids[1],to_article_id=sids[1],description='آیین‌نامه مالی و تأمین مالی موضوع ماده ۱ قانون درآمد پایدار.')
        add_relation(c,docs[RO],'implements',docs[RM],from_article_id=oids[1],to_article_id=mids[104],description='آیین‌نامه مالی موضوع ماده ۱۰۴ قانون شهرداری.')
        add_relation(c,docs[R577],'interprets',docs[RM],from_article_id=rid577,to_article_id=mids[100],description='لزوم تصریح مصداق عدم رعایت اصول سه‌گانه در رأی قلع.')
        add_relation(c,docs[R1509],'interprets',docs[RM],from_article_id=rid1509,to_article_id=mids[100],description='دیوارکشی عملیات ساختمانی و مشمول صلاحیت کمیسیون ماده ۱۰۰ است.')
        add_relation(c,docs[R227],'interprets',docs[RM],from_article_id=rid227,to_article_id=mids[100],description='ماده ۱۰۰ مجوزی برای خسارت تأخیر بر جریمه قطعی ایجاد نمی‌کند.')
        add_relation(c,docs[R1310],'interprets',docs[RM],from_article_id=rid1310,description='حدود اختیار شورا در وضع عوارض تفکیک، نقل‌وانتقال و ارزش افزوده تغییر کاربری.')
        add_relation(c,docs[R1310],'cites',docs[RN],from_article_id=rid1310,description='تمایز عوارض قانونی شهری، تفکیک و ارزش افزوده ناشی از طرح‌ها و تغییر کاربری.')
        # Cross-package links remain document-level so rerunning destination loaders cannot cascade-delete them.
        for src,target,desc in ((RS,'QMM-1366','مبنای ارزش معاملاتی عوارض محلی ماده ۶۴ قانون مالیات‌های مستقیم.'),(RS,'QMA-1392','ضمانت اجرای کیفری تخلف از مقررات عوارض و طرح تفصیلی.'),(RF,'QBOV-1384','ابزارهای بازار سرمایه و نهادهای مالی در تأمین مالی شهری.')):
            x=c.execute('select id from documents where reference_code=?',(target,)).fetchone()
            if x:add_relation(c,docs[src],'cites',x['id'],description=desc)
        c.commit()
        z=c.execute('select (select count(*)from documents)d,(select count(*)from articles)a,(select count(*)from articles where is_current=1)c,(select count(*)from articles where is_current=0)h,(select count(*)from relations)r').fetchone()
        print('[OK] قانون شهرداری: ۱۱۹ شماره / ۱۲۱ نسخه / ۴۷ جاری / ۷۴ تاریخی')
        print('[OK] نوسازی شهری: ۳۶ شماره / ۴۰ نسخه / ۳۳ جاری / ۷ تاریخی | درآمد پایدار=۱۷ | آیین‌نامه جدید=۱۸ | آیین‌نامه مالی ۱۳۴۶=۴۸')
        print('[OK] آرای شاخص دیوان عدالت اداری=۴ (رأی ۵۷۷ با برچسب صریح خلاصه)')
        print(f"[TOTAL] اسناد: {z['d']} | مواد/نسخه‌ها: {z['a']} | جاری: {z['c']} | تاریخی: {z['h']} | روابط: {z['r']}")
    except Exception:
        c.rollback();raise
    finally:c.close()
if __name__=='__main__':main()
