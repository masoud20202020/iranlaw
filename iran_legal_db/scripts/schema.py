"""
Iran Legal Database - Schema Definition
=======================================
A comprehensive, extensible SQLite schema for the complete legal database of Iran.

Covers:
    1. All types of legal documents (قوانین، آیین‌نامه‌ها، بخشنامه‌ها، آرای وحدت رویه،
       نظریات مشورتی، آرای دیوان عدالت اداری، اصلاحیه‌ها، ...)
    2. Article-level versioning/history (تاریخچه تغییرات هر ماده)
    3. Cross-references between documents (ارتباطات بین اسناد)
    4. Tagging, categorization, keyword search, and source traceability
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "iran_legal.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA_SQL = """
-- =========================================================
-- 1) Document types (نوع سند)
-- =========================================================
CREATE TABLE IF NOT EXISTS document_types (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT NOT NULL UNIQUE,        -- law, regulation, circular, unified_ruling,
                                               -- advisory_opinion, divan_ruling, constitution,
                                               -- statute, bylaw, directive, etc.
    name_fa       TEXT NOT NULL,               -- قانون، آیین‌نامه، بخشنامه، رأی وحدت رویه، ...
    description   TEXT
);

-- =========================================================
-- 2) Issuing authorities (مراجع صادرکننده)
-- =========================================================
CREATE TABLE IF NOT EXISTS authorities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fa       TEXT NOT NULL UNIQUE,        -- مجلس شورای اسلامی، هیئت وزیران، رئیس قوه قضائیه، ...
    authority_type TEXT,                       -- legislative, executive, judicial, administrative
    description   TEXT
);

-- =========================================================
-- 3) Status of documents (وضعیت سند: معتبر، منسوخ، اصلاحی، ...)
-- =========================================================
CREATE TABLE IF NOT EXISTS statuses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT NOT NULL UNIQUE,
    name_fa       TEXT NOT NULL,
    description   TEXT
);

-- =========================================================
-- 4) Topics / categories (موضوع/دسته‌بندی حقوقی)
-- =========================================================
CREATE TABLE IF NOT EXISTS topics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fa       TEXT NOT NULL UNIQUE,        -- حقوق مدنی، کیفری، تجارت، خانواده، کار، ...
    parent_id     INTEGER REFERENCES topics(id) ON DELETE SET NULL
);

-- =========================================================
-- 5) Documents (اسناد حقوقی)
-- =========================================================
CREATE TABLE IF NOT EXISTS documents (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT NOT NULL,           -- عنوان کامل سند
    short_title       TEXT,                    -- عنوان کوتاه/مخفف (ق.م.، ق.ت.، ق.م.ا.، ...)
    type_id           INTEGER NOT NULL REFERENCES document_types(id),
    issuing_authority_id INTEGER REFERENCES authorities(id),
    status_id         INTEGER REFERENCES statuses(id),
    ratification_date TEXT,                    -- تاریخ تصویب (ISO YYYY-MM-DD)
    publication_date  TEXT,                    -- تاریخ انتشار در روزنامه رسمی
    effective_date    TEXT,                    -- تاریخ اجرا
    official_newspaper_no TEXT,                -- شماره روزنامه رسمی
    reference_code    TEXT UNIQUE,             -- کد یکتا (مثلاً QM-1307 برای قانون مدنی ۱۳۰۷)
    notes             TEXT,                    -- توضیحات کلی
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status_id);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);

-- =========================================================
-- 6) Articles / clauses (مواد و تبصره‌ها)
--    Versioning is handled by storing every version as a row,
--    linked to its parent article and flagged as current/historical.
-- =========================================================
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    article_no      TEXT NOT NULL,            -- شماره ماده (مثلاً "۱۰", "تبصره ۱ ماده ۱۰", "۱۰ اصلاحی")
    article_key     TEXT,                     -- کلید پایدارِ ماده برای ردیابی در اصلاحات (e.g., "DOCID:10")
    version_no      INTEGER NOT NULL DEFAULT 1,
    is_current      INTEGER NOT NULL DEFAULT 1, -- 1 = آخرین نسخه معتبر
    effective_date  TEXT,                     -- از چه تاریخی این نسخه اعمال می‌شود
    expiry_date     TEXT,                     -- در صورت ابطال، تاریخ پایان اعتبار
    text            TEXT NOT NULL,            -- متن ماده
    source_note     TEXT,                     -- منبع استخراج متن (روزنامه رسمی، وبگاه معتبر، ...)
    notes           TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_doc ON articles(document_id);
CREATE INDEX IF NOT EXISTS idx_articles_key ON articles(article_key);
CREATE INDEX IF NOT EXISTS idx_articles_current ON articles(document_id, is_current);

-- =========================================================
-- 7) Cross-references between documents / articles (ارتباطات)
--    relation_type examples:
--      amends         : این سند، سندی دیگر را اصلاح می‌کند
--      abrogates      : این سند، سندی دیگر را نسخ می‌کند
--      implements     : این آیین‌نامه، قانونی را اجرا می‌کند
--      cites          : این ماده به ماده/سند دیگر استناد می‌کند
--      interprets     : رأی وحدت رویه / نظریه مشورتی، ماده‌ای را تفسیر می‌کند
--      ruled_by_dian  : رأی دیوان عدالت اداری در خصوص ماده/بخشنامه
--      overrules      : رأیی، رأی یا بخشنامه‌ای را ابطال می‌کند
-- =========================================================
CREATE TABLE IF NOT EXISTS relations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    from_article_id  INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    to_document_id   INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    to_article_id    INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    relation_type    TEXT NOT NULL,
    description      TEXT,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_relations_from_doc ON relations(from_document_id);
