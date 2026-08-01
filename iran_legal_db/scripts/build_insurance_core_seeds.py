# -*- coding: utf-8 -*-
"""Build core insurance statutes and three generations of compulsory third-party insurance."""
from __future__ import annotations
import pprint,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'data'/'source_cache';OUT=ROOT/'data'/'seed'/'insurance_core.py'
F2A=str.maketrans('۰۱۲۳۴۵۶۷۸۹','0123456789');A2F=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
def clean(s):
 s=re.sub(r'(?m)^\s*\[(?:آیین|دستورالعمل)[^]]*\]\([^)]+\)\s*$','',s)
 s=re.sub(r'!\[[^]]*\]\([^)]+\)','',s);s=re.sub(r'\[\[[^]]+\]\]\([^)]+\)','',s);s=re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('\\-','-').replace('\ufeff','').replace('\u200e','‌').replace('\u200f','‌').replace('\u00ad','‌')
 for a,b in {'ي':'ی','ى':'ی','ك':'ک','ة':'ه','هیات':'هیأت','مسوول':'مسئول','مسؤول':'مسئول','موسسات':'مؤسسات','موسسه':'مؤسسه','آئین':'آیین','بیمه گذار':'بیمه‌گذار','بیمه گر':'بیمه‌گر','بیمه نامه':'بیمه‌نامه','می باشد':'می‌باشد','می شود':'می‌شود','می گردد':'می‌گردد','می نماید':'می‌نماید','لازم الاجرا':'لازم‌الاجرا','تامین':'تأمین','زیان دیده':'زیان‌دیده','شورایعالی':'شورای عالی','حق بیمه':'حق‌بیمه','بمنظور':'به منظور','بعهده':'به عهده','بموجب':'به موجب','بعمل':'به عمل','میباشد':'می‌باشد','میشود':'می‌شود','نموده است':'کرده است'}.items():s=s.replace(a,b)
 s=re.sub(r'(?m)^>\s?','',s);s=re.sub(r'(?m)^#{1,6}\s*.*$','',s);s=re.sub(r'\[\]\([^)]*\)','',s);s=re.sub(r'(?m)^\s*\*\s*\*\s*\*\s*$','',s)
 s=re.sub(r'[ \t]*‌[ \t]*','‌',s);s=re.sub(r'[ \t]+',' ',s);s=re.sub(r' *\n *','\n',s);s=re.sub(r'\n{3,}','\n\n',s)
 return s.translate(A2F).strip(' ‌\n-*')
def norm(l):return re.sub(r'\s+',' ',re.sub(r'\[([^]]*)\]\([^)]+\)',r'\1',l).replace('*','').replace('‌',' ').replace('ـ','-')).strip()
def parse_seq_text(text,start,end,occurrence=0):
 lines=text.splitlines();heads=[]
 for i,l in enumerate(lines):
  m=re.match(r'^ماده\s*([۰-۹0-9]+)(?![۰-۹0-9])\s*[-–]?',norm(l))
  if m:heads.append((int(m.group(1).translate(F2A)),i))
 out=[]
 for n in range(start,end+1):
  choices=[(idx,pos) for idx,(no,pos) in enumerate(heads) if no==n]
  if len(choices)<=occurrence:raise ValueError(f'missing article {n} occurrence {occurrence}')
  idx,b=choices[occurrence];e=heads[idx+1][1] if idx+1<len(heads) else len(lines);t=clean('\n'.join(lines[b:e]));t=re.sub(r'^ماده\s*[۰-۹]+\s*[-–ـ]?\s*','',t,count=1)
  for z in ('قانون فوق مشتمل','این قانون که مشتمل','رئیس مجلس','### تازه','مطالب مرتبط','منبع:'):
   if z in t:t=t.split(z,1)[0].strip()
  out.append((str(n),t))
 return tuple(out)
