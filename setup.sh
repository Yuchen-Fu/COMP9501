#!/usr/bin/env bash
# CPU environment + data for the ports-vs-counts experiment. Idempotent; run from anywhere.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
uv venv .venv --python python3.13 --allow-existing -q
uv pip install -q --python $PY torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install -q --python $PY pyg_lib==0.5.0 -f https://data.pyg.org/whl/torch-2.8.0+cpu.html
uv pip install -q --python $PY -r requirements.txt
if [ ! -f data/hi_small.pt ]; then
  mkdir -p data/raw
  curl -sSfL -o data/raw/HI-Small_Trans.csv.zip "https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/resolve/6412f57ab89c9c28633ce5e837eca4c9a35c5dbe/HI-Small_Trans.csv.zip"
  echo "4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080  data/raw/HI-Small_Trans.csv.zip" | sha256sum -c --quiet
  unzip -o -q data/raw/HI-Small_Trans.csv.zip -d data/raw
  $PY -I src/prepare.py data/raw/HI-Small_Trans.csv data/hi_small.pt
fi
$PY -c "import torch, torch_geometric, pyg_lib; print('ready: torch', torch.__version__, '| pyg', torch_geometric.__version__)"
