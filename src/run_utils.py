"""Shared utils: env logging, seeding, safe ultralytics import, result IO."""
from __future__ import annotations
import json, os, platform, random, sys
from datetime import datetime, timezone
from pathlib import Path

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def results_dir() -> Path:
    d = repo_root() / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d

def set_seed(seed: int = 0) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(False)  # explicit: we log, not force (perf gate)
    except Exception:
        pass

def env_snapshot() -> dict:
    snap = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
    }
    for pkg in ["torch", "torchvision", "ultralytics", "onnxruntime", "numpy", "cv2", "PIL"]:
        try:
            m = __import__(pkg)
            snap[pkg] = getattr(m, "__version__", "installed")
        except Exception as e:
            snap[pkg] = f"missing: {e}"
    try:
        import torch
        snap["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            snap["cuda_device"] = torch.cuda.get_device_name(0)
    except Exception:
        snap["cuda_available"] = False
    return snap

def save_json(name: str, payload: dict) -> Path:
    p = results_dir() / name
    p.write_text(json.dumps(payload, indent=2, default=str))
    return p

def try_import_yolo():
    try:
        from ultralytics import YOLO
        import ultralytics
        return YOLO, getattr(ultralytics, "__version__", "unknown")
    except Exception as e:
        return None, f"ultralytics import failed: {e}"
