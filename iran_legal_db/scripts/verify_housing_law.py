# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QRM-1356','QRM-1362','QRM-1376','AIRM-1378','QTAP-1343','AITAP-1347','QPFS-1389','AIPFS-1393','QERF-1403');FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();d={}
 for r in REFS:
  x=c.execute('select id from documents where reference_code=?',(r,)).fetchone();q(x,'missing '+r);d[r]=x['id']
 exp={'QRM-1356':(32,32,0),'QRM-1362':(15,15,0),'QRM-1376':(14,13,1),'AIRM-1378':(20,19,1),'QTAP-1343':(16,16,0),'AITAP-1347':(28,27,1),'QPFS-1389':(28,23,5),'AIPFS-1393':(22,22,0),'QERF-1403':(15,15,0)}
 for r,w in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c,sum(case when is_current=0 then 1 else 0 end)h from articles where document_id=?',(d[r],)).fetchone();q((x['n'],x['c'] or 0,x['h'])==w,'counts '+r)
 for r,end in (('QRM-1356',32),('QRM-1362',15),('QRM-1376',13),('AIRM-1378',20),('AITAP-1347',27),('QPFS-1389',25),('AIPFS-1393',22),('QERF-1403',15)):
  keys={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[r],))};q(keys=={f'{r}:{n}' for n in range(1,end+1)},'coverage '+r)
 akeys={x[0] for x in c.execute('select article_key from articles where document_id=?',(d['QTAP-1343'],))};q(akeys=={f'QTAP-1343:{n}' for n in range(1,16)}|{'QTAP-1343:10bis'},'apartment keys')
 q(c.execute("select count(*)from articles where article_key='QRM-1376:2'").fetchone()[0]==2,'rent article2 history')
 l2=c.execute("select text,id from articles where article_key='QRM-1376:2' and is_current=1").fetchone();q('رهگیری' in l2['text'] and 'سامانه' in l2['text'],'rent2 current')
 x=c.execute("select is_current from articles where article_key='AIRM-1378:16'").fetchone();q(x['is_current']==0,'bylaw16 historical')
 a16=c.execute("select text from articles where article_key='AITAP-1347:16' and is_current=1").fetchone()['text'];q('تبصره ۱' in a16 and 'تبصره ۲' not in a16,'apartment bylaw16')
 q(c.execute("select count(*)from articles where article_key='QPFS-1389:1'").fetchone()[0]==2,'presale1 history')
 q(c.execute("select count(*)from articles where article_key='QPFS-1389:2'").fetchone()[0]==2,'presale2 history')
 q(c.execute("select count(*)from articles where article_key='QPFS-1389:4'").fetchone()[0]==2,'presale4 history')
 for n in (20,21):q(not c.execute('select 1 from articles where article_key=? and is_current=1',(f'QPFS-1389:{n}',)).fetchone(),'presale repeal')
 p2=c.execute("select text from articles where article_key='QPFS-1389:2' and is_current=1").fetchone()['text'];q('متن پروانه ساختمانی' in p2 and 'معرفی داوران' not in p2,'presale2 current')
 p4=c.execute("select text from articles where article_key='QPFS-1389:4' and is_current=1").fetchone()['text'];q('پاسخ استعلام' in p4 and 'پایان عملیات پی' not in p4,'presale4 current')
 r15=c.execute("select text from articles where article_key='QERF-1403:15'").fetchone()['text'];q('قانون پیش‌فروش ساختمان' in r15 and 'مواد (۲۰) و (۲۱)' in r15,'registration15')
 rows=c.execute('select article_no,text from articles where document_id in ('+','.join('?'*len(d))+')',tuple(d.values())).fetchall();q(all(x['text'].strip() for x in rows),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii');q(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] for x in rows),'leak')
 for term in ('حق کسب و پیشه','سرقفلی','کد رهگیری','قسمت‌های مشترک','هزینه‌های مشترک','پیش‌فروش ساختمان','شناسنامه فنی','سامانه ساماندهی اسناد غیررسمی'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute('select count(*)from relations where from_document_id=? and to_document_id=? and relation_type in("amends","abrogates")',(d['QERF-1403'],d['QPFS-1389'])).fetchone()[0]>=6,'registration relations')
 q(c.execute('select count(*)from relations where from_document_id in ('+','.join('?'*len(d))+')',tuple(d.values())).fetchone()[0]>=17,'relations');q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=l2['id'];c.close()
 for args in (['stats'],['history','QRM-1376:2'],['history','QPFS-1389:2'],['search','سامانه ساماندهی اسناد غیررسمی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);q(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client();pages=['/','/?q=سرقفلی','/types','/by-type/law','/by-type/regulation']
 for did in d.values():pages += [f'/doc/{did}',f'/doc/{did}?view=all',f'/doc/{did}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_housing_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');c.close()
 print('[OK] Tenancy laws 1356/1362/1376=32/15/13; tenancy bylaw=20 numbers, 19 current')
 print('[OK] Apartment law/bylaw=16/28 versions; presale=28 versions/23 current; presale bylaw=22; registration law=15')
 print('[OK] Coverage, 1403 histories/repeals, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
