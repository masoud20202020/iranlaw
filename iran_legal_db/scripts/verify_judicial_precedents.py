# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "data" / "seed")]

from judicial_precedents_phase1 import DIVAN_RULINGS_PHASE1, UNIFIED_RULINGS_PHASE1  # noqa: E402
from judicial_precedents_phase2 import DIVAN_RULINGS_PHASE2, UNIFIED_RULINGS_PHASE2  # noqa: E402
from judicial_precedents_phase3 import DIVAN_RULINGS_PHASE3, UNIFIED_RULINGS_PHASE3  # noqa: E402
from judicial_precedents_phase4 import DIVAN_RULINGS_PHASE4, UNIFIED_RULINGS_PHASE4  # noqa: E402
from judicial_precedents_phase5 import DIVAN_RULINGS_PHASE5, UNIFIED_RULINGS_PHASE5  # noqa: E402
from judicial_precedents_phase6 import DIVAN_RULINGS_PHASE6, UNIFIED_RULINGS_PHASE6  # noqa: E402
from judicial_precedents_phase7 import DIVAN_RULINGS_PHASE7, UNIFIED_RULINGS_PHASE7  # noqa: E402
from judicial_precedents_phase8 import DIVAN_RULINGS_PHASE8, UNIFIED_RULINGS_PHASE8  # noqa: E402
from judicial_precedents_phase9 import DIVAN_RULINGS_PHASE9, UNIFIED_RULINGS_PHASE9  # noqa: E402
from judicial_precedents_full_text import FULL_TEXT_OVERRIDES  # noqa: E402
from verification_utils import require, verify_package  # noqa: E402
from schema import get_connection  # noqa: E402

ITEMS = [
    *UNIFIED_RULINGS_PHASE1,
    *UNIFIED_RULINGS_PHASE2,
    *UNIFIED_RULINGS_PHASE3,
    *UNIFIED_RULINGS_PHASE4,
    *UNIFIED_RULINGS_PHASE5,
    *UNIFIED_RULINGS_PHASE6,
    *UNIFIED_RULINGS_PHASE7,
    *UNIFIED_RULINGS_PHASE8,
    *UNIFIED_RULINGS_PHASE9,
    *DIVAN_RULINGS_PHASE1,
    *DIVAN_RULINGS_PHASE2,
    *DIVAN_RULINGS_PHASE3,
    *DIVAN_RULINGS_PHASE4,
    *DIVAN_RULINGS_PHASE5,
    *DIVAN_RULINGS_PHASE6,
    *DIVAN_RULINGS_PHASE7,
    *DIVAN_RULINGS_PHASE8,
    *DIVAN_RULINGS_PHASE9,
]
# RVR-869 and RVR-878 are already owned by the insurance/customs loaders, but are
# included here to verify continuous coverage of the recent RVR 847-878 block.
EXTERNAL_EXISTING_REFS = ("RVR-869-1404", "RVR-878-1405")
REFS = tuple(item["ref"] for item in ITEMS) + EXTERNAL_EXISTING_REFS

def verify_full_text_overrides():
    conn = get_connection()
    try:
        for ref, override in FULL_TEXT_OVERRIDES.items():
            row = conn.execute(
                """
                SELECT a.text, a.notes
                FROM documents d JOIN articles a ON a.document_id=d.id
                WHERE d.reference_code=? AND a.article_key=? AND a.is_current=1
                """,
                (ref, f"{ref}:ruling"),
            ).fetchone()
            require(row, f"missing full-text override article for {ref}")
            require(row["text"] == override["text"], f"full-text override mismatch for {ref}")
            require("خلاصه/گزیده" not in row["notes"], f"old summary note remains for {ref}")
            require("متن کامل بخش رأی" in row["notes"] or "متن کامل بخش رأی/حکم" in row["notes"], f"full-text note missing for {ref}")
    finally:
        conn.close()
    print(f"[OK] judicial_precedents full-text overrides: {len(FULL_TEXT_OVERRIDES)} ruling sections")


if __name__ == "__main__":
    verify_package(
        package_name="judicial_precedents",
        refs=REFS,
        expected_counts={ref: (1, 1) for ref in REFS},
        loader_script="load_judicial_precedents.py",
        search_terms=(
            "وحدت رویه",
            "دیوان عدالت اداری",
            "کلاهبرداری",
            "حق‌التحریر",
            "دانشگاه فرهنگیان",
            "تأخیر تأدیه",
            "شرکت سهامی",
            "جاسوسی",
        ),
        history_keys=("RVR-847-1403:ruling", "RVR-850-1403:ruling", "DAD-NOTARYFEE-1404:ruling"),
        relation_min=120,
    )
    verify_full_text_overrides()
