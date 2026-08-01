# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
E={'QCSE-1391':76,'QGMO-1374':18,'QTSAJ-1374':20,'QTG-1375':1}
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();ids={}
 for ref,n in E.items():
  d=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();ok(d,'missing '+ref);ids[ref]=d['id'];a=c.execute('select * from articles where document_id=? and is_current=1',(d['id'],)).fetchall();ok(len(a)==n,'count '+ref);ok(all(x['text'].strip() and x['source_note'] for x in a),'source '+ref);ok(all(not re.search(r'[0-9]',x['article_no']) for x in a),'numbers '+ref)
  if ref!='QTG-1375':ok({x['article_key'] for x in a}=={f'{ref}:{i}' for i in range(1,n+1)},'coverage '+ref)
 for term in ('ایثارگران','گزینش','جانبازان','اعاده به خدمت'):ok(c.execute('select count(*)from articles_fts where articles_fts match ?',('"'+term+'"',)).fetchone()[0]>0,'fts '+term)
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity');before=snap(c);aid=c.execute("select id from articles where article_key='QCSE-1391:21'").fetchone()['id'];c.close()
 for ar in (['stats'],['show',str(ids['QCSE-1391'])],['search','ایثارگران']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*ar],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'cli')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_administrative_employment_core.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idempotency');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'fk');ok(not c.execute('select article_key,count(*) from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'current duplicate');c.close();print('[OK] phase-three core statutes: 115 current provisions; coverage, FTS, CLI, Flask, integrity and idempotency')
if __name__=='__main__':main()
