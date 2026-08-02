#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اجرای سراسری verifierهای بسته‌های حقوقی.

نمونه استفاده:
    python3 scripts/verify_all.py --list
    python3 scripts/verify_all.py
    python3 scripts/verify_all.py --continue-on-error
    python3 scripts/verify_all.py --only insurance,aml,banking
    python3 scripts/verify_all.py --skip-flask-check

نکته: بسیاری از verifierهای موجود رابط Flask را هم تست می‌کنند؛ بنابراین اگر Flask نصب نیست
ابتدا در یک محیط مجازی نصب کنید:
    python3 -m venv /tmp/iranlaw-venv
    /tmp/iranlaw-venv/bin/python -m pip install 'flask>=3.1,<3.2'
    /tmp/iranlaw-venv/bin/python scripts/verify_all.py
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


@dataclass
class Result:
    name: str
    path: Path
    returncode: int
    seconds: float
    stdout: str
    stderr: str


def discover() -> list[Path]:
    return sorted(
        p for p in SCRIPTS.glob("verify_*.py")
        if p.name != "verify_all.py" and not p.name.startswith("verify__")
    )


def flask_available() -> bool:
    return importlib.util.find_spec("flask") is not None


def filter_scripts(paths: list[Path], only: str | None, exclude: str | None) -> list[Path]:
    if only:
        tokens = [t.strip() for t in only.split(",") if t.strip()]
        paths = [p for p in paths if any(t in p.stem.replace("verify_", "") for t in tokens)]
    if exclude:
        tokens = [t.strip() for t in exclude.split(",") if t.strip()]
        paths = [p for p in paths if not any(t in p.stem.replace("verify_", "") for t in tokens)]
    return paths


def run_one(path: Path, timeout: int) -> Result:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return Result(
        name=path.stem.replace("verify_", ""),
        path=path,
        returncode=proc.returncode,
        seconds=time.perf_counter() - started,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def print_result(result: Result, verbose: bool = False) -> None:
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"[{status}] {result.name} ({result.seconds:.1f}s)")
    if verbose or result.returncode != 0:
        if result.stdout.strip():
            print("--- stdout ---")
            print(result.stdout.rstrip())
        if result.stderr.strip():
            print("--- stderr ---")
            print(result.stderr.rstrip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="اجرای همه verify_*.py های پروژه")
    parser.add_argument("--list", action="store_true", help="فقط فهرست verifierها را چاپ کند")
    parser.add_argument("--only", help="فقط verifierهایی که نامشان شامل این عبارت‌هاست؛ جداشده با ویرگول")
    parser.add_argument("--exclude", help="حذف verifierهایی که نامشان شامل این عبارت‌هاست؛ جداشده با ویرگول")
    parser.add_argument("--timeout", type=int, default=420, help="حداکثر زمان هر verifier بر حسب ثانیه")
    parser.add_argument("--continue-on-error", action="store_true", help="پس از خطای یک verifier ادامه دهد")
    parser.add_argument("--verbose", action="store_true", help="stdout/stderr موفق‌ها را هم چاپ کند")
    parser.add_argument("--skip-flask-check", action="store_true", help="کنترل اولیه نصب Flask را انجام ندهد")
    args = parser.parse_args(argv)

    paths = filter_scripts(discover(), args.only, args.exclude)
    if args.list:
        for p in paths:
            print(p.name)
        print(f"total: {len(paths)}")
        return 0

    if not args.skip_flask_check and not flask_available():
        print("[ERROR] Flask نصب نیست، در حالی که بیشتر verifierها app Flask را تست می‌کنند.", file=sys.stderr)
        print("یک محیط مجازی بسازید و با همان Python اجرا کنید؛ مثال:", file=sys.stderr)
        print("  python3 -m venv /tmp/iranlaw-venv", file=sys.stderr)
        print("  /tmp/iranlaw-venv/bin/python -m pip install 'flask>=3.1,<3.2'", file=sys.stderr)
        print("  /tmp/iranlaw-venv/bin/python scripts/verify_all.py", file=sys.stderr)
        return 2

    print(f"Running {len(paths)} verifier(s) with {sys.executable}")
    started_all = time.perf_counter()
    results: list[Result] = []
    for i, path in enumerate(paths, 1):
        print(f"\n[{i}/{len(paths)}] {path.name}")
        try:
            result = run_one(path, args.timeout)
        except subprocess.TimeoutExpired as exc:
            result = Result(
                name=path.stem.replace("verify_", ""),
                path=path,
                returncode=124,
                seconds=args.timeout,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\nTimeout after {args.timeout}s",
            )
        results.append(result)
        print_result(result, args.verbose)
        if result.returncode != 0 and not args.continue_on_error:
            break

    failed = [r for r in results if r.returncode != 0]
    print("\n=== verify_all summary ===")
    print(f"executed: {len(results)}/{len(paths)}")
    print(f"passed:   {len(results) - len(failed)}")
    print(f"failed:   {len(failed)}")
    print(f"elapsed:  {time.perf_counter() - started_all:.1f}s")
    if failed:
        print("failed packages:", ", ".join(r.name for r in failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
