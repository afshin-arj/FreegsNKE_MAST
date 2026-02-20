"""
Deterministic forward-check evaluation (v7.0.0).

We interpret 'forward check' as a held-out evaluation using scenario outputs.
No fitting; uses existing scenario metrics if present, else falls back to robust-choice metric.

Mechanism:
- baseline_value: robust_choice[primary_metric] per window (if available)
- heldout_value: best matching scenario metric among diagnostic_subset scenarios (if identifiable), else None
- relative_degradation: (heldout-baseline)/max(|baseline|,eps)

© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import pandas as pd

from .schema import CVSplit, ForwardCheckRow

def _read_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if v != v:  # nan
            return None
        return v
    except Exception:
        return None

def _rel_deg(b: Optional[float], h: Optional[float]) -> Optional[float]:
    if b is None or h is None:
        return None
    denom = abs(b) if abs(b) > 1e-12 else 1.0
    return (h - b) / denom

def _window_baseline(window_dir: Path, primary_metric: str) -> Optional[float]:
    rc = window_dir / "robust_choice.json"
    if not rc.exists():
        return None
    obj = _read_json(rc)
    return _safe_float(obj.get(primary_metric, obj.get("score_total")))

def _scenario_metric(window_dir: Path, scenario_id: str, primary_metric: str) -> Optional[float]:
    # v4 structure: scenarios/<scenario_id>/metrics.json
    mp = window_dir / "scenarios" / scenario_id / "metrics.json"
    if mp.exists():
        obj = _read_json(mp)
        return _safe_float(obj.get(primary_metric, obj.get("score_total"), obj.get("chi2_total")))
    return None

def run_forward_checks(run_dir: Path, splits: List[CVSplit], primary_metric: str) -> pd.DataFrame:
    run_dir = Path(run_dir)
    rob = run_dir / "robustness_v4"
    windows_dir = rob / "windows"
    if not windows_dir.exists():
        raise FileNotFoundError(f"Missing windows directory: {windows_dir}")

    rows: List[Dict[str, Any]] = []

    for wdir in sorted([p for p in windows_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
        baseline = _window_baseline(wdir, primary_metric)

        # discover available scenario ids (if any)
        scen_root = wdir / "scenarios"
        scenario_ids = sorted([p.name for p in scen_root.iterdir() if p.is_dir()]) if scen_root.exists() else []

        for sp in splits:
            scen = None
            held = None
            note = ""
            # For now: deterministic mapping - if scenario id contains heldout diag string, prefer it.
            if scenario_ids and sp.holdout:
                # exact match first
                for s in scenario_ids:
                    if any(h in s for h in sp.holdout):
                        scen = s
                        break
            if scen is not None:
                held = _scenario_metric(wdir, scen, primary_metric)
                note = "matched scenario by substring"
            else:
                note = "no matching scenario found"

            rows.append(ForwardCheckRow(
                split_id=sp.split_id,
                window_id=wdir.name,
                scenario_id=scen,
                metric=primary_metric,
                baseline_value=baseline,
                heldout_value=held,
                relative_degradation=_rel_deg(baseline, held),
                notes=note,
            ).to_dict())

    df = pd.DataFrame(rows)
    return df
