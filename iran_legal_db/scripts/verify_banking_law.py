# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
CB='QBC-1402';PB='QPB-1351';UF='QOBR-1362';BR='AITMP-1362';BF='AITAB-1362';FL='QTSB-1386';R794='RVR-794-1399';REFS=(CB,PB,UF,BR,BF,FL,R794)
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from tags),(select count(*)from articles_fts)').fetchone())
def art(c,key,cur=1,v=None):
 sql='select * from articles where article_key=?';a=[key]
 if cur is not None:sql+=' and is_current=?';a.append(cur)
 if v is not None:sql+=' and version_no=?';a.append(v)
 return c.execute(sql+' order by version_no desc limit 1',a).fetchone()
def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={CB:(67,67,67),PB:(46,15,45),UF:(28,27,27),BR:(12,12,12),BF:(90,90,90),FL:(9,9,9),R794:(1,1,1)}
 for ref,w in exp.items():
  x=c.execute('select count(*)n,coalesce(sum(is_current),0)c,count(distinct article_key)k from articles where document_id=?',(d[ref],)).fetchone();q((x['n'],x['c'],x['k'])==w,'counts '+ref+str(tuple(x)))
 for ref,end in ((CB,67),(PB,45),(UF,27),(BR,12),(BF,90),(FL,9)):
  got={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[ref],))};q(got=={f'{ref}:{n}' for n in range(1,end+1)},'coverage '+ref)
 # Central Bank law.
 q('گزیر' in art(c,f'{CB}:1')['text'] and 'رمز‌پول' in art(c,f'{CB}:1')['text'],'CB definitions')
 q('تنظیم‌گری' in art(c,f'{CB}:4')['text'] and 'رمزپول' in art(c,f'{CB}:4')['text'],'CB powers')
 q('تسهیلات و تعهدات کلان' in art(c,f'{CB}:20')['text'] and 'اشخاص مرتبط' in art(c,f'{CB}:20')['text'],'CB prudential')
 q('هیئت انتظامی' in art(c,f'{CB}:22')['text'] and 'دیوان عدالت اداری' in art(c,f'{CB}:22')['text'],'CB discipline')
 q('مدیر گزیر' in art(c,f'{CB}:30')['text'] or 'فرایند گزیر' in art(c,f'{CB}:30')['text'],'CB resolution')
 q('تسهیلات اضطراری' in art(c,f'{CB}:45')['text'],'CB emergency liquidity')
 q('مواد (۱) تا (۱۷)' in art(c,f'{CB}:67')['text'] and 'شش‌ماه پس از ابلاغ' in art(c,f'{CB}:67')['text'],'CB repeal/effective')
 # 1351 temporal structure.
 rep=set(range(1,18))|set(range(19,27))|{39,40,42,43,44}
 for n in rep:q(art(c,f'{PB}:{n}',1) is None,'repealed PB '+str(n))
 currents={18,*range(27,39),41,45};q({int(x[0].split(':')[-1]) for x in c.execute('select article_key from articles where document_id=? and is_current=1',(d[PB],))}==currents,'PB current set')
 q(c.execute('select count(*)from articles where article_key=?',(f'{PB}:18',)).fetchone()[0]==2,'PB18 history')
 q('فقط بند الف باقی است' in c.execute('select notes from articles where article_key=? and is_current=1',(f'{PB}:18',)).fetchone()[0],'PB18 note')
 q('ورشکستگی بانکی' in art(c,f'{PB}:41')['text'] or 'ورشکستگی بانکی' in art(c,f'{PB}:41')['text'].replace('بانک','بانکی'),'PB41 bankruptcy')
 # Usury-free operations and bylaws.
 q(c.execute('select count(*)from articles where article_key=?',(f'{UF}:9',)).fetchone()[0]==2,'UF9 history')
 q('قرارداد مضاربه' in art(c,f'{UF}:9',0,1)['text'] and 'مرابحه' not in art(c,f'{UF}:9',0,1)['text'],'UF9 former')
 q(all(x in art(c,f'{UF}:9')['text'] for x in ('مضاربه','استصناع','مرابحه','خرید دین')),'UF9 current')
 q('در حکم اسناد رسمی' in art(c,f'{UF}:15')['text'] and 'صندوق نوآوری' in art(c,f'{UF}:15')['text'],'UF15 execution')
 q('سپرده‌های سرمایه‌گذاری' in art(c,f'{BR}:9')['text'] and 'وکالت' in art(c,f'{BR}:10')['text'],'resources bylaw')
 q('تأمین کافی' in art(c,f'{BF}:6')['text'] and 'اسناد رسمی' in art(c,f'{BF}:6')['text'],'facilities security')
 q('مشارکت مدنی' in art(c,f'{BF}:18')['text'] and 'مضاربه' in art(c,f'{BF}:36')['text'],'facilities contracts')
 q('مرابحه قراردادی' in art(c,f'{BF}:81')['text'] and 'کارت‌های الکترونیکی' in art(c,f'{BF}:85')['text'],'murabaha')
 q('خرید دین قراردادی' in art(c,f'{BF}:86')['text'] and 'حقیقی بودن دین' in art(c,f'{BF}:89')['text'],'debt purchase')
 q('چهل و پنج روز' in art(c,f'{FL}:1')['text'] and 'وثیقه' in art(c,f'{FL}:1')['text'],'facilitation law')
 q('در حکم اسناد رسمی' in art(c,f'{FL}:7')['text'],'facilitation execution')
 # Ruling 794.
 rt=art(c,f'{R794}:decision')['text'];q('سود مازاد' in rt and 'باطل است' in rt and 'لازم‌الاتباع' in rt,'ruling 794')
 ph=','.join('?'*len(d));rr=c.execute(f'select article_no,text,source_note from articles where document_id in ({ph})',tuple(d.values())).fetchall()
 q(all(x['text'].strip() and x['source_note'] for x in rr),'empty/source');q(all(not re.search(r'[0-9]',x['article_no']) for x in rr),'ascii number');q(all('http://' not in x['text'] and 'https://' not in x['text'] and '###' not in x['text'] and 'تازه‌های قوانین' not in x['text'] and '�' not in x['text'] for x in rr),'source leak');q(all(not re.match(r'^‌?ماده\s*[۰-۹]',x['text']) for x in rr),'heading leak')
 for term in ('هیأت‌عالی بانک مرکزی','گزیر','تسهیلات بانکی','قرض‌الحسنه','مرابحه','خرید دین','سود مازاد'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==44,'relations')
 q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=art(c,f'{CB}:1')['id'];c.close()
 for args in (['stats'],['show',str(d[CB])],['history',f'{PB}:18'],['history',f'{PB}:10'],['history',f'{UF}:9'],['search','گزیر'],['search','مرابحه'],['search','سود مازاد']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90);q(p.returncode==0 and p.stdout.strip(),'query '+p.stderr)
 cl=app.test_client();pages=['/','/?q=بانک+مرکزی','/?q=مرابحه','/?q=گزیر','/types','/by-type/law','/by-type/regulation','/by-type/unified_ruling']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts/load_banking_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('pragma foreign_key_check').fetchall(),'fk after');q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'dupe refs');q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] Central Bank=67; monetary/banking=45 keys/46 rows (15 current, 31 historical)')
 print('[OK] Usury-free=27 keys/28 rows; resources/facilities bylaws=12/90; facilitation law=9; ruling=1')
 print('[OK] Repeal map, histories, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
