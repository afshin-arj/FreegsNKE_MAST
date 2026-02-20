"""
Model-form audit runner (v7.0.0):
- generate deterministic CV splits
- run forward checks
- compute MFE tier

Tiering uses worst-case relative_degradation across all rows with finite values.

© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd

from .schema import ModelFormConfig, ModelFormScorecard
from .splits import generate_cv_splits
from .forward import run_forward_checks

def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)

def _tier(val: float, green: float, yellow: float) -> str:
    if val <= green:
        return "MFE-GREEN"
    if val <= yellow:
        return "MFE-YELLOW"
    return "MFE-RED"

def run_model_form_audit(run_dir: Path, cfg: ModelFormConfig) -> ModelFormScorecard:
    run_dir = Path(run_dir)
    rob = run_dir / "robustness_v4"
    out = rob / "model_form"
    out.mkdir(parents=True, exist_ok=True)

    splits = generate_cv_splits(run_dir, max_splits=cfg.max_splits)
    _write_json(out / "cv_splits.json", {
        "schema_version": "v7.0.0",
        "splits": [s.to_dict() for s in splits],
        "config": cfg.to_dict(),
    })

    df = run_forward_checks(run_dir, splits, primary_metric=cfg.primary_metric)
    df.to_csv(out / "forward_checks.csv", index=False)

    # compute worst-case relative degradation (only finite)
    series = pd.to_numeric(df.get("relative_degradation"), errors="coerce")
    finite = series.dropna()
    worst = float(finite.max()) if len(finite) else 0.0

    tier = _tier(worst, cfg.mfe_green, cfg.mfe_yellow)
    score = ModelFormScorecard(
        tier=tier,
        worst_relative_degradation=worst,
        metric=cfg.primary_metric,
        config_hash=cfg.hash(),
        n_rows=int(len(df)),
        n_splits=int(len(splits)),
    )
    _write_json(out / "model_form_scorecard.json", score.to_dict())

    md = []
    md.append("# Model-Form Error Summary\n\n")
    md.append(f"Tier: **{tier}**\n\n")
    md.append(f"Worst relative degradation: `{worst:.6g}` (green<= {cfg.mfe_green}, yellow<= {cfg.mfe_yellow})\n\n")
    md.append(f"Metric: `{cfg.primary_metric}`\n\n")
    (out / "model_form_summary.md").write_text("".join(md), encoding="utf-8")

    return score
