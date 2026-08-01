"""
Importer utilities - for adding documents and articles easily.
"""
import os
import sqlite3
from typing import Optional, List, Dict, Any
from schema import get_connection, DB_PATH


def get_or_create_document(
    conn: sqlite3.Connection,
    title: str,
    type_code: str,
    *,
    short_title: Optional[str] = None,
    issuing_authority: Optional[str] = None,
    status_code: str = "in_force",
    ratification_date: Optional[str] = None,
    publication_date: Optional[str] = None,
    effective_date: Optional[str] = None,
    official_newspaper_no: Optional[str] = None,
    reference_code: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Get or create a document and return its id."""
    if reference_code:
        cur = conn.execute("SELECT id FROM documents WHERE reference_code=?", (reference_code,))
        row = cur.fetchone()
        if row:
            return row["id"]

    type_id = conn.execute("SELECT id FROM document_types WHERE code=?", (type_code,)).fetchone()
    if not type_id:
        raise ValueError(f"Unknown document_type code: {type_code}")

    auth_id = None
    if issuing_authority:
        a = conn.execute("SELECT id FROM authorities WHERE name_fa=?", (issuing_authority,)).fetchone()
        if a:
            auth_id = a["id"]
        else:
            cur = conn.execute(
                "INSERT INTO authorities(name_fa, authority_type) VALUES(?, 'legislative')",
                (issuing_authority,),
            )
            auth_id = cur.lastrowid

    status_id = conn.execute("SELECT id FROM statuses WHERE code=?", (status_code,)).fetchone()["id"]

    cur = conn.execute(
        """INSERT INTO documents(title, short_title, type_id, issuing_authority_id,
                                  status_id, ratification_date, publication_date,
                                  effective_date, official_newspaper_no, reference_code, notes)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (title, short_title, type_id["id"], auth_id, status_id,
         ratification_date, publication_date, effective_date,
         official_newspaper_no, reference_code, notes),
    )
    return cur.lastrowid


def add_article(
    conn: sqlite3.Connection,
    document_id: int,
    article_no: str,
    text: str,
    *,
    article_key: Optional[str] = None,
    version_no: int = 1,
    is_current: int = 1,
    effective_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    source_note: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO articles(document_id, article_no, article_key, version_no, is_current,
                                effective_date, expiry_date, text, source_note, notes)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (document_id, article_no, article_key, version_no, is_current,
         effective_date, expiry_date, text, source_note, notes),
    )
    aid = cur.lastrowid
    # Insert into FTS
    doc = conn.execute("SELECT title FROM documents WHERE id=?", (document_id,)).fetchone()
    conn.execute(
        "INSERT INTO articles_fts(article_id, document_id, title, article_no, text) VALUES(?,?,?,?,?)",
        (aid, document_id, doc["title"], article_no, text),
    )
    return aid


def add_relation(
    conn: sqlite3.Connection,
    from_document_id: int,
    relation_type: str,
    to_document_id: int,
    *,
    from_article_id: Optional[int] = None,
    to_article_id: Optional[int] = None,
    description: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO relations(from_document_id, from_article_id, to_document_id,
                                 to_article_id, relation_type, description)
           VALUES(?,?,?,?,?,?)""",
        (from_document_id, from_article_id, to_document_id, to_article_id, relation_type, description),
    )
    return cur.lastrowid


def add_tag(conn: sqlite3.Connection, name_fa: str) -> int:
    cur = conn.execute("INSERT OR IGNORE INTO tags(name_fa) VALUES(?)", (name_fa,))
    return conn.execute("SELECT id FROM tags WHERE name_fa=?", (name_fa,)).fetchone()["id"]


def link_document_tag(conn: sqlite3.Connection, document_id: int, tag_id: int):
    conn.execute(
        "INSERT OR IGNORE INTO document_tags(document_id, tag_id) VALUES(?,?)",
        (document_id, tag_id),
    )


def link_document_topic(conn: sqlite3.Connection, document_id: int, topic_name: str):
    t = conn.execute("SELECT id FROM topics WHERE name_fa=?", (topic_name,)).fetchone()
    if t:
        conn.execute(
            "INSERT OR IGNORE INTO document_topics(document_id, topic_id) VALUES(?,?)",
            (document_id, t["id"]),
        )


def bulk_add_articles(
    conn: sqlite3.Connection,
    document_id: int,
    articles: List[Dict[str, Any]],
):
    """articles: list of dicts with keys: article_no, text, [effective_date, source_note, notes, article_key]"""
    for art in articles:
        add_article(conn, document_id, **art)
    conn.commit()
