#!/usr/bin/env bash
# Smoke data: COCO128 (tiny, canonical). Real, public, fast.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data
if [ -d data/coco128/images ]; then echo "[data] coco128 present"; exit 0; fi
echo "[data] fetching COCO128..."
wget -q --show-progress -O data/coco128.zip https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip
unzip -q -o data/coco128.zip -d data/
ls data/coco128/images/train2017 | head
echo "[data] OK"
