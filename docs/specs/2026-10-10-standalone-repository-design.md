# Standalone ScaleAlign-DETR Repository Design

Date: 2026-10-10  
Owner: cpc

## Objective

Create `ScaleAlign-DETR` as an independent, reproducible repository that carries
the ScaleAlign method and integrates it with DINO, RF-DETR, and D-FINE without
copying complete upstream repositories into the project history.

The repository must let a new user reproduce the exact supported source trees
from pinned upstream revisions, apply the ScaleAlign integrations, validate the
result, and launch the documented experiments. Dataset contents, checkpoints,
virtual environments, and generated training outputs are not versioned.

## Scope

The first local release contains:

- The complete DINO ScaleAlign S/M/L integration, including ESM, SGQG, SAA,
  diagnostics, profiling utilities, experiment configurations, and tests.
- The complete RF-DETR-2XL ScaleAlign integration, including the multi-scale
  decoder path, matched continuation configurations, diagnostics, and tests.
- The current D-FINE ScalePrior integration, including its model wiring,
  configuration, utilities, and supporting tests.
- Framework-neutral documentation, schemas, result records, and mathematical
  reference utilities where they can be shared without changing proven host
  implementations.

The first release does not refactor all three detectors onto a single runtime
implementation. Their tensor layouts, registries, decoder APIs, and training
contracts differ enough that doing so would increase regression risk. Shared
interfaces are documented centrally; tested host-specific implementations stay
inside adapters.

## Repository Layout

```text
ScaleAlign-DETR/
  README.md
  LICENSE
  CITATION.cff
  pyproject.toml
  .gitmodules
  scalealign/
    geometry.py
    metrics.py
    schemas.py
  adapters/
    dino/
      adapter.toml
      patches/
      overlay/
    rfdetr/
      adapter.toml
      patches/
      overlay/
    dfine/
      adapter.toml
      patches/
      overlay/
  configs/
    dino/
    rfdetr/
    dfine/
  scripts/
    bootstrap.py
    verify.py
  tests/
  docs/
    specs/
    experiments/
    upstream.md
  results/
    manifests/
    tables/
  third_party/
    DINO/
    RF-DETR/
    D-FINE/
```

`third_party/*` entries are Git submodules. Adapter files are owned by this
repository; generated patched trees are never committed as ordinary files.

## Pinned Upstreams

| Host | Upstream URL | Branch lineage | Pinned clean base |
|---|---|---|---|
| DINO | `https://github.com/IDEA-Research/DINO.git` | `main` | `d84a491d41898b3befd8294d1cf2614661fc0953` |
| RF-DETR | `https://github.com/roboflow/rf-detr.git` | `develop` | `c107a748bbf369ad455cd41d85b9c91a5a0ecbad` |
| D-FINE | `https://github.com/Peterande/D-FINE.git` | `master` | `d6694750683b0c7e9f523ba6953d16f112a376ae` |

The submodule gitlink must point to the pinned clean base, not to a local
ScaleAlign branch. This keeps provenance explicit and makes the adapter itself
the complete record of our changes.

## Adapter Contract

Each `adapter.toml` records:

- adapter name and host framework;
- upstream URL and exact base commit;
- ordered patch list and SHA-256 digest for every patch;
- overlay file list and SHA-256 digest for every file;
- supported Python and PyTorch ranges;
- verification commands;
- configuration entrypoints and expected output schema.

Tracked modifications relative to the pinned base are exported as ordered Git
patches. New files that are clearer as standalone assets, such as experiment
configuration, scripts, tests, and documentation, are stored in `overlay/`
while retaining their upstream-relative paths. The manifest makes both forms
part of one atomic adapter.

`scripts/bootstrap.py` performs these steps:

1. Check that every submodule is initialized at its manifest commit.
2. Refuse to modify a dirty submodule unless `--force-dirty` is explicitly
   supplied.
3. Verify all patch and overlay digests.
4. Run `git apply --check` for the complete ordered series.
5. Apply patches and copy overlays without overwriting unrecorded local files.
6. Write a machine-readable bootstrap receipt containing upstream commits,
   adapter digests, timestamp, and tool versions.

The command is idempotent: a fully applied adapter reports success without
duplicating changes. A partially applied or mismatched tree fails with a
specific recovery message.

