# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
AML='QAML-1386';EA='EAML-1397';AB='AICML-1398';EAB='EAICML-1404';AOLD='AIAML-1388';CFT='QCFT-1394';EC='ECFT-1397';COLD='AICFT-1396';TARGET='AITFT-1404';FIU='AIFIU-1398';ACCESS='QCFTC-1404';REFS=(AML,EA,AB,EAB,AOLD,CFT,EC,COLD,TARGET,FIU,ACCESS)
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from tags),(select count(*)from articles_fts)').fetchone())
def art(c,key,cur=1,v=None):
 sql='select * from articles where article_key=?';a=[key]
 if cur is not None:sql+=' and is_current=?';a.append(cur)
 if v is not None:sql+=' and version_no=?';a.append(v)
 return c.execute(sql+' order by version_no desc limit 1',a).fetchone()
def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={AML:(25,15,15),EA:(13,13,13),AB:(168,168,168),EAB:(57,57,57),AOLD:(49,0,49),CFT:(22,17,17),EC:(5,5,5),COLD:(30,0,30),TARGET:(31,30,31),FIU:(8,8,8),ACCESS:(1,1,1)}
 for ref,w in exp.items():
  x=c.execute('select count(*)n,coalesce(sum(is_current),0)c,count(distinct article_key)k from articles where document_id=?',(d[ref],)).fetchone();q(tuple(x)==w,'counts '+ref+str(tuple(x)))
 expected={AML:{*map(str,range(1,15)),'7bis'},EA:{*map(str,range(1,14))},AB:{*map(str,range(1,165)),'9bis','27bis','150bis','152bis'},EAB:{*map(str,range(1,58))},AOLD:{*map(str,range(1,50))},CFT:{*map(str,range(1,18))},EC:{*map(str,range(1,6))},COLD:{*map(str,range(1,31))},TARGET:{*map(str,range(1,32))},FIU:{*map(str,range(1,9))},ACCESS:{'single'}}
 for ref,keys in expected.items():
  got={x[0].split(':',1)[1] for x in c.execute('select distinct article_key from articles where document_id=?',(d[ref],))};q(got==keys,'coverage '+ref+str((keys-got,got-keys)))
 # AML law and history.
 for k in [*map(str,range(1,10)),'11']:q(c.execute('select count(*)from articles where article_key=?',(f'{AML}:{k}',)).fetchone()[0]==2,'AML history '+k)
 q('جرم منشأ' in art(c,f'{AML}:1')['text'] and 'مال حاصل از جرم' in art(c,f'{AML}:1')['text'],'AML definitions')
 q('ظن نزدیک به علم' in art(c,f'{AML}:2')['text'] and 'اسناد مثبته' in art(c,f'{AML}:2')['text'],'AML burden')
 q('شورای عالی مقابله' in art(c,f'{AML}:4')['text'] and 'سازمان اطلاعات سپاه' in art(c,f'{AML}:4')['text'],'AML council')
 q('مالکان واقعی' in art(c,f'{AML}:7')['text'] and 'حداقل به مدت پنج سال' in art(c,f'{AML}:7')['text'],'AML duties')
 q('مرکز اطلاعات مالی' in art(c,f'{AML}:7bis')['text'] and 'ضابط دادگستری' in art(c,f'{AML}:7bis')['text'],'AML FIU')
 q('حبس تعزیری درجه پنج' in art(c,f'{AML}:9')['text'] and 'سازمان‌یافته' in art(c,f'{AML}:9')['text'],'AML penalty')
 q('ماده (۱۴)' in art(c,f'{EA}:13')['text'] and 'آیین‌‌نامه اجرائی' in art(c,f'{EA}:13')['text'],'AML amendment')
 # Current combined bylaw.
 q('دارایی مجازی' in art(c,f'{AB}:1')['text'] and 'حرف و مشاغل غیرمالی' in art(c,f'{AB}:1')['text'],'bylaw definitions')
 q('طبقه بندی خطر' in art(c,f'{AB}:8')['text'] and 'ارباب‌رجوع' in art(c,f'{AB}:8')['text'],'risk approach')
 q('اشخاص با خطر' in art(c,f'{AB}:9')['text'] and 'اشخاص سیاسی خارجی' in art(c,f'{AB}:9bis')['text'],'high-risk/PEP')
 q('سازمان بورس' in art(c,f'{AB}:27bis')['text'] and 'سبد سهام' in art(c,f'{AB}:27bis')['text'],'securities data')
 q('برنامه‌های نظارت' in art(c,f'{AB}:41')['text'] and 'ضمانت اجرا' in art(c,f'{AB}:41')['text'],'supervision')
 q('احراز هویت' in art(c,f'{AB}:59')['text'] and 'خدمات الکترونیکی' in art(c,f'{AB}:59')['text'],'identity')
 q('دارایی‌های مجازی' in art(c,f'{AB}:97')['text'] and 'پایگاه یکپارچه' in art(c,f'{AB}:97')['text'],'virtual assets')
 q('وجه نقد ریالی' in art(c,f'{AB}:116')['text'] and 'سقف اعلامی' in art(c,f'{AB}:116')['text'],'cash ceiling')
 q('بلافاصله و بدون اطلاع ارباب‌رجوع' in art(c,f'{AB}:135')['text'],'suspicious report')
 q('۱۰٫۰۰۰' in art(c,f'{AB}:139')['text'] and '۱٫۰۰۰٫۰۰۰٫۰۰۰' in art(c,f'{AB}:139')['text'],'cash report thresholds')
 q('سامانه جامع مشارکت' in art(c,f'{AB}:150bis')['text'] and 'سازمان' in art(c,f'{AB}:152bis')['text'],'nonprofits')
 q('منسوخ بودن آیین نامه اجرایی' in art(c,f'{AB}:164')['text'],'old bylaw repeal')
 q(all(art(c,f'{AOLD}:{n}',1) is None for n in range(1,50)),'old AML historical')
 q('دارایی مجازی' in art(c,f'{EAB}:1')['text'] and 'مؤسسه مالی' in art(c,f'{EAB}:1')['text'],'1404 clause1')
 q('شماره مواد' in art(c,f'{EAB}:57')['text'],'1404 renumber')
 # CFT statute, amendment and regulations.
 for k in ('1','2','5','10','14'):q(c.execute('select count(*)from articles where article_key=?',(f'{CFT}:{k}',)).fetchone()[0]==2,'CFT history '+k)
 q('شورای عالی امنیت ملی' in art(c,f'{CFT}:1')['text'] and 'سازمان‌های تروریستی' in art(c,f'{CFT}:1')['text'],'CFT definition')
 q('محاربه' in art(c,f'{CFT}:2')['text'] and 'دو تا پنج سال حبس' in art(c,f'{CFT}:2')['text'],'CFT penalty')
 q('مسدودکردن وجوه' in art(c,f'{CFT}:5')['text'] and 'بیست و چهار ساعت' in art(c,f'{CFT}:5')['text'],'CFT freeze')
 q('گزارش عملیات مشکوک' in art(c,f'{CFT}:14')['text'] and 'مجازات معاون جرم' in art(c,f'{CFT}:14')['text'],'CFT reporting')
 q('ماده (۱۴)' in art(c,f'{EC}:5')['text'] and 'درجه هفت' in art(c,f'{EC}:5')['text'],'CFT amendment')
 q(all(art(c,f'{COLD}:{n}',1) is None for n in range(1,31)),'old CFT bylaw historical')
 q('اقدام مالی هدفمند' in art(c,f'{TARGET}:1')['text'] and 'بدون تأخیر' in art(c,f'{TARGET}:1')['text'],'target definitions')
 q('شورای عالی امنیت ملی' in art(c,f'{TARGET}:2')['text'] and 'کمیته های ۱۲۶۷' in art(c,f'{TARGET}:2')['text'],'target working group')
 q('رفع انسداد' in art(c,f'{TARGET}:13')['text'],'target delisting')
 q(art(c,f'{TARGET}:31',1) is None and 'اختیارات و وظایف شورای عالی امنیت ملی' in art(c,f'{TARGET}:31',0)['text'],'target article31 history')
 q('نسخ' in art(c,f'{TARGET}:30')['text'] and '۱۳۹۶' in art(c,f'{TARGET}:30')['text'],'old target bylaw repeal')
 # FIU and accession.
 q('استقلال اداری و مالی' in art(c,f'{FIU}:2')['text'] and 'معاون وزیر' in art(c,f'{FIU}:3')['text'],'FIU structure')
 q('خلاصه ساختاری' in art(c,f'{FIU}:4')['notes'] and '۲۶-' in art(c,f'{FIU}:4')['text'],'FIU labeled summary')
 q('هفتاد و هفتم' in art(c,f'{ACCESS}:single')['text'] and 'هفت شرط' not in art(c,f'{ACCESS}:single')['text'] and 'رژیم اشغالگر صهیونیستی' in art(c,f'{ACCESS}:single')['text'],'accession conditions')
 ph=','.join('?'*len(d));rr=c.execute(f'select article_no,text,source_note from articles where document_id in ({ph})',tuple(d.values())).fetchall();q(all(x['text'].strip() and x['source_note'] for x in rr),'empty/source');q(all(not re.search(r'[0-9]',x['article_no']) for x in rr),'ascii no');q(all('http://' not in x['text'] and 'https://' not in x['text'] and '###' not in x['text'] and 'تازه‌های قوانین' not in x['text'] and '�' not in x['text'] for x in rr),'source leak');q(all(not re.match(r'^‌?ماده\s*[۰-۹]',x['text']) for x in rr),'heading leak')
 for term in ('پولشویی','مالک واقعی','دارایی مجازی','مرکز اطلاعات مالی','تأمین مالی تروریسم','اقدام مالی هدفمند','معاملات مشکوک'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==35,'relations')
 q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=art(c,f'{AB}:1')['id'];c.close()
 for args in (['stats'],['show',str(d[AB])],['history',f'{AML}:1'],['history',f'{CFT}:1'],['history',f'{TARGET}:31'],['search','دارایی مجازی'],['search','معاملات مشکوک'],['search','اقدام مالی هدفمند']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90);q(p.returncode==0 and p.stdout.strip(),'query '+p.stderr)
 cl=app.test_client();pages=['/','/?q=پولشویی','/?q=تأمین+مالی+تروریسم','/?q=دارایی+مجازی','/types','/by-type/law','/by-type/amendment','/by-type/regulation']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_aml_cft.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=400);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('pragma foreign_key_check').fetchall(),'fk after');q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'dupe refs');q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] AML=15 keys/25 rows; amendment=13; current bylaw=168; amendment=57; former bylaw=49 historical')
 print('[OK] CFT=17/22; amendment=5; former bylaw=30; targeted=31 rows; FIU=8; accession act=1')
 print('[OK] Histories, 1404/1405 consolidation, Persian numbers, FTS5, relations, Flask and idempotency')
if __name__=='__main__':main()
