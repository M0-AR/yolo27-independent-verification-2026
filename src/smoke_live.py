"""Smoke on REAL public data — no fabrication.

Downloads (if missing):
  - COCO128 (Ultralytics assets, 128 images, canonical smoke set)
  - 2 sample images via Ultralytics assets (bus.jpg, zidane.jpg pattern)
Runs YOLO26n inference on CPU, times it, writes results/smoke.json.

If network/weights unavailable, writes status=SKIPPED with reason —
never writes fake mAP/latency.
"""
from __future__ import annotations
import time, urllib.request, zipfile
from pathlib import Path
from src.run_utils import env_snapshot, repo_root, save_json, set_seed, try_import_yolo

COCO128_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"

def ensure_coco128() -> Path:
    base = repo_root() / "data" / "coco128"
    if (base / "images" / "train2017").exists():
        return base
    zpath = repo_root() / "data" / "coco128.zip"
    zpath.parent.mkdir(parents=True, exist_ok=True)
    print(f"[smoke] downloading {COCO128_URL}")
    urllib.request.urlretrieve(COCO128_URL, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(repo_root() / "data")
    return base

def main() -> int:
    set_seed(0)
    env = env_snapshot()
    YOLO, uver = try_import_yolo()
    if YOLO is None:
        p = save_json("smoke.json", {"status": "SKIPPED", "reason": uver, "env": env})
        print(f"[smoke] SKIP ultralytics missing -> {p}"); return 2
    try:
        base = ensure_coco128()
        imgs = sorted((base / "images" / "train2017").glob("*.jpg"))[:8]
        assert imgs, "no images after extract"
        model = YOLO("yolo26n.pt")  # triggers real download on first run
        lat = []
        counts = []
        for im in imgs:
            t0 = time.perf_counter()
            r = model(str(im), verbose=False)
            lat.append((time.perf_counter() - t0) * 1000)
            counts.append(len(r[0].boxes) if r[0].boxes is not None else 0)
        lat_sorted = sorted(lat)
        payload = {
            "status": "OK_REAL_RUN",
            "ultralytics_version": uver,
            "weights": "yolo26n.pt (real, downloaded by ultralytics)",
            "n_images": len(imgs),
            "latency_ms": lat,
            "p50_ms": lat_sorted[len(lat_sorted)//2],
            "mean_detections_per_image": sum(counts)/max(1, len(counts)),
            "env": env,
            "note": "CPU smoke only; full mAP gate is benchmark_yolo26 --full on COCO val2017.",
        }
        p = save_json("smoke.json", payload)
        print(f"[smoke] OK p50={payload['p50_ms']:.1f}ms mean_det={payload['mean_detections_per_image']:.2f} -> {p}")
        return 0
    except Exception as e:
        p = save_json("smoke.json", {"status": "SKIPPED", "reason": str(e), "env": env})
        print(f"[smoke] SKIP ({e}) -> {p}"); return 2

if __name__ == "__main__":
    raise SystemExit(main())