CREATE INDEX IF NOT EXISTS idx_relations_to_doc ON relations(to_document_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);

-- =========================================================
-- 8) Tags / keywords (برچسب‌ها و کلیدواژه‌ها)
-- =========================================================
CREATE TABLE IF NOT EXISTS tags (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fa    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id     INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- =========================================================
-- 9) Document ↔ Topics (چند به چند)
-- =========================================================
CREATE TABLE IF NOT EXISTS document_topics (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    topic_id    INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, topic_id)
);

-- =========================================================
-- 10) Full-text search (FTS5 virtual table) روی متن مواد
-- =========================================================
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    article_id UNINDEXED,
    document_id UNINDEXED,
    title,          -- عنوان سند برای context
    article_no,
    text,
    tokenize = "unicode61 remove_diacritics 2"
);

-- =========================================================
-- Views for convenience
-- =========================================================
CREATE VIEW IF NOT EXISTS v_current_articles AS
SELECT a.id, a.article_no, a.article_key, a.text,
       d.id AS document_id, d.title, d.short_title
FROM articles a
JOIN documents d ON d.id = a.document_id
WHERE a.is_current = 1;

-- =========================================================
-- Seed lookup tables
-- =========================================================
INSERT OR IGNORE INTO document_types(code, name_fa, description) VALUES
    ('constitution',   'قانون اساسی',         'قانون اساسی جمهوری اسلامی ایران و اصلاحات آن'),
    ('law',            'قانون',               'قوانین عادی مصوب مجلس'),
    ('amendment',      'قانون اصلاحی',        'قوانین یا موادی که قانون دیگری را اصلاح می‌کنند'),
    ('regulation',     'آیین‌نامه',           'آیین‌نامه‌های اجرایی مصوب هیئت وزیران، کمیسیون‌ها، ...'),
    ('bylaw',          'اساسنامه / آئین‌نامه داخلی', 'اساسنامه نهادها و آیین‌نامه‌های داخلی'),
    ('circular',       'بخشنامه',             'بخشنامه‌ها، دستورالعمل‌ها و راهنماهای اداری'),
    ('directive',      'دستورالعمل / شیوه‌نامه', 'دستورالعمل‌های اجرایی'),
    ('unified_ruling', 'رأی وحدت رویه',        'آرای وحدت رویه هیئت عمومی دیوان عالی کشور'),
    ('advisory_opinion','نظریه مشورتی',        'نظریات اداره حقوقی قوه قضائیه / شورای نگهبان / ...'),
    ('divan_ruling',   'رأی دیوان عدالت اداری','آرای هیئت عمومی و شعب دیوان عدالت اداری'),
    ('judicial_precedent','رأی اصراری / رویه قضایی','آرای اصراری و رویه‌های مهم قضایی'),
    ('treaty',         'قرارداد/کنوانسیون بین‌المللی','معاهدات و کنوانسیون‌های بین‌المللی');

INSERT OR IGNORE INTO statuses(code, name_fa, description) VALUES
    ('in_force',    'معتبر و لازم‌الاجرا', 'سند در حال حاضر اعتبار دارد'),
    ('amended',     'اصلاح‌شده',          'بخشی از سند اصلاح شده ولی اصل آن معتبر است'),
    ('abrogated',   'منسوخ',              'سند کامل یا بخشی از آن نسخ شده است'),
    ('expired',     'منقضی',              'مدت اعتبار سند به پایان رسیده'),
    ('suspended',   'معلق',               'اجرا به صورت موقت متوقف شده'),
    ('draft',       'پیش‌نویس',           'پیش‌نویس، هنوز تصویب نشده');

INSERT OR IGNORE INTO authorities(name_fa, authority_type) VALUES
    ('مجلس شورای اسلامی', 'legislative'),
    ('مجلس خبرگان رهبری', 'legislative'),
    ('شورای نگهبان', 'oversight'),
    ('مجمع تشخیص مصلحت نظام', 'oversight'),
    ('هیئت وزیران', 'executive'),
    ('رئیس قوه قضائیه', 'judicial'),
    ('دیوان عالی کشور', 'judicial'),
    ('اداره کل حقوقی قوه قضائیه', 'judicial'),
    ('دیوان عدالت اداری', 'judicial'),
    ('رئیس‌جمهور', 'executive'),
    ('وزارت دادگستری', 'executive'),
    ('شورای عالی انقلاب فرهنگی', 'executive'),
    ('مجلس شورای ملی (پیش از انقلاب)', 'legislative');

INSERT OR IGNORE INTO topics(name_fa) VALUES
    ('حقوق اساسی'),
    ('حقوق مدنی'),
    ('حقوق خانواده'),
    ('حقوق تجارت'),
    ('حقوق کیفری'),
    ('آیین دادرسی مدنی'),
    ('آیین دادرسی کیفری'),
    ('حقوق اداری'),
    ('حقوق کار و تأمین اجتماعی'),
    ('حقوق مالیاتی'),
    ('حقوق ثبت اسناد و املاک'),
    ('حقوق شهرداری‌ها'),
    ('حقوق محیط زیست'),
    ('حقوق بین‌الملل'),
    ('حقوق مالکیت فکری'),
    ('حقوق پول و بانک'),
    ('حقوق بیمه'),
    ('حقوق تجارت الکترونیک');
"""


def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    print(f"[OK] Database initialized at: {db_path}")


if __name__ == "__main__":
    init_db()
