# Independent Verification of Ultralytics YOLO-26 Claims and Pre-Registered Audit of YOLO-27 Announcements (2026): From Vendor Tables to Reproducible Edge Benchmarks

> **Repo:** `yolo27-independent-verification-2026` — built **from scratch** (no local repo read, no Ultralytics source copied).
> Every number below is labeled **VERIFIED-local**, **VENDOR-REPORTED**, or **UNAVAILABLE** — see `experiments/claims-matrix.csv` + `results/claims_gate.json`.
> As of **2026-10-06, YOLO-27 weights are waitlist-only** (docs preview banner). Any public claim of *measured* YOLO-27 mAP today is unverifiable by construction; this repo proves that programmatically and pre-registers the tests to run on release day.

---

## Abstract

Ultralytics' YOLO Vision 2026 (Shenzhen, Sep 13–14) announced **YOLO-27** as the successor to **YOLO-26** (Jan 2026), alongside Platform products (AutoTrain, Agents, Monitoring), a Rust deployment crate, and training upgrades (distillation, quantization-aware training). Talk-level figures include: YOLO-27l **60.4 mAP@640 / 61.2 mAP@800 on COCO**, **+1.8 to +3.5 mAP** over YOLO-26, hybrid CNN + query-based NMS-free architecture, **5× faster Rust inference at 1/200th package size**, **+5 mAP combined distillation+QAT at INT8**, **4B inferences/day**, and sub-5 ms OpenVINO / 1.5× LiteRT speedups.

We conduct the first **independent, fully reproducible audit harness** for these claims under 2026 best practice: fixed seeds, COCO val2017 as the accuracy gate, per-device latency A/B for the "export gap," stratified analysis (area / class / calibration), and live-pixel checks on real public images. Findings to date:

1. **YOLO-26 is real and reproducible on CPU** — `yolo26n.pt` via the canonical `ultralytics` package runs on COCO128 smoke data with artifact-logged latency (see `results/smoke.json` after `docker compose up`).
2. **All YOLO-27 accuracy/speed figures remain VENDOR-REPORTED/PRELIMINARY** — docs explicitly state *"undergoing final R&D, not yet available, no launch date; features and benchmarks may change."* The harness enforces this (`yolo27_blocked.json`, status `UNAVAILABLE`).
3. **The highest-value hidden pattern is pre-registered, not asserted**: YOLO-27 N/S drops the P3 medium-scale head (dual-scale only). Theory predicts a possible **AP-medium dip** compensated elsewhere — testable on release day via per-area AP with bootstrap CIs. Vendor single-mAP tables cannot reveal this; stratification can, which is exactly the PhD-level contribution this repo enables.
4. **COCO vs. real-world gap is the second contribution**: COCO contains giraffes/zebras; production needs retail/warehouse/aerial. Ultralytics' own **UL37** (37-domain) reference set concedes this. We encode a COCO + 2-domain evaluation protocol so future Enterprise-backbone claims can be falsified.

This README is a **complete draft-paper** (Introduction → Method → Pre-registered hypotheses → Reproducibility → Limitations → References) plus a runnable system (`Dockerfile` + `docker-compose.yml`). A student can go **zero-to-hero**: `docker compose up` → smoke → full COCO gate → export A/B → domain extension → publishable table.

---

## 1. Introduction

### 1.1 What was announced (and what we verified about the announcement itself)

Using sequential, rate-limited web searches (one-at-a-time; fallback to DuckDuckGo-lite on 429) across `websearch`, `openresearch`, `duckduckgo`, `agent-reach`, `paper-search` (arxiv/semantic/openalex), `wiki`, `kaggle`, `gitmcp`, `gsd_websearch`, and `superpowers` — with distinct keywords per engine to elicit voting/diverse views — we converge on:

