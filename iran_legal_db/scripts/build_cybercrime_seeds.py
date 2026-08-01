# -*- coding: utf-8 -*-
"""Build static seeds for the cybercrime and electronic-evidence package.

The script reads cached, human-readable copies of the sources.  It does not
perform network access, so rebuilding the seed is deterministic.
"""
from __future__ import annotations

import pprint
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "source_cache"
OUT = ROOT / "data" / "seed" / "cybercrime_law.py"
PERSIAN_TO_ASCII = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ASCII_TO_PERSIAN = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_int(value: str) -> int:
    return int(value.translate(PERSIAN_TO_ASCII))


def fa_money(value: int) -> str:
    return f"{value:,}".translate(ASCII_TO_PERSIAN).replace(",", "٬")


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("_", "")
    text = text.replace("\\-", "-").replace("\\[", "[").replace("\\]", "]")
    return text.strip()


def clean_text(text: str) -> str:
    replacements = {
        "\u200e": "‌", "\u200f": "‌", "\ufeff": "", "‎": "‌", "‏": "‌",
        "ي": "ی", "ك": "ک", "ة": "ه",
        "سعات رسمی": "ساعت رسمی", "فنآوری": "فناوری", "فنآوری": "فناوری",
        "تفتیض": "تفتیش", "تویقف": "توقیف", "درخوا��ت": "درخواست",
        "برو مراتب": "برود، مراتب", "نباشدف": "نباشد،", "حی اجرای": "حین اجرای",
        "استفرار": "استقرار", "مگر ان که": "مگر آنکه", "حفظ فوری ان ": "حفظ فوری آن ",
        "وضعتیت": "وضعیت", "مشخاص": "مشخصات", "جمع‌آوری اداله": "جمع‌آوری ادله",
        "وطول مدت": "طول مدت", "صدمیلیون": "صد میلیون", "ازخدمت": "از خدمت",
        "هردو": "هر دو", "سایرجرائمی": "سایر جرائمی", "قرارمی": "قرار می",
        "مسؤول": "مسئول", "رییس": "رئیس", "آئین": "آیین",
        "سامانه‌رایانه": "سامانه رایانه", "مقام‌قضائی": "مقام قضائی",
        "جزای‌نقدی": "جزای نقدی", "قوه‌قضاییه": "قوه قضاییه",
        "سازمان‌صدا": "سازمان صدا", "داده های‌رایانه": "داده‌های رایانه",
        "آسیب‌داده‌ها": "آسیب داده‌ها", "مگر ان‌که": "مگر آنکه",
        "فن‌آوری": "فناوری", "بی احتیاطی": "بی‌احتیاطی", "بی مبالاتی": "بی‌مبالاتی",
        "کارگروه(کمیته)": "کارگروه (کمیته)",
        "سامانه های‌رایانه": "سامانه‌های رایانه", "ارائه دهندگان": "ارائه‌دهندگان",
        "رایانه ای": "رایانه‌ای", "سامانه های ": "سامانه‌های ", "داده های ": "داده‌های ",
        "حامل های ": "حامل‌های ", "مجازات های ": "مجازات‌های ", "وب سایت": "وب‌سایت",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s*\(اصلاحی[^)]*\)", "", text)
    text = re.sub(r"‌+", "‌", text)
    text = re.sub(r"\s*‌\s*", "‌", text)
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_grouped_numbers(text: str) -> str:
    """Normalize printed monetary figures without touching dates or article refs."""
    pattern = re.compile(r"(?<![۰-۹0-9])[۰-۹0-9]{1,3}(?:\s*[./٬،]\s*[۰-۹0-9]{1,3}){1,4}(?![۰-۹0-9])")

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        groups = re.findall(r"[۰-۹0-9]+", raw)
        # Dates such as 19/4/1373 have a four-digit component and are not money.
        if any(len(g) > 3 for g in groups):
            return raw
        ascii_groups = [g.translate(PERSIAN_TO_ASCII) for g in groups]
        # RTL copies sometimes expose 20,000,000 as 000/000/20.
        if ascii_groups[0] == "000" and ascii_groups[-1] != "000":
            ascii_groups.reverse()
        try:
            value = int("".join(x.zfill(3) if i else x for i, x in enumerate(ascii_groups)))
        except ValueError:
            return raw
        if value < 100_000:
            return raw
        return fa_money(value)

    text = pattern.sub(repl, text)
    # Remove redundant amount words around an unambiguous parenthetical figure.
    amount_words = (
        "یک|دو|پنج|شش|ده|پانزده|بیست|بیست و پنج|چهل|پنجاه|شصت|هشتاد|"
        "یکصد|صد|دویست|دویست و پنجاه|سیصد|یک میلیارد"
    )
    text = re.sub(
        rf"(?:{amount_words})\s+(?:میلیون|میلیارد)?\s*\(([۰-۹]+(?:٬[۰-۹]{{3}})+)\)\s*ریال",
        r"\1 ریال",
        text,
    )
    return text


