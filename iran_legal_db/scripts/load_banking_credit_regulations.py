# -*- coding: utf-8 -*-
import os,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'scripts')]
from schema import get_connection
from importer import add_article,add_relation,add_tag,get_or_create_document,link_document_tag,link_document_topic
D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def parse(fn,n):
 l=(R/'data/source_cache'/fn).read_text().splitlines();h=[]
 for i,x in enumerate(l):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)',x.replace('*','').replace('#','').replace('\u200c',' '))
  if m:h.append((int(m.group(1).translate(D)),i))
 o=[]
 for j,(k,b) in enumerate(h):
  if k>n or k in {x[0] for x in o}:continue
  e=h[j+1][1] if j+1<len(h) else len(l);x='\n'.join(l[b:e]);x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('ي','ی').replace('ك','ک');x=re.sub(r'^ماده\s*[۰-۹0-9]+\s*[-ـ–:]?\s*','',x.strip(),1);o.append((k,re.sub(r'[ \t]+',' ',x).strip()))
 assert len(o)==n,(fn,len(o));return o
def one(c,q,v):
 r=c.execute(q,(v,)).fetchone();return r['id'] if r else None
def main():
 c=get_connection(); specs=[('AEMAG-1393','آیین‌نامه نحوه تأسیس و اداره مؤسسات اعتباری غیردولتی','مؤسسات اعتباری غیردولتی','2015-01-18','credit_institutions.md',109,'https://www.ekhtebar.ir/آیین‌نامه-نحوه-تأسیس-و-اداره-مؤسسات-ا/'),('APDA-1404','آیین‌نامه اجرایی ماده ۵ قانون تأمین مالی تولید و زیرساخت‌ها درباره پایگاه داده اعتباری','پایگاه داده اعتباری','2025-05-17','credit_data.md',18,'https://www.ekhtebar.ir/آیین-نامه-اجرایی-ماده-5-قانون-تأمین-مال/')]
 try:
  c.execute('begin');ds={}
  for r,t,s,date,f,n,u in specs:
   d=one(c,'select id from documents where reference_code=?',r)
   if not d:d=get_or_create_document(c,title=t,short_title=s,type_code='regulation',issuing_authority='هیئت وزیران',status_code='in_force',ratification_date=date,effective_date=date,reference_code=r,notes=f'متن کامل {n} ماده.')
   c.execute('update documents set title=?,short_title=?,type_id=?,issuing_authority_id=?,status_id=?,ratification_date=?,effective_date=?,notes=? where id=?',(t,s,one(c,'select id from document_types where code=?','regulation'),one(c,'select id from authorities where name_fa=?','هیئت وزیران'),one(c,'select id from statuses where code=?','in_force'),date,date,f'متن کامل {n} ماده.',d));ds[r]=d
   for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
   link_document_topic(c,d,'حقوق تجارت')
   for z in ('بانکداری','مؤسسه اعتباری','تسهیلات بانکی','اعتبارسنجی'):link_document_tag(c,d,add_tag(c,z))
   for no,text in parse(f,n):add_article(c,d,article_no=str(no).translate(F),article_key=f'{r}:{no}',version_no=1,is_current=1,effective_date=date,text=text,source_note=u)
  base=one(c,'select id from documents where reference_code=?','QBC-1402')
  if base:add_relation(c,ds['AEMAG-1393'],'implements',base,description='مقررات احتیاطی و نظارت مؤسسات اعتباری.')
  c.commit();print('loaded banking credit regulations',127)
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
