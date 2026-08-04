#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build normalized seeds from the category folders uploaded to ``data/``.

The uploaded material is a collection of TXT/HTML pages.  The canonical raw
files are kept in ``data/archive/uploaded_category_sources.tar.gz`` and restored
locally before rebuilding.  The builder uses TXT as the extraction source, groups
obvious chapter/range splits back into one document, keeps related bylaws as
separate documents, removes website chrome, extracts article boundaries when
present, and writes a reproducible seed consumed by ``load_uploaded_data.py``.

The operational database is consulted only to avoid importing a document that is
already represented by a non-uploaded stable reference.  Existing uploaded refs
(``UPL-*``) are ignored during this comparison so the builder remains safe to rerun.
"""
from __future__ import annotations

import hashlib
import pprint
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
OUTPUT = DATA_ROOT / "seed" / "uploaded_data.py"
DB_PATH = DATA_ROOT / "iran_legal.db"

ASCII_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

CATEGORY_CODES = {
    "آموزش_و_پرورش": "EDU",
    "اراضی_و_املاک": "LAND",
    "ایثارگران": "ISAAR",
    "بین_الملل": "INTL",
    "ثبت_و_اسناد": "REG",
    "حقوقی": "LEGAL",
    "حمل_و_نقل": "TRANS",
    "خانواده": "FAMILY",
    "داوری": "ARBIT",
    "شهر_و_شهرداری": "CITY",
    "مالکیت_معنوی": "IP",
    "مالی": "FIN",
    "مالیاتی": "TAX",
    "محیط_زیست": "ENV",
    "موجر_و_مستأجر": "HOUS",
    "نظامی_و_انتظامی": "MIL",
    "ورزشی": "SPORT",
    "وکالت": "BAR",
}

TOPIC_NAMES = {
    "آموزش_و_پرورش": "حقوق آموزش و پرورش",
    "اراضی_و_املاک": "حقوق اراضی و املاک",
    "ایثارگران": "حقوق ایثارگران",
    "بین_الملل": "حقوق بین‌الملل",
    "ثبت_و_اسناد": "حقوق ثبت اسناد و املاک",
    "حقوقی": "حقوق عمومی و قضایی",
    "حمل_و_نقل": "حقوق حمل‌ونقل",
    "خانواده": "حقوق خانواده",
    "داوری": "داوری و میانجی‌گری",
    "شهر_و_شهرداری": "حقوق شهرداری‌ها",
    "مالکیت_معنوی": "حقوق مالکیت فکری",
    "مالی": "حقوق مالی و بودجه",
    "مالیاتی": "حقوق مالیاتی",
    "محیط_زیست": "حقوق محیط زیست",
    "موجر_و_مستأجر": "حقوق املاک و مسکن",
    "نظامی_و_انتظامی": "حقوق نظامی و انتظامی",
    "ورزشی": "حقوق ورزش",
    "وکالت": "حقوق وکالت و کانون‌های وکلا",
}

DEFAULT_AUTHORITIES = {
    "آموزش_و_پرورش": "وزارت آموزش و پرورش",
    "اراضی_و_املاک": "وزارت دادگستری",
    "ایثارگران": "بنیاد شهید و امور ایثارگران",
    "بین_الملل": "وزارت امور خارجه",
    "ثبت_و_اسناد": "سازمان ثبت اسناد و املاک کشور",
    "حقوقی": "قوه قضائیه",
    "حمل_و_نقل": "وزارت راه و شهرسازی",
    "خانواده": "قوه قضائیه",
    "داوری": "مرجع داوری مندرج در منبع",
    "شهر_و_شهرداری": "وزارت کشور",
    "مالکیت_معنوی": "وزارت دادگستری",
    "مالی": "وزارت امور اقتصادی و دارایی",
    "مالیاتی": "وزارت امور اقتصادی و دارایی",
    "محیط_زیست": "سازمان حفاظت محیط زیست",
    "موجر_و_مستأجر": "وزارت راه و شهرسازی",
    "نظامی_و_انتظامی": "وزارت دفاع و پشتیبانی نیروهای مسلح",
    "ورزشی": "وزارت ورزش و جوانان",
    "وکالت": "قوه قضائیه",
}

ARTICLE_RE = re.compile(
    r"^\s*(?P<kind>ماده|مادّه|ماه|اصل)\s*"
    r"(?:\(?\s*(?P<number>واحده|[۰-۹0-9]+(?:\s*(?:مکرر|الحاقی)(?:\s*[۰-۹0-9]+)?)?)\s*\)?)"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)
RANGE_RE = re.compile(r"\(\s*[0-9۰-۹]+\s*-\s*[0-9۰-۹]+\s*\)")
DATE_RE = re.compile(r"(?<![0-9۰-۹])(1[12-4][0-9۰-۹]{2}|[۱۲۳۴][۰-۹]{3})\s*[/.-]\s*([0-9۰-۹]{1,2})\s*[/.-]\s*([0-9۰-۹]{1,2})")
YEAR_RE = re.compile(r"(?<![0-9۰-۹])(1[12-4][0-9۰-۹]{2}|[۱۲۳۴][۰-۹]{3})(?![0-9۰-۹])")

NAV_EXACT = {
    "صفحه اصلی", "قوانین کاربردی", "قوانین و مقررات", "درباره ما", "دریافت اپلیکیشن",
    "شبکه های اجتماعی", "ورود", "ثبت نام", "مطالب مرتبط", "تازه های قوانین", "تازه‌های قوانین",
    "ارسال دیدگاه", "ثبت دیدگاه", "نظرات کاربران", "قانون در جیب شما", "قانون درجیب شما",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("\ufeff", "").replace("\r", "")
    value = value.replace("\u00a0", " ").replace("\u00ad", "")
    value = value.replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه")
    value = value.replace("أ", "ا").replace("إ", "ا").replace("ؤ", "و")
    value = value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    value = value.replace("\u200f", "").replace("\u200e", "")
    return value


def clean_title(value: str) -> str:
    value = normalize_text(value).replace("_", " ").replace("\u200c", " ").strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" -–—:؛،")
    return value


def match_key(value: str) -> str:
    value = clean_title(value).lower().translate(ASCII_DIGITS)
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"(?:با اصلاحات|و اصلاحات|الحاقات|متن کامل|خلاصه ساختاری|با آخرین اصلاحات).*", " ", value)
    value = re.sub(r"\b(?:مصوب|سال|متن|جاری|منسوخ)\b", " ", value)
    value = value.replace("آیین نامه", "آییننامه").replace("آیین‌نامه", "آییننامه")
    value = re.sub(r"[^\w\u0600-\u06ff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def article_match(line: str):
    candidate = normalize_text(line).strip().lstrip("*#").strip()
    return ARTICLE_RE.match(candidate)


def source_url(lines: list[str]) -> str:
    for line in lines[:40]:
        if "لینک:" in line:
            return line.split("لینک:", 1)[1].strip()
    return ""


def first_article_index(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if article_match(line):
            return i
    return None


def header_title(lines: list[str], fallback: str) -> str:
    # The export repeats the page title before the date.  Looking only at this
    # short header window prevents a treaty preamble or an article body from
    # being mistaken for the document title when a page has no «ماده» heading.
    url_i = next((i for i, line in enumerate(lines[:60]) if "لینک:" in line), None)
    start = url_i + 1 if url_i is not None else 0
    end = min(len(lines), start + 45)
    candidates: list[str] = []
    for line in lines[start:end]:
        clean = clean_title(line)
        if not clean or clean in NAV_EXACT or "لینک:" in clean or set(clean) <= {"="}:
            continue
        if re.match(r"^(?:مصوب|ابلاغ|تاریخ|صفحه|قوانین|ورود|دسته)", clean):
            continue
        if len(clean) >= 4:
            candidates.append(clean)
    if candidates:
        for candidate in candidates:
            if any(token in candidate for token in ("قانون", "آیین", "اساسنامه", "مقررات", "معاهده", "کنوانسیون", "دستورالعمل", "بخشنامه", "رأی", "دادنامه", "منشور")):
                return candidate
        return candidates[-1]
    return clean_title(fallback)


def raw_date(text: str, title: str = "") -> str | None:
    # Store a Gregorian year when the source gives a Persian year.  The exact
    # Persian date remains in the source text and notes; this avoids inventing a
    # Gregorian day/month conversion for pages with incomplete dates.
    normalized = normalize_text(text + "\n" + title)
    m = DATE_RE.search(normalized)
    if not m:
        m = YEAR_RE.search(normalized)
        if not m:
            # A few international instruments identify themselves only by a
            # Gregorian convention year (1944/1945/1949/1980/1982).
            m_greg = re.search(r"(?<![0-9])(18[0-9]{2}|19[0-9]{2}|20[0-2][0-9])(?![0-9])", normalized)
            return m_greg.group(1) if m_greg else None
        year = int(m.group(1).translate(ASCII_DIGITS))
        return str(year + 621 if year >= 1200 else year)
    year = int(m.group(1).translate(ASCII_DIGITS))
    return str(year + 621 if year >= 1200 else year)


def infer_authority(category: str, title: str, text: str) -> str:
    tail = normalize_text(text[-5000:])
    checks = (
        ("شورای عالی انقلاب فرهنگی", "شورای عالی انقلاب فرهنگی"),
        ("رئیس قوه قضائیه", "رئیس قوه قضائیه"),
        ("رییس قوه قضاییه", "رئیس قوه قضائیه"),
        ("مجلس شورای اسلامی", "مجلس شورای اسلامی"),
        ("مجلس شورای ملی", "مجلس شورای ملی (پیش از انقلاب)"),
        ("هیئت وزیران", "هیئت وزیران"),
        ("هیات وزیران", "هیئت وزیران"),
    )
    for needle, authority in checks:
        if needle in tail:
            return authority
    return DEFAULT_AUTHORITIES[category]


def infer_type(title: str, category: str) -> str:
    t = clean_title(title)
    if re.search(r"(?:^|\s)(?:رأی|رای|دادنامه)(?:\s|$)", t):
        if "دیوان عدالت" in t:
            return "divan_ruling"
        return "judicial_precedent"
    if "معاهده" in t or "کنوانسیون" in t or "عهدنامه" in t or "منشور" in t:
        return "treaty"
    if "بخشنامه" in t:
        return "circular"
    if "دستورالعمل" in t or "ضوابط" in t or "تصویب نامه" in t or "تصویب‌نامه" in t:
        return "directive"
    if "اساسنامه" in t:
        return "bylaw"
    if any(x in t for x in ("آیین نامه", "آیین‌نامه", "نظامنامه", "مقررات", "شرایط")):
        return "regulation"
    if "لایحه" in t or "قانون" in t:
        return "law"
    if category == "داوری":
        return "judicial_precedent"
    return "regulation"


def is_noise(line: str) -> bool:
    s = clean_title(line)
    if not s or s in NAV_EXACT or "لینک:" in s:
        return True
    if set(s) <= {"=", "-", "_", "*"}:
        return True
    if s.startswith("قوانین ") and len(s) < 30:
        return True
    return False


def clean_body(lines: list[str], match=None) -> str:
    if match is not None:
        first = normalize_text(lines[0]).strip().lstrip("*#").strip()
        rest = match.group("rest")
        rest = re.sub(r"^\s*[\-ـ–—:：]\s*", "", rest).strip()
        body = ([rest] if rest else []) + [normalize_text(x).strip() for x in lines[1:]]
    else:
        body = [normalize_text(x).strip() for x in lines]
        # Drop the export header and navigation for non-article pages.
        url_i = next((i for i, line in enumerate(body[:50]) if "لینک:" in line), None)
        if url_i is not None:
            body = body[url_i + 1 :]
        while body and (is_noise(body[0]) or body[0].strip() in {"قانون", "آیین نامه", "آیین‌نامه"}):
            body.pop(0)

    cleaned: list[str] = []
    for line in body:
        line = normalize_text(line).replace("\t", " ").strip()
        if re.match(r"^\s*(?:تازه\s*های\s*قوانین|تازه‌های\s*قوانین|مطالب مرتبط|ارسال دیدگاه|ثبت دیدگاه|نظرات کاربران)\b", line):
            break
        if re.search(r"https?://", line):
            continue
        if is_noise(line):
            continue
        line = re.sub(r"[ \t]+", " ", line)
        cleaned.append(line)
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    out: list[str] = []
    previous_blank = False
    for line in cleaned:
        blank = not line
        if blank and previous_blank:
            continue
        out.append(line)
        previous_blank = blank
    return "\n".join(out).strip()


def canonical_article(kind: str, raw: str, fallback_index: int) -> str:
    raw = normalize_text(raw).strip()
    if raw == "واحده":
        return "ماده واحده"
    raw = re.sub(r"\s+", " ", raw.translate(ASCII_DIGITS)).strip()
    prefix = "اصل" if kind == "اصل" else "ماده"
    if not raw:
        return f"بخش {str(fallback_index).translate(PERSIAN_DIGITS)}"
    return f"{prefix} {raw.translate(PERSIAN_DIGITS)}"


def parse_file(path: Path) -> tuple[str, list[dict]]:
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    url = source_url(lines)
    heads = []
    for i, line in enumerate(lines):
        m = article_match(line)
        if m:
            heads.append((i, m))
    rows: list[dict] = []
    if heads:
        for pos, (start, m) in enumerate(heads):
            end = heads[pos + 1][0] if pos + 1 < len(heads) else len(lines)
            text = clean_body(lines[start:end], m)
            if not text:
                continue
            rows.append({"article_no": canonical_article(m.group("kind"), m.group("number"), pos + 1), "text": text})
    else:
        text = clean_body(lines)
        if text:
            rows.append({"article_no": "متن", "text": text})
    return url, rows


def file_min_article(path: Path) -> int:
    try:
        _url, rows = parse_file(path)
        for row in rows:
            m = re.search(r"[۰-۹0-9]+", row["article_no"])
            if m:
                return int(m.group(0).translate(ASCII_DIGITS))
    except Exception:
        pass
    m = re.search(r"\(\s*([۰-۹0-9]+)", path.stem)
    return int(m.group(1).translate(ASCII_DIGITS)) if m else 999999


def is_chunk_name(stem: str) -> bool:
    return bool(RANGE_RE.search(stem) or re.match(r"^(?:فصل|باب|بخش|مقدمه|کلیات|تعاریف)(?:_|$)", normalize_text(stem)))


@dataclass
class Unit:
    category: str
    group: str
    files: list[Path]
    title: str
    key: str


def iter_units() -> list[Unit]:
    units: list[Unit] = []
    categories = sorted(p for p in DATA_ROOT.iterdir() if p.is_dir() and p.name not in {"seed", "source_cache", "archive", "بهداشت_و_درمان"})
    if not any(category.name in CATEGORY_CODES and any(category.rglob("*.txt")) for category in categories):
        raise SystemExit(
            "raw uploaded category sources are not restored; run "
            "python3 scripts/restore_uploaded_sources.py before rebuilding uploaded_data.py"
        )
    for category_dir in categories:
        category = category_dir.name
        groups: dict[str, list[Path]] = {}
        for path in category_dir.rglob("*.txt"):
            rel = path.relative_to(category_dir)
            groups.setdefault(rel.parts[0], []).append(path)
        for group, raw_files in sorted(groups.items()):
            files = sorted(raw_files)
            base = [p for p in files if p.name == "مشاهده_متن_قانون.txt"]
            if base:
                units.append(make_unit(category, group, base, is_combined=False))
                for path in files:
                    if path not in base:
                        units.append(make_unit(category, group, [path], is_combined=False))
                continue
            chunk_files = [p for p in files if is_chunk_name(p.stem)]
            other_files = [p for p in files if p not in chunk_files]
            if chunk_files:
                units.append(make_unit(category, group, sorted(chunk_files, key=file_min_article), is_combined=True))
            for path in other_files:
                units.append(make_unit(category, group, [path], is_combined=False))
    return units


def make_unit(category: str, group: str, files: list[Path], is_combined: bool) -> Unit:
    if is_combined or len(files) > 1:
        title = clean_title(group)
    else:
        path = files[0]
        lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        title = clean_title(group) if path.name == "مشاهده_متن_قانون.txt" else header_title(lines, path.stem)
        if path.name != "مشاهده_متن_قانون.txt" and group != path.stem:
            # Related regulations/pages are separate legal documents, not extra
            # versions of the parent law.  For named legal sub-pages use the
            # filename as the leading title: the page header often repeats the
            # parent law before displaying «آیین‌نامه اجرایی».
            stem_title = clean_title(path.stem)
            if any(token in stem_title for token in ("آیین نامه", "آیین‌نامه", "دستورالعمل", "بخشنامه", "اساسنامه", "قانون", "مقررات")):
                title = stem_title
            if title in {"آیین نامه اجرایی", "دستورالعمل اجرایی", "مشاهده متن قانون"} or title.startswith("آیین نامه اجرایی"):
                title = f"{title} {clean_title(group)}"
            elif title != clean_title(group) and clean_title(group) not in title and any(token in stem_title for token in ("آیین نامه", "آیین‌نامه", "دستورالعمل", "بخشنامه", "اساسنامه")):
                title = f"{title} {clean_title(group)}"
    rels = [str(p.relative_to(ROOT)).replace("\\", "/") for p in files]
    key = category + "|" + group + "|" + "|".join(rels)
    return Unit(category, group, files, clean_title(title), key)


def existing_documents() -> list[tuple[str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    try:
        return [tuple(row) for row in conn.execute("SELECT reference_code, title, (SELECT code FROM document_types WHERE id=documents.type_id) FROM documents WHERE reference_code NOT LIKE 'UPL-%'")]
    finally:
        conn.close()


def title_matches_existing(title: str, type_code: str, existing: list[tuple[str, str, str]]) -> tuple[str, str] | None:
    key = match_key(title)
    if not key or len(key.split()) < 2:
        return None
    source_tokens = set(key.split())
    for ref, old_title, old_type in existing:
        old_key = match_key(old_title)
        if key == old_key and type_code == old_type:
            return ref, old_title
    # A raw upload often has a shorter title while the database keeps a precise
    # title/date suffix.  Only accept subset matches for sufficiently specific
    # titles and the same document type.
    if len(source_tokens) >= 3:
        for ref, old_title, old_type in existing:
            if type_code != old_type:
                continue
            old_tokens = set(match_key(old_title).split())
            if source_tokens <= old_tokens and len(source_tokens & old_tokens) >= 3:
                return ref, old_title
            # A source title can be slightly more specific than the database
            # title (for example «قانون دریایی ایران» vs «قانون دریایی»).
            if old_tokens <= source_tokens and len(source_tokens - old_tokens) <= 2 and len(old_tokens) >= 3:
                return ref, old_title
    return None


def build_unit(unit: Unit) -> dict:
    all_rows: list[dict] = []
    urls: list[str] = []
    texts: list[str] = []
    for path in unit.files:
        url, rows = parse_file(path)
        if url and url not in urls:
            urls.append(url)
        texts.append(path.read_text(encoding="utf-8", errors="replace"))
        all_rows.extend(rows)
    if not all_rows:
        raise ValueError(f"no extractable text: {unit.key}")
    # For combined split documents, rows are already file-sorted by first article.
    # Use a stable row index as article_key suffix because source pages sometimes
    # contain duplicate/overlapping article numbers or multiple instruments.
    source_text = "\n".join(texts)
    ref = f"UPL-{CATEGORY_CODES[unit.category]}-{hashlib.sha1(unit.key.encode('utf-8')).hexdigest()[:10].upper()}"
    type_code = infer_type(unit.title, unit.category)
    date = raw_date(source_text, unit.title)
    authority = infer_authority(unit.category, unit.title, source_text)
    status = "abrogated" if "منسوخ" in source_text[-6000:] or "لغو شد" in source_text[-6000:] else ("amended" if "اصلاح" in source_text[:10000] or "الحاق" in source_text[:10000] else "in_force")
    source_paths = [str(p.relative_to(ROOT)).replace("\\", "/") for p in unit.files]
    rendered_rows = []
    for i, row in enumerate(all_rows, 1):
        article_no = row["article_no"]
        if article_no == "متن" and len(all_rows) > 1:
            article_no = f"بخش {str(i).translate(PERSIAN_DIGITS)}"
        rendered_rows.append({
            "article_no": article_no,
            "article_key_suffix": f"r{i:04d}",
            "text": row["text"],
        })
    return {
        "ref": ref,
        "title": unit.title,
        "short": unit.title[:80],
        "category": unit.category,
        "topic": TOPIC_NAMES[unit.category],
        "type_code": type_code,
        "status_code": status,
        "authority": authority,
        "date": date,
        "source_urls": urls,
        "source_paths": source_paths,
        "notes": "داده خام آپلودشده در data؛ متن از TXT صفحه منبع استخراج و نویز وب حذف شده است. مرجع صادرکننده/تاریخ و وضعیت تنقیحی در صورت نبود صراحت، برآورد خودکار است و برای استناد رسمی باید با منبع رسمی مقابله شود.",
        "article_count": len(rendered_rows),
        "rows": rendered_rows,
    }


def main() -> None:
    existing = existing_documents()
    documents: list[dict] = []
    skipped: list[dict] = []
    failures: list[str] = []
    for unit in iter_units():
        try:
            doc = build_unit(unit)
        except Exception as exc:
            failures.append(f"{unit.key}: {exc}")
            continue
        match = title_matches_existing(doc["title"], doc["type_code"], existing)
        if match:
            skipped.append({"ref": doc["ref"], "title": doc["title"], "existing_ref": match[0], "existing_title": match[1], "source_paths": doc["source_paths"]})
        else:
            documents.append(doc)

    if failures:
        raise SystemExit("\n".join(["extraction failures:"] + failures))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    content = "# -*- coding: utf-8 -*-\n\n"
    content += "# Generated by scripts/build_uploaded_data_seeds.py; sources restore from data/archive/ before a rebuild.\n"
    content += "DOCUMENTS = " + pprint.pformat(documents, width=120, sort_dicts=False, compact=False) + "\n\n"
    content += "SKIPPED_EXISTING = " + pprint.pformat(skipped, width=120, sort_dicts=False, compact=False) + "\n"
    OUTPUT.write_text(content, encoding="utf-8")
    total_rows = sum(d["article_count"] for d in documents)
    print(f"[OK] scanned {len(documents) + len(skipped)} source units")
    print(f"[OK] new documents: {len(documents)} / {total_rows} extracted articles")
    print(f"[OK] skipped existing documents: {len(skipped)}")
    print(f"[OK] seed: {OUTPUT}")
    for category in sorted(CATEGORY_CODES):
        count = sum(1 for d in documents if d["category"] == category)
        if count:
            print(f"  {category}: {count} new documents")


if __name__ == "__main__":
    main()
