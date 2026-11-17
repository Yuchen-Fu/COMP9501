#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p data/raw
aml_archive=data/raw/HI-Small_Trans.csv.zip
if [[ ! -f "$aml_archive" ]]; then
  curl -fL -o "$aml_archive.part" 'https://huggingface.co/datasets/eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans/resolve/6412f57ab89c9c28633ce5e837eca4c9a35c5dbe/HI-Small_Trans.csv.zip'
  mv "$aml_archive.part" "$aml_archive"
fi
echo "4407435ec99e37262294b3d4e317f3adcb8a89caa0df66927d1c6ba4f46e8080  $aml_archive" | sha256sum -c
if [[ ! -f data/raw/HI-Small_Trans.csv ]]; then
  unzip -oq "$aml_archive" -d data/raw
fi
if [[ ! -f data/hi_small.pt ]]; then
  .venv/bin/python -I src/prepare.py data/raw/HI-Small_Trans.csv data/hi_small.part
  mv data/hi_small.part data/hi_small.pt
fi
sha256sum data/hi_small.pt
