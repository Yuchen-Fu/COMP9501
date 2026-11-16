#!/usr/bin/env bash
# Install into this package's private environment; never change system Python.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
device="${1:-cuda}"
case "$device" in
  cuda) torch_index="https://download.pytorch.org/whl/cu126"; pyg_build="cu126" ;;
  cpu) torch_index="https://download.pytorch.org/whl/cpu"; pyg_build="cpu" ;;
  *) echo "Usage: bash scripts/representation/install.sh [cuda|cpu]" >&2; exit 2 ;;
esac
python_bin="${PYTHON:-python3}"
"$python_bin" -c 'import sys; assert sys.version_info[:2] in ((3, 11), (3, 12)), "Use Python 3.11 or 3.12 for these pinned wheels."'
"$python_bin" -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip==25.1.1'
.venv/bin/python -m pip install 'torch==2.8.0' --index-url "$torch_index"
.venv/bin/python -m pip install --no-index 'pyg_lib==0.4.0' -f "https://data.pyg.org/whl/torch-2.8.0+${pyg_build}.html"
.venv/bin/python -m pip install -r scripts/representation/requirements.txt
.venv/bin/python -m pip check
printf '\nInstalled %s environment. Run the batch only inside a GPU allocation or on an authorised compute node.\n' "$device"
if [[ "$device" == cuda ]]; then
  printf 'CUDA 12.6 wheels require a compatible NVIDIA driver (560 or newer recommended). The batch checks actual CUDA execution.\n'
fi
