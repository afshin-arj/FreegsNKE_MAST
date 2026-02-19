from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import numpy as np
import pandas as pd

def load_scenario_metrics(scenarios_dir: Path) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if not scenarios_dir.exists():
        return pd.DataFrame()
    for p in sorted(scenarios_dir.iterdir()):
        m = p / "metrics.json"
        if not m.exists():
            continue
        obj = json.loads(m.read_text())
        rows.append({
            "scenario_id": obj.get("scenario_id"),
            "family": obj.get("family"),
            "window_id": obj.get("window_id"),
            "name": obj.get("name"),
            "ok": bool(obj.get("score", {}).get("ok", False)),
            "n_scored": int(obj.get("score", {}).get("n_scored", 0)),
            "score_total": float(obj.get("score", {}).get("score_total", float("inf"))),
        })
    return pd.DataFrame(rows)

def select_robust_choice(df: pd.DataFrame, policy: str) -> Dict[str, Any]:
    """
    Deterministic robust selection.

    Policies:
      - maximin: choose scenario minimizing score_total worst-case (here: score_total itself per scenario)
      - quantile75: choose first scenario with score_total <= 75th percentile threshold (stable sort by scenario_id)
    """
    if df.empty:
        return {"ok": False, "error": "no scenarios", "policy": policy}

    df2 = df.copy()
    df2 = df2.sort_values(["score_total", "scenario_id"], ascending=[True, True], kind="mergesort")

    if policy == "maximin":
        best = df2.iloc[0]
        return {"ok": True, "policy": policy, "scenario_id": best["scenario_id"], "score_total": float(best["score_total"])}
    elif policy == "quantile75":
        thr = float(df2["score_total"].quantile(0.75))
        cand = df2[df2["score_total"] <= thr]
        if cand.empty:
            best = df2.iloc[0]
        else:
            best = cand.iloc[0]
        return {"ok": True, "policy": policy, "threshold": thr, "scenario_id": best["scenario_id"], "score_total": float(best["score_total"])}
    else:
        raise ValueError(f"unknown policy: {policy}")

def stability_tiering(df: pd.DataFrame, green: float = 0.05, yellow: float = 0.15) -> Dict[str, Any]:
    """
    Compute GREEN/YELLOW/RED based on relative degradation of score_total across scenarios within a window.

    baseline := min(score_total)
    worst := max(score_total)
    degradation := (worst-baseline)/baseline
    """
    if df.empty:
        return {"ok": False, "error": "no scenarios"}
    baseline = float(df["score_total"].min())
    worst = float(df["score_total"].max())
    if not np.isfinite(baseline) or baseline <= 0:
        return {"ok": False, "error": "invalid baseline", "baseline": baseline, "worst": worst}
    degradation = (worst - baseline) / baseline
    if degradation <= green:
        tier = "GREEN"
    elif degradation <= yellow:
        tier = "YELLOW"
    else:
        tier = "RED"
    return {"ok": True, "baseline": baseline, "worst_case": worst, "relative_degradation": float(degradation), "tier": tier, "thresholds": {"green": green, "yellow": yellow}}

def continuity_metrics(per_window_choice: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Build simple continuity metrics across windows based on chosen score_total.

    Returns a dataframe with delta_score to previous window in sorted window_id order.
    """
    if not per_window_choice:
        return pd.DataFrame()
    df = pd.DataFrame(per_window_choice).sort_values(["window_id"], kind="mergesort")
    df["delta_score_prev"] = df["score_total"].diff()
    return df
