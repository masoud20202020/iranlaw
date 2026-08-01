# -*- coding: utf-8 -*-
import os,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'scripts')]
from schema import get_connection
from importer import add_article,add_tag,get_or_create_document,link_document_tag,link_document_topic
D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
S={'QTIJ-1370':'https://www.ekhtebar.ir/قانون-توسعه-صنعت-ایرانگردی-و-جهانگردی/','QOMCG-1382':'https://www.ekhtebar.ir/قانون-تشکیل-سازمان-میراث-فرهنگی-و-گردش/','QMRB-1398':'https://www.ekhtebar.ir/قانون-حمایت-از-مرمت-و-احیای-بافت‌های-ت/'}
def parse(f,n):
 l=(R/'data/source_cache'/f).read_text().splitlines();h=[]
 for i,x in enumerate(l):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)',x.replace('*','').replace('#','').replace('\u200c',' '));
  if m:h.append((int(m.group(1).translate(D)),i))
 o=[]
 for k in range(1,n+1):
  j=next(j for j,(a,_) in enumerate(h) if a==k);b=h[j][1];e=h[j+1][1] if j+1<len(h) else len(l);x='\n'.join(l[b:e]);x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('ي','ی').replace('ك','ک');x=re.sub(r'^ماده\s*[۰-۹0-9]+\s*[-ـ–:]?\s*','',x.strip(),1);o.append((k,re.sub(r'[ \t]+',' ',x).strip()))
 return o
def main():
 c=get_connection();sp=[('QTIJ-1370','قانون توسعه صنعت ایرانگردی و جهانگردی','توسعه صنعت گردشگری','1991-09-29','tourism.md',12),('QOMCG-1382','قانون تشکیل سازمان میراث فرهنگی و گردشگری','سازمان میراث فرهنگی و گردشگری','2003-10-27','heritage_org.md',12),('QMRB-1398','قانون حمایت از مرمت و احیای بافت‌های تاریخی ـ فرهنگی','مرمت و احیای بافت‌های تاریخی','2019-06-23','historic_restoration.md',17)]
 try:
  c.execute('begin')
  for r,t,s,date,f,n in sp:
   q=c.execute('select id from documents where reference_code=?',(r,)).fetchone();d=q['id'] if q else get_or_create_document(c,title=t,short_title=s,type_code='law',issuing_authority='مجلس شورای اسلامی',status_code='in_force',ratification_date=date,effective_date=date,reference_code=r,notes=f'متن کامل {n} ماده.')
   for x in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(x,(d,))
   link_document_topic(c,d,'حقوق عمومی')
   for z in ('گردشگری','میراث فرهنگی','آثار تاریخی','صنایع دستی'):link_document_tag(c,d,add_tag(c,z))
   for no,text in parse(f,n):add_article(c,d,article_no=str(no).translate(F),article_key=f'{r}:{no}',version_no=1,is_current=1,effective_date=date,text=text,source_note=S[r])
  c.commit();print('loaded tourism heritage',41)
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
