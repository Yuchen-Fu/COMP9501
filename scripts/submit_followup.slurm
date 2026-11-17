#!/usr/bin/env bash
#SBATCH --job-name=aml-followup
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --gpus=rtx_3090:4
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=aml-followup-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the repository root.}"
.venv/bin/python -I scripts/run_followup.py
