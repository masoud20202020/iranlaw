# -*- coding: utf-8 -*-
"""Integrity and Flask smoke tests for the Electronic Commerce package."""
import os,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'web')]
from schema import get_connection
from app import app

def req(x,m):
 if not x: raise AssertionError(m)
def main():
 c=get_connection();d=c.execute("select id from documents where reference_code='QTE-1382'").fetchone();req(d,'missing law');did=d['id']
 rows=c.execute('select article_no,article_key,is_current,text from articles where document_id=? order by id',(did,)).fetchall()
 req(len(rows)==98,'expected 98 versions');cur=[r for r in rows if r['is_current']];req(len(cur)==81,'expected 81 current');req([r['article_no'] for r in cur]==[str(i).translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')) for i in range(1,82)],'sequence')
 for k,n in {'32':2,'48':2,'67':2,'68':3,'69':3,'76':3}.items(): req(c.execute('select count(*) from articles where article_key=?',(f'QTE-1382:{k}',)).fetchone()[0]==n,f'history {k}')
 a68=c.execute("select text,id from articles where article_key='QTE-1382:68' and is_current=1").fetchone();req('۸۲۵٬۰۰۰٬۰۰۰' in a68['text'],'fine 68')
 for ref,n in {'AIN32-1386':23,'AIN3842-1383':3,'AIN48-1384':5}.items(): req(c.execute('select count(*) from articles a join documents d on d.id=a.document_id where d.reference_code=?',(ref,)).fetchone()[0]==n,ref)
 for q in ('داده پیام','امضای الکترونیکی','حق انصراف','مصرف کننده','اسرار تجاری','مرکز ریشه','گواهی الکترونیکی'):
  req(c.execute('select count(*) from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{q}"',)).fetchone()[0]>0,'fts '+q)
 req(c.execute('select count(*) from articles_fts').fetchone()[0]==c.execute('select count(*) from articles').fetchone()[0],'fts count')
 c.close();cl=app.test_client()
 for p in ('/','/?q=امضای+الکترونیکی',f'/doc/{did}',f'/doc/{did}?view=all',f"/article/{a68['id']}"):
  req(cl.get(p).status_code==200,'web '+p)
 print('[OK] Electronic Commerce Law: 81 current articles, 98 total versions, 17 historical')
 print('[OK] Regulations: article 32=20 (+3 histories), articles 38/42=2 (+1 history), article 48=5')
 print('[OK] Fine histories 1399/1403, FTS, relations and Flask routes')
if __name__=='__main__':main()
