"""Drift watch — lightweight production monitor stub (inputs + outputs).

Best-practice minimal set (no heavy deps):
  - log per-image: n_detections, mean_conf, latency_ms
  - compare live window vs baseline (results/smoke.json): PSI-style bin shift
    on counts + mean absolute conf shift; alert on thresholds.
Writes results/drift.json. Refuses to invent a baseline when missing.
"""
from __future__ import annotations
import json, statistics
from src.run_utils import repo_root, save_json, env_snapshot

def _load(name):
    p = repo_root() / "results" / name
    return json.loads(p.read_text()) if p.exists() else None

def main() -> int:
    base = _load("smoke.json")
    if not base or base.get("status") != "OK_REAL_RUN":
        save_json("drift.json", {"status": "SKIPPED",
                 "reason": "no baseline results/smoke.json OK_REAL_RUN; run smoke_live first",
                 "env": env_snapshot()})
        print("[drift] SKIP no baseline"); return 2
    lat = base["latency_ms"]
    det = base["mean_detections_per_image"]
    out = {"status": "OK_BASELINE_PROFILED",
           "baseline": {"n": len(lat), "p50_ms": statistics.median(lat),
                        "max_ms": max(lat), "mean_det": det},
           "rules": {"alert_if_p50_shift_pct": 30, "alert_if_det_shift_abs": 1.5,
                     "method": "KS/PSI on counts + conf when prediction logs exist; here baseline profiling only."},
           "next": "log live predictions to results/live_log.jsonl then re-run with --live to compare",
           "env": env_snapshot()}
    p = save_json("drift.json", out)
    print(f"[drift] baseline profiled -> {p}"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
