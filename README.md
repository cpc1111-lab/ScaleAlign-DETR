# ScaleAlign-DETR

ScaleAlign-DETR models object scale as a continuous state derived from predicted
geometry. The same state coordinates two limited resources: SGQG allocates
decoder query slots and SAA allocates evidence across multi-scale feature
levels.

This repository provides reproducible integrations for three detector hosts:

- **DINO:** ScaleAlign S/M/L configurations, ESM, SGQG, SAA, diagnostics,
  profiling, dataset conversion, and evaluation tools.
- **RF-DETR:** RF-DETR-2XL ESM, SGQG, SAA, multi-scale warm start, matched
  continuation runs, diagnostics, and tests.
- **D-FINE:** ScalePrior model wiring, configurations, and prior construction
  utilities.

Upstream projects remain pinned Git submodules. The ScaleAlign changes live in
reviewable adapter patches, so this repository does not duplicate upstream
history or depend on an unpublished fork.

## Clone And Bootstrap

```bash
git clone --recurse-submodules https://github.com/cpc1111-lab/ScaleAlign-DETR.git
cd ScaleAlign-DETR
python scripts/verify.py
python scripts/bootstrap.py --dry-run
python scripts/bootstrap.py
```

To initialize submodules after a non-recursive clone:

```bash
git submodule update --init --recursive
```

Apply only selected hosts by passing one or more names:

```bash
python scripts/bootstrap.py dino rfdetr
```

The bootstrap command validates the pinned commit and patch digest, refuses a
dirty submodule, applies the patch, and writes an idempotency receipt. Running
the same command again reports `already-applied`.

## DINO

COCO S training follows the migrated DINO schedule:

```bash
cd third_party/DINO
python -u main.py \
  -c config/ScaleAlign/coco_s.py \
  --coco_path /path/to/coco \
  --pretrain_model_path /path/to/checkpoint0011_5scale.pth \
  --output_dir outputs/scalealign_coco_s \
  --device cuda --amp --progress --save_log --seed 0 --num_workers 4
```

Replace `coco_s.py` with `coco_m.py` or `coco_l.py` for the other model sizes.
VOC and VisDrone configurations are in the same directory.

## RF-DETR

The RF-DETR adapter preserves the official 2XL architecture and query budget.
After setting dataset and checkpoint arguments in the run configuration:

```bash
cd third_party/RF-DETR
python -u scripts/run_scalealign_ms_local.py --branch scalealign
```

Equal-budget controls are launched with `scripts/run_equal_budget.py`.

## D-FINE

```bash
cd third_party/D-FINE
python train.py -c configs/dfine/NSAD_coco.yml --use-amp --seed 0
```

Dataset paths remain external inputs and should be overridden in the host
configuration. No dataset, model checkpoint, virtual environment, or generated
experiment output is stored in this repository.

## Verification

```bash
python -m pytest -q
python scripts/verify.py
git diff --check
```

See [upstream sources](docs/upstream.md) for exact revisions and attribution.
