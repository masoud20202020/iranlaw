# -*- coding: utf-8 -*-
"""Shared FTS5 query normalization and a small Persian legal synonym map."""


def _key(text: str) -> str:
    return (
        text.strip()
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("‌", " ")
    )


LEGAL_SYNONYMS = {
    "سفته": "(سفته OR فته)",
    "فته طلب": "(سفته OR فته)",
    "هیئت مدیره": '("هیئت مدیره" OR "هیات مدیره")',
    "هیات مدیره": '("هیئت مدیره" OR "هیات مدیره")',
}


def expand_fts_query(text: str) -> str:
    """Return an FTS5 expression, expanding only known exact legal aliases."""
    return LEGAL_SYNONYMS.get(_key(text), text.strip())