def parse_articles(path: Path, wanted: set[int], bold: bool = False) -> dict[int, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    articles: dict[int, list[str]] = {}
    current: int | None = None
    for raw in lines:
        line = strip_markdown(raw)
        match = re.match(r"^ماده\s+([۰-۹0-9]+)(?:\s*\([^)]*\))?\s*[–ـ-]\s*(.*)$", line)
        if match:
            number = fa_int(match.group(1))
            current = number if number in wanted else None
            if current is not None:
                articles[current] = []
                if match.group(2).strip():
                    articles[current].append(match.group(2).strip())
            continue
        if current is None or not line:
            continue
        if line.startswith("#") or re.match(r"^(بخش|فصل|مبحث)\s", line):
            continue
        if line.startswith("جزای نقدی مندرج در این") and "۱۴۰۳" in line:
            continue
        if line.startswith("قانون فوق مشتمل") or line.startswith("رئیس مجلس") or line.startswith("صادق آملی"):
            current = None
            continue
        articles[current].append(line)
    missing = sorted(wanted - set(articles))
    if missing:
        raise ValueError(f"missing articles in {path.name}: {missing}")
    return {
        n: normalize_grouped_numbers(clean_text("\n".join(parts)))
        for n, parts in articles.items()
    }


MONEY_1388 = {
    1: (5_000_000, 20_000_000), 2: (10_000_000, 40_000_000),
    3: (20_000_000, 60_000_000), 4: (10_000_000, 40_000_000),
    5: (5_000_000, 40_000_000), 6: (20_000_000, 100_000_000),
    8: (10_000_000, 40_000_000), 9: (10_000_000, 40_000_000),
    10: (5_000_000, 20_000_000),
    12: (1_000_000, 20_000_000, 5_000_000, 20_000_000),
    13: (20_000_000, 100_000_000),
    14: (5_000_000, 40_000_000, 1_000_000, 5_000_000),
    15: (5_000_000, 20_000_000, 2_000_000, 5_000_000, 5_000_000, 20_000_000),
    16: (5_000_000, 40_000_000), 17: (5_000_000, 40_000_000),
    18: (5_000_000, 40_000_000),
    21: (20_000_000, 100_000_000, 100_000_000, 1_000_000_000),
    23: (20_000_000, 100_000_000, 100_000_000, 1_000_000_000),
    24: (100_000_000, 1_000_000_000), 25: (5_000_000, 20_000_000),
}
MONEY_1399 = {
    1: (20_000_000, 80_000_000), 2: (25_000_000, 150_000_000),
    3: (60_000_000, 180_000_000), 4: (25_000_000, 150_000_000),
    5: (15_000_000, 100_000_000), 6: (50_000_000, 250_000_000),
    8: (50_000_000, 250_000_000), 9: (25_000_000, 100_000_000),
    10: (20_000_000, 80_000_000),
    12: (6_000_000, 50_000_000, 20_000_000, 80_000_000),
    13: (50_000_000, 250_000_000),
    14: (15_000_000, 100_000_000, 5_000_000, 20_000_000),
    15: (20_000_000, 80_000_000, 5_000_000, 20_000_000, 20_000_000, 80_000_000),
    16: (15_000_000, 100_000_000), 17: (20_000_000, 150_000_000),
    18: (20_000_000, 150_000_000),
    21: (60_000_000, 250_000_000, 100_000_000, 1_000_000_000),
    23: (60_000_000, 250_000_000, 100_000_000, 1_000_000_000),
    24: (100_000_000, 1_000_000_000), 25: (20_000_000, 80_000_000),
}
MONEY_1403 = {
    1: (66_000_000, 264_000_000), 2: (82_500_000, 500_000_000),
    3: (200_000_000, 600_000_000), 4: (82_500_000, 500_000_000),
    5: (50_000_000, 330_000_000), 6: (165_000_000, 825_000_000),
    8: (82_500_000, 330_000_000), 9: (82_500_000, 330_000_000),
    10: (66_000_000, 264_000_000),
    12: (20_000_000, 165_000_000, 66_000_000, 264_000_000),
    13: (165_000_000, 825_000_000),
    14: (50_000_000, 330_000_000, 16_500_000, 66_000_000),
    15: (66_000_000, 264_000_000, 16_500_000, 66_000_000, 66_000_000, 264_000_000),
    16: (50_000_000, 330_000_000), 17: (66_000_000, 500_000_000),
    18: (66_000_000, 500_000_000),
    21: (200_000_000, 825_000_000, 330_000_000, 3_300_000_000),
    23: (200_000_000, 825_000_000, 330_000_000, 3_300_000_000),
    24: (330_000_000, 3_300_000_000), 25: (66_000_000, 264_000_000),
}


def replace_money_sequence(text: str, old: tuple[int, ...], new: tuple[int, ...]) -> str:
    if len(old) != len(new):
        raise ValueError("money sequence size mismatch")
    tokens = re.findall(r"[۰-۹]{1,3}(?:٬[۰-۹]{3})+", text)
    expected = [fa_money(x) for x in old]
    if tokens != expected:
        raise ValueError(f"money mismatch\nexpected={expected}\nfound={tokens}\n{text}")
    iterator = iter(new)
    return re.sub(r"[۰-۹]{1,3}(?:٬[۰-۹]{3})+", lambda _m: fa_money(next(iterator)), text)


def main() -> None:
    # The Shenasname copy exposes standalone numbering 1-56 and the 1399 figures.
    law_1399 = parse_articles(CACHE / "cybercrime_law_1399.md", set(range(1, 57)))
    law_original = dict(law_1399)
    law_current = dict(law_1399)
    for number in MONEY_1399:
        law_original[number] = replace_money_sequence(law_1399[number], MONEY_1399[number], MONEY_1388[number])
        law_current[number] = replace_money_sequence(law_1399[number], MONEY_1399[number], MONEY_1403[number])

    # Article 16 also received a statutory imprisonment reduction in May 1399.
    old_prison = "حبس از نود و یک روز تا دو سال"
    reduced_prison = "حبس از چهل و پنج روز و دوازده ساعت تا یک سال"
    if old_prison not in law_1399[16]:
        raise ValueError("article 16 imprisonment phrase not found")
    art16_reduction = law_original[16].replace(old_prison, reduced_prison)
    law_1399[16] = law_1399[16].replace(old_prison, reduced_prison)
    law_current[16] = law_current[16].replace(old_prison, reduced_prison)

    # Full relevant electronic-procedure sections plus repeal/effective clauses.
    proc_numbers = set(range(649, 688)) | {698, 699}
    procedure_original = parse_articles(
        CACHE / "criminal_procedure_cyber_1393.md", proc_numbers, bold=True
    )
    procedure_1399 = dict(procedure_original)
    procedure_current = dict(procedure_original)
    procedure_replacements = {
        660: ("از بیست تا دویست میلیون ریال", "از ۳۰٬۰۰۰٬۰۰۰ تا ۳۰۰٬۰۰۰٬۰۰۰ ریال", "از ۱۰۰٬۰۰۰٬۰۰۰ تا ۱٬۰۰۰٬۰۰۰٬۰۰۰ ریال"),
        661: ("از ده تا صد میلیون ریال", "از ۱۵٬۰۰۰٬۰۰۰ تا ۱۵۰٬۰۰۰٬۰۰۰ ریال", "از ۵۰٬۰۰۰٬۰۰۰ تا ۵۰۰٬۰۰۰٬۰۰۰ ریال"),
        669: ("از پنج تا ده میلیون ریال", "از ۱۰٬۰۰۰٬۰۰۰ تا ۲۰٬۰۰۰٬۰۰۰ ریال", "از ۳۳٬۰۰۰٬۰۰۰ تا ۶۶٬۰۰۰٬۰۰۰ ریال"),
    }
    for number, (old, mid, current) in procedure_replacements.items():
        if old not in procedure_original[number]:
            raise ValueError(f"procedure amount phrase missing: {number}")
        procedure_1399[number] = procedure_original[number].replace(old, mid)
        procedure_current[number] = procedure_original[number].replace(old, current)

    bylaw = parse_articles(CACHE / "electronic_evidence_bylaw_1393.md", set(range(1, 49)))
    missing_note = "تبصره- چنانچه برای نگهداری و مراقبت مدت بیشتری مورد نیاز باشد، مدت مذکور به صورت مستدل توسط مقام قضایی تمدید می‌شود."
    if missing_note not in bylaw[41]:
        bylaw[41] = bylaw[41].rstrip() + "\n" + missing_note

    ruling = (
        "نظر به اینکه در صلاحیت محلی، اصل صلاحیت دادگاه محل وقوع جرم است و این اصل در قانون جرایم رایانه‌ای نیز ـ مستفاد از ماده ۲۹ ـ مورد تأکید قانونگذار قرار گرفته، بنابراین در جرم کلاهبرداری مرتبط با رایانه، هرگاه تمهید مقدمات و نتیجه حاصل از آن در حوزه‌های قضایی مختلف صورت گرفته باشد، دادگاهی که بانک افتتاح‌کننده حساب زیان‌دیده از بزه که پول به طور متقلبانه از آن برداشت شده در حوزه آن قرار دارد، صالح به رسیدگی است. بنا به مراتب آرای شعب یازدهم و سی و دوم دیوان عالی کشور که بر اساس این نظر صادر شده به اکثریت آرا صحیح و قانونی تشخیص داده و تأیید می‌گردد. این رأی طبق ماده ۲۷۰ قانون آیین دادرسی دادگاه‌های عمومی و انقلاب در امور کیفری در موارد مشابه برای شعب دیوان عالی کشور و دادگاه‌ها لازم‌الاتباع است."
    )
    opinion = (
        "اولاً، ملاک تحقق بزه موضوع ماده ۷۴۱ قانون مجازات اسلامی مصوب ۱۳۷۵ ـ الحاقی ۱۳۸۸/۳/۵ (ماده ۱۳ قانون جرایم رایانه‌ای مصوب ۱۳۸۸) این است که «وجه یا مال یا منفعت یا خدمات یا امتیازات» با استفاده غیرمجاز از سامانه‌های رایانه‌ای یا مخابراتی و با ارتکاب اعمالی از قبیل وارد کردن، تغییر، محو، ایجاد، متوقف کردن داده‌ها یا مختل کردن سامانه‌ها تحصیل گردد؛ وگرنه اگر کسی بدون ارتکاب چنین اعمالی ولی با استفاده از سامانه‌های رایانه‌ای یا مخابراتی موجب فریب فرد یا افرادی گردد و مالی از آنان تحصیل نماید، موضوع از مصادیق کلاهبرداری ماده یک قانون تشدید مجازات مرتکبین ارتشاء و اختلاس و کلاهبرداری خواهد بود. به عنوان مثال، چنانچه فردی با استفاده از سامانه‌های رایانه‌ای یا مخابراتی به قصد فریب، با امیدوار کردن به امر واهی، افراد شرکت‌کننده در قرعه‌کشی واهی را فریب دهد و از این طریق وجوه آنان را تصاحب کند، موضوع از مصادیق بزه ماده یک قانون تشدید مجازات مرتکبین ارتشاء و اختلاس و کلاهبرداری خواهد بود. بنا به مراتب فوق و با لحاظ آنکه ارزهای الکترونیک واجد ارزش عرفی و مال تلقی می‌شود، رفتار ارتکابی با تحقق شرایط حسب مورد می‌تواند از مصادیق ماده ۷۴۱ فوق‌الاشعار یا ماده یک قانون تشدید مجازات مرتکبین ارتشاء، اختلاس و کلاهبرداری تلقی شود.\n\nثانیاً، با عنایت به مقررات مربوط از جمله ماده ۳۱۲ قانون مدنی و ماده ۷۴۱ قانون مجازات اسلامی (ماده ۱۳ قانون جرایم رایانه‌ای مصوب ۱۳۸۸)، معادل آنچه از کیف پول الکترونیکی برده شده است باید به مالباخته مسترد شود؛ از آنجا که مال موضوع سؤال مثلی تلقی می‌شود، دادگاه باید حکم به پرداخت ارز دیجیتال صادر کند و در صورت امتناع، با عنایت به اینکه معامله ارزهای دیجیتال بر اساس مقررات بانک مرکزی و تصویب‌نامه شماره ۵۸۱۴۴/ت۵۵۶۳۷هـ مورخ ۱۳۹۸/۵/۶ هیئت وزیران در مبادلات داخلی رسمیت ندارد، توقیف و فروش آن به وسیله اجرای احکام ممکن نیست؛ بنابراین در حکم مالی است که به آن دسترسی نیست و با توجه به ملاک ماده ۴۶ قانون اجرای احکام مدنی مصوب ۱۳۵۶، قیمت آن به تراضی طرفین و در صورت عدم تراضی، بهای آن به قیمت یوم‌الاداء به وسیله کارشناس و خبره محاسبه و از محکوم‌علیه وصول و به محکوم‌له پرداخت می‌شود."
    )

    header = '''# -*- coding: utf-8 -*-\n"""Generated static legal texts for the cybercrime/electronic-evidence package."""\n# Generated by scripts/build_cybercrime_seeds.py from cached sources.\n\n'''
    values = {
        "CYBER_ORIGINAL_1388": tuple(sorted(law_original.items())),
        "CYBER_FINE_1399": {n: law_1399[n] for n in MONEY_1399},
        "CYBER_CURRENT_1403": tuple(sorted(law_current.items())),
        "CYBER_ART16_REDUCTION_1399": art16_reduction,
        "CYBER_FINE_ARTICLES": tuple(MONEY_1399),
        "CYBER_REPEALED_PROCEDURE": tuple(range(28, 52)),
        "ELECTRONIC_PROCEDURE_ORIGINAL_1393": tuple(sorted(procedure_original.items())),
        "ELECTRONIC_PROCEDURE_FINE_1399": {n: procedure_1399[n] for n in procedure_replacements},
        "ELECTRONIC_PROCEDURE_CURRENT_1403": tuple(sorted(procedure_current.items())),
        "ELECTRONIC_PROCEDURE_FINE_ARTICLES": tuple(procedure_replacements),
        "ELECTRONIC_EVIDENCE_BYLAW_1393": tuple(sorted(bylaw.items())),
        "UNIFIED_RULING_729": ruling,
        "ADVISORY_1402_679": opinion,
    }
    body = "".join(
        f"{name} = {pprint.pformat(value, width=120, sort_dicts=False)}\n\n"
        for name, value in values.items()
    )
    OUT.write_text(header + body, encoding="utf-8")
    print(f"[OK] cybercrime original/current: {len(law_original)}/{len(law_current)} articles")
    print(f"[OK] electronic procedure: {len(procedure_current)} provisions; evidence bylaw: {len(bylaw)} articles")
    print(f"[OK] wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
