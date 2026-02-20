"""
Physics audit reviewer pack builder.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json
import shutil
import hashlib

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)

def build_physics_audit_pack(run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    root = run_dir / "robustness_v4" / "physics_audit"
    if not root.exists():
        raise FileNotFoundError(f"Missing physics_audit output directory: {root}. Run physics-audit-run first.")

    pack_dir = run_dir / "PHYSICS_AUDIT_REVIEWER_PACK"
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)

    # Copy key artifacts
    key_files = [
        root / "physics_consistency_scorecard.json",
        root / "physics_consistency_summary.md",
        root / "per_window_physics.csv",
    ]
    manifests = {"files": []}
    for f in key_files:
        if f.exists():
            dest = pack_dir / f.name
            shutil.copy2(f, dest)
            manifests["files"].append({"path": dest.name, "sha256": _sha256_file(dest)})

    # Also include per-window closure/budget jsons (by reference copy)
    windows = run_dir / "robustness_v4" / "windows"
    win_out = pack_dir / "windows"
    win_out.mkdir(exist_ok=True)
    for wdir in sorted([p for p in windows.iterdir() if p.is_dir()], key=lambda p: p.name):
        wd = win_out / wdir.name
        wd.mkdir(parents=True, exist_ok=True)
        for name in ["closure_tests.json", "residual_budget.json"]:
            src = wdir / name
            if src.exists():
                dst = wd / name
                shutil.copy2(src, dst)
                manifests["files"].append({"path": str(Path("windows")/wdir.name/name), "sha256": _sha256_file(dst)})

    _write_json(pack_dir / "pack_manifest.json", manifests)
    return pack_dir
