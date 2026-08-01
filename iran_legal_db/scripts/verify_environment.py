# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
E={'QHBE-1353':21,'QHP-1396':34,'QMP-1383':23,'AIMP-1384':39,'QHBJM-1346':63}
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();d={}
 for r,n in E.items():
  x=c.execute('select id from documents where reference_code=?',(r,)).fetchone();ok(x,'missing');d[r]=x['id'];a=c.execute('select *from articles where document_id=? and is_current=1',(x['id'],)).fetchall();ok(len(a)==n,'count '+r);ok(all(z['text'].strip() and z['source_note'] for z in a),'source');ok(all(not re.search(r'[0-9]',z['article_no']) for z in a),'digits')
 for t in ('محیط زیست','هوای پاک','پسماند','جنگل'):ok(c.execute('select count(*)from articles_fts where articles_fts match ?',('"'+t+'"',)).fetchone()[0]>0,'fts')
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity');before=snap(c);aid=c.execute("select id from articles where article_key='QHP-1396:1'").fetchone()['id'];c.close()
 for a in (['stats'],['show',str(d['QHP-1396'])],['search','پسماند']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*a],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'cli')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'flask');p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_environment.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idem');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'fk');ok(not c.execute('select article_key,count(*)from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'dup');c.close();print('[OK] environment 5 documents / 180 provisions')
if __name__=='__main__':main()
