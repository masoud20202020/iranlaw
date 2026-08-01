# -*- coding: utf-8 -*-
"""Verification for family protection and non-contentious matters package."""
from __future__ import annotations
import os,re,subprocess,sys
ROOT=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(ROOT,'scripts'),os.path.join(ROOT,'web')]
from schema import get_connection
from app import app
REFS=('QHKH-1391','AQHKH-1392','QAH-1319');FA=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def req(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('''select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)''').fetchone())
def main():
 c=get_connection();docs={}
 for ref in REFS:
  r=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();req(r,'missing '+ref);docs[ref]=r['id']
 expected={'QHKH-1391':(58,58,0),'AQHKH-1392':(75,67,8),'QAH-1319':(379,378,1)}
 for ref,w in expected.items():
  r=c.execute('''select count(*)n,sum(is_current)c,sum(case when is_current=0 then 1 else 0 end)h from articles where document_id=?''',(docs[ref],)).fetchone();req((r['n'],r['c'],r['h'])==w,'counts '+ref)
 for ref,end in (('QHKH-1391',58),('AQHKH-1392',69),('QAH-1319',378)):
  keys={r[0] for r in c.execute('select distinct article_key from articles where document_id=?',(docs[ref],))};req(keys=={f'{ref}:{n}' for n in range(1,end+1)},'coverage '+ref)
 fnums=[r[0] for r in c.execute('select article_no from articles where document_id=? and is_current=1 order by id',(docs['QHKH-1391'],))];req(fnums==[str(n).translate(FA) for n in range(1,59)],'family sequence')
 bcur={r[0] for r in c.execute('select article_key from articles where document_id=? and is_current=1',(docs['AQHKH-1392'],))};req(bcur=={f'AQHKH-1392:{n}' for n in range(1,70) if n not in (14,15)},'bylaw current')
 for n in (10,32,33,34,36,47):req(c.execute('select count(*) from articles where article_key=?',(f'AQHKH-1392:{n}',)).fetchone()[0]==2,f'history {n}')
 for n in (14,15):
  r=c.execute('select is_current,expiry_date from articles where article_key=?',(f'AQHKH-1392:{n}',)).fetchone();req(r['is_current']==0 and r['expiry_date']=='2021-08-29',f'repeal {n}')
 b10=c.execute("select text from articles where article_key='AQHKH-1392:10' and is_current=1").fetchone()['text'];req('رتبه‌بندی مراکز' in b10 and 'در بند ز ماده' not in b10,'article 10 current')
 b32=c.execute("select text from articles where article_key='AQHKH-1392:32' and is_current=1").fetchone()['text'];req('هر سال یک بار' in b32 and 'انتصاب رئیس واحد مشاوره استان' in b32,'article 32')
 b34=c.execute("select text from articles where article_key='AQHKH-1392:34' and is_current=1").fetchone()['text'];req('حداقل ۳۵ سال سن و ۳ سال سابقه' in b34 and 'صدور مجوز تأسیس مرکز برای وکلا' in b34,'article34')
 b47=c.execute("select text from articles where article_key='AQHKH-1392:47' and is_current=1").fetchone()['text'];req('درجه۷' in b47 and 'ابطال پروانه فعالیت' in b47,'article47')
 h375=c.execute("select text from articles where article_key='QAH-1319:375' and is_current=1").fetchone()['text'];req('پانصد ریال' in h375,'hasbi 375')
 rows=c.execute('select article_no,text from articles where document_id in (?,?,?)',tuple(docs.values())).fetchall();req(all(x['text'].strip() for x in rows),'empty');req(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii article no');req(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] for x in rows),'leak/filler')
 for term in ('دادگاه خانواده','طلاق توافقی','مهریه','ملاقات والدین','قیمومت','غایب مفقودالاثر','تحریر ترکه','انحصار وراثت'):
  n=c.execute('''select count(*) from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1''',(f'"{term}"',)).fetchone()[0];req(n>0,'fts '+term)
 req(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 req(c.execute('select count(*)from relations where from_document_id=? and relation_type="implements"',(docs['AQHKH-1392'],)).fetchone()[0]==4,'bylaw relations')
 req(c.execute('select count(*)from relations where from_document_id in (?,?,?)',tuple(docs.values())).fetchone()[0]>=9,'relations')
 req(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 aid=c.execute("select id from articles where article_key='AQHKH-1392:10' and is_current=1").fetchone()[0];before=snap(c);c.close()
 for args in (['stats'],['history','AQHKH-1392:10'],['history','QAH-1319:375'],['search','غایب مفقودالاثر']):
  p=subprocess.run([sys.executable,os.path.join(ROOT,'scripts','query.py'),*args],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);req(p.returncode==0 and p.stdout.strip(),'query')
 cl=app.test_client();pages=['/','/?q=دادگاه+خانواده','/types','/by-type/law','/by-type/regulation']
 for d in docs.values():pages += [f'/doc/{d}',f'/doc/{d}?view=all',f'/doc/{d}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:req(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(ROOT,'scripts','load_family_law.py')],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120);req(p.returncode==0,p.stderr)
 c=get_connection();after=snap(c);req(before==after,f'idempotency {before}!={after}');req(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');c.close()
 print('[OK] Family Protection Law=58; bylaw=69/75 versions, 67 current, 8 historical')
 print('[OK] Non-Contentious Matters Law=378 current, 379 versions')
 print('[OK] Coverage, amendment/repeal histories, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
