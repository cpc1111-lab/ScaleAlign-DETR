#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scalealign_repo.verify import verify_repository  # noqa: E402


def main() -> int:
    errors = verify_repository(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("OK manifests, patch digests, submodule revisions, and patch state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
