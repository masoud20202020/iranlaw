# -*- coding: utf-8 -*-
import os,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
def q(x,m):
 if not x:raise AssertionError(m)
def main():
 c=get_connection();d=c.execute("select id from documents where reference_code='QATV-1318'").fetchone();q(d,'doc');did=d['id']
 rs=c.execute('select article_no,article_key,is_current,text from articles where document_id=? order by id',(did,)).fetchall();q(len(rs)==62,'versions');q(sum(r['is_current'] for r in rs)==58,'current');q(len({r['article_key'] for r in rs})==60,'coverage')
 q(c.execute("select count(*) from articles where article_key='QATV-1318:54'").fetchone()[0]==3,'history54')
 for n in (53,56):q(c.execute('select count(*) from articles where article_key=? and is_current=1',(f'QATV-1318:{n}',)).fetchone()[0]==0,f'repeal {n}')
 for ref,n in [('AATV-1318',67),('QSFB-1344',3)]:q(c.execute('select count(*) from articles a join documents d on d.id=a.document_id where d.reference_code=?',(ref,)).fetchone()[0]==n,ref)
 for term in ('ورشکستگی','بستانکاران','مزایده','وثیقه','صندوق الف','صندوق ب','مهر و موم'):
  q(c.execute('select count(*) from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0]>0,'fts '+term)
 a=c.execute("select id from articles where article_key='QATV-1318:54' and is_current=1").fetchone()['id'];c.close();cl=app.test_client()
 for p in ('/','/?q=ورشکستگی',f'/doc/{did}',f'/doc/{did}?view=all',f'/article/{a}'):q(cl.get(p).status_code==200,p)
 print('[OK] Bankruptcy liquidation law: 60 numbers, 62 versions, 58 current, 4 historical')
 print('[OK] Bylaw=67; funds law=3; repeals 1403; FTS and Flask routes')
if __name__=='__main__':main()
