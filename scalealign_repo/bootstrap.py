from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .manifests import AdapterManifest, verify_patch_digest


RECEIPT = ".scalealign-adapter.json"


class AdapterError(RuntimeError):
    """Raised when an adapter cannot be applied reproducibly."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )


def _receipt_matches(manifest: AdapterManifest) -> bool:
    receipt_path = manifest.submodule / RECEIPT
    if not receipt_path.is_file():
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (
        receipt.get("base_commit") == manifest.base_commit
        and receipt.get("patch_sha256") == manifest.patch_sha256
    )


def apply_manifest(
    manifest: AdapterManifest,
    *,
    dry_run: bool = False,
    force_dirty: bool = False,
) -> str:
    try:
        verify_patch_digest(manifest)
    except ValueError as error:
        raise AdapterError(str(error)) from error

    if not (manifest.submodule / ".git").exists():
        raise AdapterError(f"submodule is not initialized: {manifest.submodule}")

    head = _git(manifest.submodule, "rev-parse", "HEAD").stdout.strip()
    if head != manifest.base_commit:
        raise AdapterError(
            f"{manifest.host} base commit mismatch: expected "
            f"{manifest.base_commit}, got {head}"
        )

    if _receipt_matches(manifest):
        reverse = _git(
            manifest.submodule,
            "apply",
            "--reverse",
            "--check",
            str(manifest.patch),
            check=False,
        )
        if reverse.returncode == 0:
            return "already-applied"
        raise AdapterError(f"{manifest.host} receipt exists but patched files differ")

    dirty = _git(manifest.submodule, "status", "--porcelain").stdout.strip()
    if dirty and not force_dirty:
        raise AdapterError(f"{manifest.host} submodule is dirty; refusing to apply adapter")

    check = _git(
        manifest.submodule,
        "apply",
        "--check",
        str(manifest.patch),
        check=False,
    )
    if check.returncode != 0:
        detail = check.stderr.strip() or check.stdout.strip()
        raise AdapterError(f"{manifest.host} patch check failed: {detail}")
    if dry_run:
        return "ready"

    _git(manifest.submodule, "apply", str(manifest.patch))
    receipt = {
        "adapter": manifest.name,
        "base_commit": manifest.base_commit,
        "patch_sha256": manifest.patch_sha256,
        "source_commit": manifest.source_commit,
    }
    (manifest.submodule / RECEIPT).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return "applied"
