from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

import pandas as pd

from ..util import ensure_dir, write_json, sha256_file

def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text())

def compare_atlases(atlas_a: Path, atlas_b: Path, out_dir: Path) -> Path:
    """Certified comparator for two atlas directories.

    Inputs:
      atlas_a/atlas_metrics.csv, atlas_a/atlas_summary.json
      atlas_b/atlas_metrics.csv, atlas_b/atlas_summary.json

    Output:
      out_dir/delta_scorecards.json
      out_dir/delta_summary.md
    """
    atlas_a = atlas_a.resolve()
    atlas_b = atlas_b.resolve()
    out = ensure_dir(out_dir.resolve())

    a_df = pd.read_csv(atlas_a / "atlas_metrics.csv")
    b_df = pd.read_csv(atlas_b / "atlas_metrics.csv")

    # join by shot when possible, else by run_dir
    key = "shot" if ("shot" in a_df.columns and "shot" in b_df.columns) else "run_dir"
    a_df = a_df.dropna(subset=[key])
    b_df = b_df.dropna(subset=[key])

    merged = a_df.merge(b_df, on=key, suffixes=("_A","_B"))
    merged.to_csv(out / "paired_metrics.csv", index=False)

    def counts(series):
        return series.value_counts(dropna=False).to_dict()

    tierA = counts(merged["tier_A"])
    tierB = counts(merged["tier_B"])
    famA = counts(merged["dominant_family_A"])
    famB = counts(merged["dominant_family_B"])

    # deterministic effect sizes (no p-values)
    relA = merged["relative_degradation_A"].astype(float)
    relB = merged["relative_degradation_B"].astype(float)
    delta_rel = (relB - relA)

    delta = {
        "schema_version": "v5.0.0",
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
        "hashes": {
            "paired_metrics.csv": sha256_file(out / "paired_metrics.csv"),
            "atlasA/atlas_metrics.csv": sha256_file(atlas_a / "atlas_metrics.csv"),
            "atlasB/atlas_metrics.csv": sha256_file(atlas_b / "atlas_metrics.csv"),
        },
    }
    write_json(out / "delta_scorecards.json", delta)

    # Markdown summary (deterministic ordering)
    lines = []
    lines.append("# Atlas Comparator Summary (A/B)\n")
    lines.append(f"- Paired items: {delta['n_paired']} (key: {key})\n")
    lines.append("## Tier counts\n")
    for t in ["GREEN","YELLOW","RED",None]:
        lines.append(f"- {t}: A={tierA.get(t,0)}  B={tierB.get(t,0)}\n")
    rd = delta["relative_degradation"]
    lines.append("\n## Relative degradation effect sizes\n")
    lines.append(f"- median(A)={rd['median_A']}  median(B)={rd['median_B']}  median(Δ)={rd['median_delta_B_minus_A']}\n")
    lines.append(f"- worst(A)={rd['worst_A']}  worst(B)={rd['worst_B']}  worst(Δ)={rd['worst_delta_B_minus_A']}\n")
    (out / "delta_summary.md").write_text("".join(lines))
    return out