def parse_seq(path,start,end,occurrence=0):return parse_seq_text(path.read_text(),start,end,occurrence)
def parse_central():
 s=(CACHE/'central_insurance_law_1350.md').read_text();pat=re.compile(r'\*\*ماده\s*(?:\*+)?\s*([۰-۹0-9]+)(?:\*+)?\s*[-–ـ]?(?:\*+)?');h=list(pat.finditer(s));out=[]
 if [int(m.group(1).translate(F2A)) for m in h]!=list(range(1,78)):raise ValueError('central insurance coverage')
 for i,m in enumerate(h):
  n=i+1;e=h[i+1].start() if i+1<len(h) else len(s);t=clean(s[m.start():e]);t=re.sub(r'^ماده\s*[۰-۹]+\s*[-–ـ]?\s*','',t,count=1);t=re.sub(r'(?:قسمت|فصل|بخش)\s*(?:اول|دوم|سوم|چهارم|پنجم|ششم|هفتم).*$', '',t,flags=re.S).strip();t=t.split('قانون فوق مشتمل',1)[0].strip().lstrip('. ');out.append((str(n),t))
 return tuple(out)
AMEND_1353='''ماده‌واحده- مواد (۲۸) و (۳۵) قانون تأسیس بیمه مرکزی ایران و بیمه‌گری مصوب ۱۳۵۰/۳/۳۰ به شرح زیر اصلاح می‌شود:\nالف- ماده ۲۸- بیمه مرکزی ایران مجاز خواهد بود که موجودی‌های نقدی خود را به‌صورت حساب جاری و یا سپرده نزد بانک ملی ایران نگهداری نماید یا براساس بودجه مصوب از محل سرمایه و ذخایر و اندوخته‌های خود و صندوق تأمین خسارت‌های بدنی تا مبلغ یکصد میلیون ریال در هر سال با تصویب هیأت عامل و مازاد بر آن با تصویب مجمع عمومی به هر نوع عملیات دیگر از جمله خرید سهام و مشارکت در بانک‌ها و شرکت‌های دیگر با حق فروش و انتقال آنها که برای توسعه و پیشرفت وظایف بیمه مرکزی ضروری یا مفید باشد مبادرت نماید.\nب- ماده ۳۵- واگذاری سهام مؤسسات بیمه ایرانی غیردولتی به اشخاص حقیقی یا حقوقی تبعه خارج تا بیست درصد با موافقت بیمه مرکزی ایران مجاز است و بیش از آن موکول به پیشنهاد بیمه مرکزی ایران و تأیید شورای عالی بیمه و تصویب هیأت وزیران خواهد بود. در مورد اخیر انتقال سود سهام سهامداران خارجی در هر سال نباید از دوازده درصد مجموع سرمایه پرداخت‌شده و سود انتقال‌نیافته سال‌های قبل تجاوز نماید.\nتبصره- انتقال سهام مؤسسات بیمه ایرانی به دولت‌های خارجی یا انتقال بیش از چهل و نه درصد سهام آنها به اشخاص حقیقی یا حقوقی خارجی مطلقاً ممنوع است. انتقال سهام بین سهامداران اتباع خارجی باید با موافقت قبلی بیمه مرکزی ایران صورت گیرد.'''
def main():
 insurance=parse_seq(CACHE/'insurance_law_1316.md',1,36);central=parse_central();third=parse_seq(CACHE/'third_party_law_1395.md',1,66)
 combo=(CACHE/'third_party_law_1387.md').read_text();starts=[m.start() for m in re.finditer(r'(?m)^ماده[‌\s]*[۱1]\s*[-ـ]',combo)];split=starts[1];old47=list(parse_seq_text(combo[:split],1,14,0));old47[-1]=(old47[-1][0],re.split(r'\n(?:قانون اصلاح|این قانون)',old47[-1][1],maxsplit=1)[0].strip());old47=tuple(old47);old87=parse_seq_text(combo[split:],1,30,0)
 vals={'INSURANCE_LAW':insurance,'CENTRAL_INSURANCE_LAW':central,'CENTRAL_AMENDMENT_1353':clean(AMEND_1353),'THIRD_PARTY_1395':third,'THIRD_PARTY_1387':old87,'THIRD_PARTY_1347':old47}
 head='# -*- coding: utf-8 -*-\n"""Generated core insurance and compulsory third-party statutes."""\n# Generated by scripts/build_insurance_core_seeds.py.\n\n';OUT.write_text(head+''.join(f'{k} = {pprint.pformat(v,width=120,sort_dicts=False)}\n\n' for k,v in vals.items()))
 print('[OK] Insurance=36; Central Insurance=77; amendment=1; Third-party=66; former laws=30+14 historical')
 print(f'[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
