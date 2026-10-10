from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from scalealign_repo.manifests import HOSTS, load_manifest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("host", HOSTS)
def test_manifest_references_a_valid_patch(host: str) -> None:
    manifest = load_manifest(ROOT, host)

    assert len(manifest.base_commit) == 40
    assert all(character in "0123456789abcdef" for character in manifest.base_commit)
    assert manifest.patch.is_file()
    assert hashlib.sha256(manifest.patch.read_bytes()).hexdigest() == manifest.patch_sha256


@pytest.mark.parametrize("host", HOSTS)
def test_patch_applies_to_pinned_submodule(host: str) -> None:
    manifest = load_manifest(ROOT, host)
    submodule = ROOT / manifest.submodule

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=submodule,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == manifest.base_commit

    subprocess.run(
        ["git", "apply", "--check", str(manifest.patch)],
        cwd=submodule,
        check=True,
        capture_output=True,
        text=True,
    )
