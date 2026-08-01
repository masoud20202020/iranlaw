# -*- coding: utf-8 -*-
"""
وب‌اپ ساده برای مرور و جست‌وجو در بانک اطلاعاتی حقوقی ایران.
اجرا:
    cd iran_legal_db
    python3 web/app.py
سپس در مرورگر: http://127.0.0.1:5050
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from flask import Flask, render_template, request, g, abort
from schema import get_connection, DB_PATH
from search_utils import expand_fts_query

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static"))


def get_db():
    if "db" not in g:
        db_path = os.environ.get("LEGAL_DB", DB_PATH)
        g.db = get_connection(db_path)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    db = get_db()
    stats = {
        "docs": db.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"],
        "articles": db.execute("SELECT COUNT(*) c FROM articles WHERE is_current=1").fetchone()["c"],
        "history": db.execute("SELECT COUNT(*) c FROM articles WHERE is_current=0").fetchone()["c"],
        "relations": db.execute("SELECT COUNT(*) c FROM relations").fetchone()["c"],
        "types": db.execute("SELECT COUNT(*) c FROM document_types").fetchone()["c"],
    }
    types = db.execute("""SELECT dt.name_fa, dt.code, COUNT(d.id) c
                          FROM document_types dt
                          LEFT JOIN documents d ON d.type_id = dt.id
                          GROUP BY dt.id ORDER BY c DESC""").fetchall()
    recent = db.execute("""SELECT d.id, d.title, d.short_title, dt.name_fa type, s.name_fa status
                           FROM documents d
                           JOIN document_types dt ON dt.id=d.type_id
                           JOIN statuses s ON s.id=d.status_id
                           ORDER BY d.id DESC LIMIT 8""").fetchall()
    q = request.args.get("q", "").strip()
    results = None
    if q and len(q) >= 2:
        results = db.execute("""
            SELECT a.id AS aid, a.article_no, a.text, d.id AS did, d.title, d.short_title,
                   rank, snippet(articles_fts, 4, '<mark>', '</mark>', '...', 16) AS snip
            FROM articles_fts
            JOIN articles a ON a.id = articles_fts.article_id
            JOIN documents d ON d.id = a.document_id
            WHERE articles_fts MATCH ? AND a.is_current=1
            ORDER BY rank LIMIT 50
        """, (expand_fts_query(q),)).fetchall()
    return render_template("index.html", stats=stats, types=types, recent=recent,
                           q=q, results=results)


@app.route("/doc/<int:doc_id>")
def doc(doc_id):
    db = get_db()
    d = db.execute("""
        SELECT d.*, dt.name_fa type, s.name_fa status, a.name_fa authority
        FROM documents d
        JOIN document_types dt ON dt.id=d.type_id
        JOIN statuses s ON s.id=d.status_id
        LEFT JOIN authorities a ON a.id=d.issuing_authority_id
        WHERE d.id=?
    """, (doc_id,)).fetchone()
    if not d: abort(404)

    article_stats = db.execute("""
        SELECT COUNT(*) versions,
               COUNT(DISTINCT article_no) article_numbers,
               SUM(CASE WHEN is_current=1 THEN 1 ELSE 0 END) current_count,
               SUM(CASE WHEN is_current=0 THEN 1 ELSE 0 END) historical_count
        FROM articles WHERE document_id=?
    """, (doc_id,)).fetchone()
    view_mode = request.args.get("view", "current")
    if view_mode == "all":
        article_where = "document_id=?"
    elif view_mode == "historical":
        article_where = "document_id=? AND is_current=0"
    else:
        view_mode = "current"
        article_where = "document_id=? AND is_current=1"
    articles = db.execute(f"""
        SELECT id, article_no, text, version_no, is_current, effective_date, expiry_date
        FROM articles WHERE {article_where} ORDER BY id
    """, (doc_id,)).fetchall()
    rels_from = db.execute("""
        SELECT r.relation_type, r.description, d.id did, d.title, d.short_title,
               ta.article_no from_art, tb.article_no to_art
        FROM relations r
        LEFT JOIN documents d ON d.id=r.to_document_id
        LEFT JOIN articles ta ON ta.id=r.from_article_id
        LEFT JOIN articles tb ON tb.id=r.to_article_id
        WHERE r.from_document_id=?
    """, (doc_id,)).fetchall()
    rels_to = db.execute("""
        SELECT r.relation_type, r.description, d.id did, d.title, d.short_title,
               ta.article_no from_art, tb.article_no to_art
        FROM relations r JOIN documents d ON d.id=r.from_document_id
        LEFT JOIN articles ta ON ta.id=r.from_article_id
        LEFT JOIN articles tb ON tb.id=r.to_article_id
        WHERE r.to_document_id=?
    """, (doc_id,)).fetchall()
    tags = db.execute("""SELECT t.name_fa FROM tags t
                         JOIN document_tags dt ON dt.tag_id=t.id
                         WHERE dt.document_id=?""", (doc_id,)).fetchall()
    return render_template("doc.html", d=d, articles=articles,
                           article_stats=article_stats, view_mode=view_mode,
                           rels_from=rels_from, rels_to=rels_to, tags=tags)


@app.route("/types")
def types():
    db = get_db()
    types = db.execute("""SELECT dt.id, dt.code, dt.name_fa, dt.description, COUNT(d.id) c
                          FROM document_types dt
                          LEFT JOIN documents d ON d.type_id=dt.id
                          GROUP BY dt.id ORDER BY c DESC""").fetchall()
    return render_template("types.html", types=types)


@app.route("/by-type/<code>")
def by_type(code):
    db = get_db()
    dt = db.execute("SELECT * FROM document_types WHERE code=?", (code,)).fetchone()
    if not dt: abort(404)
    docs = db.execute("""SELECT d.id, d.title, d.short_title, s.name_fa status,
                                a.name_fa authority, d.ratification_date
                         FROM documents d
                         JOIN statuses s ON s.id=d.status_id
                         LEFT JOIN authorities a ON a.id=d.issuing_authority_id
                         WHERE d.type_id=? ORDER BY d.ratification_date DESC, d.id DESC""",
                      (dt["id"],)).fetchall()
    return render_template("by_type.html", dt=dt, docs=docs)


@app.route("/article/<int:aid>")
def article(aid):
    db = get_db()
    art = db.execute("""
        SELECT a.*, d.title doc_title, d.id doc_id, d.short_title
        FROM articles a JOIN documents d ON d.id=a.document_id WHERE a.id=?
    """, (aid,)).fetchone()
    if not art: abort(404)
    # history
    if art["article_key"]:
        hist = db.execute("""SELECT * FROM articles WHERE article_key=? ORDER BY version_no""",
                          (art["article_key"],)).fetchall()
    else:
        hist = None
    rels = db.execute("""
        SELECT r.relation_type, r.description, d.id did, d.title, d.short_title
        FROM relations r
        LEFT JOIN documents d ON d.id = CASE
            WHEN r.from_article_id=? THEN r.to_document_id
            ELSE r.from_document_id END
        WHERE r.from_article_id=? OR r.to_article_id=?
    """, (aid, aid, aid)).fetchall()
    return render_template("article.html", art=art, hist=hist, rels=rels)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
