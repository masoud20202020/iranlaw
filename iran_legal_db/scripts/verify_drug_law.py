# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QMM-1367','E45MM-1396','AIMM-1377','AIDM-1391','RVR-738-1393','RVR-743-1394','RVR-814-1400','RVR-826-1401','RVR-846-1403')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def row(c,key,cur=1):return c.execute('select * from articles where article_key=? and is_current=?',(key,cur)).fetchone()
def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={'QMM-1367':(57,44),'E45MM-1396':(1,1),'AIMM-1377':(35,28),'AIDM-1391':(15,15),'RVR-738-1393':(1,1),'RVR-743-1394':(1,1),'RVR-814-1400':(1,1),'RVR-826-1401':(1,1),'RVR-846-1403':(1,1)}
 for ref,(n,cur) in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c from articles where document_id=?',(d[ref],)).fetchone();q((x['n'],x['c'])==(n,cur),'counts '+ref)
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QMM-1367'],))}=={f'QMM-1367:{n}' for n in range(1,47)},'law coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['AIMM-1377'],))}=={f'AIMM-1377:{n}' for n in range(1,35)},'bylaw coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['AIDM-1391'],))}=={f'AIDM-1391:{n}' for n in range(1,16)},'treatment coverage')
 q(row(c,'QMM-1367:10') is None and row(c,'QMM-1367:32') is None,'repealed law current')
 q('تا یک گرم' in row(c,'QMM-1367:10',0)['text'] and 'تأیید رییس دیوان عالی کشور' in row(c,'QMM-1367:32',0)['text'],'historical law text')
 for n in (2,3,4,5,8,9,14,19,20,30):q(c.execute('select count(*)from articles where article_key=?',(f'QMM-1367:{n}',)).fetchone()[0]==2,'fine history '+str(n))
 q('۳۳۰,۰۰۰,۰۰۰ تا ۸۲۵,۰۰۰,۰۰۰' in row(c,'QMM-1367:2')['text'] and '۳۳۰,۰۰۰,۰۰۰ تا ۸۲۵,۰۰۰,۰۰۰' not in row(c,'QMM-1367:2',0)['text'],'fine current')
 q('مفسد‌فی‌الارض' in row(c,'QMM-1367:45')['text'] and 'بیش از پنجاه کیلوگرم' in row(c,'QMM-1367:45')['text'],'article45')
 v46=c.execute("select version_no,article_no,is_current,text from articles where article_key='QMM-1367:46' order by version_no").fetchall();q(len(v46)==2 and v46[0]['article_no']=='۴۵' and v46[1]['article_no']=='۴۶' and v46[1]['is_current']==1,'renumber46')
 q('تازه‌های قوانین' not in v46[1]['text'] and 'قانون بودجه سال' not in v46[1]['text'],'law page leak')
 q('ماده‌واحده' in row(c,'E45MM-1396:single')['text'] and 'ماده۴۵' in row(c,'E45MM-1396:single')['text'],'amendment')
 for n in (2,3,5,7,9,12):q(row(c,f'AIMM-1377:{n}') is None and row(c,f'AIMM-1377:{n}',0) is not None,'bylaw repeal '+str(n))
 q('زمانی قرار موقوفی تعقیب' in row(c,'AIMM-1377:4',0)['text'] and 'زمانی قرار موقوفی تعقیب' not in row(c,'AIMM-1377:4')['text'],'bylaw4 history')
 q('[پاورقی' not in row(c,'AIMM-1377:2',0)['text'],'footnote leak')
 q('مرکز درمان سرپایی' in row(c,'AIDM-1391:1')['text'] and 'آگونیست' in row(c,'AIDM-1391:1')['text'],'treatment1')
 q('سامانه ملی اطلاعات' in row(c,'AIDM-1391:14')['text'] and 'قانون مجازات اسلامی + متن کامل' not in row(c,'AIDM-1391:15')['text'],'treatment clean')
 q('ماده ۱۳۴' in row(c,'RVR-738-1393:decision')['text'] and 'تعدد بزه' in row(c,'RVR-738-1393:decision')['text'],'r738')
 q('قابل فرجام‌خواهی' in row(c,'RVR-743-1394:decision')['text'] and 'ماده ۴۲۸' in row(c,'RVR-743-1394:decision')['text'],'r743')
 q('صرفاً شامل ارسال این مواد به خارج از کشور' in row(c,'RVR-814-1400:decision')['text'],'r814')
 q('محکومیت قابل اجرا' in row(c,'RVR-826-1401:decision')['text'] and 'عفو یا تخفیف' in row(c,'RVR-826-1401:decision')['text'],'r826')
 q('مانع از اعمال تخفیف در مرحله صدور حکم' in row(c,'RVR-846-1403:decision')['text'],'r846')
 ph=','.join('?'*len(d));rows=c.execute(f'select article_no,text from articles where document_id in ({ph})',tuple(d.values())).fetchall();q(all(x['text'].strip() for x in rows),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii');q(all('https://' not in x['text'] and x['text'].strip()!='*' and '�' not in x['text'] for x in rows),'leak')
 for term in ('مواد مخدر','روان‌گردان‌های صنعتی','مجازات اعدام','تعدد جرم','فرجام‌خواهی','ارسال این مواد به خارج از کشور','عفو یا تخفیف','درمان و کاهش آسیب','داروهای آگونیست'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==16,'relations');q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=row(c,'QMM-1367:45')['id'];did=d['QMM-1367'];c.close()
 for args in (['stats'],['show',str(did)],['history','QMM-1367:2'],['history','QMM-1367:46'],['search','مجازات اعدام مواد مخدر'],['search','درمان و کاهش آسیب']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);q(p.returncode==0 and p.stdout.strip(),'query '+p.stderr)
 cl=app.test_client();pages=['/','/?q=مواد+مخدر','/?q=درمان+و+کاهش+آسیب','/types','/by-type/law','/by-type/regulation','/by-type/unified_ruling']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_drug_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'dupe refs');q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] Narcotics law=46 numbers/57 rows (44 current, 13 historical); article-45 amendment=1')
 print('[OK] General bylaw=34/35 rows (28 current); treatment bylaw=15; unified rulings=5')
 print('[OK] Coverage, fines, repeals, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
