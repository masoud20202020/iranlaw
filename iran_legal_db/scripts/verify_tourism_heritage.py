# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="tourism_heritage",
        refs=(
            "QTIJ-1370", "QOMCG-1382", "QMRB-1398", "QWMCH-1398", "QPHA-1347",
            "QCHM-1309", "QNRM-1352", "QMA-HERITAGE-1392", "AITF-1394", "AITG-1394",
            "AICP-1381", "CWH-1353", "CICH-1384", "AICIE-1354", "AITA-1380",
            "DBECO-1393", "DAD-447774-1404",
        ),
        expected_counts={
            "QTIJ-1370": (12, 12),
            "QOMCG-1382": (12, 12),
            "QMRB-1398": (17, 17),
            "QWMCH-1398": (4, 4),
            "QPHA-1347": (7, 7),
            "QCHM-1309": (20, 20),
            "QNRM-1352": (1, 1),
            "QMA-HERITAGE-1392": (12, 12),
            "AITF-1394": (26, 26),
            "AITG-1394": (8, 8),
            "AICP-1381": (24, 24),
            "CWH-1353": (5, 5),
            "CICH-1384": (6, 6),
            "AICIE-1354": (27, 27),
            "AITA-1380": (34, 34),
            "DBECO-1393": (9, 9),
            "DAD-447774-1404": (3, 3),
        },
        loader_script="load_tourism_heritage.py",
        search_terms=(
            "گردشگری", "میراث فرهنگی", "بافت‌های تاریخی", "حفاری", "وزارت میراث",
            "آثار ملی", "تأسیسات گردشگری", "راهنمایان گردشگری", "اموال فرهنگی",
            "میراث جهانی", "میراث فرهنگی ناملموس", "ورود و صدور اموال فرهنگی",
            "دفاتر خدمات مسافرتی", "بوم‌گردی", "پایانکار",
        ),
        history_keys=(
            "QTIJ-1370:1", "QMRB-1398:1", "QCHM-1309:1", "AITF-1394:1",
            "QMA-HERITAGE-1392:558", "AITA-1380:1", "DBECO-1393:بند-1",
        ),
        relation_min=26,
    )
