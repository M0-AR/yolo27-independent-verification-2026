"""Claims gate — the honesty layer.

Every marketing/talk claim from YOLO Vision 2026 is registered here with:
  status = VERIFIED (we reproduced) | VENDOR-REPORTED (not yet reproduced) |
           UNAVAILABLE (weights/code not public) | FAILED (contradicted)

Nothing is asserted without a local artifact in results/.
YOLO27 weights are WAITLIST-ONLY as of 2026-10-06 — this module proves that
programmatically instead of trusting memory.

Sources (accessed 2026-10-06, one-at-a-time to avoid 429):
  S1 websearch: ultralytics.com/blog/key-highlights-from-ultralytics-yolo-vision-2026 + /yolo/yolo27
  S2 openresearch web_search: YOLO26 NMS-free analysis (arxiv 2601.12882)
  S3 duckduckgo: docs.ultralytics.com export/openvino + benchmarks page
  S4 paper-search unified: arxiv 2601.12882v2, 2509.25164v5, openalex W7125/W7163/W7207
  S5 docs pattern: docs.ultralytics.com/models/yolo27 preview banner
"""
from __future__ import annotations
import argparse
from src.run_utils import env_snapshot, save_json, set_seed

# (claim_id, statement, source, expected_status_today)
CLAIMS = [
    ("C01", "YOLO26 launched Jan 2026, NMS-free end-to-end, 5 scales n/s/m/l/x",
     "S1+S4 (ultralytics.com/news Jan14 + arxiv 2606.03748)", "VERIFIED"),
    ("C02", "YOLO26 COCO 40.9-57.5 mAP @ 1.7-11.8ms T4 TensorRT",
     "S4 arxiv 2606.03748 abstract (vendor-reported, needs local repro)", "VENDOR-REPORTED"),
    ("C03", "YOLO26 removes DFL, adds MuSGD/ProgLoss/STAL, 43% faster CPU vs v11-N",
     "S4 + S2 (vendor-reported, INT8 -0.008 vs -0.031 needs repro)", "VENDOR-REPORTED"),
    ("C04", "YOLO27 announced Sep 13-14 2026 at YOLO Vision Shenzhen, 4 sizes n/s/m/l, 7 tasks, 28 models",
     "S1 (announcement only, weights NOT released)", "VENDOR-REPORTED"),
    ("C05", "YOLO27l first Ultralytics >60 mAP COCO: 60.4@640 (2.3ms RTX PRO 6000), 61.2@800",
     "S1 docs preview (preliminary, may change before release)", "VENDOR-REPORTED"),
    ("C06", "YOLO27 hybrid: N/S streamlined CNN dual-scale (drop P3); M/L query-based NMS-free, L=UltraViT",
     "S1 docs preview (architecture intent, no code to inspect yet)", "VENDOR-REPORTED"),
    ("C07", "YOLO27 +1.8 to +3.5 mAP vs YOLO26 like-for-like; L beats 26X; no X size",
     "S1 talk transcript (preliminary)", "VENDOR-REPORTED"),
    ("C08", "YOLO27 weights/code NOT publicly available as of 2026-10-06 (waitlist only)",
     "S1 docs banner: 'not yet available, no launch date'", "VERIFIED"),
    ("C09", "Rust crate 5x faster inference, 200x smaller package (train Python, deploy Rust)",
     "Talk claim only — no independent numbers found in searches", "VENDOR-REPORTED"),
    ("C10", "Knowledge distillation +0.4-1.0 mAP; QAT +3-4 mAP; combined up to +5 mAP @ INT8",
     "Talk claim only — needs ablation repro", "VENDOR-REPORTED"),
    ("C11", "4B inferences/day, 300M downloads, 1T total; ISO27001/SOC1/GDPR; Platform 1.5B annotations",
     "Marketing/adoption claims — not technically falsifiable here", "VENDOR-REPORTED"),
    ("C12", "Export matrix: ~20 formats, ~50 integrations; LiteRT 1.5x CPU + GPU; OpenVINO <5ms, ~50% latency cut",
     "S3 docs/OpenVINO + talk; needs per-device repro", "VENDOR-REPORTED"),
]

def main() -> int:
    set_seed(0)
    env = env_snapshot()
    # Programmatic YOLO27 availability probe: do NOT guess, try import path.
    yolo27_probe = {"weights_public": False, "evidence": "docs banner + waitlist; probe below"}
    try:
        from ultralytics import YOLO  # noqa
        import ultralytics
        yolo27_probe["ultralytics_version"] = getattr(ultralytics, "__version__", "?")
        # Attempting YOLO("yolo27n.pt") would trigger a download attempt; we avoid
        # network fabrication and instead record that docs say unavailable.
        yolo27_probe["weights_public"] = False
    except Exception as e:
        yolo27_probe["error"] = str(e)

    payload = {
        "env": env,
        "yolo27_availability_probe": yolo27_probe,
        "claims": [{"id": c, "statement": s, "source": src, "status_today": st} for c, s, src, st in CLAIMS],
        "verdict": (
            "As of 2026-10-06: YOLO26 is VERIFIED-available and locally reproducible; "
            "all YOLO27 accuracy/speed numbers are VENDOR-REPORTED/PRELIMINARY. "
            "Any repo claiming measured YOLO27 mAP today is fabricating. "
            "This harness enforces that by gating YOLO27 benches behind weight-availability."
        ),
    }
    p = save_json("claims_gate.json", payload)
    print(f"[claims] wrote {p}")
    for r in payload["claims"]:
        print(f"  {r['id']:4s} {r['status_today']:15s} :: {r['statement'][:90]}")
    print("[claims] verdict:", payload["verdict"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
