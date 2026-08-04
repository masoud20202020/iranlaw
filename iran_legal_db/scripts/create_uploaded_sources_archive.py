#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create the canonical archive and checksum manifest for uploaded HTML/TXT sources.

The normalized seed and SQLite database are the active data layer.  The raw
category trees are archived separately so they can be restored for a full seed
rebuild without keeping hundreds of web-export files in the working tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
ARCHIVE_DIR = DATA_ROOT / "archive"
ARCHIVE_PATH = ARCHIVE_DIR / "uploaded_category_sources.tar.gz"
MANIFEST_PATH = ARCHIVE_DIR / "uploaded_category_sources_manifest.json"

CATEGORIES = (
    "آموزش_و_پرورش", "اراضی_و_املاک", "ایثارگران", "بین_الملل", "ثبت_و_اسناد",
    "حقوقی", "حمل_و_نقل", "خانواده", "داوری", "شهر_و_شهرداری", "مالکیت_معنوی",
    "مالی", "مالیاتی", "محیط_زیست", "موجر_و_مستأجر", "نظامی_و_انتظامی", "ورزشی", "وکالت",
)
FORMATS = {".html": "html", ".txt": "txt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect() -> list[dict]:
    rows: list[dict] = []
    for category in CATEGORIES:
        root = DATA_ROOT / category
        for path in sorted(root.rglob("*")) if root.exists() else ():
            if not path.is_file() or path.suffix.lower() not in FORMATS:
                continue
            rel = path.relative_to(DATA_ROOT).as_posix()
            rows.append({
                "path": rel,
                "category": category,
                "format": FORMATS[path.suffix.lower()],
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ARCHIVE_PATH), help="archive output path")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH), help="manifest output path")
    args = parser.parse_args(argv)

    files = collect()
    if not files:
        raise SystemExit("no raw uploaded HTML/TXT files found; restore the archive first")
    archive = Path(args.output)
    manifest_path = Path(args.manifest)
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Build atomically so an interrupted compression never becomes the canonical archive.
    with tempfile.NamedTemporaryFile(prefix=archive.name + ".", dir=archive.parent, delete=False) as tmp:
        temp_archive = Path(tmp.name)
    try:
        with tarfile.open(temp_archive, mode="w:gz") as tar:
            for row in files:
                tar.add(DATA_ROOT / row["path"], arcname=row["path"], recursive=False)
        temp_archive.replace(archive)
    finally:
        temp_archive.unlink(missing_ok=True)

    archive_hash = sha256(archive)
    manifest = {
        "format": 1,
        "generated_at": date.today().isoformat(),
        "archive": archive.relative_to(ROOT).as_posix(),
        "archive_sha256": archive_hash,
        "categories": list(CATEGORIES),
        "file_count": len(files),
        "total_bytes": sum(row["bytes"] for row in files),
        "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] archived {len(files)} files / {manifest['total_bytes']} bytes")
    print(f"[OK] archive: {archive} ({archive.stat().st_size} bytes)")
    print(f"[OK] archive sha256: {archive_hash}")
    print(f"[OK] manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
