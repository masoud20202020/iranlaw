# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
E={'QHMMH-1348':33,'QHPNR-1379':17,'QTKA-1352':12,'QMS-1403':150}
def ok(x,m):
 if not x:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();ids=[]
 for ref,n in E.items():
  d=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();ok(d,'missing '+ref);ids.append(d['id']);a=c.execute('select * from articles where document_id=? and is_current=1',(d['id'],)).fetchall();ok(len(a)==n,'count '+ref);ok({x['article_key'] for x in a}=={f'{ref}:{i}' for i in range(1,n+1)},'coverage '+ref);ok(all(x['text'].strip() and x['source_note'] for x in a),'source '+ref);ok(all(not re.search(r'[0-9]',x['article_no']) for x in a),'numbers '+ref)
 for t in ('حق مؤلف','نرم‌افزار','تکثیر','اختراع','علامت تجاری'):ok(c.execute('select count(*)from articles_fts where articles_fts match ?',('"'+t+'"',)).fetchone()[0]>0,'fts '+t)
 ok(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts');before=snap(c);aid=c.execute("select id from articles where article_key='QMS-1403:1'").fetchone()['id'];c.close()
 for a in (['stats'],['show',str(ids[-1])],['search','مالکیت صنعتی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*a],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0 and p.stdout.strip(),'cli')
 ok(app.test_client().get('/article/'+str(aid)).status_code==200,'flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_intellectual_property.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);ok(p.returncode==0,p.stderr)
 c=get_connection();ok(snap(c)==before,'idempotency');ok(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');ok(not c.execute('pragma foreign_key_check').fetchall(),'fk');c.close();print('[OK] intellectual property: 4 statutes / 212 provisions; coverage, FTS, CLI, Flask and idempotency')
if __name__=='__main__':main()
