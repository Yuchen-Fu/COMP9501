#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
device="${1:-cpu}"
case "$device" in
  cpu) torch_index="https://download.pytorch.org/whl/cpu"; pyg_build="cpu" ;;
  cuda) torch_index="https://download.pytorch.org/whl/cu126"; pyg_build="cu126" ;;
  *) echo "Usage: bash scripts/install.sh [cpu|cuda]" >&2; exit 2 ;;
esac
aml_python="${AML_PYTHON:-python3}"
"$aml_python" -c 'import sys; assert sys.version_info[:2] in ((3, 11), (3, 12)), "Use Python 3.11 or 3.12."'
"$aml_python" -m venv .venv
.venv/bin/python -m pip install 'pip==25.1.1'
.venv/bin/python -m pip install 'torch==2.8.0' --index-url "$torch_index"
.venv/bin/python -m pip install --no-index 'pyg_lib==0.4.0' -f "https://data.pyg.org/whl/torch-2.8.0+${pyg_build}.html"
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
