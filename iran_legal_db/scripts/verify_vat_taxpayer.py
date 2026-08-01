# -*- coding: utf-8 -*-
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__));sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app
REFS=('QMAF-1400','QMAF-1387','QPSM-1398','QTTM-1402','QMS-1404','AIM14-1403','AIM26-1401','AIM9-1400','AIKP-1401','DAD-348-1397','DAD-2558-1400','DAD-2432139-1403')
def q(v,m):
 if not v:raise AssertionError(m)
def snap(c):return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def row(c,key,cur=1):return c.execute('select * from articles where article_key=? and is_current=?',(key,cur)).fetchone()
def main():
 c=get_connection();d={}
 for ref in REFS:
  x=c.execute('select id from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);d[ref]=x['id']
 exp={'QMAF-1400':(63,57),'QMAF-1387':(53,0),'QPSM-1398':(48,31),'QTTM-1402':(10,10),'QMS-1404':(28,28),'AIM14-1403':(12,12),'AIM26-1401':(42,42),'AIM9-1400':(3,3),'AIKP-1401':(6,6),'DAD-348-1397':(1,1),'DAD-2558-1400':(1,1),'DAD-2432139-1403':(1,1)}
 for ref,(n,cur) in exp.items():
  x=c.execute('select count(*)n,coalesce(sum(is_current),0)c from articles where document_id=?',(d[ref],)).fetchone();q((x['n'],x['c'])==(n,cur),'counts '+ref)
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QMAF-1400'],))}=={f'QMAF-1400:{n}' for n in range(1,58)},'vat coverage')
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QMAF-1387'],))}=={f'QMAF-1387:{n}' for n in range(1,54)},'old vat coverage')
 tkeys={f'QPSM-1398:{n}' for n in range(1,30)}|{'QPSM-1398:14bis','QPSM-1398:16bis'}
 q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d['QPSM-1398'],))}==tkeys,'terminal coverage')
 for ref,end in (('QTTM-1402',10),('QMS-1404',28),('AIM14-1403',12),('AIM26-1401',42),('AIM9-1400',3),('AIKP-1401',6)):
  q({x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(d[ref],))}=={f'{ref}:{n}' for n in range(1,end+1)},'coverage '+ref)
 # VAT rate history through the reliable 1405 budget.
 for k in ('7','26'):
  vs=c.execute('select version_no,is_current,effective_date,expiry_date,text from articles where article_key=? order by version_no',(f'QMAF-1400:{k}',)).fetchall();q(len(vs)==4 and vs[-1]['is_current']==1,'vat history '+k)
 q('نه‌درصد (۹%)' in c.execute("select text from articles where article_key='QMAF-1400:7' and version_no=1").fetchone()[0],'vat base rate')
 q('سال ۱۴۰۵' in row(c,'QMAF-1400:7')['text'] and 'ده درصد (۱۰٪)' in row(c,'QMAF-1400:7')['text'],'vat current rate')
 q('اصل طلا' in row(c,'QMAF-1400:26')['text'] and 'ده درصد (۱۰٪)' in row(c,'QMAF-1400:26')['text'],'gold current rate')
 q(all(x[0]==0 for x in c.execute('select is_current from articles where document_id=?',(d['QMAF-1387'],))),'old vat historical')
 q('قانون مالیات بر ارزش افزوده' in row(c,'QMAF-1400:57')['text'] and 'شش‌ماه پس از ابلاغ' in row(c,'QMAF-1400:57')['text'],'vat enactment')
 # Material terminal-law histories.
 changed=(1,2,3,5,6,10,11,12,13,14,15,19,20,22,25,26,29)
 for n in changed:q(c.execute('select count(*)from articles where article_key=?',(f'QPSM-1398:{n}',)).fetchone()[0]==2,'terminal history '+str(n))
 q('کارپوشه غیرتجاری' in row(c,'QPSM-1398:1')['text'] and 'کارپوشه غیرتجاری' not in row(c,'QPSM-1398:1',0)['text'],'terminal article1')
 q('پنج برابر فروش' in row(c,'QPSM-1398:6')['text'] and 'سه برابر فروش' in row(c,'QPSM-1398:6',0)['text'],'terminal article6')
 q('ریز تراکنش' in row(c,'QPSM-1398:11')['text'] and 'شناسه یکتا' in row(c,'QPSM-1398:11')['text'],'terminal article11')
 q('بیست و پنج برابر معافیت' in row(c,'QPSM-1398:14bis')['text'] and 'پایان سال ۱۴۰۴' in row(c,'QPSM-1398:14bis')['text'],'terminal 14bis')
 q('حداکثر بیست ماه' in row(c,'QPSM-1398:16bis')['text'] and 'کارپوشه غیرتجاری' in row(c,'QPSM-1398:16bis')['text'],'terminal 16bis')
 q('هزینه‌های دارای صورت‌حساب الکترونیکی' in row(c,'QPSM-1398:25')['text'],'terminal article25')
 q('اصل مالیات متعلق' in row(c,'QPSM-1398:22')['text'],'terminal article22')
 # Amending acts.
 q('کلیه مؤدیان اعم از حقیقی و حقوقی' in row(c,'QTTM-1402:1')['text'] and 'پایان سال ۱۴۰۵' in row(c,'QTTM-1402:10')['text'],'facilitation')
 q('قانون مالیات‌های مستقیم' in row(c,'QMS-1404:1')['text'] and 'ماده (۱۶) مکرر' in row(c,'QMS-1404:8')['text'],'spec law')
 q('مشروط به استقرار بستر اجرائی' in row(c,'QMS-1404:12')['text'] and 'بیست ماه پس از لازم‌الاجرا' in row(c,'QMS-1404:28')['text'],'spec transition')
 # Regulations.
 q('مؤدیان معاف' in row(c,'AIM14-1403:1')['text'] and 'کاربرگ' in row(c,'AIM14-1403:7')['text'] and 'اخذ مالیات بر ارزش افزوده' in row(c,'AIM14-1403:12')['text'],'14bis bylaw')
 q('شرکت معتمد' in row(c,'AIM26-1401:1')['text'] and 'سه سال' in row(c,'AIM26-1401:9')['text'] and 'آیین‌نامه موضوع ماده ۲۶' in row(c,'AIM26-1401:42')['text'],'trusted bylaw')
 q('خدمات پژوهشی' in row(c,'AIM9-1400:2')['text'] and 'خدمات ورزشی' in row(c,'AIM9-1400:2')['text'],'education bylaw')
 q('کارپوشه غیر‌فعال' in row(c,'AIKP-1401:1')['text'] and 'مسدود نماید' in row(c,'AIKP-1401:4')['text'],'inactive bylaw')
 # Divan holdings.
 q('درآمد حقوق' in row(c,'DAD-348-1397:decision')['text'] and 'ابطال می‌شود' in row(c,'DAD-348-1397:decision')['text'],'d348')
 q('پیش از پرداخت' in c.execute('select notes from documents where id=?',(d['DAD-2558-1400'],)).fetchone()[0] and 'از تاریخ تصویب ابطال' in row(c,'DAD-2558-1400:decision')['text'],'d2558')
 q('سهم و کمیسیون دریافتی شرکت' in row(c,'DAD-2432139-1403:decision')['text'] and 'ابطال نشد' in row(c,'DAD-2432139-1403:decision')['text'],'tapsi')
 ph=','.join('?'*len(d));rr=c.execute(f'select article_no,text from articles where document_id in ({ph})',tuple(d.values())).fetchall();q(all(x['text'].strip() for x in rr),'empty');q(all(not re.search(r'[0-9]',x['article_no']) for x in rr),'ascii article no');q(all('https://' not in x['text'] and '###' not in x['text'] and 'هنوز دیدگاهی' not in x['text'] and '�' not in x['text'] for x in rr),'source leak')
 for term in ('مالیات بر ارزش افزوده','اعتبار مالیاتی','صورت‌حساب الکترونیکی','سامانه مؤدیان','کارپوشه غیرتجاری','شرکت معتمد','مالیات بر عایدی سرمایه','تاکسی‌های اینترنتی'):
  n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
 q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
 q(c.execute(f'select count(*)from relations where from_document_id in ({ph})',tuple(d.values())).fetchone()[0]==29,'relations')
 q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
 before=snap(c);aid=row(c,'QMAF-1400:7')['id'];did=d['QMAF-1400'];c.close()
 for args in (['stats'],['show',str(did)],['history','QMAF-1400:7'],['history','QPSM-1398:6'],['search','صورتحساب الکترونیکی'],['search','مالیات بر عایدی سرمایه'],['search','تاکسی اینترنتی']):
  p=subprocess.run([sys.executable,os.path.join(R,'scripts/query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60);q(p.returncode==0 and p.stdout.strip(),'query '+p.stderr)
 cl=app.test_client();pages=['/','/?q=مالیات+بر+ارزش+افزوده','/?q=سامانه+مؤدیان','/?q=مالیات+بر+عایدی+سرمایه','/types','/by-type/law','/by-type/amendment','/by-type/regulation','/by-type/divan_ruling']
 for x in d.values():pages += [f'/doc/{x}',f'/doc/{x}?view=all',f'/doc/{x}?view=historical']
 pages.append(f'/article/{aid}')
 for p in pages:q(cl.get(p).status_code==200,'flask '+p)
 p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_vat_taxpayer.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);q(p.returncode==0,p.stderr)
 c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity');q(not c.execute('pragma foreign_key_check').fetchall(),'fk after');q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'dupe refs');q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current');c.close()
 print('[OK] Permanent VAT=57 numbers/63 rows; former VAT=53 historical rows')
 print('[OK] Taxpayer terminals=31 keys/48 rows; facilitation=10; speculation tax=28')
 print('[OK] Regulations=12+42+3+6; Divan rulings=3')
 print('[OK] Coverage, rates, histories, Persian numbers, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
