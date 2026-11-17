#!/usr/bin/env bash
# Optional historical proposal; no extension outputs are supplied.
# Primary 2x2 factorial (counts x ports) on seeds 0-9, then the counts+novelty cell on seeds 0-4.
# CPU-only box (4 cores): a queue of 2-thread jobs, two at a time. Finished runs are skipped.
set -euo pipefail
cd "$(dirname "$0")"
export EPOCHS=${EPOCHS:-5}
mkdir -p results/runs results/logs
run() {  # run <cell> <seed>
  local cell=$1 seed=$2 flags=()
  [[ -f results/runs/${cell}_s${seed}.json ]] && return 0   # finished earlier
  for f in counts novelty ports; do [[ $cell == *$f* ]] && flags+=(--$f); done
  OMP_NUM_THREADS=2 .venv/bin/python -I src/train.py "${flags[@]}" --seed "$seed" --epochs "$EPOCHS" \
    --out results/runs > "results/logs/${cell}_s${seed}.log" 2>&1
}
export -f run
{ for s in 0 1 2 3 4 5 6 7 8 9; do for c in base ports counts counts+ports; do echo "$c $s"; done; done
  for s in 0 1 2 3 4; do echo "counts+novelty $s"; done; } | xargs -P 2 -L 1 bash -c 'run "$0" "$1"'
echo "all runs done"
