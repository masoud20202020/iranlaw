# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QEA-1356','QNEM-1394','AINEM-1399','QNEM-1377','AIW-1322','AIH299-1322');FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def main():
 c=get_connection();docs={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);docs[ref]=x['id']
 exp={'QEA-1356':(181,180,1),'QNEM-1394':(29,29,0),'AINEM-1399':(28,28,0),'QNEM-1377':(7,0,7),'AIW-1322':(5,5,0),'AIH299-1322':(14,14,0)}
 for ref,w in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c,sum(case when is_current=0 then 1 else 0 end)h from articles where document_id=?',(docs[ref],)).fetchone();q((x['n'],x['c'] or 0,x['h'])==w,'counts '+ref)
 for ref,end in (('QEA-1356',180),('QNEM-1394',29),('AINEM-1399',28),('QNEM-1377',7),('AIW-1322',5),('AIH299-1322',14)):
  keys={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(docs[ref],))};q(keys=={f'{ref}:{n}' for n in range(1,end+1)},'coverage '+ref)
 nums=[x[0] for x in c.execute('select article_no from articles where document_id=? and is_current=1 order by id',(docs['QEA-1356'],))];q(nums==[str(n).translate(FA) for n in range(1,181)],'execution sequence')
 q(c.execute("select count(*)from articles where article_key='QEA-1356:96'").fetchone()[0]==2,'history 96')
 cur96=c.execute("select text,id from articles where article_key='QEA-1356:96' and is_current=1").fetchone();q('کمیته امداد' in cur96['text'] and 'سازمان بهزیستی' in cur96['text'],'current 96')
 for n in range(1,8):
  x=c.execute('select is_current,expiry_date from articles where article_key=?',(f'QNEM-1377:{n}',)).fetchone();q(x['is_current']==0 and x['expiry_date']=='2015-06-13','old law '+str(n))
 f24=c.execute("select text from articles where article_key='QNEM-1394:24'").fetchone()['text'];q('مستثنیات دین' in f24 and 'منزل مسکونی' in f24,'financial 24')
 b9=c.execute("select text from articles where article_key='AINEM-1399:9'").fetchone()['text'];q('یک چهارم' in b9 and 'یک سوم' in b9,'bylaw 9')
 w5=c.execute("select text from articles where article_key='AIW-1322:5'").fetchone()['text'];q('فوت موصی' in w5 and 'وصیت‌نامه' in w5,'will bylaw')
 x8=c.execute("select text from articles where article_key='AIH299-1322:8'").fetchone()['text'];q(('سه مرتبه' in x8 or 'سه نوبت' in x8) and 'اعتراض' in x8,'299 bylaw')
 rows=c.execute('select article_no,text from articles where document_id in (?,?,?,?,?,?)',tuple(docs.values())).fetchall();q(all(x['text'].strip() for x in rows),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii');q(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] for x in rows),'leak/filler')
 for term in ('اجراییه','توقیف اموال','مزایده','اعتراض ثالث','مستثنیات دین','دعوای اعسار','وصیت‌نامه سری','موصی‌له'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute('select count(*)from relations where from_document_id=? and to_document_id=? and relation_type="abrogates"',(docs['QNEM-1394'],docs['QNEM-1377'])).fetchone()[0]==7,'abrogations')
 q(c.execute('select count(*)from relations where from_document_id in (?,?,?,?,?,?)',tuple(docs.values())).fetchone()[0]>=15,'relations');q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=cur96['id'];c.close()
 for args in (['stats'],['history','QEA-1356:96'],['search','مستثنیات دین'],['search','وصیت نامه سری']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);q(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client();pages=['/','/?q=اجرای+احکام','/types','/by-type/law','/by-type/regulation']
 for d in docs.values():pages += [f'/doc/{d}',f'/doc/{d}?view=all',f'/doc/{d}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_enforcement_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120);q(p.returncode==0,p.stderr)
 c=get_connection();after=snap(c);q(before==after,'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');c.close()
 print('[OK] Civil Execution Law=180 current/181 versions; financial law/bylaw=29/28')
 print('[OK] Former 1377 law=7 historical; secret-will/article-299 bylaws=5/14')
 print('[OK] Coverage, history, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
