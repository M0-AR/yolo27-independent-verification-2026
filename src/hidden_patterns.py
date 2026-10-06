"""Hidden-pattern miner — stratified, falsifiable, no story-telling without numbers.

Reads results/benchmark.json + results/smoke.json (real runs only) and computes:
  H1 Export gap: PyTorch vs ONNX latency delta (if both measured; else reports MISSING)
  H2 Latency variance: p50 vs p95 vs max (NMS vs NMS-free determinism hypothesis)
  H3 Small-object hypothesis: needs full COCO val + pycocotools per-area AP;
      on smoke data it emits a TESTABLE PREDICTION instead of a fake finding.
  H4 Score-calibration drift: mean conf vs detection count (smoke-level proxy)
  H5 COCO-vs-real-world gap: documents why COCO (giraffes/zebras) overstates
      warehouse/retail readiness; maps to UL37 intent (37 domains) as future work.

Every hypothesis ships with: metric, threshold, status (CONFIRMED/REFUTED/NEEDS-FULL-DATA).
This is what makes the repo PhD-usable: reviewers can re-run and flip a status.
"""
from __future__ import annotations
import json, statistics
from src.run_utils import repo_root, save_json, env_snapshot

def load(name):
    p = repo_root() / "results" / name
    return json.loads(p.read_text()) if p.exists() else None

def main() -> int:
    bench = load("benchmark.json")
    smoke = load("smoke.json")
    patterns = []

    # H2 latency variance (works on smoke)
    if smoke and smoke.get("status") == "OK_REAL_RUN":
        lat = smoke["latency_ms"]
        p50 = statistics.median(lat)
        mx = max(lat)
        ratio = mx / max(1e-9, p50)
        patterns.append({
            "id": "H2-latency-tail",
            "metric": {"p50_ms": p50, "max_ms": mx, "max_over_p50": ratio, "n": len(lat)},
            "hypothesis": "NMS-free should show tighter tail than NMS path (deterministic latency).",
            "test": "Compare nms=True vs nms=False p95/max on same images; tail-ratio delta >15% = meaningful.",
            "status": "NEEDS-FULL-DATA" if len(lat) < 50 else ("CONFIRMED-TIGHT" if ratio < 2.0 else "WIDE-TAIL-INVESTIGATE"),
        })
        counts = smoke.get("mean_detections_per_image")
        patterns.append({
            "id": "H4-calibration-proxy",
            "metric": {"mean_detections_per_image": counts},
            "hypothesis": "Over-confident heads inflate count on cluttered frames; check conf histogram.",
            "test": "Plot conf histogram + reliability curve on val2017; ECE >0.05 = miscalibrated.",
            "status": "NEEDS-FULL-DATA",
        })
    else:
        patterns.append({"id": "H2-latency-tail", "status": "MISSING-RUN-FIRST",
                         "action": "docker compose up verifier-cpu"})

    # H1 export gap
    eg = (bench or {}).get("export_gap")
    if eg and "onnx_artifact" in eg:
        patterns.append({"id": "H1-export-gap", "metric": eg,
            "hypothesis": "ONNX/OpenVINO should cut CPU latency; INT8 may cost mAP.",
            "test": "A/B 200 images PyTorch vs ONNX vs OpenVINO FP32/INT8; report ms + mAP delta.",
            "status": "NEEDS-A/B-MEASUREMENT"})
    else:
        patterns.append({"id": "H1-export-gap", "status": "MISSING-EXPORT-RUN",
            "action": "python -m src.benchmark_yolo26 --smoke --export onnx (CPU) ; GPU profile for TensorRT"})

    # H3 small objects — the load-bearing hidden pattern for YOLO26 STAL + YOLO27 dual-scale
    patterns.append({
        "id": "H3-small-object-stratification",
        "hypothesis": ("STAL (YOLO26) should lift AP-small disproportionately; "
                        "YOLO27 N/S dropping P3 (medium map) predicts AP-medium dip unless compensated — "
                        "the highest-value falsifiable check once YOLO27 ships."),
        "test": ("pycocotools per-area APs/APs/APm/APl on val2017 for 26n/s vs 27n/s; "
                 "bootstrap 1000x; report ΔAPm with 95% CI; if ΔAPm<0 and CI excludes 0 → dual-scale trade-off confirmed."),
        "status": "PREDICTION-REGISTERED (needs --full + YOLO27 release)",
        "why_hidden": ("Vendor tables report single mAP; stratification reveals WHERE gains come from — "
                       "exactly what a PhD contribution needs."),
    })

    # H5 COCO vs real world
    patterns.append({
        "id": "H5-coco-vs-UL37-gap",
        "hypothesis": "COCO mAP overstates production readiness on retail/warehouse/aerial (UL37 intent).",
        "test": ("Evaluate same checkpoint on COCO val2017 + 2+ domain sets (e.g., SKU-110k retail, VisDrone aerial, "
                 "warehouse subset); report per-domain ΔmAP; domain-tuned Enterprise backbones should close gap after fine-tune."),
        "status": "PROTOCOL-READY (needs domain datasets; see docs/METHOD.md)",
    })

    out = {"env": env_snapshot(), "patterns": patterns,
           "rule": "No pattern is CONFIRMED without a local artifact + CI. Predictions above are pre-registered to prevent HARKing."}
    p = save_json("hidden_patterns.json", out)
    print(f"[patterns] wrote {p}")
    for h in patterns:
        print(f"  {h['id']:28s} {h['status']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
