# -*- coding: utf-8 -*-
"""Verify municipal law, urban renewal, finance regulations and leading rulings."""
import os,re,subprocess,sys
R=os.path.dirname(os.path.dirname(__file__))
sys.path[:0]=[os.path.join(R,'scripts'),os.path.join(R,'web')]
from schema import get_connection
from app import app

REFS=('QSH-1334','QNO-1347','QDPSH-1401','AIM1-1401','AISH-1346','DAD-577-1393','DAD-1509-1399','DAD-227-1395','DAD-1310-1397')
def q(v,m):
    if not v:raise AssertionError(m)
def snap(c):
    return tuple(c.execute('select (select count(*)from documents),(select count(*)from articles),(select count(*)from articles where is_current=1),(select count(*)from articles where is_current=0),(select count(*)from relations),(select count(*)from articles_fts)').fetchone())
def row(c,key,current=1):
    return c.execute('select * from articles where article_key=? and is_current=?',(key,current)).fetchone()

def main():
    c=get_connection();docs={}
    for ref in REFS:
        x=c.execute('select id,notes from documents where reference_code=?',(ref,)).fetchone();q(x,'missing '+ref);docs[ref]=x['id']
    expected={
        'QSH-1334':(121,47),'QNO-1347':(40,33),'QDPSH-1401':(17,17),'AIM1-1401':(18,18),
        'AISH-1346':(48,48),'DAD-577-1393':(1,1),'DAD-1509-1399':(1,1),'DAD-227-1395':(1,1),'DAD-1310-1397':(1,1),
    }
    for ref,(total,current) in expected.items():
        x=c.execute('select count(*)n,sum(is_current)c from articles where document_id=?',(docs[ref],)).fetchone();q((x['n'],x['c'])==(total,current),'counts '+ref)
    for ref,start,end in (('QSH-1334',1,119),('QNO-1347',1,36),('QDPSH-1401',1,17),('AIM1-1401',1,18),('AISH-1346',1,48)):
        keys={x[0] for x in c.execute('select distinct article_key from articles where document_id=?',(docs[ref],))}
        q(keys=={f'{ref}:{n}' for n in range(start,end+1)},'coverage '+ref)

    # Municipality history and current material.
    x=c.execute("select version_no,is_current,text from articles where article_key='QSH-1334:100' order by version_no").fetchall()
    q(len(x)==2 and x[0]['is_current']==0 and x[1]['is_current']==1,'article100 versions')
    q('یازده تبصره' in c.execute("select notes from articles where article_key='QSH-1334:100' and is_current=1").fetchone()[0],'article100 note')
    q('کمیسیون' in x[1]['text'] and 'عدم احداث پارکینگ' in x[1]['text'] and 'رأی این کمیسیون قطعی است' in x[1]['text'],'article100 text')
    x101=row(c,'QSH-1334:101');q('بیست و پنج درصد' in x101['text'] and 'سند ششدانگ' in x101['text'] and 'کمیسیون ماده (۵)' in x101['text'],'article101 current')
    q(c.execute("select count(*)from articles where article_key='QSH-1334:101'").fetchone()[0]==2,'article101 history')
    q(row(c,'QSH-1334:4') is None and row(c,'QSH-1334:119') is None,'municipality repealed current')
    q(row(c,'QSH-1334:1') is not None and 'منسوخه' not in row(c,'QSH-1334:1')['text'],'nested repeal removed')
    q('۵ - رفع اختلافات صنفی' in row(c,'QSH-1334:45')['text'] and '۱ (منسوخه' not in row(c,'QSH-1334:45')['text'],'article45 current pruning')

    # Urban-renewal generations and explicit 1400 repeals.
    rate=c.execute("select version_no,is_current,text from articles where article_key='QNO-1347:2' order by version_no").fetchall()
    q(len(rate)==3 and [r['is_current'] for r in rate]==[0,0,1],'renovation rate versions')
    q('پنج در هزار' in rate[0]['text'] and 'یک درصد' in rate[1]['text'] and 'دو و نیم درصد' in rate[2]['text'],'renovation rates')
    n10old=c.execute("select text from articles where article_key='QNO-1347:10' and is_current=0").fetchone()[0];n10=row(c,'QNO-1347:10')['text']
    q('ساختمان‌های اساسی' in n10old and 'ساختمان‌های اساسی' not in n10,'article10 repeal')
    n16old=c.execute("select text from articles where article_key='QNO-1347:16' and is_current=0").fetchone()[0];n16=row(c,'QNO-1347:16')['text']
    q('نحوه تشکیل هیئت‌های ارزیابی' in n16old and 'نحوه تشکیل هیئت‌های ارزیابی' not in n16,'article16 repeal')
    for n in (18,25,26):q(row(c,f'QNO-1347:{n}') is None,'urban repealed '+str(n))
    q('نرخ عوارض نوسازی' in row(c,'QDPSH-1401:3')['text'],'sustainable law article3')
    q('طرح تفصیلی' in row(c,'QDPSH-1401:17')['text'] and 'کمیسیون ماده (۵)' in row(c,'QDPSH-1401:17')['text'],'sustainable law article17')
    q('اوراق مالی اسلامی' in row(c,'AIM1-1401:3')['text'],'new finance bylaw')
    q('آیین‌نامه فوق مشتمل' not in row(c,'AISH-1346:48')['text'],'old finance approval leak')
    q('نصاب‌های ریالی' in c.execute('select notes from documents where id=?',(docs['AISH-1346'],)).fetchone()[0],'old finance caveat')

    # Rulings and transparent summary label.
    r577=row(c,'DAD-577-1393:decision');q(r577 and r577['article_no']=='خلاصه رأی' and r577['text'].startswith('خلاصه نتیجه'),'ruling577 summary')
    q('صریحاً خلاصه' in c.execute('select notes from documents where id=?',(docs['DAD-577-1393'],)).fetchone()[0],'ruling577 doc caveat')
    q('احداث دیوار نیز عملیات ساختمانی محسوب می‌شود' in row(c,'DAD-1509-1399:decision')['text'],'ruling1509')
    q('خسارت تأخیر' in row(c,'DAD-227-1395:decision')['text'] and 'ابطال می' in row(c,'DAD-227-1395:decision')['text'],'ruling227')
    q('عوارض تفکیک و نقل و انتقال' in row(c,'DAD-1310-1397:decision')['text'] and 'تغییر کاربری املاک' in row(c,'DAD-1310-1397:decision')['text'],'ruling1310')

    placeholders=','.join('?'*len(docs));rows=c.execute(f'select article_no,text from articles where document_id in ({placeholders})',tuple(docs.values())).fetchall()
    q(all(x['text'].strip() for x in rows),'empty text')
    q(all(not re.search(r'[0-9]',x['article_no']) for x in rows),'ascii article number')
    q(all('https://' not in x['text'] and 'متن نمونه' not in x['text'] and '�' not in x['text'] for x in rows),'leak/filler/replacement')
    for term in ('کمیسیون ماده ۱۰۰','عدم احداث پارکینگ','تفکیک یا افراز','عوارض نوسازی','درآمد پایدار','اوراق مالی اسلامی','مناقصه یا مزایده','دیوارکشی','خسارت تأخیر'):
        n=c.execute('select count(*)from articles_fts f join articles a on a.id=f.article_id where articles_fts match ? and a.is_current=1',(f'"{term}"',)).fetchone()[0];q(n>0,'fts '+term)
    q(c.execute('select count(*)from articles_fts').fetchone()[0]==c.execute('select count(*)from articles').fetchone()[0],'fts parity')
    q(c.execute(f'select count(*)from relations where from_document_id in ({placeholders})',tuple(docs.values())).fetchone()[0]>=14,'relations')
    q(c.execute('select count(*)from relations where from_document_id=? and relation_type="amends"',(docs['QDPSH-1401'],)).fetchone()[0]==1,'rate relation')
    q(c.execute('select count(*)from relations where from_document_id in (?,?,?,?) and relation_type="interprets"',(docs['DAD-577-1393'],docs['DAD-1509-1399'],docs['DAD-227-1395'],docs['DAD-1310-1397'])).fetchone()[0]==4,'ruling relations')
    q(not c.execute('pragma foreign_key_check').fetchall(),'fk')
    before=snap(c);aid=x101['id'];first_doc=docs['QSH-1334'];c.close()

    for args in (['stats'],['show',str(first_doc)],['history','QSH-1334:100'],['history','QSH-1334:101'],['history','QNO-1347:2'],['search','کمیسیون ماده ۱۰۰'],['search','عوارض نوسازی']):
        p=subprocess.run([sys.executable,os.path.join(R,'scripts','query.py'),*args],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45);q(p.returncode==0 and p.stdout.strip(),'query '+' '.join(args)+' '+p.stderr)
    cl=app.test_client();pages=['/','/?q=کمیسیون+ماده+۱۰۰','/?q=عوارض+نوسازی','/types','/by-type/law','/by-type/regulation','/by-type/divan_ruling']
    for did in docs.values():pages += [f'/doc/{did}',f'/doc/{did}?view=all',f'/doc/{did}?view=historical']
    pages.append(f'/article/{aid}')
    for page in pages:q(cl.get(page).status_code==200,'flask '+page)
    p=subprocess.run([sys.executable,os.path.join(R,'scripts','load_municipal_law.py')],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180);q(p.returncode==0,p.stderr)
    c=get_connection();q(before==snap(c),'idempotency');q(c.execute('pragma integrity_check').fetchone()[0]=='ok','integrity')
    q(not c.execute('select reference_code,count(*)n from documents where reference_code is not null group by reference_code having n>1').fetchall(),'duplicate refs')
    q(not c.execute('select article_key,count(*)n from articles where is_current=1 and article_key is not null group by article_key having n>1').fetchall(),'multiple current')
    c.close()
    print('[OK] Municipality=119 numbers/121 rows (47 current, 74 historical); urban renewal=36/40 (33 current, 7 historical)')
    print('[OK] Sustainable revenue=17; financing bylaw=18; municipal financial bylaw=48; leading Divan rulings=4')
    print('[OK] Coverage, Persian numbers, histories, 1400 repeals, FTS5, relations, query.py, Flask and idempotency')
if __name__=='__main__':main()