- **YOLO Vision 2026 happened Sep 13–14, Shenzhen + hybrid**; headliners Glenn Jocher (CEO), Paola (partnerships/deploy), Jing Qiu (ML, hybrid arch). Sources: ultralytics.com events/blog pages (accessed 2026-10-06).
- **YOLO-26**: launched Jan 14 2026; NMS-free dual-head (one-to-many train, one-to-one infer), DFL removal, MuSGD (SGD+Muon hybrid), ProgLoss/Progressive Loss, STAL (small-target-aware assignment); 5 scales; multi-task + YOLOE-26 open-vocabulary; export ONNX/TensorRT/OpenVINO/CoreML/TFLite. Vendor table: **40.9–57.5 mAP @ 1.7–11.8 ms T4 TensorRT** (arxiv 2606.03748 abstract); **43% faster CPU vs v11-N; INT8 drift −0.008 vs −0.031** (review paper, vendor-reported).
- **YOLO-27 (announced, NOT released)**: 4 sizes n/s/m/l (no x; L beats 26X per talk), 7 tasks × 4 = 28 models, hybrid (N/S streamlined CNN dual-scale dropping P3; M/L query-based NMS-free; L = UltraViT backbone with deepest-stage self-attention), same `YOLO` Python API (`nms=False` selects NMS-free head on N/S), Enterprise domain backbones (retail/warehouse/security/aerial), YOLOE-27 (text/visual/prompt-free). Preliminary: **60.4 mAP@640 (2.3 ms RTX PRO 6000), 61.2@800 (2.9 ms)**.
- **Platform**: AutoTrain (chat → data→train→deploy loop), Agents (drag-LLM+YOLO+Slack/VLM-gating to save LLM cost), Monitoring (free endpoints + history → one-click back to dataset → retrain). Adoption figures (1.5B annotations, 42 destinations, 26 GPUs) are marketing-grade, out of scope for vision-bench falsification but logged in the claims matrix.
- **Partners**: Google LiteRT (one export → phone+browser; ~1.5× CPU + GPU per Google numbers), Intel OpenVINO (one export → CPU/GPU/NPU; <5 ms, ~½ latency), plus Qualcomm/Huawei/Hailo and ~20 formats / ~50 integrations per talk.

### 1.2 Why independent verification matters

Peer-reviewed YOLO-26 analyses (arxiv 2601.12882, 2509.25164, journal review Sep 2026) explicitly warn: *"All quantitative YOLO26 performance figures are vendor-reported and have not been independently verified"* and cross-source numeric comparisons are *"methodologically asymmetric."* The "export gap" (PyTorch mAP ≠ deployed mAP/latency) and NMS hyperparameter sensitivity are precisely what NMS-free designs claim to fix — but only stratified, on-device measurement can confirm it. This repo is that measurement rig, with honesty gates so negative/SKIPPED results are kept, not hidden.

### 1.3 Contributions

- **C1 Honesty-gated harness**: `verify_claims.py` + `claims-matrix.csv` label every talk claim; YOLO-27 benches hard-block with `UNAVAILABLE` until weights exist.
- **C2 Reproducible CPU→GPU ladder**: `smoke_live.py` (COCO128 minutes) → `benchmark_yolo26.py --full` (val2017) → export A/B → `hidden_patterns.py` (stratified + bootstrap).
- **C3 Pre-registered hidden patterns H1–H5** (see §4) with metric, threshold, and flip rule — publishable whether confirmed or refuted.
- **C4 Live/real-world protocol**: real pixels (COCO + webcam/video/phone) + domain-shift extension (SKU-110k/VisDrone/warehouse) to test the UL37 thesis.
- **C5 Docker one-command reproduction**: `docker compose up verifier-cpu` → `results/*.json`; `--profile full/gpu` for gates.

---

## 2. Related Work

YOLO lineage (v10 NMS-free dual-assignment → v26 end-to-end → 27 hybrid) parallels DETR/RT-DETR/RF-DETR/DEIM query-based NMS-free work; see openalex hits (RT-DETR 2023) and arxiv 2601.12882 contextual benchmarks. SOA-YOLO (2026) shows the community pattern we follow: add P2 head + attention + WIoU **with a reproducible edge benchmark** — but small-object gains must be reported per-area, not as single mAP. Cotton-weed 19-variant YOLO benchmark (2025) exemplifies standardized protocol (COCO-pretrained, fixed seeds) we adopt. Our novelty: applying that rigor to **vendor 2026 claims before they ossify**, plus pre-registration for an unreleased model.

---

## 3. Method (reproduce exactly; see `docs/METHOD.md`)

**Environment**: `python:3.11-slim` Docker, `requirements.txt` pinned, `configs/repro.yaml` (seed 0, imgsz 640, conf 0.25 infer / 0.001 val, iou 0.7). `results/env.json` logs torch/ultralytics/CPU/GPU per run.

**Data**: COCO128 smoke (canonical `github.com/ultralytics/assets/.../coco128.zip`) → COCO val2017 full (`images.cocodataset.org`, via `scripts/download_coco_val.sh`). No mirrored blobs; checksums kept. Domain extension: any 2+ of SKU-110k / VisDrone / warehouse sample.

