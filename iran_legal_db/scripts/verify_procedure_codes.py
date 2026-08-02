# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="procedure_codes",
        refs=("QADM-1379", "QADK-1392"),
        expected_counts={"QADM-1379": (539, 539), "QADK-1392": (570, 570)},
        loader_script="load_procedure_codes.py",
        search_terms=("دادخواست", "بازپرس", "تجدیدنظر"),
        history_keys=("QADM-1379:1", "QADK-1392:1"),
        relation_min=4,
    )
