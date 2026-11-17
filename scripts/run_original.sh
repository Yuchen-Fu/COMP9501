#!/usr/bin/env bash
# The original five-cell, five-seed, five-epoch experiment.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export aml_output="${1:-outputs/original}"
mkdir -p "$aml_output/runs" "$aml_output/logs"
run() {
  local cell=$1 seed=$2 flags=()
  [[ -f "$aml_output/runs/${cell}_s${seed}.json" ]] && return 0
  for feature in counts novelty ports; do
    if [[ $cell == *$feature* ]]; then flags+=(--"$feature"); fi
  done
  OMP_NUM_THREADS=2 .venv/bin/python -I src/train.py "${flags[@]}" --seed "$seed" --epochs 5 \
    --out "$aml_output/runs" > "$aml_output/logs/${cell}_s${seed}.log" 2>&1
}
export -f run
{ for seed in 0 1 2 3 4; do
    for cell in base ports counts counts+ports; do echo "$cell $seed"; done
  done
  for seed in 0 1 2 3 4; do echo "counts+novelty $seed"; done
} | xargs -P 2 -L 1 bash -c 'run "$0" "$1"'
.venv/bin/python -I src/analyze.py --runs "$aml_output/runs" --out "$aml_output"
.venv/bin/python -I src/plot_results.py --summary "$aml_output/summary.json" --out "$aml_output/figures"
