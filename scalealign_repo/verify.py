from __future__ import annotations

import subprocess
from pathlib import Path

from .manifests import HOSTS, load_manifest, verify_patch_digest


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def verify_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for host in HOSTS:
        try:
            manifest = load_manifest(root, host)
            verify_patch_digest(manifest)
        except (OSError, ValueError, KeyError) as error:
            errors.append(f"{host}: {error}")
            continue

        if not (manifest.submodule / ".git").exists():
            errors.append(f"{host}: submodule is not initialized")
            continue
        head = _git(manifest.submodule, "rev-parse", "HEAD")
        if head.returncode != 0 or head.stdout.strip() != manifest.base_commit:
            errors.append(f"{host}: submodule is not at the pinned base commit")
            continue

        forward = _git(manifest.submodule, "apply", "--check", str(manifest.patch))
        reverse = _git(
            manifest.submodule,
            "apply",
            "--reverse",
            "--check",
            str(manifest.patch),
        )
        if forward.returncode != 0 and reverse.returncode != 0:
            errors.append(f"{host}: patch is neither cleanly applicable nor fully applied")
    return errors
