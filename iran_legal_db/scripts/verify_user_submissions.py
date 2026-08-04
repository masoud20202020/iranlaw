#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifier for the five user-submitted legal texts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "seed"))

from verification_utils import verify_package  # noqa: E402
from user_submissions import DOCUMENTS  # noqa: E402


if __name__ == "__main__":
    refs = tuple(d["ref"] for d in DOCUMENTS)
    counts = {d["ref"]: (d["article_count"], d["article_count"]) for d in DOCUMENTS}
    verify_package(
        package_name="user_submissions",
        refs=refs,
        expected_counts=counts,
        loader_script="load_user_submissions.py",
        search_terms=("مواد مخدر", "صحنه جرم", "اجرای احکام", "خدمات عمومی رایگان", "تالاب"),
        history_keys=("CIR-MM-714-1396:b01", "AICR-768-1396:a001", "AIM79-1393:a001"),
        relation_min=5,
    )