## Source Selection

### DINO

The adapter is built from the current `scalealign-sml` branch plus selected
uncommitted worktree improvements. It includes the S/M/L model definitions,
full ESM/SGQG/SAA integration, stride-calibrated geometric SAA, query and
attention diagnostics, embedding-quality measurement, complexity profiling,
qualitative simulation, configurations, and their tests.

Local datasets, checkpoints, output directories, caches, and generated figure
bitmaps are excluded. Small JSON/CSV result summaries may be included only when
their provenance manifest records the checkpoint hash, dataset split, command,
seed, and source commit.

### RF-DETR

The adapter is built from the current `scalealign-rfdetr-2xl` branch plus the
selected local configuration and launcher fixes. It includes continuous scale
state, SGQG query selection, SAA before deformable-attention softmax, per-layer
state refresh, multi-scale warm start, matched continuation controls,
diagnostics, and tests.

The `experiments/` directory, downloaded weights, COCO data, virtual
environments, and run logs are excluded.

### D-FINE

Only the ScalePrior-related source, configuration, and supporting tools are
included in the first adapter. Dataset path edits, personal inference scripts,
IDE state, CUDA/Conda caches, outputs, external repositories, and unrelated
local modifications are excluded.

The README and manifest describe the implemented D-FINE components directly,
without assigning a special adapter status.

## Configuration And Data

Published configurations use repository-relative paths or command-line
overrides. They must not contain workstation-specific absolute paths.

Dataset and checkpoint files are external inputs. Each supported experiment has
a manifest containing expected directory layout, download/source URL where
licensing permits, file size, and SHA-256. Commands accept explicit
`--data-root`, `--checkpoint`, and `--output-dir` arguments.

Secrets, authentication tokens, and private artifact URLs are never committed.

## Verification

`scripts/verify.py` runs validation in increasing cost order:

1. Validate TOML manifests, hashes, submodule revisions, and forbidden paths.
2. Test patch application against clean temporary indexes.
3. Run framework-neutral unit tests for scale geometry and metrics.
4. Run adapter import and configuration smoke tests.
5. Build one synthetic CPU forward pass where supported.
6. Optionally run CUDA smoke tests and one real-data evaluation batch when the
   required external assets are supplied.

The initial acceptance matrix is:

| Adapter | Manifest | Apply check | Unit tests | Import/config smoke | CUDA smoke |
|---|---:|---:|---:|---:|---:|
| DINO | required | required | required | required | optional locally |
| RF-DETR | required | required | required | required | optional locally |
| D-FINE | required | required | required | required | optional locally |

No adapter is declared reproducible until its clean-base application test and
documented smoke command pass.

## Licensing And Attribution

All three upstream projects use Apache License 2.0. The standalone repository
uses Apache License 2.0, retains upstream copyright and notice information in
derived files, lists all pinned sources in `docs/upstream.md`, and clearly
separates upstream code from ScaleAlign-authored modifications.

`CITATION.cff` cites ScaleAlign-DETR and links the DINO, RF-DETR, and D-FINE
projects. The README distinguishes upstream benchmark numbers from locally
measured results.

## Local And Publishing Phases

Phase 1 creates and verifies the selected local repository as `$PROJECT_ROOT`,
with Git branch `main` and author identity `cpc <cpcchhoo@163.com>`.

Phase 2 creates a remote repository only after local verification. Because the
GitHub CLI is not installed and network access is currently unavailable, remote
creation and push are intentionally outside Phase 1. The later publish step
adds a user-provided remote URL, verifies it is empty or compatible, and pushes
`main` plus submodule metadata. No large local artifacts are uploaded.

## Definition Of Done

- A fresh clone plus `git submodule update --init --recursive` and one bootstrap
  command recreates each supported integration from its exact pinned base.
- DINO, RF-DETR, and D-FINE adapters are documented by their implemented
  components without special status labels.
- The repository contains no dataset, checkpoint, virtual environment, cache,
  training output, absolute workstation path, or credential.
- Adapter digests and clean-application checks pass.
- Unit and import/config smoke tests pass for all three adapters.
- README commands cover environment setup, bootstrap, verification, training,
  evaluation, diagnostics, and later remote publication.
