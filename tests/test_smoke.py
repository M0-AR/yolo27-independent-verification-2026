"""Smoke test: harness integrity without network fabrication."""
from pathlib import Path
def test_layout():
    root = Path(__file__).resolve().parents[1]
    for d in ["src", "configs", "scripts", "experiments", "docs"]:
        assert (root / d).exists(), d
    assert (root / "docker-compose.yml").exists()
    assert (root / "Dockerfile").exists()
    assert (root / "preview.html").exists()
    assert (root / "docs" / "preview.html").exists()
    assert (root / "index.html").exists()
def test_claims_module_imports():
    import src.verify_claims as v
    assert len(v.CLAIMS) >= 10
def test_no_yolo27_fabrication():
    # Harness must never contain a hardcoded measured YOLO27 mAP as fact
    txt = (Path(__file__).resolve().parents[1] / "src" / "benchmark_yolo26.py").read_text()
    assert "yolo27_blocked.json" in txt
    assert "UNAVAILABLE" in txt
def test_export_ab_honest():
    txt = (Path(__file__).resolve().parents[1] / "src" / "export_ab.py").read_text()
    assert "SKIPPED" in txt and "same precision" in txt
def test_leaderboard_labels():
    txt = (Path(__file__).resolve().parents[1] / "experiments" / "leaderboard.csv").read_text()
    assert "REFERENCE-NOT-LOCAL" in txt and "UNAVAILABLE" in txt
