# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QSA-1355','AISA-1385','QNM-1376','AINM-1378','AKNM-1387','AISM-1391','QTF-1385','EQTF-1398','AITF-1399','QGO-1351','AIPZ-1363','RVR-748-1395','RVR-732-1393','RVR-726-1391','RVR-658-1381','RVR-617-1376','NM-586-1403')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def row(c,key,cur=1):return c.execute('select * from articles where article_key=? and is_current=?',(key,cur)).fetchone()
def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={'QSA-1355':(57,55),'AISA-1385':(14,14),'QNM-1376':(6,6),'AINM-1378':(14,14),'AKNM-1387':(10,10),'AISM-1391':(13,13),'QTF-1385':(2,1),'EQTF-1398':(1,1),'AITF-1399':(24,24),'QGO-1351':(56,42),'AIPZ-1363':(11,11),'RVR-748-1395':(1,1),'RVR-732-1393':(1,1),'RVR-726-1391':(1,1),'RVR-658-1381':(1,1),'RVR-617-1376':(1,1),'NM-586-1403':(1,1)}
 for ref,(n,cur) in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c from articles where document_id=?',(d[ref],)).fetchone();q((x['n'],x['c'])==(n,cur),'counts '+ref)
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QSA-1355'],))}=={f'QSA-1355:{n}' for n in range(1,56)},'registry coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['AISA-1385'],))}=={f'AISA-1385:{n}' for n in range(1,15)},'registry bylaw coverage')
 for ref,end in (('QNM-1376',6),('AINM-1378',14),('AKNM-1387',10),('AISM-1391',13),('AITF-1399',24),('AIPZ-1363',11)):
  q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[ref],))}=={f'{ref}:{n}' for n in range(1,end+1)},'coverage '+ref)
 pkeys={f'QGO-1351:{n}' for n in range(1,43)}|{'QGO-1351:35bis'}
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QGO-1351'],))}==pkeys,'passport coverage')
 q(row(c,'QGO-1351:26') is None and 'مدت پنج‌ساله' in row(c,'QGO-1351:26',0)['text'],'passport 26 historical')
 # Nationality book is repaired inside the existing Civil Code.
 nr=c.execute("select count(*)n,sum(is_current)c from articles where article_key in (%s)"%','.join('?'*16),tuple(f'QM:{n}' for n in range(976,992))).fetchone();q((nr['n'],nr['c'])==(17,15),'nationality rows')
 q(row(c,'QM:981') is None and 'فراری از خدمت نظام' in row(c,'QM:981',0)['text'],'article 981 historical substantive')
 q('اتباع ایران نمی‌توانند' in row(c,'QM:988')['text'] and not row(c,'QM:988')['text'].startswith('و تبصره'),'article 988')
 v989=c.execute("select version_no,is_current,text from articles where article_key='QM:989' order by version_no").fetchall();q(len(v989)==2 and 'به فروش رسیده' in v989[0]['text'] and 'به فروش رسیده' not in v989[1]['text'] and v989[1]['is_current']==1,'article 989 history')
 q('اصلاحی ۱۴۰۴' in v989[1]['text'] and 'مشاغل دولتی' in v989[1]['text'],'article 989 current')
 # Registry law histories.
 q('کارگروه تعامل' in row(c,'QSA-1355:34')['text'] and 'دولتی ذی‌صلاح' in row(c,'QSA-1355:34',0)['text'],'registry 34 history')
 q('۱,۳۲۰,۰۰۰ تا ۳۳,۰۰۰,۰۰۰' in row(c,'QSA-1355:48')['text'] and '۱,۳۲۰,۰۰۰' not in row(c,'QSA-1355:48',0)['text'],'registry fine')
 q('هیأت حل اختلاف' in row(c,'QSA-1355:3')['text'] and 'هویت و تابعیت' in row(c,'QSA-1355:45')['text'],'registry core')
 # National ID and smart card.
 q('ده رقمی و منحصر به فرد' in row(c,'AINM-1378:1')['text'] and 'تنها مرجع رسمی' in row(c,'AINM-1378:4')['text'],'national id bylaw')
 q('مبنای احراز هویت' in row(c,'AKNM-1387:1')['text'] and 'مجازات مقرر در ماده (۶۴۸)' in row(c,'AKNM-1387:10')['text'],'applied ID')
 q('کارت هوشمند ملی چند منظوره' in row(c,'AISM-1391:1')['text'] and 'رضایت اولیای دم' in row(c,'AISM-1391:13')['text'],'smart id')
 # Citizenship special law and bylaw.
 cv=c.execute("select version_no,is_current,text from articles where article_key='QTF-1385:single' order by version_no").fetchall();q(len(cv)==2 and 'بعد از رسیدن به سن هجده سال' in cv[0]['text'] and 'قبل از رسیدن به سن هجده سال' in cv[1]['text'],'citizenship history')
 q('عنوان و ماده‌واحده' in row(c,'EQTF-1398:single')['text'] and 'سازمان اطلاعات سپاه' in row(c,'EQTF-1398:single')['text'],'citizenship amendment')
 q('عدم ارسال پاسخ روشن ظرف سه ماه' in row(c,'AITF-1399:13')['text'] and 'کارت ملی و شناسنامه' in row(c,'AITF-1399:13')['text'],'citizenship bylaw')
 # Passport histories and current monetary amounts.
 q(c.execute("select count(*) from articles where article_key='QGO-1351:18'").fetchone()[0]==3 and 'فقط در موارد ذیل' in c.execute("select text from articles where article_key='QGO-1351:18' and version_no=2").fetchone()[0] and 'فقط در موارد ذیل' not in row(c,'QGO-1351:18')['text'],'passport 18')
 for n in (10,11,12,13,25,36):q(c.execute('select count(*)from articles where article_key=?',(f'QGO-1351:{n}',)).fetchone()[0]==2,'passport history '+str(n))
 for n in (34,35):q(c.execute('select count(*)from articles where article_key=?',(f'QGO-1351:{n}',)).fetchone()[0]==3,'passport criminal history '+str(n))
 q('۸۰,۰۰۰,۰۰۰ تا ۳۳۰,۰۰۰,۰۰۰' in row(c,'QGO-1351:34')['text'] and '۸۰,۰۰۰,۰۰۰ تا ۳۳۰,۰۰۰,۰۰۰' in row(c,'QGO-1351:35')['text'],'passport fines')
 q('۴۰,۰۰۰,۰۰۰ تا ۳۳۰,۰۰۰,۰۰۰' in row(c,'QGO-1351:35bis')['text'] and '۳۳,۰۰۰,۰۰۰ تا ۱۳۲,۰۰۰,۰۰۰' in row(c,'QGO-1351:35bis')['text'],'passport 35bis')
 # Precedents and advisory opinion.
 q('پدر عرفی' in row(c,'RVR-617-1376:decision')['text'] and 'توارث' in row(c,'RVR-617-1376:decision')['text'],'r617')
 q('شورای تأمین' in row(c,'RVR-658-1381:decision')['text'] and 'هیأت حل اختلاف' in row(c,'RVR-658-1381:decision')['text'],'r658')
 q('محل اقامت خواهان' in row(c,'RVR-726-1391:decision')['text'],'r726')
 q('صلاحیت دادگاه‌های عمومی حقوقی' in row(c,'RVR-732-1393:decision')['text'],'r732')
 q('دعوای او در دادگاه قابل رسیدگی است' in row(c,'RVR-748-1395:decision')['text'],'r748')
 q('نیازی به صدور قرار عدم استماع' in row(c,'NM-586-1403:answer')['text'] and 'اعتراض فاقد مهلت است' in row(c,'NM-586-1403:answer')['text'],'advisory')
 ph=','.join('?'*len(d));rr=c.execute(f'select article_no,text from articles where document_id in ({ph})',tuple(d.values())).fetchall();q(all(x['text'].strip() for x in rr),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rr),'ascii article no');q(all('https://' not in x['text'] and 'نوشته های تازه' not in x['text'] and 'دیدگاهتان' not in x['text'] and '�' not in x['text'] for x in rr),'source leak')
 for term in ('هیأت حل اختلاف','فاقد شناسنامه','شماره ملی','کارت هوشمند ملی','فرزندان حاصل از ازدواج شرعی','شورای تأمین','گذرنامه سیاسی','برگ بازگشت','پروانه گذر زیارتی'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==25,'relations')
 q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=row(c,'QSA-1355:45')['id'];did=d['QSA-1355'];c.close()
 for args in (['stats'],['show',str(did)],['history','QSA-1355:34'],['history','QM:989'],['history','QGO-1351:18'],['search','فاقد شناسنامه'],['search','کارت هوشمند ملی'],['search','پروانه گذر زیارتی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);q(p.returncode==0 and p.stdout.strip(),'query '+p.stderr)
 cl=app.test_client();pages=['/','/?q=ثبت+احوال','/?q=تابعیت','/?q=گذرنامه','/types','/by-type/law','/by-type/regulation','/by-type/unified_ruling','/by-type/advisory_opinion']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_identity_citizenship.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('pragma foreign_key_check').fetchall(),'fk after');q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'dupe refs');q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] Registry=55 numbers/57 rows; identity-card rules=6+14+10+13')
 print('[OK] Nationality book=16 numbers/17 rows (15 current); citizenship special law=2 versions+amendment+24')
 print('[OK] Passport=43 keys/56 rows (42 current); unified rulings=5; advisory opinion=1')
 print('[OK] Coverage, histories, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
