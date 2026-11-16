#!/usr/bin/env bash
# HKU's login banner advertises this GPU syntax. Uses the default partition.
# Add --partition/--account only if required by the local scheduler.
#SBATCH --job-name=aml-pair-study
#SBATCH --nodes=1
#SBATCH --gpus=rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=aml-pair-study-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit this script from the extracted package root.}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export CUBLAS_WORKSPACE_CONFIG=:4096:8
.venv/bin/python -I scripts/representation/run_batch.py --device cuda