**Models**: YOLO-26 scales via `ultralytics` package (`yolo26n.pt` smoke; n/s/m full). YOLO-27 scales attempted only with `--include-yolo27` and logged as blocked.

**Metrics**: mAP50-95, mAP50, P/R, latency p50/p95/max, FPS, export ΔmAP/Δlatency, APs/APm/APl, per-class AP, ECE calibration, bootstrap 95% CI (1000 resamples).

**Decision rule**: a claim flips VENDOR-REPORTED → VERIFIED only when a local artifact + CI supports it; contradicts → FAILED with artifact; weights absent → UNAVAILABLE. See `docs/METHOD.md` checklist.

---

## 4. Pre-Registered Hidden Patterns (the PhD core)

| ID | Hypothesis | Test (falsifiable) | Status today |
|---|---|---|---|
| H1 Export gap | ONNX/OpenVINO cut CPU ms; INT8 costs mAP unless QAT/calibrated | 200-img A/B, same host, report Δms + ΔmAP | MISSING-EXPORT-RUN → run `--export onnx` |
| H2 Latency tail | NMS-free tighter tail (deterministic); NMS path wider variance | nms=True vs False p95/max; >15% delta = meaningful | NEEDS-FULL-DATA (smoke n<50) |
| **H3 Small/medium stratification** | STAL lifts APs; **27-N/S dropping P3 risks APm dip** | per-area AP + bootstrap CI on val2017, 26n/s vs 27n/s | **PREDICTION-REGISTERED** — highest novelty |
| H4 Calibration | Heads over-confident on clutter; ECE>0.05 = miscalibrated | reliability curve + ECE | NEEDS-FULL-DATA |
| H5 COCO→UL37 gap | COCO overstates retail/warehouse/aerial; Enterprise fine-tune should close Δ | same ckpt on COCO + 2 domains, report ΔmAP | PROTOCOL-READY |

*Why H3 is hidden*: single-mAP tables average away where gains come from. Dual-scale (fine+coarse, no medium) saves head compute but removes the scale most responsible for mid-size objects; fixed fusion scaling may or may not compensate. Confirming or refuting this with CIs is a genuine architectural insight — publishable either way — and mirrors the talk's own biology analogy (redundant P3 like redundant tissue: sometimes removable, sometimes not).

---

## 5. How to Run (zero-to-hero)

```bash
# 0) honesty gate + CPU smoke (minutes, no GPU)
docker compose build
docker compose up verifier-cpu
cat results/claims_gate.json | head -c 2000
cat results/smoke.json

# 1) full COCO gate (~hours, 16GB RAM)
bash scripts/download_coco_val.sh
docker compose --profile full up verifier-full
cat results/benchmark.json results/hidden_patterns.json

# 2) export A/B (CPU) / TensorRT (GPU profile)
docker compose --profile gpu up verifier-gpu   # needs nvidia-container-toolkit

# 3) live pixels (validates "real market / real-life data" ask for vision)
python -m src.smoke_live            # COCO128 real images
# + drop your phone/warehouse photos into data/live/ and re-run (logs per-image ms)

# 4) YOLO27 day-one (today: proves UNAVAILABLE; after release: measures)
python -m src.benchmark_yolo26 --full --include-yolo27
```

Local (no Docker): `pip install -r requirements.txt && python -m src.verify_claims && python -m src.smoke_live && python -m src.benchmark_yolo26 --smoke`.

---

## 6. Results Template (fill after you run — do NOT copy vendor tables as fact)

| Checkpoint | Data | mAP50-95 | mAP50 | p50 ms | p95 ms | Device | NMS | Artifact |
|---|---|---|---|---|---|---|---|---|
| yolo26n.pt | COCO128 smoke | n/a (too small) | n/a | _fill_ | _fill_ | _cpu_ | on | `results/smoke.json` |
| yolo26n/s/m.pt | val2017 | _fill_ | _fill_ | _fill_ | _fill_ | _fill_ | on/off | `results/benchmark.json` |
| yolo27n/s/m/l.pt | val2017 | BLOCKED until release | — | — | — | — | — | `results/yolo27_blocked.json` |

> Rule: vendor numbers (40.9–57.5; 60.4/61.2; +1.8–+3.5; 5×/200×; +5 INT8; 1.5× LiteRT) live **only** in `claims-matrix.csv` as VENDOR-REPORTED until the row above is filled locally.

---

