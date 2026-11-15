#!/usr/bin/env bash
# Shared CPU setup for the completed study and the optional course runner.
set -euo pipefail
cd "$(dirname "$0")"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/comp9501-uv-cache}"
mkdir -p data/raw data/reference
aml_archive=data/raw/HI-Small_Trans.csv.zip
if [[ ! -f "$aml_archive" ]]; then
  curl -fsSL -o "$aml_archive.part" 'https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/resolve/6412f57ab89c9c28633ce5e837eca4c9a35c5dbe/HI-Small_Trans.csv.zip'
  mv "$aml_archive.part" "$aml_archive"
fi
echo "4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080  $aml_archive" | sha256sum -c
if [[ ! -f data/raw/HI-Small_Trans.csv ]]; then
  unzip -oq "$aml_archive" -d data/raw
fi
# Only the optional 100-epoch runner imports this pinned reference model.
if [[ ! -f data/reference/models.py ]]; then
  curl -fsSL -o data/reference/models.py.part 'https://raw.githubusercontent.com/IBM/Multi-GNN/252b0252afca109d1d216c411c59ff70753b25fc/models.py'
  mv data/reference/models.py.part data/reference/models.py
fi
echo '00ef7142e81d3080114142106867e6ef3002d5a01ff5474e9f75cab957fcefe7  data/reference/models.py' | sha256sum -c
uv venv .venv --python 3.13 --allow-existing -q
aml_python=.venv/bin/python
uv pip install -q --python "$aml_python" torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install -q --python "$aml_python" pyg_lib==0.5.0 -f https://data.pyg.org/whl/torch-2.8.0+cpu.html
uv pip install -q --python "$aml_python" -r requirements.txt
if [[ ! -f data/hi_small.pt ]]; then
  "$aml_python" -I src/prepare.py data/raw/HI-Small_Trans.csv data/hi_small.part
  mv data/hi_small.part data/hi_small.pt
fi
"$aml_python" -c "import torch, torch_geometric, pyg_lib; print('ready: torch', torch.__version__, '| pyg', torch_geometric.__version__, '| graph: data/hi_small.pt')"
