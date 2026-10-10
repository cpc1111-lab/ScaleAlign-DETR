#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scalealign_repo.bootstrap import AdapterError, apply_manifest  # noqa: E402
from scalealign_repo.manifests import HOSTS, load_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply ScaleAlign host adapters")
    parser.add_argument("hosts", nargs="*", choices=HOSTS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-dirty", action="store_true")
    args = parser.parse_args()

    try:
        for host in args.hosts or HOSTS:
            manifest = load_manifest(ROOT, host)
            result = apply_manifest(
                manifest,
                dry_run=args.dry_run,
                force_dirty=args.force_dirty,
            )
            print(f"{host}: {result}")
    except (AdapterError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
