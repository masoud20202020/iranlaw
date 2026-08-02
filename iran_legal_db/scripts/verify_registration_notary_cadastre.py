# -*- coding: utf-8 -*-
from verification_utils import get_connection, require, verify_package


def extra_checks():
    conn = get_connection()
    try:
        refs = ["QS-1310", "QDSR-1354", "QCH-1393", "QTVFS-1390", "AITVFS-1391", "AIDSR-1399", "AIESL-1387", "AQS-1317", "RVR-569-1370", "RVR-623-1377", "RVR-672-1383", "RVR-784-1398", "QAFM-1357", "AIAFM-1358"]
        docs = {}
        for ref in refs:
            row = conn.execute("SELECT id FROM documents WHERE reference_code=?", (ref,)).fetchone()
            require(row, f"missing {ref}")
            docs[ref] = row["id"]
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='QCH-1393:10bis'", (docs["QCH-1393"],)).fetchone()[0] == 1, "missing cadastre inserted article")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type='amends'", (docs["QCH-1393"], docs["QS-1310"])).fetchone()[0] >= 1, "cadastre must amend/abrogate registration article 156")
        require("نسخ" in conn.execute("SELECT text FROM articles WHERE article_key='QS-1310:156'").fetchone()["text"], "QS:156 should be marked repealed")
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='QTVFS-1390:18'", (docs["QTVFS-1390"],)).fetchone()[0] == 1, "missing untitled lands article 18")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=?", (docs["QTVFS-1390"], docs["QS-1310"])).fetchone()[0] >= 1, "untitled lands must link to registration law")
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='AITVFS-1391:21'", (docs["AITVFS-1391"],)).fetchone()[0] == 1, "missing untitled lands bylaw article 21")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type='implements'", (docs["AITVFS-1391"], docs["QTVFS-1390"])).fetchone()[0] >= 1, "bylaw must implement untitled lands law")
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='AIDSR-1399:93'", (docs["AIDSR-1399"],)).fetchone()[0] == 1, "missing notary bylaw article 93")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type='implements'", (docs["AIDSR-1399"], docs["QDSR-1354"])).fetchone()[0] >= 1, "notary bylaw must implement notary law")
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='AIESL-1387:203'", (docs["AIESL-1387"],)).fetchone()[0] == 1, "missing execution bylaw article 203")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type='implements'", (docs["AIESL-1387"], docs["QS-1310"])).fetchone()[0] >= 1, "execution bylaw must implement registration law")
        require(conn.execute("SELECT COUNT(*) FROM articles WHERE document_id=? AND article_key='AQS-1317:164'", (docs["AQS-1317"],)).fetchone()[0] == 1, "missing registration bylaw article 164")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=? AND relation_type='implements'", (docs["AQS-1317"], docs["QS-1310"])).fetchone()[0] >= 1, "registration bylaw must implement registration law")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=?", (docs["RVR-784-1398"], docs["AIESL-1387"])).fetchone()[0] >= 1, "ruling 784 must link to execution bylaw")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=?", (docs["RVR-672-1383"], docs["QS-1310"])).fetchone()[0] >= 3, "ruling 672 must link to registration articles 46-48")
        require(conn.execute("SELECT COUNT(*) FROM relations WHERE from_document_id=? AND to_document_id=?", (docs["AIAFM-1358"], docs["QAFM-1357"])).fetchone()[0] >= 1, "afraz bylaw must implement afraz law")
    finally:
        conn.close()


if __name__ == "__main__":
    extra_checks()
    verify_package(
        package_name="registration_notary_cadastre",
        refs=("QS-1310", "QDSR-1354", "QCH-1393", "QTVFS-1390", "AITVFS-1391", "AIDSR-1399", "AIESL-1387", "AQS-1317", "RVR-569-1370", "RVR-623-1377", "RVR-672-1383", "RVR-784-1398", "QAFM-1357", "AIAFM-1358"),
        expected_counts={"QS-1310": (157, 157), "QDSR-1354": (76, 76), "QCH-1393": (21, 21), "QTVFS-1390": (18, 18), "AITVFS-1391": (21, 21), "AIDSR-1399": (93, 93), "AIESL-1387": (203, 203), "AQS-1317": (164, 164), "RVR-569-1370": (1, 1), "RVR-623-1377": (1, 1), "RVR-672-1383": (1, 1), "RVR-784-1398": (1, 1), "QAFM-1357": (6, 6), "AIAFM-1358": (10, 10)},
        loader_script="load_registration_notary_cadastre.py",
        search_terms=("حدنگار", "دفترخانه", "فاقد سند رسمی"),
        history_keys=("QS-1310:22", "QCH-1393:20"),
        relation_min=4,
    )
    extra_checks()
