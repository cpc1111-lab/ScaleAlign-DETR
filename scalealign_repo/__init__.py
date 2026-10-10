"""Repository tooling for the ScaleAlign detector adapters."""

from .manifests import HOSTS, AdapterManifest, load_manifest

__all__ = ["HOSTS", "AdapterManifest", "load_manifest"]
