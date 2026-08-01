# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
E={'QE44-1386':92,'QHMC-1388':22,'AIHMC-1390':42,'QHMCA-1386':11}
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();d={}
 for ref,n in E.items():
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();ok(x,'missing '+ref);d[ref]=x['id'];a=c.execute('select * from articles where document_id=? and is_current=1',(x['id'],)).fetchall();ok(len(a)==n,'count '+ref);ok(all(z['text'].strip() and z['source_note'] for z in a),'text/source '+ref);ok(all(not re.search(r'[0-9]',z['article_no']) for z in a),'number '+ref)
  if ref!='AIHMC-1390':ok({z['article_key'] for z in a}=={f'{ref}:{i}' for i in range(1,n+1)},'coverage '+ref)
 ok({z['article_key'] for z in c.execute('select article_key from articles where document_id=? and is_current=1',(d['AIHMC-1390'],))}=={f'AIHMC-1390:{i}' for i in list(range(1,39))+list(range(40,44))},'bylaw gap')
 for t in ('مصرف‌کننده','شورای رقابت','ضدرقابتی','ضمانت‌نامه','خودرو'):ok(c.execute('select count(*)from articles_fts where articles_fts match ?',('"'+t+'"',)).fetchone()[0]>0,'fts '+t)
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts');before=snap(c);aid=c.execute("select id from articles where article_key='QE44-1386:45'").fetchone()['id'];c.close()
 for a in (['stats'],['show',str(d['QE44-1386'])],['search','شورای رقابت']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*a],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'cli')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_consumer_competition.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idempotency');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'fk');ok(not c.execute('select article_key,count(*) from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'duplicate');c.close();print('[OK] consumer/competition: 4 documents / 167 provisions; coverage, FTS, CLI, Flask, integrity and idempotency')
if __name__=='__main__':main()
