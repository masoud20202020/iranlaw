# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
INS='QBI-1316';CI='QBMC-1350';ECI='EQBMC-1353';TP='QST-1395';TP87='QST-1387';TP47='QST-1347';REFS=(INS,CI,ECI,TP,TP87,TP47)
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def art(c,k,cur=1):return c.execute('select * from articles where article_key=? and is_current=?',(k,cur)).fetchone()
def main():
 c=get_connection();d={}
 for r in REFS:
  x=c.execute('select id from documents where reference_code=?',(r,)).fetchone();q(x,'missing '+r);d[r]=x['id']
 exp={INS:(36,36),CI:(77,77),ECI:(1,1),TP:(66,66),TP87:(30,0),TP47:(14,0)}
 for r,w in exp.items():
  x=c.execute('select count(*)n,coalesce(sum(is_current),0)c from articles where document_id=?',(d[r],)).fetchone();q(tuple(x)==w,'count '+r)
 for r,end in ((INS,36),(CI,77),(TP,66),(TP87,30),(TP47,14)):
  got={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[r],))};q(got=={f'{r}:{n}' for n in range(1,end+1)},'coverage '+r)
 q('بیمه عقدی است' in art(c,f'{INS}:1')['text'],'insurance contract');q('اظهارات کاذبه' in art(c,f'{INS}:12')['text'],'disclosure');q('قائم‌مقامی' in art(c,f'{INS}:30')['text'] or 'قائم مقام' in art(c,f'{INS}:30')['text'],'subrogation')
 q('شورای عالی بیمه' in art(c,f'{CI}:17')['text'] and 'شرائط عمومی بیمه' in art(c,f'{CI}:17')['text'],'council');q('اتکائی' in art(c,f'{CI}:71')['text'] or 'اتکایی' in art(c,f'{CI}:71')['text'],'reinsurance');q('ماده ۲۸' in art(c,f'{ECI}:single')['text'] and 'ماده ۳۵' in art(c,f'{ECI}:single')['text'],'amendment')
 q('خسارت بدنی' in art(c,f'{TP}:1')['text'] and 'صندوق' in art(c,f'{TP}:1')['text'],'definitions');q('راننده مسبب حادثه' in art(c,f'{TP}:3')['text'],'driver');q('بدون لحاظ جنسیت و دین' in art(c,f'{TP}:10')['text'],'equal compensation');q('بدون هیچ شرط' in art(c,f'{TP}:15')['text'] and 'تضمین' in art(c,f'{TP}:15')['text'],'recourse');q('صندوق مکلف است' in art(c,f'{TP}:25')['text'],'fund');q('بیست روز' in art(c,f'{TP}:32')['text'] and 'تودیع' in art(c,f'{TP}:32')['text'],'payment deadline');q('نسخ می‌شود' in art(c,f'{TP}:66')['text'],'repeal')
 q(all(art(c,f'{TP87}:{n}',1) is None for n in range(1,31)),'old87');q(all(art(c,f'{TP47}:{n}',1) is None for n in range(1,15)),'old47')
 ph=','.join('?'*len(d));rr=c.execute(f'select article_no,text,source_note from articles where document_id in ({ph})',tuple(d.values())).fetchall();q(all(x['text'].strip() and x['source_note'] for x in rr),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rr),'ascii');q(all('http://' not in x['text'] and 'https://' not in x['text'] and '�' not in x['text'] for x in rr),'leak')
 for term in ('عقد بیمه','بیمه اتکایی','صندوق تأمین خسارت‌های بدنی','راننده مسبب حادثه'):
  q(c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0]>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity');q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==49,'relations');q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=art(c,f'{TP}:1')['id'];c.close()
 for args in (['stats'],['show',str(d[TP])],['history',f'{TP87}:1'],['search','صندوق تأمین خسارت‌های بدنی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90);q(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client()
 for p in ['/',f'/article/{aid}',*[f'/doc/{x}' for x in d.values()]]:q(cl.get(p).status_code==200,'flask')
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_insurance_core.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('pragma foreign_key_check').fetchall(),'fk2');q(not c.execute('select article_key,count(*) from articles where is_current=1 and article_key is not null group by article_key having count(*)>1').fetchall(),'multi');c.close();print('[OK] Insurance=36; Central Insurance=77; amendment=1; third-party=66; former laws=30+14 historical');print('[OK] Coverage, repeal network, Persian numbers, FTS5, Flask and idempotency')
if __name__=='__main__':main()
