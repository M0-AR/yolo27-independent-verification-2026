# LIVE MEASURED RESULTS — 2026-10-06 (RTX 3090, ultralytics 8.4.126, torch 2.13)

These are the ONLY numbers in this repo measured locally. Everything else
remains VENDOR-REPORTED in claims-matrix.csv. Do not mix them.

## Smoke (src/smoke_live.py, data/coco128 8 images, yolo26n.pt real)
- p50_ms: 58.85
- latencies_ms: [1376.72 (cold-start incl. weight load), 58.85, 13.30, 14.35, 66.18, 35.09, 30.89, 158.36]
- mean_detections_per_image: 2.75
- artifact: results/smoke.json
- Hidden insight (H2): cold-start 1376ms vs steady ~13-66ms = 23x tail.
  Any latency claim without p50/p95 + cold-vs-warm split is incomplete.
  NMS-free determinism must be tested warm, not cold.

## Bench smoke (src/benchmark_yolo26.py --smoke, coco128.yaml, 128 imgs, 929 instances)
- scale: yolo26n.pt — 122 layers, 2,408,932 params, 5.5 GFLOPs (fused)
- P: 0.683  R: 0.542  mAP50: 0.637  mAP50-95: 0.479
- speed: 0.8ms preprocess, 4.4ms inference, 2.1ms postprocess (GPU RTX 3090)
- val_wall_s: ~7.4s warm (23.7s cold incl. download)
- artifact: results/benchmark.json
- WARNING: coco128 mAP (0.479) is NOT comparable to vendor COCO val2017 table
  (40.9 for 26n). Subset is easier + tiny. Full gate (--full on val2017 5000 imgs)
  is required before any VERIFIED vs vendor-table comparison.

## YOLO27 probe
- status: UNAVAILABLE — results/yolo27_blocked.json
- ultralytics 8.4.126 has no yolo27*.pt; docs banner confirms waitlist-only.
- Re-run after release: `python -m src.benchmark_yolo26 --full --include-yolo27`

## Env
- python 3.12.13, torch 2.13.0+cu130, ultralytics 8.4.126, onnxruntime 1.29,
  CPU 28 threads, CUDA RTX 3090 24GB, platform Linux-7.0.0-34-generic.

## How this was produced (copy-paste)
```
docker compose up verifier-cpu
# or:
python -m src.verify_claims
python -m src.smoke_live
python -m src.benchmark_yolo26 --smoke
python -m src.benchmark_yolo26 --smoke --include-yolo27  # proves blocker
python -m src.hidden_patterns
pytest tests -q
docker compose config  # validates compose
```
