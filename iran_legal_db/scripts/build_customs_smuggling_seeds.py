# -*- coding: utf-8 -*-
"""Build static seeds for anti-smuggling and customs legislation."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'customs_smuggling.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')

def sm(s):
 s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
 return s.replace('**','').replace('__','').replace('\\-','-').strip()

def clean(s):
 repl={'ي':'ی','ك':'ک','ة':'ه','\ufeff':'','\u00ad':'‌','\u200e':'‌','\u200f':'‌','‎':'‌','‏':'‌','�':'ـ',
 'آئین':'آیین','هیات':'هیأت','مسوول':'مسئول','موسسات':'مؤسسات','میباشد':'می‌باشد','میشود':'می‌شود','میشوند':'می‌شوند','میگردد':'می‌گردد','میکند':'می‌کند','میتواند':'می‌تواند','می نماید':'می‌نماید','می شود':'می‌شود','می گردد':'می‌گردد','می باشد':'می‌باشد','نمی باشد':'نمی‌باشد','بموجب':'به موجب','بعهده':'به عهده','بمنظور':'به منظور','بترتیب':'به ترتیب','بموقع':'به موقع','بمیزان':'به میزان','بنام':'به نام','بوسیله':'به وسیله','لازم الاجرا':'لازم‌الاجرا','غیر منقول':'غیرمنقول','قائم مقام':'قائم‌مقام','صورت جلسه':'صورت‌جلسه','صورت مجلس':'صورت‌مجلس','ذی ربط':'ذی‌ربط','یکماه':'یک ماه','یکسال':'یک سال','یکبار':'یک بار','ششماه':'شش ماه','بهشرح':'به شرح','به‌صورتمجموعه':'به‌صورت مجموعه','بیانی‌های':'بیانیه‌ای','حمل ونقل':'حمل‌ونقل','ماشینآلات':'ماشین‌آلات','انجام مییابد':'انجام می‌یابد','رسیدگیکننده':'رسیدگی‌کننده','پروندههای':'پرونده‌های','گونهای':'گونه‌ای'}
 for a,b in repl.items():s=s.replace(a,b)
 s=re.sub(r'‌+','‌',s);s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'(^|\n)‌',r'\1',s);s=re.sub(r'([)\]،؛:.])‌',r'\1 ',s)
 s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip()

def key_for(n,bis):
 b=(bis or '').replace(' ','').replace('‌','')
 return str(n)+{'مکرر':'bis','مکرر۱':'bis1','مکرر۲':'bis2','مکرر۳':'bis3'}.get(b,'')

def article_no(key):
 m=re.match(r'(\d+)(.*)',key);n=m.group(1).translate(A2F);s=m.group(2)
 return n+{'':'','bis':' مکرر','bis1':' مکرر ۱','bis2':' مکرر ۲','bis3':' مکرر ۳'}[s]

def parse_expected(path,expected,skip_previous=False):
 arts={};cur=None;idx=0;skip_one=False
 pat=re.compile(r'^ماده[\s‌]*(?:\()?([۰-۹0-9]+)(?:\))?([\s‌]+مکرر(?:[\s‌]*[۰-۹0-9]+)?)?\s*(.*)$')
 for raw in path.read_text().splitlines():
  if re.match(r'^\s*\[[^]]+\]\([^)]+\)\s*$',raw):continue
  line=sm(raw).lstrip('‌ ');m=pat.match(line)
  if m:
   n=int(m.group(1).translate(F2A));k=key_for(n,m.group(2));rest=m.group(3)
   if idx<len(expected) and k==expected[idx]:
    cur=k;idx+=1;rest=re.sub(r'^\s*\((?:اصلاحی|الحاقی|منسوخه?|منسوخ)[^)]*\)\s*[ـ–-]?\s*','',rest).lstrip('ـ–- .')
    arts[k]=[rest] if rest else []
    skip_one=False;continue
   # A nested target article inside an amending act belongs to the current amending article.
   if cur is not None and idx<len(expected):arts[cur].append(line)
   continue
  if cur is None or not line:continue
  if skip_previous:
   if line.startswith('متن تبصره سابق'):
    skip_one=True;continue
   if skip_one:
    skip_one=False;continue
  if line.startswith(('#','* * *','### تازه','معاون اول رئیس')):continue
  if line.startswith(('قانون فوق مشتمل','قانون بالا مشتمل','رئیس مجلس شورای اسلامی','برای مطالعه قانون')):continue
  if 'https://' in line:continue
  arts[cur].append(line)
 if idx!=len(expected):raise ValueError(f'{path.name}: expected {expected[idx:idx+8]}, got {len(arts)}')
 out={k:clean('\n'.join(arts[k])) for k in expected}
 for k,v in out.items():
  if not v:raise ValueError(f'{path.name}: empty {k}')
 return out

def numbered(a,b):return [str(i) for i in range(a,b+1)]
def smuggling_keys(last):
 extras={2:['2bis'],6:['6bis1','6bis2'],18:['18bis'],25:['25bis'],33:['33bis1','33bis2'],42:['42bis'],50:['50bis1','50bis2','50bis3']}
 out=[]
 for n in range(1,last+1):out.append(str(n));out.extend(extras.get(n,[]))
 return out

def parse_amendment():
 # Main provisions are sequential 1..47; embedded replacement articles remain within each provision.
 return parse_expected(CACHE/'smuggling_amendment_1400.md',numbered(1,47))

def ruling(path,start,end):
 txt=path.read_text();part=txt.split(start,1)[1].split(end,1)[0]
 return clean(sm(part))

def main():
 current=parse_expected(CACHE/'smuggling_law_current.md',smuggling_keys(78),skip_previous=True)
 # The web consolidation places the final four clauses of article 2 after article 2 bis.
 # Restore them to article 2 according to the structure of the amending act.
 tail_marker='د- عرضه کالا به استناد حواله‌های فروش'
 if tail_marker in current['2bis']:
  head,tail=current['2bis'].split(tail_marker,1)
  current['2bis']=head.strip()
  current['2']=(current['2'].rstrip()+'\n'+tail_marker+tail).replace('\nذ- ذ –','\nذ-').replace('\nذ- ذ -','\nذ-')
 # Remove components expressly repealed by the 1400 reform from otherwise-current articles.
 for key in ('2','7','50','55','66'):
  current[key]='\n'.join(line for line in current[key].splitlines() if '(منسوخ)' not in line).strip()
 pre=parse_expected(CACHE/'smuggling_law_pre1400.md',numbered(1,18)+['18bis']+numbered(19,77))
 amendment=parse_amendment()
 customs=parse_expected(CACHE/'customs_law_current.md',numbered(1,165))
 customs_old=parse_expected(CACHE/'customs_law_original.md',numbered(1,165))
 customs_bylaw=parse_expected(CACHE/'customs_bylaw_current.md',numbered(1,189)+['189bis']+numbered(190,221))
 sys_bylaw=parse_expected(CACHE/'smuggling_bylaw_5_6.md',numbered(1,46))
 disposal=parse_expected(CACHE/'smuggling_bylaw_55_56_1401.md',numbered(1,25))
 # Current-law corrections supported by the independent consolidated source.
 smuggling_4_historical=current['4']
 smuggling_76_historical=current['76']
 # Before the 1400 reform, article 77 contained the repeal list and a financial-allocation proviso.
 old77=pre['77'];parts=re.split(r'\nتبصره[ـ-]',old77,maxsplit=1)
 old78_base=parts[0].strip();old77_finance=(parts[1].strip() if len(parts)>1 else old77)
 # Article 119 customs law: remove the expressly repealed clause from the current version.
 customs119_old=customs['119']
 customs119_current='\n'.join(x for x in customs119_old.splitlines() if not (x.startswith('غ') and 'واردات ماشین آلات خط تولید' in x)).strip()
 # Rulings: only the operative, binding section.
 r736=ruling(CACHE/'unified_ruling_736_smuggling.md','د: رأی وحدت رویه شماره 736 ـ 4 /9 /1393 هیأت عمومی دیوان عالی کشور','هیأت عمومی دیوان عالی کشور')
 r839=ruling(CACHE/'unified_ruling_839_smuggling.md','#### **ج) رأی وحدت‌ رویه شماره ۸۳۹ – ۱۴۰۲/۰۹/۱۴ هیئت‌ عمومی دیوان ‌عالی ‌کشور**','هیئت‌ عمومی دیوان‌ عالی‌ کشور')
 r878=ruling(CACHE/'unified_ruling_878_smuggling.md','#### **ج) رأی وحدت رویه شماره ۸۷۸ – ۱۴۰۵/۰۳/۲۶ هیأت عمومی دیوان عالی کشور**','رئیس هیأت عمومی دیوان عالی کشور')
 vals={
 'SMUGGLING_CURRENT':tuple((k,article_no(k),current[k]) for k in smuggling_keys(78)),
 'SMUGGLING_PRE1400':tuple((k,article_no(k),pre[k]) for k in (numbered(1,18)+['18bis']+numbered(19,77))),
 'SMUGGLING_ART4_HISTORICAL':smuggling_4_historical,'SMUGGLING_ART76_HISTORICAL':smuggling_76_historical,
 'SMUGGLING_OLD_ART77_FINANCE':old77_finance,'SMUGGLING_OLD_ART78_BASE':old78_base,
 'SMUGGLING_AMENDMENT_1400':tuple(amendment.items()),
 'CUSTOMS_LAW_CURRENT':tuple(customs.items()),'CUSTOMS_LAW_ORIGINAL':tuple(customs_old.items()),
 'CUSTOMS_ART119_OLD':customs119_old,'CUSTOMS_ART119_CURRENT':customs119_current,
 'CUSTOMS_BYLAW':tuple((k,article_no(k),customs_bylaw[k]) for k in (numbered(1,189)+['189bis']+numbered(190,221))),
 'SMUGGLING_SYSTEMS_BYLAW':tuple(sys_bylaw.items()),'SMUGGLING_DISPOSAL_BYLAW':tuple(disposal.items()),
 'RULING_736':r736,'RULING_839':r839,'RULING_878':r878,
 }
 head='# -*- coding: utf-8 -*-\n"""Generated anti-smuggling and customs legislation texts."""\n# Generated by scripts/build_customs_smuggling_seeds.py.\n\n'
 OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] anti-smuggling current=89 structural rows; pre-1400=78; amendment act=47')
 print('[OK] customs law=165; customs bylaw=222 (including article 189 bis); systems bylaw=46; disposal bylaw=25')
 print('[OK] unified rulings=736/839/878')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
