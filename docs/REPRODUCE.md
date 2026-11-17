# Reproduction

The repository contains completed results. The commands below are for optional reruns and write to `outputs/`, leaving the published results intact.

## Install and prepare data

Use Python 3.11 or 3.12, `curl`, and `unzip`. The installer pins the follow-up software stack. Set `AML_PYTHON` to select a Python executable.

```bash
bash scripts/install.sh cpu          # use cuda for the GPU study
bash scripts/prepare_data.sh
```

The original CPU runs used Python 3.13.5 and the package versions in `results/environment.json`. The installer uses the recorded follow-up versions instead; rerunning the original study in this environment is not a claim of bitwise reproduction.

The data script downloads the pinned HI-Small archive and builds `data/hi_small.pt` if it is absent. For the frozen follow-up, use the exact prepared graph from the completed server run; its required checksum is in `docs/DATA.md`. Different PyTorch serializers may produce different bytes for the same tensors, and the follow-up deliberately rejects a different checksum.

## Original experiment

```bash
bash scripts/run_original.sh outputs/original
```

This runs five feature cells, seeds 0–4, five epochs each, with two CPU jobs at a time. Completed run JSON files are skipped on restart; the original trainer does not save partial-epoch checkpoints.

To recompute the published original analysis from its saved predictions, after preparing the graph:

```bash
.venv/bin/python -I src/analyze.py --data data/hi_small.pt --runs results/runs --out outputs/original-analysis
.venv/bin/python -I src/plot_results.py --summary outputs/original-analysis/summary.json --out outputs/original-analysis/figures
```

## Controlled follow-up

Install with `bash scripts/install.sh cuda`, then submit from the repository root on a cluster with the corresponding partition and GPU allocation:

```bash
sbatch scripts/submit_followup.slurm
```

Alternatively, inside a four-GPU allocation:

```bash
.venv/bin/python -I scripts/run_followup.py --out outputs/followup
```

The launcher reads the unchanged frozen protocol: three cells, seeds 15–19, 20–30 epochs, patience 10, and validation-AP progress threshold 0.001. It runs diagnostics, training, the full analysis and five probes. `--dry-run` prints the fifteen training commands without executing them. Training checkpoints remain resumable. The Slurm allocation supplies the eight-hour limit. The launcher is new orchestration; the eight research modules retain their original contents.

The saved follow-up JSON files are sufficient to inspect the published results, but a prediction-level analysis needs transaction probabilities and probes need model checkpoints. Those large artifacts remain on the university server and are not included in this repository. A fresh run creates them under its output directory. Do not mix a partial rerun with the published records.

## Integrity

From the repository root:

```bash
sha256sum -c results/SHA256SUMS
```

The checksum list covers retained JSON records, the frozen protocol and original prediction archives. Original runtime source hashes are retained as provenance; hashes for retired orchestration scripts are historical records, not live dependencies.
