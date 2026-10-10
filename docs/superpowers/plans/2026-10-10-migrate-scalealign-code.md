# ScaleAlign Code Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the existing DINO, RF-DETR, and D-FINE ScaleAlign work into the standalone repository as reproducible adapters over pinned upstream submodules.

**Architecture:** Each host repository is pinned as a Git submodule at its clean upstream base. A host adapter contains one complete binary-safe patch and a TOML manifest with the base revision and patch digest; the bootstrap command validates and applies adapters idempotently. Repository-level tests validate manifests, hashes, clean application, forbidden artifacts, and documentation commands.

**Tech Stack:** Git submodules and patches, Python 3.11+, `tomllib`, `hashlib`, `subprocess`, pytest.

---

### Task 1: Repository contract and manifest loader

**Files:**
- Create: `tests/test_manifests.py`
- Create: `scalealign_repo/__init__.py`
- Create: `scalealign_repo/manifests.py`
- Create: `pyproject.toml`
- Create: `.gitignore`

- [x] Write tests asserting that all three manifests exist, use 40-character base commits, reference existing patches, and match SHA-256 digests.
- [x] Run `python -m pytest tests/test_manifests.py -q` and confirm failure because the package and manifests do not exist.
- [x] Implement typed manifest loading with `tomllib`, path containment checks, digest validation, and host enumeration.
- [x] Run the test again and confirm that only missing adapter assets remain.
- [x] Commit the repository contract.

### Task 2: Pinned upstream submodules

**Files:**
- Create: `.gitmodules`
- Create gitlinks: `third_party/DINO`, `third_party/RF-DETR`, `third_party/D-FINE`
- Modify: `tests/test_manifests.py`

- [x] Add a failing test asserting each submodule URL and gitlink revision equals its manifest.
- [x] Run the focused test and confirm failure before adding submodules.
- [x] Add official upstream submodules and check out DINO `d84a491d41898b3befd8294d1cf2614661fc0953`, RF-DETR `c107a748bbf369ad455cd41d85b9c91a5a0ecbad`, and D-FINE `d6694750683b0c7e9f523ba6953d16f112a376ae`.
- [x] Re-run the focused test and commit the pinned upstreams.

### Task 3: Migrate host code as deterministic adapters

**Files:**
- Create: `adapters/dino/adapter.toml`
- Create: `adapters/dino/scalealign.patch`
- Create: `adapters/rfdetr/adapter.toml`
- Create: `adapters/rfdetr/scalealign.patch`
- Create: `adapters/dfine/adapter.toml`
- Create: `adapters/dfine/scalealign.patch`
- Modify: `tests/test_manifests.py`

- [x] Add a failing clean-application test that copies each pinned tree to a temporary Git worktree and runs `git apply --check` on its adapter patch.
- [x] Generate binary-safe patches from temporary indexes so tracked changes and explicitly selected untracked ScaleAlign files are included without changing source repository indexes.
- [x] Exclude checkpoints, datasets, environments, caches, generated images, experiment directories, personal paths, and unrelated planning documents.
- [x] Write manifests with exact base revisions, patch paths, SHA-256 digests, and source snapshot revisions.
- [x] Run manifest and clean-application tests, then commit all three adapters.

### Task 4: Idempotent bootstrap command

**Files:**
- Create: `tests/test_bootstrap.py`
- Create: `scalealign_repo/bootstrap.py`
- Create: `scripts/bootstrap.py`

- [x] Add failing tests for dry-run validation, first application, repeated application, wrong base revision, dirty-tree refusal, and digest mismatch.
- [x] Implement validation and application using argument arrays rather than shell interpolation.
- [x] Record `.scalealign-adapter.json` receipts inside applied submodules and use the receipt plus patch reverse-check to recognize an already-applied adapter.
- [x] Run `python -m pytest tests/test_bootstrap.py -q`, then run the complete test suite and commit.

### Task 5: Verification and user documentation

**Files:**
- Create: `tests/test_repository_policy.py`
- Create: `scalealign_repo/verify.py`
- Create: `scripts/verify.py`
- Create: `README.md`
- Create: `docs/upstream.md`
- Create: `LICENSE`
- Create: `CITATION.cff`
- Modify: `docs/specs/2026-10-10-standalone-repository-design.md`

- [x] Add failing policy tests for forbidden large files, absolute workstation paths, credentials, missing attribution, and stale patch hashes.
- [x] Implement repository verification and concise CLI output.
- [x] Document clone, submodule setup, adapter bootstrap, host-specific training and evaluation entrypoints, and artifact exclusions.
- [x] Remove special-status terminology from the design and document all adapters uniformly.
- [x] Run `python -m pytest -q`, `python scripts/verify.py`, and `git diff --check`.
- [x] Commit documentation and verification tooling.

### Task 6: Publish migrated repository

**Files:**
- Modify: Git remote branch `origin/main`

- [ ] Confirm `git status --short` contains only the intended migration changes.
- [ ] Confirm no tracked file exceeds the repository policy limit and no checkpoint/data output is staged.
- [ ] Push `main` to `ssh://git@ssh.github.com:443/cpc1111-lab/ScaleAlign-DETR.git`.
- [ ] Verify the remote `main` hash with `git ls-remote --heads origin main`.