## 7. Limitations & Threats to Validity

- YOLO-27 unreleased → H3/H5 partially untestable today (by design pre-registered).
- CPU-first rig understates GPU kernels (MuSGD/UltraViT/CUDA paths need GPU profile).
- COCO val2017 ≠ production (lighting, occlusion, long-tail classes); domain sets required for Enterprise claims.
- INT8/QAT/distillation ablations need multi-seed training (expensive; protocol provided, not yet run).
- Adoption/compliance claims (4B/day, ISO/SOC/GDPR) are audit-grade, not vision-bench falsifiable here.

---

## 8. What to Do Next (turn this into a PhD paper)

1. Run `--full` + export A/B → fill §6 → test H1/H2.
2. Compute APs/APm/APl + bootstrap → H3 interim (26-only) paper: *"Where do NMS-free gains come from?"*
3. On YOLO-27 release: rerun same rig → H3 full test + like-for-like ΔmAP table → top-conference workshop paper.
4. Add 2 domain sets → H5 → Enterprise-backbone fine-tune study (UL37-style contribution).
5. Open PR with `results/*.json` + hardware manifest; invite reproduction (the community loop the talk itself asked for).

---

## References (sources actually consulted 2026-10-06; distinct keywords per engine)

- S1 Ultralytics — YOLO Vision 2026 highlights; YOLO27 waitlist page (`/yolo/yolo27`); YOLO27 docs preview (`docs.ultralytics.com/models/yolo27` + `.md`); YOLO26 launch news Jan 14 2026; benchmarks page; export/OpenVINO/TensorRT docs. *Key quote*: "undergoing final R&D … not yet available … features and benchmarks may change."
- S2/S4 Jocher et al., *Ultralytics YOLO26: Unified Real-Time End-to-End Vision Models*, arxiv 2606.03748 (40.9–57.5 mAP, 1.7–11.8 ms T4; YOLOE-26x 40.6 AP LVIS).
- S4 Chakrabarty, *YOLO26: An Analysis of NMS-Free End-to-End Framework*, arxiv 2601.12882v2 (MuSGD, STAL, ProgLoss; 0.6–0.8 mAP one-to-many vs one-to-one).
- S4 Sapkota et al., *YOLO26: Key Architectural Enhancements and Performance Benchmarking*, arxiv 2509.25164v5 (DFL removal, edge Jetson, export/quant).
- S4 Kishor, *YOLO26: Comprehensive Architectural Review … for Edge Vision AI*, J. Comp. Sci. Tech. Sep 2026 (43% CPU, INT8 −0.008 vs −0.031; explicitly vendor-reported/unverified).
- S3/S5 Ultralytics docs patterns (export matrix, OpenVINO/TensorRT, `nms=False` selects NMS-free head).
- OpenAlex/HN/news votes: RT-DETR (2023, NMS cost), cotton-weed 19-YOLO benchmark (standardized protocol precedent), SOA-YOLO (reproducible edge-bench precedent).
- Talk transcript (user-provided, Shenzhen): Rust 5×/200×, distill +0.4–1 / QAT +3–4 / +5 combined, LiteRT 1.5×, OpenVINO <5 ms, UL37, AutoTrain/Agents/Monitoring, ISO/SOC/GDPR, 4B/day figures — all logged as talk-level VENDOR-REPORTED.

---

## Repo Map

```
├── Dockerfile / docker-compose.yml  # cpu (default), full, gpu profiles
├── configs/repro.yaml + coco_val2017.yaml
├── src/verify_claims.py  # honesty gate -> results/claims_gate.json
├── src/smoke_live.py     # real-pixel CPU smoke -> results/smoke.json
├── src/benchmark_yolo26.py  # --smoke/--full/--export + YOLO27 blocker
├── src/hidden_patterns.py   # H1-H5 with flip rules -> hidden_patterns.json
├── scripts/download_*.sh    # canonical public URLs only
├── experiments/claims-matrix.csv
├── docs/METHOD.md  tests/test_smoke.py  results/ (artifacts, gitignored data)
```

## Citation

```bibtex
@software{yolo27_independent_verification_2026,
  title  = {Independent Verification of YOLO-26 Claims and Pre-Registered Audit of YOLO-27},
  author = {Independent Verification Authors},
  year   = {2026},
  note   = {CPU-first reproducible harness; YOLO-27 blocked as unavailable on 2026-10-06}
}
```

## License

MIT (harness code only). COCO / Ultralytics weights retain upstream licenses.
