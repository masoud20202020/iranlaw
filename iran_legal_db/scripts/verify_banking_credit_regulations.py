# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="banking_credit_regulations",
        refs=("AEMAG-1393", "APDA-1404"),
        expected_counts={"AEMAG-1393": (109, 109), "APDA-1404": (18, 18)},
        loader_script="load_banking_credit_regulations.py",
        search_terms=("مؤسسه اعتباری", "پایگاه داده اعتباری", "اعتبارسنجی"),
        history_keys=("AEMAG-1393:1", "APDA-1404:1"),
        relation_min=1,
    )
