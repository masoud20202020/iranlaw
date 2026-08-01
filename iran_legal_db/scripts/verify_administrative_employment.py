# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS={'QCSM-1386':128,'PCSM-1397':1,'ECSM44-1399':1,'AICSM46-1396':6,'DICSM46-1397':12,'AIEP-1368':30,'AICSM84-1389':5,'QTAK-1372':27,'AITAK-1373':47,'QDA-1392':124,'EQDAD-1402':62}
def ok(x,m):
 if not x:raise AssertionError(m)
def snapshot(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();docs={}
 for ref,count in REFS.items():
  r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();ok(r,'missing '+ref);docs[ref]=r['id']
  rows=c.execute('select article_key,article_no,is_current,text,source_note from articles where document_id=?',(r['id'],)).fetchall();ok(sum(x['is_current'] for x in rows)==count,'current count '+ref);ok({x['article_key'] for x in rows if x['is_current']}=={f'{ref}:{n}' for n in range(1,count+1)},'coverage '+ref);ok(all(x['text'].strip() and x['source_note'] for x in rows),'source/text '+ref);ok(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'Persian article number '+ref)
 ok(c.execute("select count(*) from articles where article_key='QDA-1392:2' and is_current=0").fetchone()[0]==1,'Divan history')
 for term in ('مدیریت خدمات کشوری','تخلفات اداری','دیوان عدالت اداری','تبدیل وضعیت'):
  ok(c.execute('select count(*) from articles_fts where articles_fts match ?',('"'+term+'"',)).fetchone()[0]>0,'fts '+term)
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 ok(c.execute('select count(*)from relations where from_document_id in (%s)'%(','.join('?'*len(docs))),tuple(docs.values())).fetchone()[0]==7,'relations')
 before=snapshot(c); aid=c.execute("select id from articles where article_key='QCSM-1386:44' and is_current=1").fetchone()['id']; c.close()
 for args in (['stats'],['show',str(docs['QCSM-1386'])],['history','QDA-1392:2'],['search','تخلفات اداری']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60);ok(p.returncode==0 and p.stdout.strip(),'cli '+str(args))
 cl=app.test_client()
 for p in ['/',f'/article/{aid}',f"/doc/{docs['QDA-1392']}"]:ok(cl.get(p).status_code==200,'Flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_administrative_employment.py')],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snapshot(c)==before,'idempotency');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'foreign keys');ok(not c.execute('select article_key,count(*) from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'multiple current');c.close();print('[OK] administrative/employment: 11 documents, complete coverage, Divan history, FTS, CLI, Flask and idempotency')
if __name__=='__main__':main()
