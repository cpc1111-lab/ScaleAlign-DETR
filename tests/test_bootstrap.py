from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scalealign_repo.bootstrap import AdapterError, apply_manifest
from scalealign_repo.manifests import AdapterManifest


ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def adapter(tmp_path: Path) -> AdapterManifest:
    repo = tmp_path / "host"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "model.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "add", "model.py")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")

    patch = tmp_path / "scalealign.patch"
    patch.write_text(
        """diff --git a/model.py b/model.py
index 5c49f9d..44b6934 100644
--- a/model.py
+++ b/model.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
""",
        encoding="utf-8",
    )
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    return AdapterManifest(
        name="test adapter",
        host="test",
        upstream_url="https://example.invalid/test.git",
        base_commit=base,
        source_commit="1" * 40,
        submodule=repo,
        patch=patch,
        patch_sha256=digest,
    )


def test_apply_manifest_is_idempotent(adapter: AdapterManifest) -> None:
    assert apply_manifest(adapter) == "applied"
    assert (adapter.submodule / "model.py").read_text(encoding="utf-8") == "VALUE = 2\n"
    assert apply_manifest(adapter) == "already-applied"


def test_dry_run_does_not_modify_tree(adapter: AdapterManifest) -> None:
    assert apply_manifest(adapter, dry_run=True) == "ready"
    assert (adapter.submodule / "model.py").read_text(encoding="utf-8") == "VALUE = 1\n"


def test_rejects_wrong_base(adapter: AdapterManifest) -> None:
    (adapter.submodule / "other.txt").write_text("next\n", encoding="utf-8")
    _git(adapter.submodule, "add", "other.txt")
    _git(adapter.submodule, "commit", "-qm", "next")

    with pytest.raises(AdapterError, match="base commit"):
        apply_manifest(adapter)


def test_rejects_dirty_tree(adapter: AdapterManifest) -> None:
    (adapter.submodule / "model.py").write_text("LOCAL = True\n", encoding="utf-8")

    with pytest.raises(AdapterError, match="dirty"):
        apply_manifest(adapter)


def test_rejects_patch_digest_mismatch(adapter: AdapterManifest) -> None:
    adapter.patch.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(AdapterError, match="digest"):
        apply_manifest(adapter)


def test_cli_defaults_to_all_hosts() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bootstrap.py", "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "dino: ready",
        "rfdetr: ready",
        "dfine: ready",
    ]
