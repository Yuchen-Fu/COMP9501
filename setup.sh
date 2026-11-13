#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data/raw data/reference
zip=data/raw/HI-Small_Trans.csv.zip
if [[ ! -f "$zip" ]]; then
  curl -fsSL -o "$zip.part" 'https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/resolve/6412f57ab89c9c28633ce5e837eca4c9a35c5dbe/HI-Small_Trans.csv.zip'
  mv "$zip.part" "$zip"
fi
echo "4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080  $zip" | sha256sum -c
unzip -oq "$zip" -d data/raw
# The pinned IBM file supplies GINe itself. Keep it beside the generated graph.
curl -fsSL -o data/reference/models.py 'https://raw.githubusercontent.com/IBM/Multi-GNN/252b0252afca109d1d216c411c59ff70753b25fc/models.py'
uv venv .venv --python 3.13 --allow-existing -q
PY=.venv/bin/python
uv pip install -q --python "$PY" torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install -q --python "$PY" pyg_lib==0.5.0 -f https://data.pyg.org/whl/torch-2.8.0+cpu.html
uv pip install -q --python "$PY" -r requirements.txt
if [[ ! -f data/course-graph.pt ]]; then
  "$PY" -I src/prepare.py data/raw/HI-Small_Trans.csv data/course-graph.part
  mv data/course-graph.part data/course-graph.pt
fi
