#!/usr/bin/env bash
# HKU login banner: up to four RTX3090 GPUs per server in debug.
#SBATCH --job-name=aml-pair-8h
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --gpus=rtx_3090:4
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=aml-pair-8h-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the extracted study directory.}"
export PYTHONUNBUFFERED=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
.venv/bin/python -I scripts/representation/run_8h.py
