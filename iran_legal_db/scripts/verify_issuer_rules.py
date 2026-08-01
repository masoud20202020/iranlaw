# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('DAFSH-1386','DPT-1386','EPT-1402','DPF-1388','EPF-1402')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();docs={}
 for ref in REFS:
  r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(r,ref);docs[ref]=r['id']
 expected={'DAFSH-1386':(46,23,23),'DPT-1386':(61,61,0),'EPT-1402':(3,3,0),'DPF-1388':(44,44,0),'EPF-1402':(1,1,0)}
 for ref,e in expected.items():
  r=c.execute('select count(*)n,sum(is_current)c,sum(case when is_current=0 then 1 else 0 end)h from articles where document_id=?',(docs[ref],)).fetchone();q((r['n'],r['c'],r['h'])==e,'count '+ref)
 q({r[0] for r in c.execute('select distinct article_key from articles where document_id=?',(docs['DPT-1386'],))}=={f'DPT-1386:{i}' for i in range(1,62)},'Tehran coverage')
 q({r[0] for r in c.execute('select distinct article_key from articles where document_id=?',(docs['DPF-1388'],))}=={f'DPF-1388:{i}' for i in range(1,45)},'Farabourse coverage')
 curkeys={r[0] for r in c.execute('select article_key from articles where document_id=? and is_current=1',(docs['DAFSH-1386'],))}
 for k in ('1','2','2bis','2bis3','7','12bis','13','14bis','14bis1','20'):q(f'DAFSH-1386:{k}' in curkeys,'disclosure '+k)
 for k in ('6','14','21','2bis1','2bis2'):q(c.execute('select count(*) from articles where article_key=? and is_current=0',(f'DAFSH-1386:{k}',)).fetchone()[0]>0,'deleted '+k)
 rows=c.execute('select article_no,text from articles where document_id in ('+','.join('?'*len(docs))+')',tuple(docs.values())).fetchall();q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii no');q(all(x['text'].strip() for x in rows),'empty');q(all('ساختار تکمیلی' not in x['text'] and 'متن نمونه' not in x['text'] for x in rows),'filler')
 for term in ('کدال','افشای فوری','گزارش تفسیری مدیریت','هیئت پذیرش','لغو پذیرش','بازار نوآفرین','سهام شناور آزاد'):
  n=c.execute('select count(*) from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*) from relations where from_document_id in ('+','.join('?'*len(docs))+')',tuple(docs.values())).fetchone()[0]>=12,'relations')
 aid=c.execute('select id from articles where document_id=? and is_current=1 limit 1',(docs['DAFSH-1386'],)).fetchone()['id'];before=snap(c);c.close()
 for args in (['stats'],['history','DAFSH-1386:2'],['search','بازار نوآفرین']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);q(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client();pages=['/','/?q=کدال','/types','/by-type/directive']
 for d in docs.values():pages += [f'/doc/{d}',f'/doc/{d}?view=all',f'/doc/{d}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_issuer_rules.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90);q(p.returncode==0,p.stderr)
 c=get_connection();after=snap(c);c.close();q(before==after,'idempotency')
 print('[OK] Disclosure: 23 current + 23 historical rows')
 print('[OK] Tehran admission=61; 1402 summary=3; Farabourse base=44; amendment table=1')
 print('[OK] Coverage, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
