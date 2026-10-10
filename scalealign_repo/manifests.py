from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


HOSTS = ("dino", "rfdetr", "dfine")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class AdapterManifest:
    name: str
    host: str
    upstream_url: str
    base_commit: str
    source_commit: str
    submodule: Path
    patch: Path
    patch_sha256: str


def _contained(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"manifest path escapes repository: {candidate}")
    return resolved


def load_manifest(root: Path, host: str) -> AdapterManifest:
    if host not in HOSTS:
        raise ValueError(f"unknown adapter host: {host}")

    root = root.resolve()
    manifest_path = root / "adapters" / host / "adapter.toml"
    with manifest_path.open("rb") as stream:
        data = tomllib.load(stream)

    base_commit = data["upstream"]["base_commit"]
    source_commit = data["source"]["commit"]
    patch_sha256 = data["adapter"]["patch_sha256"]
    for field, value in (
        ("base_commit", base_commit),
        ("source_commit", source_commit),
        ("patch_sha256", patch_sha256),
    ):
        expected = r"[0-9a-f]{64}" if field == "patch_sha256" else r"[0-9a-f]{40}"
        if re.fullmatch(expected, value) is None:
            raise ValueError(f"invalid {field} in {manifest_path}")

    return AdapterManifest(
        name=data["adapter"]["name"],
        host=host,
        upstream_url=data["upstream"]["url"],
        base_commit=base_commit,
        source_commit=source_commit,
        submodule=_contained(root, root / data["upstream"]["submodule"]),
        patch=_contained(manifest_path.parent, manifest_path.parent / data["adapter"]["patch"]),
        patch_sha256=patch_sha256,
    )


def verify_patch_digest(manifest: AdapterManifest) -> None:
    actual = hashlib.sha256(manifest.patch.read_bytes()).hexdigest()
    if actual != manifest.patch_sha256:
        raise ValueError(
            f"patch digest mismatch for {manifest.host}: "
            f"expected {manifest.patch_sha256}, got {actual}"
        )
