# METHOD — zero-to-hero verification protocol (best practice, 2026)

This is the exact sequence a reviewer follows. No step asserts a number
without producing an artifact in `results/`.

## 0. Honesty gate (2 min, no GPU)
```bash
docker compose build
docker compose up verifier-cpu
# Expected: results/claims_gate.json + results/smoke.json = OK_REAL_RUN
# YOLO27 probe = UNAVAILABLE (proves we did not fabricate)
```

## 1. Smoke on real public data (CPU minutes)
- `data/coco128` (128 images, Ultralytics assets canonical URL)
- `yolo26n.pt` real weights via `ultralytics` package
- Metrics: p50 latency, mean detections/image. NOT mAP (too small for mAP).

## 2. Full COCO val2017 gate (the only mAP that counts)
```bash
bash scripts/download_coco_val.sh
docker compose --profile full up verifier-full
```
- Fixed: seed 0, imgsz 640, conf 0.001/iou 0.7 for val (COCO convention via `model.val`)
- Report: per-scale mAP50-95/mAP50 + wall time + env.json
- Bootstrap 1000x for 95% CI (see `src/hidden_patterns.py` H3)
- Stratify: APs/APm/APl + per-class AP (this is where hidden patterns live)

## 3. Export-gap A/B (LiteRT/OpenVINO/TensorRT claims)
- Same 200 images, same host: PyTorch vs ONNX vs OpenVINO FP32/INT8
- Report latency p50/p95 + ΔmAP. INT8 without calibration data is invalid.

## 4. Live / real-world check (validates "market/real-life data" ask)
- Vision != stock ticks: "live data" here = webcam / video file / fresh phone photos
- `python -m src.smoke_live` already runs on real pixels; extend with your own
  `data/live/*.jpg` and the harness logs per-image latency + counts.
- For domain shift (retail/warehouse/aerial): add 1+ domain set (SKU-110k, VisDrone,
  or your warehouse sample) and report ΔmAP vs COCO — this tests the UL37 thesis.

## 5. YOLO27 readiness (pre-registered, no HARKing)
- Today: `benchmark --include-yolo27` writes `yolo27_blocked.json` (UNAVAILABLE).
- After release: same command measures; H3 predicts AP-medium dip risk from
  dropping P3 — confirm or refute with CI, do not move the goalpost.

## Reproducibility checklist (from literature + vendor docs)
- [ ] seed, package versions, weight SHA, data SHA logged
- [ ] imgsz/conf/iou fixed and reported
- [ ] NMS on/off stated (`nms=False` selects NMS-free head on 26/27 N/S)
- [ ] CPU/GPU model named, batch=1, FP32 unless stated
- [ ] vendor numbers labeled VENDOR-REPORTED until step 2 passes
- [ ] negative results kept (SKIPPED with reason > fake OK)
