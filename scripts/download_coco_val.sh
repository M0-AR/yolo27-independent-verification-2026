#!/usr/bin/env bash
# Full gate: COCO val2017 (~1GB ann + ~8GB images). Run once; keep checksums.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/coco
cd data/coco
for f in val2017.zip annotations_trainval2017.zip; do
  if [ -f "$f" ]; then echo "[coco] $f present"; continue; fi
  if [[ "$f" == val* ]]; then U="http://images.cocodataset.org/zips/$f";
  else U="http://images.cocodataset.org/annotations/$f"; fi
  echo "[coco] fetching $U"
  wget -q --show-progress "$U"
done
unzip -q -n val2017.zip || true
unzip -q -n annotations_trainval2017.zip || true
ls val2017 | wc -l
echo "[coco] OK — point configs/coco_val2017.yaml at data/coco"
