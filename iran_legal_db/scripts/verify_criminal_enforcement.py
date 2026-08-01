# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QADK-1392-EXEC','AIEK-1398','AIZ-1400','AIME-1397','AIN79-1393','DSKZ-1398','DMEL-1401');FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();d={}
 for r in REFS:
  x=c.execute('select id from documents where reference_code=?',(r,)).fetchone();q(x,'missing '+r);d[r]=x['id']
 exp={'QADK-1392-EXEC':75,'AIEK-1398':148,'AIZ-1400':342,'AIME-1397':28,'AIN79-1393':16,'DSKZ-1398':29,'DMEL-1401':4}
 for r,n in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c from articles where document_id=?',(d[r],)).fetchone();q((x['n'],x['c'])==(n,n),'counts '+r)
 ekeys={x[0] for x in c.execute('select article_key from articles where document_id=?',(d['QADK-1392-EXEC'],))};q(ekeys=={f'QADK-1392-EXEC:{n}' for n in range(484,559)},'execution coverage')
 for r,start,end in (('AIEK-1398',1,148),('AIZ-1400',1,342),('AIME-1397',1,28),('AIN79-1393',1,16),('DSKZ-1398',1,29),('DMEL-1401',1,4)):
  keys={x[0] for x in c.execute('select article_key from articles where document_id=?',(d[r],))};q(keys=={f'{r}:{n}' for n in range(start,end+1)},'coverage '+r)
 e557=c.execute("select text,id from articles where article_key='QADK-1392-EXEC:557'").fetchone();q('نظارت سامانه‌های الکترونیکی' in e557['text'] and 'جایگزین حبس' in e557['text'],'article557')
 j40=c.execute("select text from articles where article_key='AIEK-1398:40'").fetchone()['text'];q('قصاص نفس' in j40 or 'اعدام' in j40,'judgment40')
 p194=c.execute("select text from articles where article_key='AIZ-1400:194'").fetchone()['text'];q('مرخصی' in p194 and 'درجه اعتباری' in p194,'prison194')
 m24=c.execute("select text from articles where article_key='AIME-1397:24'").fetchone()['text'];q('شبانه روزی' in m24 and 'مامور ناظر' in m24,'monitor24')
 a2=c.execute("select text from articles where article_key='AIN79-1393:2'").fetchone()['text'];q('خدمات عمومی رایگان' in a2,'alternative2')
 l1=c.execute("select text from articles where article_key='DMEL-1401:1'").fetchone()['text'];q('۲۰۰ متر' in l1 and '۱۰۰۰ متر' in l1,'limits')
 rows=c.execute('select article_no,text from articles where document_id in ('+','.join('?'*len(d))+')',tuple(d.values())).fetchall();q(all(x['text'].strip() for x in rows),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii');q(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] for x in rows),'leak/filler')
 for term in ('قاضی اجرای احکام کیفری','آزادی مشروط','قصاص نفس','مرخصی زندانیان','کانون اصلاح و تربیت','مراقبت الکترونیکی','خدمات عمومی رایگان','کاهش جمعیت کیفری'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute('select count(*)from relations where from_document_id in ('+','.join('?'*len(d))+')',tuple(d.values())).fetchone()[0]>=12,'relations');q(c.execute('select count(*)from relations where from_document_id=? and relation_type="implements"',(d['AIEK-1398'],)).fetchone()[0]==1,'judgment relation');q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=e557['id'];c.close()
 for args in (['stats'],['history','QADK-1392-EXEC:557'],['search','نظام نیمه آزادی'],['search','مراقبت الکترونیکی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);q(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client();pages=['/','/?q=آزادی+مشروط','/types','/by-type/law','/by-type/regulation','/by-type/directive']
 for did in d.values():pages += [f'/doc/{did}',f'/doc/{did}?view=all',f'/doc/{did}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_criminal_enforcement.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');c.close()
 print('[OK] Criminal execution section=75; judgment-execution bylaw=148; prisons bylaw=342')
 print('[OK] Electronic monitoring=28; alternative punishment=16; population directive=29; limits=4')
 print('[OK] Coverage, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
