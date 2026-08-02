# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="energy",
        refs=("QN-1366", "QAEM-1389", "QOBI-1346", "QMEP-1401", "QSATBA-1395", "AIPC-1395", "QVMN-1391", "QHSE-1394", "QTMN-1353", "QUG-1396", "AHEPL-1394", "ANGC-1356", "QWTE-1399", "AIEO-1403", "DMBE-1403", "AIREP-1394", "DTEP-1404", "AIKBRE-1401", "DAD-POWER-UNAUTH-1403", "DAD-POWERPLANT-ZARGAN-1381", "DAD-ELECTRIC-DIGGING-1401", "DAD-OIL-GAS-RETIRE-1400"),
        expected_counts={
            "QN-1366": (16, 16),
            "QAEM-1389": (75, 75),
            "QOBI-1346": (23, 23),
            "QMEP-1401": (19, 19),
            "QSATBA-1395": (13, 13),
            "AIPC-1395": (16, 16),
            "QVMN-1391": (15, 15),
            "QHSE-1394": (6, 6),
            "QTMN-1353": (11, 11),
            "QUG-1396": (7, 7),
            "AHEPL-1394": (13, 13),
            "ANGC-1356": (49, 49),
            "QWTE-1399": (6, 6),
            "AIEO-1403": (10, 10),
            "DMBE-1403": (10, 10),
            "AIREP-1394": (7, 7),
            "DTEP-1404": (10, 10),
            "AIKBRE-1401": (6, 6),
            "DAD-POWER-UNAUTH-1403": (1, 1),
            "DAD-POWERPLANT-ZARGAN-1381": (1, 1),
            "DAD-ELECTRIC-DIGGING-1401": (1, 1),
            "DAD-OIL-GAS-RETIRE-1400": (1, 1),
        },
        loader_script="load_energy.py",
        search_terms=("نفت", "مصرف انرژی", "بهره‌وری", "نیروی برق", "صنعت برق", "نیروگاه", "انرژی تجدیدپذیر", "ساتبا", "بورس انرژی", "قرارداد نفتی", "بالادستی نفت و گاز", "وزارت نفت", "حمایت از صنعت برق", "وزارت نیرو", "انشعاب برق", "استفاده غیرمجاز", "حریم خطوط", "شرکت ملی گاز", "گاز طبیعی", "پسماند", "خرید تضمینی برق", "گواهی صرفه‌جویی", "تابلو برق سبز", "تعرفه برق", "تعرفه تجدیدپذیر", "ماده ۶۱", "جهش تولید دانش‌بنیان", "پاسخگویی بار", "استفاده غیرمجاز از برق", "زرگان", "تیر برق", "بازنشستگی صنعت نفت", "دیوان عدالت اداری"),
        history_keys=("QN-1366:1", "QAEM-1389:18", "QOBI-1346:1", "QMEP-1401:1", "QSATBA-1395:1", "AIPC-1395:1", "QVMN-1391:1", "QHSE-1394:1", "QTMN-1353:1", "QUG-1396:1", "AHEPL-1394:1", "ANGC-1356:1", "QWTE-1399:1", "AIEO-1403:1", "DMBE-1403:1", "AIREP-1394:1", "DTEP-1404:1", "AIKBRE-1401:1", "DAD-POWER-UNAUTH-1403:1", "DAD-POWERPLANT-ZARGAN-1381:1", "DAD-ELECTRIC-DIGGING-1401:1", "DAD-OIL-GAS-RETIRE-1400:1"),
        relation_min=72,
    )
