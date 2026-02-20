from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..util import sha256_file, ensure_dir

def _savefig(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)

def generate_plots(rob_root: Path) -> Dict[str, Any]:
    """Deterministic plot generation.

    Produces:
      rob_root/plots/*.png
      rob_root/plots_manifest.json

    Notes:
      - deterministic ordering of windows and phases
      - no random elements, fixed dpi, fixed bbox
    """
    plots_dir = ensure_dir(rob_root / "plots")
    manifest: List[Dict[str, Any]] = []

    # per-window summary plot: score_total vs window_id (as categorical index)
    pws = rob_root / "per_window_summary.csv"
    if pws.exists():
        df = pd.read_csv(pws).sort_values(["window_id"], kind="mergesort")
        fig = plt.figure(figsize=(9, 4.5))
        ax = fig.add_subplot(111)
        ax.plot(range(len(df)), df["score_total"].astype(float).tolist(), marker="o")
        ax.set_title("Robust-choice score_total per window")
        ax.set_xlabel("window index (sorted by window_id)")
        ax.set_ylabel("score_total")
        ax.grid(True)
        out = plots_dir / "score_total_per_window.png"
        _savefig(fig, out)
        manifest.append({"file": str(out.relative_to(rob_root)), "sha256": sha256_file(out)})

        # tier counts bar (deterministic)
        if "tier" in df.columns:
            order = ["GREEN", "YELLOW", "RED"]
            counts = [int((df["tier"] == t).sum()) for t in order]
            fig = plt.figure(figsize=(6, 4.2))
            ax = fig.add_subplot(111)
            ax.bar(order, counts)
            ax.set_title("Stability tier counts (per-window)")
            ax.set_ylabel("count")
            ax.grid(True, axis="y")
            out = plots_dir / "tier_counts.png"
            _savefig(fig, out)
            manifest.append({"file": str(out.relative_to(rob_root)), "sha256": sha256_file(out)})

    # continuity metrics plot
    cm = rob_root / "continuity_metrics.csv"
    if cm.exists():
        df = pd.read_csv(cm).sort_values(["window_id"], kind="mergesort")
        if "delta_score_prev" in df.columns:
            fig = plt.figure(figsize=(9, 4.5))
            ax = fig.add_subplot(111)
            ax.plot(range(len(df)), df["delta_score_prev"].astype(float).tolist(), marker="o")
            ax.set_title("Delta score_total vs previous window (robust choice)")
            ax.set_xlabel("window index (sorted by window_id)")
            ax.set_ylabel("delta_score_prev")
            ax.grid(True)
            out = plots_dir / "delta_score_prev.png"
            _savefig(fig, out)
            manifest.append({"file": str(out.relative_to(rob_root)), "sha256": sha256_file(out)})

    # family-level distribution plot (box) aggregated across all windows
    windows_dir = rob_root / "windows"
    rows = []
    if windows_dir.exists():
        for wdir in sorted([p for p in windows_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            agg = wdir / "aggregated_metrics.csv"
            if not agg.exists():
                continue
            dfw = pd.read_csv(agg)
            if dfw.empty:
                continue
            rows.append(dfw[["family", "score_total"]])
    if rows:
        df = pd.concat(rows, ignore_index=True)
        df["family"] = df["family"].astype(str)
        fams = sorted(df["family"].unique().tolist())
        data = [df[df["family"] == f]["score_total"].astype(float).tolist() for f in fams]
        fig = plt.figure(figsize=(9, 4.5))
        ax = fig.add_subplot(111)
        ax.boxplot(data, labels=fams, vert=True, showfliers=False)
        ax.set_title("score_total distribution by scenario family (all windows)")
        ax.set_ylabel("score_total")
        ax.grid(True, axis="y")
        out = plots_dir / "family_boxplot.png"
        _savefig(fig, out)
        manifest.append({"file": str(out.relative_to(rob_root)), "sha256": sha256_file(out)})

    mpath = rob_root / "plots_manifest.json"
    mpath.write_text(json.dumps({"ok": True, "plots": manifest}, indent=2, sort_keys=True))
    return {"ok": True, "plots": manifest}
