# -*- coding: utf-8 -*-
"""Build deterministic static seeds for the first labor-law package."""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUT = ROOT / "data" / "seed" / "labor_law.py"
FA_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def number(value: str) -> int:
    return int(value.translate(FA_TO_ASCII))


def strip_md(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("__", "").replace("\\-", "-").strip()


def clean(text: str) -> str:
    replacements = {
        "ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "هٔ",
        "\u200e": "‌", "\u200f": "‌", "‎": "‌", "‏": "‌", "\ufeff": "", "\u00ad": "",
        "ک��رفرما": "کارفرما", "بقی��": "بقیه", "یپمانکار": "پیمانکار",
        "یپشنهاد": "پیشنهاد", "برای رای": "برابر رأی", "مـأمور": "مأمور",
        "مر��ع": "مرجع", "مسوول": "مسئول", "مسوولیت": "مسئولیت",
        "آئین نامه": "آیین‌نامه", "آئین‌نامه": "آیین‌نامه", "آئین": "آیین", "هیات": "هیأت",
        "تامین اجتماعی": "تأمین اجتماعی", "بیمه بیكاری": "بیمه بیکاری",
        "بیكار": "بیکار", "كار": "کار", "كارگر": "کارگر", "كارفرما": "کارفرما",
        "مكلف": "مکلف", "می ‌": "می‌", "می  ": "می ",
        "قراردادکار": "قرارداد کار", "کارگراز": "کارگر از", "کارفرماکار": "کارفرما کار",
        "کار فرمایان": "کارفرمایان", "کاربه": "کار به", "باتوافق": "با توافق",
        "درمقابل": "در مقابل", "وبه": "و به", "استعفای ی": "استعفای وی",
        "وسایر": "و سایر", "وامثال": "و امثال", "ونظایر": "و نظایر",
        "ودر": "و در", "وحقوق": "و حقوق", "ولواحق": "و لواحق",
        "یامحل": "یا محل", "انعقادقرارداد": "انعقاد قرارداد", "درموارد": "در موارد",
        "درصورت": "در صورت", "تازمانی": "تا زمانی", "درمدت": "در مدت",
        "کارگربدون": "کارگر بدون", "درمواد": "در مواد", "مساله": "مسئله",
        "وپس": "و پس", "کارخود": "کار خود", "دریافت‌میانگین": "دریافت میانگین",
        "یا‌حضور": "یا حضور", "ذینفع": "ذی‌نفع", "صورتجلسه": "صورت‌جلسه",
        "کار پوشه": "کارپوشه", "بیماریهای": "بیماری‌های", "تشکلهای": "تشکل‌های",
        "هیأتهای": "هیأت‌های", "موسسات": "مؤسسات",
        "انظباطی": "انضباطی", "بکار": "به کار", "بعهده": "به عهده",
        "بموجب": "به موجب", "بتصویب": "به تصویب", "بشرح": "به شرح",
        "بقوت": "به قوت", "بوجوه": "به وجوه", "بشکایات": "به شکایات",
        "میباشد": "می‌باشد", "میگردد": "می‌گردد", "میشود": "می‌شود",
        "می نماید": "می‌نماید", "می گردد": "می‌گردد", "می شود": "می‌شود",
        "می باشند": "می‌باشند", "می باشد": "می‌باشد", "نمی باشد": "نمی‌باشد",
        "لازم الاجرا": "لازم‌الاجرا", "مابه التفاوت": "مابه‌التفاوت",
        "ازکارافتادگی": "ازکارافتادگی", "غیر ارادی": "غیرارادی",
        "مقرری بگیر": "مقرری‌بگیر", "ذی ربط": "ذی‌ربط", "ذیصلاح": "ذی‌صلاح",
        "هم آهنگ": "هماهنگ", "بهداشت کار": "بهداشت کار",
        "۶ /۵ /۱۳۵۹": "۶/۵/۱۳۶۹", "۶/۵/۱۳۵۹": "۶/۵/۱۳۶۹",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s*\((?:اصلاحی|الحاقی)[^)]*\)", "", text)
    text = re.sub(r"‌+", "‌", text)
    text = re.sub(r"[ \t]*‌[ \t]*", "‌", text)
    text = re.sub(r"(^|\n)‌", r"\1", text)
    text = re.sub(r"([)\]،؛:.])‌", r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    return text.strip()


def parse_articles(path: Path, wanted: set[int], stop_text: str | None = None) -> dict[int, str]:
    articles: dict[int, list[str]] = {}
    current: int | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = strip_md(raw)
        if stop_text and stop_text in line:
            current = None
            break
        match = re.match(
            r"^(?:\([^)]*\)\s*)?ماده\s*([۰-۹0-9]+)(?:\s*\([^)]*\))?\s*[ـ–-]\s*(.*)$",
            line,
        )
        if match:
            n = number(match.group(1))
            current = n if n in wanted and n not in articles else None
            if current is not None:
                articles[current] = []
                if match.group(2).strip():
                    articles[current].append(match.group(2).strip())
            continue
        if current is None or not line:
            continue
        if line.startswith("#") or re.match(r"^(فصل|مبحث)\s", line):
            continue
        if "https://" in line or "](http" in line or line.startswith("(این فصل به موجب"):
            continue
        if line.startswith(("قانون فوق", "وزیر تعاون", "وزیر کار", "رئیس مجمع", "معاون اول رئیس جمهور")):
            current = None
            continue
        articles[current].append(line)
    missing = sorted(wanted - set(articles))
    if missing:
        raise ValueError(f"missing articles in {path.name}: {missing}")
    return {n: clean("\n".join(parts)) for n, parts in articles.items()}


def drop_lines(text: str, starts: tuple[str, ...]) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith(starts)).strip()


def main() -> None:
    labor_raw = parse_articles(CACHE / "labor_law_current.md", set(range(1, 204)))
    # The source page places a separate parliamentary interpretation between arts. 13 and 14.
    labor_raw[13] = labor_raw[13].split("موضوع استفساریه:", 1)[0].strip()

    labor_current = {}
    for n, text in labor_raw.items():
        text = text.replace("وزیر کار و امور اجتماعی", "وزیر تعاون، کار و رفاه اجتماعی")
        text = text.replace("وزارت کار و امور اجتماعی", "وزارت تعاون، کار و رفاه اجتماعی")
        labor_current[n] = text

    original_history = {
        7: drop_lines(labor_raw[7], ("تبصره ۳", "تبصره ۴")),
        10: drop_lines(labor_raw[10], ("ح-", "ح ـ")),
        14: labor_raw[14].splitlines()[0]
        + "\nتبصره- مدت خدمت نظام وظیفه (ضرورت، احتیاط و ذخیره) و همچنین مدت شرکت داوطلبانه کارگران در جبهه، جزء سوابق خدمت و کار آنان محسوب می‌شود.",
        21: drop_lines(labor_raw[21], ("ز-", "ز ـ", "ح-", "ح ـ")),
    }

    procedure = parse_articles(CACHE / "labor_procedure_current.md", set(range(1, 136)))
    unemployment = parse_articles(
        CACHE / "unemployment_law_1369.md",
        set(range(1, 15)),
        stop_text="قانون بیمه بیکاری مصوب ۱۳۶۶",
    )
    unemployment_bylaw = parse_articles(
        CACHE / "unemployment_bylaw_1369.md", set(range(1, 25))
    )

    ruling_720 = (
        "مطابق مقررات مواد ۳۰، ۳۶، ۳۹ و ۴۰ قانون تأمین اجتماعی، کارفرما مسئول پرداخت حق بیمه سهم خود و بیمه‌شده در مهلت مقرر در قانون به سازمان تأمین اجتماعی است و در صورت خودداری از انجام این تکلیف، سازمان تأمین اجتماعی مکلف به وصول حق بیمه از کارفرما و ارائه خدمت به بیمه‌شده می‌باشد؛ بنابراین در صورتی که کارفرما در ایام اشتغال بیمه‌شده به تکلیف قانونی خود عمل ننماید و بیمه‌شده خواستار الزام او به انجام تکلیف پرداخت حق بیمه ایام اشتغال و پذیرش آن از سوی سازمان تأمین اجتماعی گردد، رسیدگی به موضوع در صلاحیت سازمان تأمین اجتماعی محل خواهد بود. لذا رأی شماره ۲۷ ـ ۱۳۸۸/۱/۱۱ شعبه دوم دادگاه عمومی نجف‌آباد در حد نفی صلاحیت دادگاه، که طبق رأی شماره ۰۰۱۲۶ ـ ۱۳۸۸/۴/۱ شعبه بیست و پنجم دیوان عالی کشور تأیید شده، به اکثریت آراء صحیح و منطبق با موازین قانونی تشخیص می‌گردد. این رأی طبق ماده ۲۷۰ قانون آیین دادرسی دادگاه‌های عمومی و انقلاب در امور کیفری، در موارد مشابه برای شعب دیوان عالی کشور و دادگاه‌های سراسر کشور لازم‌الاتباع است."
    )
    divan_17_20 = (
        "اولاً- تشابه در آراء محرز است.\nثانیاً- مطابق ماده ۳۷ قانون کار، پرداخت مزد به صورت روزانه یا ساعتی یا ماهانه تعیین شده است و به وجه نقد رایج کشور یا با تراضی طرفین به وسیله چک از سوی کارفرما به کارگر پرداخت خواهد شد. ضرورت وجود اسناد پرداخت منطبق با صور ساعتی، روزانه یا ماهانه اقتضا می‌کند که کارفرما نحوه پرداخت مزد و حقوق و اسناد آن را در اختیار داشته باشد و صرف اینکه کارگر با تنظیم یادداشتی اعلام کند که مزد و حقوق مربوط را دریافت کرده، بدون اینکه کارفرما اسناد مالی ناظر بر نحوه پرداخت را ارائه کند، موجد یقین بر پرداخت مزد و حقوق کارگر نخواهد بود. از این رو در هر مورد که کارفرما مدعی پرداخت مزد و حقوق و مزایا به کارگر است و سندی منتسب به کارگر ارائه می‌کند که وی مزد و حقوق خود را دریافت کرده، ارائه اسناد مثبته پرداخت این مزد و حقوق الزامی است. با توجه به مراتب، آراء مندرج در گردش کار که اسناد ناظر بر پرداخت مزد و حقوق به کارگر را برای احراز تسویه‌حساب کارفرما با کارگر لازم دانسته، صحیح و موافق مقررات تشخیص شد و در اجرای بند ۳ ماده ۱۲ و ماده ۹۰ قانون تشکیلات و آیین دادرسی دیوان عدالت اداری مصوب ۱۳۹۲، مفاد آراء مذکور با استدلال پیش‌گفته به عنوان رأی ایجاد رویه تصویب می‌شود. این رأی برای سایر شعب دیوان عدالت اداری، ادارات و اشخاص حقیقی و حقوقی مربوط لازم‌الاتباع است."
    )

    values = {
        "LABOR_CURRENT": tuple(sorted(labor_current.items())),
        "LABOR_ORIGINAL_HISTORY": original_history,
        "LABOR_HISTORY_ARTICLES": tuple(original_history),
        "LABOR_PROCEDURE_CURRENT": tuple(sorted(procedure.items())),
        "UNEMPLOYMENT_LAW": tuple(sorted(unemployment.items())),
        "UNEMPLOYMENT_BYLAW": tuple(sorted(unemployment_bylaw.items())),
        "UNIFIED_RULING_720": ruling_720,
        "DIVAN_RULING_17_20": divan_17_20,
    }
    header = '''# -*- coding: utf-8 -*-\n"""Generated static texts for the labor and unemployment-law package."""\n# Generated by scripts/build_labor_seeds.py from cached source copies.\n\n'''
    body = "".join(
        f"{name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n\n"
        for name, value in values.items()
    )
    OUT.write_text(header + body, encoding="utf-8")
    print(f"[OK] Labor Law={len(labor_current)}; histories={len(original_history)}")
    print(f"[OK] Labor procedure={len(procedure)}; unemployment law/bylaw={len(unemployment)}/{len(unemployment_bylaw)}")
    print(f"[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
