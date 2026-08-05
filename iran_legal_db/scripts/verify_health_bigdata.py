#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifier for the additional health/medicine bigdata package."""
from verification_utils import verify_package


if __name__ == "__main__":
    verify_package(
        package_name="health_bigdata",
        refs=(
            "AIFU-1390", "AIFAC-1390", "AIRDI-1368", "AICPN-1388", "AIMED-1393",
            "AIBRAND-1328", "AIMH-1398", "AIDR-1393", "BJC-1400",
            "AIEPO-1396-11-04", "AIEPO-1396-11-28", "DMEW-1386", "QCP-1388",
            "QASAF-1390", "QEVB-1368", "QVET-1350", "QLOP-1366", "QHAP-1397",
            "QDRA-1359", "DMCAP-1400",
        ),
        expected_counts={
            "AIFU-1390": (106, 106),
            "AIFAC-1390": (129, 129),
            "AIRDI-1368": (62, 62),
            "AICPN-1388": (9, 9),
            "AIMED-1393": (28, 28),
            "AIBRAND-1328": (8, 8),
            "AIMH-1398": (12, 12),
            "AIDR-1393": (23, 23),
            "BJC-1400": (26, 26),
            "AIEPO-1396-11-04": (9, 9),
            "AIEPO-1396-11-28": (9, 9),
            "DMEW-1386": (73, 73),
            "QCP-1388": (1, 1),
            "QASAF-1390": (35, 35),
            "QEVB-1368": (1, 1),
            "QVET-1350": (21, 21),
            "QLOP-1366": (1, 1),
            "QHAP-1397": (5, 5),
            "QDRA-1359": (25, 0),
            "DMCAP-1400": (1, 1),
        },
        loader_script="load_health_bigdata.py",
        search_terms=(
            "دانشگاه", "دارو", "اورژانس", "مجانین", "پسماند", "دامپزشکی",
            "تبلیغات", "تخلیه", "مواد مخدر", "ظرفیت پزشکی",
        ),
        history_keys=(
            "AIFU-1390:1", "AIRDI-1368:1", "DMEW-1386:1", "QDRA-1359:1",
        ),
        relation_min=30,
    )
