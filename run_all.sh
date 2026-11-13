#!/usr/bin/env bash
# 2x2 factorial (counts off/on x ports off/on) x 5 seeds = 20 GIN runs.
# CPU-only box (4 cores): two 2-thread jobs at a time; one full 2x2 replicate per seed.
set -euo pipefail
cd "$(dirname "$0")"
EPOCHS=${EPOCHS:-5}
mkdir -p results/runs results/logs
run() {  # run <cell> <seed>
  local cell=$1 seed=$2 flags=()
  [[ $cell == *counts* ]] && flags+=(--counts)
  [[ $cell == *ports* ]] && flags+=(--ports)
  [[ -f results/runs/${cell}_s${seed}.json ]] && return 0   # finished earlier
  OMP_NUM_THREADS=2 .venv/bin/python -I src/train.py "${flags[@]}" --seed "$seed" --epochs "$EPOCHS" \
    --out results/runs > "results/logs/${cell}_s${seed}.log" 2>&1
}
for seed in 0 1 2 3 4; do
  run base "$seed" & run ports "$seed" & wait
  run counts "$seed" & run counts+ports "$seed" & wait
done
echo "all runs done"
