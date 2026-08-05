#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore archived uploaded HTML/TXT sources into ``data/`` for rebuilding seeds."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
ARCHIVE_PATH = DATA_ROOT / "archive" / "uploaded_category_sources.tar.gz"
MANIFEST_PATH = DATA_ROOT / "archive" / "uploaded_category_sources_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_members(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = tar.getmembers()
    for member in members:
        target = (DATA_ROOT / member.name).resolve()
        if target != DATA_ROOT.resolve() and DATA_ROOT.resolve() not in target.parents:
            raise SystemExit(f"unsafe archive member: {member.name}")
        if member.issym() or member.islnk():
            raise SystemExit(f"links are not allowed in source archive: {member.name}")
    return members


def verify(manifest: dict) -> None:
    missing: list[str] = []
    mismatched: list[str] = []
    for row in manifest["files"]:
        path = DATA_ROOT / row["path"]
        if not path.is_file():
            missing.append(row["path"])
        elif path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            mismatched.append(row["path"])
    if missing or mismatched:
        details = []
        if missing:
            details.append(f"missing={len(missing)}")
        if mismatched:
            details.append(f"mismatched={len(mismatched)}")
        raise SystemExit("restored source verification failed: " + ", ".join(details))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()
    if not ARCHIVE_PATH.is_file() or not MANIFEST_PATH.is_file():
        raise SystemExit(f"archive or manifest missing: {ARCHIVE_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if sha256(ARCHIVE_PATH) != manifest["archive_sha256"]:
        raise SystemExit("archive sha256 does not match manifest")

    with tarfile.open(ARCHIVE_PATH, mode="r:gz") as tar:
        members = safe_members(tar)
        existing = [DATA_ROOT / member.name for member in members if (DATA_ROOT / member.name).exists()]
        if existing and not args.force:
            raise SystemExit(f"{len(existing)} source paths already exist; use --force to overwrite")
        tar.extractall(DATA_ROOT, members=members)
    verify(manifest)
    print(f"[OK] restored and verified {manifest['file_count']} files / {manifest['total_bytes']} bytes")
    print("[NEXT] python3 scripts/build_uploaded_data_seeds.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
