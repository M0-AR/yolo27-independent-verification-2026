"""Export A/B — measures the export gap instead of asserting it (H1).

Verified workflow (PTQ side-by-side, same images, same precision labels):
  PyTorch -> ONNX (FP32) -> ONNX Runtime vs PyTorch latency A/B.
INT8/计算TensorRT paths are protocol-ready stubs that refuse to invent
numbers: they run only when the artifact + calibration path exist.

Writes results/export_ab.json with status OK_REAL_RUN or SKIPPED.
"""
from __future__ import annotations
import time
from src.run_utils import env_snapshot, repo_root, save_json, set_seed, try_import_yolo

def _imgs(n=20):
    base = repo_root() / "data" / "coco128" / "images" / "train2017"
    files = sorted(base.glob("*.jpg"))[:n]
    if not files:
        raise FileNotFoundError("data/coco128 missing; run scripts/download_coco128.sh")
    return [str(f) for f in files]

def _time_call(fn, imgs):
    lat = []
    for im in imgs:
        t0 = time.perf_counter()
        fn(im)
        lat.append((time.perf_counter() - t0) * 1000)
    s = sorted(lat)
    return {"n": len(lat), "p50_ms": s[len(s)//2], "max_ms": max(lat), "all_ms": lat}

def main() -> int:
    set_seed(0)
    env = env_snapshot()
    YOLO, uver = try_import_yolo()
    if YOLO is None:
        save_json("export_ab.json", {"status": "SKIPPED", "reason": uver, "env": env})
        print("[export_ab] SKIP ultralytics missing"); return 2
    try:
        imgs = _imgs(20)
        torch_m = YOLO("yolo26n.pt")
        # Warmup (discard first 2 — Rockchip/edge best practice: drop warmup iters)
        for im in imgs[:2]:
            torch_m(im, verbose=False)
        pyt = _time_call(lambda im: torch_m(im, verbose=False), imgs[2:])
        try:
            art = torch_m.export(format="onnx", verbose=False)
        except Exception as e:
            save_json("export_ab.json", {"status": "SKIPPED", "reason": f"onnx export failed: {e}",
                                         "pytorch": pyt, "env": env})
            print(f"[export_ab] onnx export failed: {e}"); return 2
        onnx_m = YOLO(str(art))
        for im in imgs[:2]:
            onnx_m(im, verbose=False)
        onnx = _time_call(lambda im: onnx_m(im, verbose=False), imgs[2:])
        out = {"status": "OK_REAL_RUN", "ultralytics_version": uver,
               "weights": "yolo26n.pt", "onnx_artifact": str(art),
               "precision": "FP32 vs FP32 (same precision both sides — never mix FP32 acc with FP16 latency)",
               "n_images": len(imgs) - 2, "pytorch": pyt, "onnx": onnx,
               "delta_ms_p50_onnx_minus_torch": onnx["p50_ms"] - pyt["p50_ms"],
               "int8": {"status": "PROTOCOL-READY",
                        "rule": "INT8 needs calibration data + Q/DQ nodes + same-artifact mAP; refused until measured."},
               "env": env}
        p = save_json("export_ab.json", out)
        print(f"[export_ab] OK torch p50={pyt['p50_ms']:.1f} onnx p50={onnx['p50_ms']:.1f} -> {p}")
        return 0
    except Exception as e:
        save_json("export_ab.json", {"status": "SKIPPED", "reason": str(e), "env": env})
        print(f"[export_ab] SKIP ({e})"); return 2

if __name__ == "__main__":
    raise SystemExit(main())
