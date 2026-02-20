from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import pandas as pd

from ..util import ensure_dir, write_json, sha256_file

def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text())

def build_atlas(corpus_dir: Path, out_dir: Optional[Path] = None) -> Path:
    """Build a cross-shot robustness atlas from an existing corpus.

    Requires corpus_dir/corpus_manifest.json and each entry's robustness_v4 artifacts.

    Outputs (in out_dir, defaults to <corpus_dir>/atlas):
      atlas_metrics.csv
      atlas_summary.json
      atlas_plots_manifest.json (hashes of generated plots)
    """
    corpus_dir = corpus_dir.resolve()
    man = _load_json(corpus_dir / "corpus_manifest.json")
    entries = man["entries"]
    out = ensure_dir((out_dir or (corpus_dir / "atlas")).resolve())

    rows: List[Dict[str, Any]] = []
    for e in entries:
        rob = Path(e["robustness_dir"])
        shot = e.get("shot")
        # per-shot summary fields
        stability = _load_json(rob / "stability_scorecard.json")
        phase_cons = _load_json(rob / "phase_consistency_scorecard.json")
        attrib = _load_json(rob / "sensitivity_attribution.json")
        choice = _load_json(rob / "global_robust_choice.json")

        # v6: physics audit (optional)
        phys_path = rob / "physics_audit" / "physics_consistency_scorecard.json"
        phys = _load_json(phys_path) if phys_path.exists() else None

        mfe_path = rob / "model_form" / "model_form_scorecard.json"
        mfe = _load_json(mfe_path) if mfe_path.exists() else None

        rows.append({
            "shot": shot,
            "run_dir": e["run_dir"],
            "tier": stability.get("tier"),
            "relative_degradation": float(stability.get("relative_degradation", 0.0)),
            "global_phase_label": phase_cons.get("global_label"),
            "dominant_family": attrib.get("dominant_family"),
            "robust_scenario_id": choice.get("scenario_id"),
            "robust_score_total": float(choice.get("score_total", float("nan"))) if choice.get("score_total") is not None else float("nan"),
            "physics_tier": (phys.get("tier") if phys else None),
            "physics_max_violation": (float(phys.get("max_violation")) if (phys and phys.get("max_violation") is not None) else float("nan")),
            "mfe_tier": (mfe.get("tier") if mfe else None),
            "mfe_worst_relative_degradation": (float(mfe.get("worst_relative_degradation")) if (mfe and mfe.get("worst_relative_degradation") is not None) else float("nan")),
        })

    df = pd.DataFrame(rows).sort_values(["shot", "run_dir"], kind="mergesort")
    df.to_csv(out / "atlas_metrics.csv", index=False)

    # Tier distribution + family distribution
    tier_counts = df["tier"].value_counts(dropna=False).to_dict()
    phase_counts = df["global_phase_label"].value_counts(dropna=False).to_dict()
    fam_counts = df["dominant_family"].value_counts(dropna=False).to_dict()

    summary = {
        "schema_version": "v7.0.0",
        "n": int(len(df)),
        "tier_counts": tier_counts,
        "phase_label_counts": phase_counts,
        "dominant_family_counts": fam_counts,
        "atlas_metrics_sha256": sha256_file(out / "atlas_metrics.csv"),
    }
    write_json(out / "atlas_summary.json", summary)

    # Deterministic plots (lightweight) and hashes
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plots_dir = ensure_dir(out / "plots")
    plot_manifest: List[Dict[str, Any]] = []

    # Plot: tier counts bar
    fig = plt.figure(figsize=(6.5, 4.0))
    ax = fig.add_subplot(111)
    tiers = ["GREEN","YELLOW","RED"]
    vals = [int(tier_counts.get(t,0)) for t in tiers]
    ax.bar(range(len(tiers)), vals)
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels(tiers)
    ax.set_title("Atlas tier counts")
    p1 = plots_dir / "tier_counts.png"
    fig.savefig(p1, dpi=120, bbox_inches="tight")
    plt.close(fig)
    plot_manifest.append({"path": str(p1.relative_to(out)), "sha256": sha256_file(p1)})

    # Plot: relative degradation histogram (fixed bins)
    if df["relative_degradation"].notna().any():
        fig = plt.figure(figsize=(7.0, 4.0))
        ax = fig.add_subplot(111)
        ax.hist(df["relative_degradation"].astype(float).tolist(), bins=20)
        ax.set_title("Relative degradation distribution")
        ax.set_xlabel("relative_degradation")
        p2 = plots_dir / "relative_degradation_hist.png"
        fig.savefig(p2, dpi=120, bbox_inches="tight")
        plt.close(fig)
        plot_manifest.append({"path": str(p2.relative_to(out)), "sha256": sha256_file(p2)})

    write_json(out / "atlas_plots_manifest.json", {"plots": plot_manifest})
    return out
