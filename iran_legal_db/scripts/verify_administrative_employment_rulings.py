# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('DAD-669-1398','DAD-1043-1400','DAD-2120727-1402','DAD-383671-1403')
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();ids=[]
 for ref in REFS:
  d=c.execute('select id,notes from documents where reference_code=?',(ref,)).fetchone();ok(d,'missing '+ref);ids.append(d['id']);ok('خلاصه ساختاری منبع‌دار' in d['notes'],'label '+ref)
  a=c.execute('select * from articles where document_id=?',(d['id'],)).fetchall();ok(len(a)==1 and a[0]['is_current'],'article '+ref);ok(a[0]['source_note'].startswith('https://'),'source '+ref);ok('خلاصه' in a[0]['text'],'summary '+ref)
 for term in ('تبدیل وضعیت','گزینش','ترمیم حقوق') :ok(c.execute('select count(*) from articles_fts where articles_fts match ?',('"'+term+'"',)).fetchone()[0]>0,'fts '+term)
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity');before=snap(c);aid=c.execute('select id from articles where article_key=?',(REFS[0]+':ruling',)).fetchone()['id'];c.close()
 for a in (['search','تبدیل وضعیت'],['show',str(ids[0])]):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*a],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'CLI')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'Flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_administrative_employment_rulings.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idempotency');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'foreign keys');c.close();print('[OK] 4 explicitly-labelled sourced administrative-employment ruling summaries; FTS, CLI, Flask and idempotency')
if __name__=='__main__':main()
