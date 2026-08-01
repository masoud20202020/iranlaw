# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
E={'QBC-1370':77,'QSC-1350':147,'EQBC-1393':27}
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();d={}
 for ref,n in E.items():
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();ok(x,'missing');d[ref]=x['id'];a=c.execute('select *from articles where document_id=? and is_current=1',(x['id'],)).fetchall();ok(len(a)==n,'count '+ref);ok(all(z['text'].strip() and z['source_note'] for z in a),'source');ok(all(not re.search(r'[0-9]',z['article_no']) for z in a),'numbers')
 ok({x['article_key'] for x in c.execute('select article_key from articles where document_id=? and is_current=1',(d['QBC-1370'],))}=={f'QBC-1370:{i}' for i in range(1,78)},'sector coverage')
 qsc={x['article_key'] for x in c.execute('select article_key from articles where document_id=? and is_current=1',(d['QSC-1350'],))};ok(qsc=={f'QSC-1350:{i}' for i in range(1,150) if i not in (65,72)},'company coverage')
 for t in ('تعاونی','اتاق تعاون','هیأت رئیسه'):ok(c.execute('select count(*)from articles_fts where articles_fts match ?',('"'+t+'"',)).fetchone()[0]>0,'fts')
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity');before=snap(c);aid=c.execute("select id from articles where article_key='QBC-1370:57'").fetchone()['id'];c.close()
 for a in (['stats'],['show',str(d['QBC-1370'])],['search','اتاق تعاون']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*a],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'cli')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_cooperative_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idem');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'fk');ok(not c.execute('select article_key,count(*)from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'dup');c.close();print('[OK] cooperative: 3 laws / 251 provisions; coverage, FTS, CLI, Flask, integrity, idempotency')
if __name__=='__main__':main()
