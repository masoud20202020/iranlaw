# -*- coding: utf-8 -*-
"""Verify anti-smuggling and customs package."""
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QMK-1392','EQMK-1400','QAG-1390','AIAG-1391','AIQK-56-1395','AIQK-5556-1401','RVR-736-1393','RVR-839-1402','RVR-878-1405')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def row(c,key,cur=1):return c.execute('select * from articles where article_key=? and is_current=?',(key,cur)).fetchone()
def smuggling_keys():
 ex={2:['2bis'],6:['6bis1','6bis2'],18:['18bis'],25:['25bis'],33:['33bis1','33bis2'],42:['42bis'],50:['50bis1','50bis2','50bis3']};out=[]
 for n in range(1,79):out.append(str(n));out.extend(ex.get(n,[]))
 return out

def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id,notes from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={'QMK-1392':(121,87),'EQMK-1400':(47,47),'QAG-1390':(167,165),'AIAG-1391':(222,222),'AIQK-56-1395':(46,46),'AIQK-5556-1401':(25,25),'RVR-736-1393':(1,1),'RVR-839-1402':(1,1),'RVR-878-1405':(1,1)}
 for ref,(n,cur) in exp.items():
  x=c.execute('select count(*)n,sum(is_current)c from articles where document_id=?',(d[ref],)).fetchone();q((x['n'],x['c'])==(n,cur),'counts '+ref)
 keys={x[0].split(':',1)[1] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QMK-1392'],))};q(keys==set(smuggling_keys()),'smuggling coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['EQMK-1400'],))}=={f'EQMK-1400:{n}' for n in range(1,48)},'amendment coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QAG-1390'],))}=={f'QAG-1390:{n}' for n in range(1,166)},'customs coverage')
 bkeys={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['AIAG-1391'],))};q(bkeys==({f'AIAG-1391:{n}' for n in range(1,222)}|{'AIAG-1391:189bis'}),'customs bylaw coverage')
 for ref,end in (('AIQK-56-1395',46),('AIQK-5556-1401',25)):
  keys={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[ref],))};q(keys=={f'{ref}:{n}' for n in range(1,end+1)},'bylaw coverage '+ref)

 # Current/historical structure of anti-smuggling law.
 q(row(c,'QMK-1392:4') is None and row(c,'QMK-1392:76') is None,'repealed articles current')
 q(row(c,'QMK-1392:4',0) is not None and row(c,'QMK-1392:76',0) is not None,'repealed history')
 for key in ('1','2','3','20','27','47','53','56','63','73','77','78'):
  q(c.execute('select count(*)from articles where article_key=?',(f'QMK-1392:{key}',)).fetchone()[0]==2,'history '+key)
 q('موارد زیر قاچاق ارز محسوب می‌شود' in row(c,'QMK-1392:2bis')['text'] and 'تعهد ارزی' in row(c,'QMK-1392:2bis')['text'],'article2bis')
 q('سامانه مقررات تجاری' in row(c,'QMK-1392:6bis1')['text'] and 'قبض انبار' in row(c,'QMK-1392:6bis2')['text'],'system bis')
 q('صادرات صوری' in row(c,'QMK-1392:33bis1')['text'] and 'کارت بازرگانی' in row(c,'QMK-1392:33bis2')['text'],'article33 bis')
 q('خلاف شرع بیّن' in row(c,'QMK-1392:50bis3')['text'],'special retrial')
 q(all('(منسوخ)' not in row(c,f'QMK-1392:{key}')['text'] for key in ('2','7','50','55','66')),'nested repeals removed')
 q('متن تبصره سابق' not in row(c,'QMK-1392:73')['text'] and 'کارگروه تعامل پذیری دولت الکترونیکی' in row(c,'QMK-1392:73')['text'],'article73 current')
 q('هزار و پانصد میلیارد' in row(c,'QMK-1392:77')['text'] and 'دویست میلیارد' in row(c,'QMK-1392:77',0)['text'],'article77 history')
 q('قانون مجازات مرتکبین قاچاق' in row(c,'QMK-1392:78')['text'],'article78')
 q('ماده (۴) قانون و تبصره‌های آن حذف' in row(c,'EQMK-1400:15')['text'],'amendment article15')
 q('ماده (۵۶) قانون به شرح زیر اصلاح' in row(c,'EQMK-1400:39')['text'],'amendment article39')

 # Customs law and implementing regulations.
 q(c.execute("select count(*)from articles where article_key='QAG-1390:1'").fetchone()[0]==2,'customs art1 history')
 q('صندوق نوآوری شکوفایی' in row(c,'QAG-1390:1')['text'] and 'صندوق نوآوری شکوفایی' not in row(c,'QAG-1390:1',0)['text'],'guarantee history')
 q('واردات ماشین آلات خط تولید' in row(c,'QAG-1390:119',0)['text'] and 'واردات ماشین آلات خط تولید' not in row(c,'QAG-1390:119')['text'],'customs119 repeal')
 q('قاچاق گمرکی محسوب می‌شود' in row(c,'QAG-1390:113')['text'],'customs smuggling')
 q(row(c,'AIAG-1391:189bis')['article_no']=='۱۸۹ مکرر' and 'تأسیسات گردشگری' in row(c,'AIAG-1391:189bis')['text'],'customs 189bis')
 q('ورود موقت برای پردازش' in row(c,'AIAG-1391:87')['text'],'customs bylaw87')
 q('سامانه جامع تجارت' in row(c,'AIQK-56-1395:3')['text'] and 'سامانه ارزی' in row(c,'AIQK-56-1395:5')['text'],'systems bylaw')
 q('سامانه یکپارچه اموال تملیکی' in row(c,'AIQK-5556-1401:18')['text'] and 'لغو می‌شود' in row(c,'AIQK-5556-1401:25')['text'],'disposal bylaw')

 # Binding rulings and temporal interaction.
 q('صلاحیت دادسرا و دادگاه انقلاب' in row(c,'RVR-736-1393:decision')['text'],'ruling736')
 q('صلاحیّت دادگاه کیفری دو' in row(c,'RVR-839-1402:decision')['text'] and 'ناسخ رأی وحدت رویه ۸۰۹' in row(c,'RVR-839-1402:decision')['text'],'ruling839')
 q('مابه التفاوت نرخ ارز' in row(c,'RVR-878-1405:decision')['text'] and 'سازمان تعزیرات حکومتی' in row(c,'RVR-878-1405:decision')['text'],'ruling878')

 ph=','.join('?'*len(d));rows=c.execute(f'select article_no,text from articles where document_id in ({ph})',tuple(d.values())).fetchall()
 q(all(x['text'].strip() for x in rows),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii number');q(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] and '�' not in x['text'] for x in rows),'leak/filler')
 for term in ('قاچاق ارز','کالای ممنوع','قاچاقچی حرفه‌ای','سامانه جامع تجارت','تعهدات ارزی','تشریفات گمرکی','حقوق ورودی','ورود موقت برای پردازش','اموال تملیکی','صلاحیّت دادگاه کیفری دو'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==59,'relations')
 q(c.execute('select count(*)from relations where from_document_id=? and relation_type="amends"',(d['EQMK-1400'],)).fetchone()[0]==42,'amend links')
 q(c.execute('select count(*)from relations where from_document_id in (?,?,?) and relation_type="interprets"',(d['RVR-736-1393'],d['RVR-839-1402'],d['RVR-878-1405'])).fetchone()[0]==6,'ruling links')
 q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=row(c,'QMK-1392:2bis')['id'];did=d['QMK-1392'];c.close()
 for args in (['stats'],['show',str(did)],['history','QMK-1392:2'],['history','QMK-1392:77'],['history','QAG-1390:1'],['search','قاچاق ارز'],['search','تشریفات گمرکی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);q(p.returncode==0 and p.stdout.strip(),'query '+' '.join(args)+' '+p.stderr)
 cl=app.test_client();pages=['/','/?q=قاچاق+ارز','/?q=تشریفات+گمرکی','/types','/by-type/law','/by-type/amendment','/by-type/regulation','/by-type/unified_ruling']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for page in pages:q(cl.get(page).status_code==200,'flask '+page)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_customs_smuggling.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity')
 q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'duplicate refs')
 q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] Anti-smuggling=89 structural keys/121 rows (87 current, 34 historical); reform act=47')
 print('[OK] Customs law=165/167 rows; customs bylaw=222; systems bylaw=46; disposal bylaw=25; unified rulings=3')
 print('[OK] Coverage, histories, Persian numbers, FTS5, 59 relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
