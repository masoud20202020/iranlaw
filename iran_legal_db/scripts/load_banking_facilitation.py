# -*- coding: utf-8 -*-
import os,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'scripts')]
from schema import get_connection
from importer import add_article,add_tag,get_or_create_document,link_document_tag,link_document_topic
D=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹');REF='QTAB-1386';URL='https://www.ekhtebar.ir/قانون-تسهیل-اعطاء-تسهیلات-بانكی-و-كاهش/'
def main():
 l=(R/'data/source_cache/bank_facilitation_1386_new.md').read_text().splitlines();h=[]
 for i,x in enumerate(l):
  m=re.match(r'^\s*ماده\s*([۰-۹0-9]+)',x.replace('*','').replace('#','').replace('\u200c',' '));
  if m:h.append((int(m.group(1).translate(D)),i))
 c=get_connection()
 try:
  c.execute('begin');r=c.execute('select id from documents where reference_code=?',(REF,)).fetchone();d=r['id'] if r else get_or_create_document(c,title='قانون تسهیل اعطای تسهیلات بانکی و کاهش هزینه‌های طرح',short_title='تسهیل تسهیلات بانکی',type_code='law',issuing_authority='مجلس شورای اسلامی',status_code='in_force',ratification_date='2007-06-26',effective_date='2007-06-26',reference_code=REF,notes='متن کامل ۹ ماده.')
  for q in ('delete from relations where from_document_id=?','delete from articles_fts where document_id=?','delete from articles where document_id=?','delete from document_tags where document_id=?','delete from document_topics where document_id=?'):c.execute(q,(d,))
  link_document_topic(c,d,'حقوق تجارت')
  for z in ('تسهیلات بانکی','وثایق بانکی','تأمین مالی تولید'):link_document_tag(c,d,add_tag(c,z))
  for j,(n,b) in enumerate(h):
   e=h[j+1][1] if j+1<len(h) else len(l);x='\n'.join(l[b:e]);x=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',x).replace('**','').replace('ي','ی').replace('ك','ک');x=re.sub(r'^ماده\s*[۰-۹0-9]+\s*[-ـ–:]?\s*','',x.strip(),1);add_article(c,d,article_no=str(n).translate(F),article_key=f'{REF}:{n}',version_no=1,is_current=1,effective_date='2007-06-26',text=re.sub(r'[ \t]+',' ',x).strip(),source_note=URL)
  c.commit();print('loaded',len(h))
 except Exception:c.rollback();raise
 finally:c.close()
if __name__=='__main__':main()
