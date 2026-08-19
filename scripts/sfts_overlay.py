#!/usr/bin/env python3
"""Local overlay entry. start.sh / start.bat / the in-app button all call this."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.updater.overlay import (  # noqa: E402
    STATUS_FAILED,
    STATUS_SKIPPED_DAILY,
    STATUS_UPDATED,
    STATUS_UP_TO_DATE,
    run_overlay,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="SFTS official-release overlay")
    parser.add_argument("--daily", action="store_true", help="Check at most once per day")
    parser.add_argument("--apply", action="store_true", help="Apply if a newer official tag exists")
    parser.add_argument("--check", action="store_true", help="Check only (still records lastCheckAt)")
    args = parser.parse_args()
    apply = args.apply or args.daily or not args.check
    if args.check and not args.apply and not args.daily:
        apply = False
    status = run_overlay(ROOT, daily=args.daily, apply=apply)
    print(f"STATUS={status}")
    if status == STATUS_UPDATED:
        print("Please close this window and run start.bat / start.sh again.")
    elif status == STATUS_UP_TO_DATE:
        print("Already on the latest official release stamp.")
    elif status == STATUS_SKIPPED_DAILY:
        print("Skipped (already checked today).")
    elif status == STATUS_FAILED:
        print("Update check failed. The previous files were kept.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
