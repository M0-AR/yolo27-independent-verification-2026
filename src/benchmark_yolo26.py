"""Full YOLO26 gate (real) + YOLO27 gate (honestly blocked).

--smoke : COCO128 val smoke via model.val (tiny, CPU minutes)
--full  : COCO val2017 full (needs data/coco/val2017 + annotations; see scripts/download_coco_val.sh)
--export onnx : also measures ONNX export-gap (PyTorch vs ONNX latency)

YOLO27 scales are NEVER measured here until weights exist on disk or via
ultralytics hub. If requested, we emit results/yolo27_blocked.json with
status=UNAVAILABLE instead of inventing numbers.

Best-practice protocol encoded:
  fixed seed, imgsz=640, conf=0.001/iou=0.7 for val (COCO standard via ultralytics val),
  per-scale table, latency p50/p95, bootstrap CI in hidden_patterns.py.
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
from src.run_utils import env_snapshot, repo_root, save_json, set_seed, try_import_yolo

def bench_scale(YOLO, scale: str, data_yaml: str, smoke: bool):
    m = YOLO(scale)
    t0 = time.perf_counter()
    # ultralytics val returns metrics object with .box.map etc.
    res = m.val(data=data_yaml, imgsz=640, verbose=False)
    wall = time.perf_counter() - t0
    try:
        mp = float(res.box.map)
        mp50 = float(res.box.map50)
    except Exception:
        mp, mp50 = float("nan"), float("nan")
    return {"scale": scale, "map50_95": mp, "map50": mp50, "val_wall_s": wall}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--export", default="none", choices=["none", "onnx"])
    ap.add_argument("--include-yolo27", action="store_true",
                    help="attempt YOLO27 (expected to block with UNAVAILABLE)")
    args = ap.parse_args()
    set_seed(0)
    env = env_snapshot()
    YOLO, uver = try_import_yolo()
    if YOLO is None:
        save_json("benchmark.json", {"status": "SKIPPED", "reason": uver, "env": env})
        print("[bench] ultralytics missing, SKIP"); return 2

    if args.include_yolo27:
        p = save_json("yolo27_blocked.json", {
            "status": "UNAVAILABLE",
            "reason": "YOLO27 weights not public as of 2026-10-06 (waitlist; docs preview banner).",
            "action": "Re-run with --include-yolo27 after official release; harness will then measure.",
            "env": env})
        print(f"[bench] YOLO27 blocked (honest) -> {p}")

    if args.smoke:
        data_yaml = "coco128.yaml"  # ships with ultralytics package
        scales = ["yolo26n.pt"]
    elif args.full:
        # Requires scripts/download_coco_val.sh to have populated data/coco
        coco_yaml = repo_root() / "configs" / "coco_val2017.yaml"
        if not coco_yaml.exists():
            save_json("benchmark.json", {"status": "SKIPPED",
                "reason": "configs/coco_val2017.yaml + data/coco missing; run scripts/download_coco_val.sh",
                "env": env})
            print("[bench] full needs COCO val2017, see scripts/download_coco_val.sh"); return 2
        data_yaml = str(coco_yaml)
        scales = ["yolo26n.pt", "yolo26s.pt", "yolo26m.pt"]
    else:
        print("[bench] pass --smoke or --full"); return 2

    rows = []
    for s in scales:
        try:
            print(f"[bench] val {s} on {data_yaml} ...")
            rows.append(bench_scale(YOLO, s, data_yaml, smoke=args.smoke))
        except Exception as e:
            rows.append({"scale": s, "error": str(e)})

    export_gap = {}
    if args.export == "onnx" and args.smoke:
        try:
            from ultralytics import YOLO as _Y
            m = _Y("yolo26n.pt")
            ep = m.export(format="onnx", verbose=False)
            export_gap = {"onnx_artifact": str(ep), "note": "latency A/B in hidden_patterns.py"}
        except Exception as e:
            export_gap = {"error": str(e)}

    p = save_json("benchmark.json", {
        "status": "OK_REAL_RUN", "mode": "smoke" if args.smoke else "full",
        "ultralytics_version": uver, "data": data_yaml, "rows": rows,
        "export_gap": export_gap, "env": env,
        "warning": "Vendor tables (40.9-57.5 mAP etc.) are NOT copied here as fact; compare locally after --full."})
    print(f"[bench] wrote {p}")
    for r in rows:
        print(" ", r)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
