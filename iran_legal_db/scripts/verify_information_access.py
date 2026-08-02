# -*- coding: utf-8 -*-
from verification_utils import verify_package

if __name__ == "__main__":
    verify_package(
        package_name="information_access",
        refs=("QDDA-1388", "AIDDA-1393"),
        expected_counts={"QDDA-1388": (23, 23), "AIDDA-1393": (11, 11)},
        loader_script="load_information_access.py",
        search_terms=("دسترسی آزاد", "اطلاعات شخصی", "مؤسسات عمومی"),
        history_keys=("QDDA-1388:1", "AIDDA-1393:1"),
        relation_min=1,
    )
