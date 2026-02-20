from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

import pandas as pd

from ..util import ensure_dir, write_json, sha256_file


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def compare_atlases(atlas_a: Path, atlas_b: Path, out_dir: Path) -> Path:
    """Certified comparator for two atlas directories (A/B).

    Inputs:
      atlas_a/atlas_metrics.csv, atlas_a/atlas_summary.json
      atlas_b/atlas_metrics.csv, atlas_b/atlas_summary.json

    Output (out_dir):
      paired_metrics.csv
      delta_scorecards.json
      delta_summary.md

    Deterministic effect sizes only (no p-values).
    """
    atlas_a = Path(atlas_a).resolve()
    atlas_b = Path(atlas_b).resolve()
    out = ensure_dir(Path(out_dir).resolve())

    a_df = pd.read_csv(atlas_a / "atlas_metrics.csv")
    b_df = pd.read_csv(atlas_b / "atlas_metrics.csv")

    key = "shot" if ("shot" in a_df.columns and "shot" in b_df.columns) else "run_dir"
    a_df = a_df.dropna(subset=[key])
    b_df = b_df.dropna(subset=[key])

    merged = a_df.merge(b_df, on=key, suffixes=("_A", "_B"))
    merged.to_csv(out / "paired_metrics.csv", index=False)

    def counts(series: pd.Series) -> Dict[Any, int]:
        return series.value_counts(dropna=False).to_dict()

    tierA = counts(merged["tier_A"]) if "tier_A" in merged.columns else {}
    tierB = counts(merged["tier_B"]) if "tier_B" in merged.columns else {}
    famA = counts(merged["dominant_family_A"]) if "dominant_family_A" in merged.columns else {}
    famB = counts(merged["dominant_family_B"]) if "dominant_family_B" in merged.columns else {}

    relA = merged["relative_degradation_A"].astype(float) if "relative_degradation_A" in merged.columns else pd.Series([], dtype=float)
    relB = merged["relative_degradation_B"].astype(float) if "relative_degradation_B" in merged.columns else pd.Series([], dtype=float)
    delta_rel = (relB - relA) if (len(relA) and len(relB)) else pd.Series([], dtype=float)

    physics = None
    if "physics_tier_A" in merged.columns and "physics_tier_B" in merged.columns:
        phyA = counts(merged["physics_tier_A"])
        phyB = counts(merged["physics_tier_B"])
        physics = {"tier_counts_A": phyA, "tier_counts_B": phyB}
        if "physics_max_violation_A" in merged.columns and "physics_max_violation_B" in merged.columns:
            vA = merged["physics_max_violation_A"].astype(float)
            vB = merged["physics_max_violation_B"].astype(float)
            dv = vB - vA
            physics["max_violation"] = {
                "median_A": float(vA.median()) if len(vA) else None,
                "median_B": float(vB.median()) if len(vB) else None,
                "median_delta_B_minus_A": float(dv.median()) if len(dv) else None,
                "worst_A": float(vA.max()) if len(vA) else None,
                "worst_B": float(vB.max()) if len(vB) else None,
                "worst_delta_B_minus_A": float(dv.max()) if len(dv) else None,
            }

    mfe = None
    if "mfe_tier_A" in merged.columns and "mfe_tier_B" in merged.columns:
        mfeA = counts(merged["mfe_tier_A"])
        mfeB = counts(merged["mfe_tier_B"])
        mfe = {"tier_counts_A": mfeA, "tier_counts_B": mfeB}
        if "mfe_worst_relative_degradation_A" in merged.columns and "mfe_worst_relative_degradation_B" in merged.columns:
            mA = merged["mfe_worst_relative_degradation_A"].astype(float)
            mB = merged["mfe_worst_relative_degradation_B"].astype(float)
            dm = mB - mA
            mfe["worst_relative_degradation"] = {
                "median_A": float(mA.median()) if len(mA) else None,
                "median_B": float(mB.median()) if len(mB) else None,
                "median_delta_B_minus_A": float(dm.median()) if len(dm) else None,
                "worst_A": float(mA.max()) if len(mA) else None,
                "worst_B": float(mB.max()) if len(mB) else None,
                "worst_delta_B_minus_A": float(dm.max()) if len(dm) else None,
            }

    delta = {
        "schema_version": "v7.0.0",
        "n_paired": int(len(merged)),
        "key": key,
        "tier_counts_A": tierA,
        "tier_counts_B": tierB,
        "dominant_family_counts_A": famA,
        "dominant_family_counts_B": famB,
        "relative_degradation": {
            "median_A": float(relA.median()) if len(relA) else None,
            "median_B": float(relB.median()) if len(relB) else None,
            "median_delta_B_minus_A": float(delta_rel.median()) if len(delta_rel) else None,
            "worst_A": float(relA.max()) if len(relA) else None,
            "worst_B": float(relB.max()) if len(relB) else None,
            "worst_delta_B_minus_A": float(delta_rel.max()) if len(delta_rel) else None,
        },
        "physics": physics,
        "model_form": mfe,
        "hashes": {
            "paired_metrics.csv": sha256_file(out / "paired_metrics.csv"),
            "atlasA/atlas_metrics.csv": sha256_file(atlas_a / "atlas_metrics.csv"),
            "atlasB/atlas_metrics.csv": sha256_file(atlas_b / "atlas_metrics.csv"),
        },
    }
    write_json(out / "delta_scorecards.json", delta)

    lines = []
    lines.append("# Atlas Comparator Summary (A/B)\n")
    lines.append(f"- Paired items: {delta['n_paired']} (key: {key})\n")

    lines.append("## Robustness tier counts\n")
    for t in ["GREEN", "YELLOW", "RED", None]:
        lines.append(f"- {t}: A={tierA.get(t,0)}  B={tierB.get(t,0)}\n")

    rd = delta["relative_degradation"]
    lines.append("\n## Robustness relative degradation effect sizes\n")
    lines.append(f"- median(A)={rd['median_A']}  median(B)={rd['median_B']}  median(Δ)={rd['median_delta_B_minus_A']}\n")
    lines.append(f"- worst(A)={rd['worst_A']}  worst(B)={rd['worst_B']}  worst(Δ)={rd['worst_delta_B_minus_A']}\n")

    if physics is not None:
        lines.append("\n## Physics-consistency tier counts\n")
        for t in ["PHYSICS-GREEN", "PHYSICS-YELLOW", "PHYSICS-RED", None]:
            lines.append(f"- {t}: A={physics['tier_counts_A'].get(t,0)}  B={physics['tier_counts_B'].get(t,0)}\n")
        if "max_violation" in physics:
            mv = physics["max_violation"]
            lines.append("\n## Physics max-violation effect sizes\n")
            lines.append(f"- median(A)={mv['median_A']}  median(B)={mv['median_B']}  median(Δ)={mv['median_delta_B_minus_A']}\n")
            lines.append(f"- worst(A)={mv['worst_A']}  worst(B)={mv['worst_B']}  worst(Δ)={mv['worst_delta_B_minus_A']}\n")

    if mfe is not None:
        lines.append("\n## Model-form (MFE) tier counts\n")
        for t in ["MFE-GREEN", "MFE-YELLOW", "MFE-RED", None]:
            lines.append(f"- {t}: A={mfe['tier_counts_A'].get(t,0)}  B={mfe['tier_counts_B'].get(t,0)}\n")
        if "worst_relative_degradation" in mfe:
            mv = mfe["worst_relative_degradation"]
            lines.append("\n## MFE worst-relative-degradation effect sizes\n")
            lines.append(f"- median(A)={mv['median_A']}  median(B)={mv['median_B']}  median(Δ)={mv['median_delta_B_minus_A']}\n")
            lines.append(f"- worst(A)={mv['worst_A']}  worst(B)={mv['worst_B']}  worst(Δ)={mv['worst_delta_B_minus_A']}\n")

    (out / "delta_summary.md").write_text("".join(lines), encoding="utf-8")
    return out
