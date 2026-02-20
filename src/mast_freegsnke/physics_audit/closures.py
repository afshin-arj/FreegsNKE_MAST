"""
Closure tests based on available robustness artifacts.
No new solvers. Purely diagnostic computations.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json

def _read_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def load_window_metrics(window_dir: Path) -> Dict[str, Any]:
    # Prefer aggregated_metrics.csv? In v4/v5 we have per-window robust_choice + stability_scorecard.
    # Here we use stability_scorecard.json + robust_choice.json where present.
    out: Dict[str, Any] = {}
    sc = window_dir / "stability_scorecard.json"
    rc = window_dir / "robust_choice.json"
    ag = window_dir / "aggregated_metrics.csv"
    if sc.exists():
        out["stability_scorecard"] = _read_json(sc)
    if rc.exists():
        out["robust_choice"] = _read_json(rc)
    # aggregated_metrics.csv not parsed here to keep dependencies minimal; audit.py can load pandas if needed.
    out["paths"] = {"stability_scorecard": str(sc) if sc.exists() else None,
                    "robust_choice": str(rc) if rc.exists() else None,
                    "aggregated_metrics": str(ag) if ag.exists() else None}
    return out

def closure_test_continuity_drift(prev_score: Optional[float], curr_score: Optional[float]) -> Optional[float]:
    if prev_score is None or curr_score is None:
        return None
    denom = abs(prev_score) if abs(prev_score) > 1e-12 else 1.0
    return abs(curr_score - prev_score) / denom

def closure_test_worstcase_spread(stability_scorecard: Dict[str, Any]) -> Optional[float]:
    # relative degradation from stability_scorecard (v4.0.0 style)
    if not stability_scorecard:
        return None
    val = stability_scorecard.get("relative_degradation")
    return _safe_float(val)

def closure_test_regime_boundary_spike(window_mid_t: Optional[float], phase_bounds: Tuple[float, float], drift: Optional[float]) -> Optional[float]:
    # deterministic proxy: if window midpoint near phase boundary, weight drift higher.
    if window_mid_t is None or drift is None:
        return None
    a, b = phase_bounds
    # distance to nearest boundary normalized by phase duration
    dur = max(b - a, 1e-6)
    d = min(abs(window_mid_t - a), abs(window_mid_t - b)) / dur
    # spike proxy: drift * (1/(d+eps)) capped
    return min(drift / (d + 0.05), 10.0)
