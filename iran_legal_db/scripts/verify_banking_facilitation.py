# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="banking_facilitation",
        refs=("QTAB-1386",),
        expected_counts={"QTAB-1386": (9, 9)},
        loader_script="load_banking_facilitation.py",
        search_terms=("تسهیلات بانکی", "وثیقه", "طرح"),
        history_keys=("QTAB-1386:1",),
    )
