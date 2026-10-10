from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".ckpt", ".onnx", ".pt", ".pth", ".engine"}


def _repository_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        ROOT / line
        for line in output.splitlines()
        if line and not line.startswith("third_party/")
    ]


def test_repository_contains_no_model_or_dataset_artifacts() -> None:
    files = _repository_files()
    forbidden = [path for path in files if path.suffix.lower() in FORBIDDEN_SUFFIXES]
    oversized = [path for path in files if path.is_file() and path.stat().st_size > 5_000_000]

    assert forbidden == []
    assert oversized == []


def test_authored_files_do_not_contain_workstation_paths() -> None:
    violations: list[str] = []
    for path in _repository_files():
        if not path.is_file():
            continue
        data = path.read_bytes()
        forbidden_paths = (b"/media/" + b"e222", b"/home/" + b"e222")
        if any(value in data for value in forbidden_paths):
            violations.append(str(path.relative_to(ROOT)))
    assert violations == []


def test_public_documentation_covers_all_hosts() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    upstream = (ROOT / "docs" / "upstream.md").read_text(encoding="utf-8")

    for name in ("DINO", "RF-DETR", "D-FINE"):
        assert name in readme
        assert name in upstream
    assert "scripts/bootstrap.py" in readme
    assert "scripts/verify.py" in readme
