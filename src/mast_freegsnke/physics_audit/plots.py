"""
Deterministic plot generation for physics audit.
No custom colors; fixed ordering; hash recorded in manifest.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json
import hashlib
import pandas as pd
import matplotlib.pyplot as plt

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

def make_plots(physics_dir: Path) -> Path:
    physics_dir = Path(physics_dir)
    csvp = physics_dir / "per_window_physics.csv"
    if not csvp.exists():
        raise FileNotFoundError(f"Missing per-window physics CSV: {csvp}")
    df = pd.read_csv(csvp)

    plots_dir = physics_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    # Plot 1: max_test_violation vs window index
    df_sorted = df.sort_values(by="window_id", kind="mergesort")
    plt.figure()
    plt.plot(range(len(df_sorted)), df_sorted["max_test_violation"].values)
    plt.xlabel("window index (sorted)")
    plt.ylabel("max test violation")
    p1 = plots_dir / "max_violation_vs_window.png"
    plt.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 2: budget_total vs window index
    plt.figure()
    plt.plot(range(len(df_sorted)), df_sorted["budget_total"].values)
    plt.xlabel("window index (sorted)")
    plt.ylabel("budget total (normalized)")
    p2 = plots_dir / "budget_total_vs_window.png"
    plt.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close()

    manifest = {
        "plots": [
            {"path": str(p1.relative_to(physics_dir)), "sha256": _sha256_file(p1)},
            {"path": str(p2.relative_to(physics_dir)), "sha256": _sha256_file(p2)},
        ]
    }
    _write_json(physics_dir / "plots_manifest.json", manifest)
    return plots_dir
