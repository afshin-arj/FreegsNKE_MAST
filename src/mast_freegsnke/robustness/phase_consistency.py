from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

def assign_windows_to_phases(per_window: pd.DataFrame, phases: Dict[str, Any]) -> pd.DataFrame:
    """Assign each window to a phase by window midpoint time.

    Deterministic rule:
      mid = 0.5*(t_start+t_end)
      choose the unique phase interval containing mid (t_start <= mid < t_end).
      If none match, phase=None.
    """
    df = per_window.copy()
    mids = 0.5 * (df["t_start"].astype(float) + df["t_end"].astype(float))
    df["t_mid"] = mids

    phase_list = list(phases.get("phases", []))
    def _phase_for_mid(x: float) -> Optional[str]:
        for ph in phase_list:
            a = float(ph["t_start"]); b = float(ph["t_end"])
            if a <= x < b:
                return str(ph["phase"])
        return None

    df["phase"] = [ _phase_for_mid(float(x)) for x in df["t_mid"].tolist() ]
    return df

def compute_phase_consistency(
    per_window_df: pd.DataFrame,
    phases: Dict[str, Any],
    *,
    dominant_fraction_green: float = 0.8,
    max_rel_score_drift_green: float = 0.10,
    max_flip_rate_yellow: float = 0.4,
) -> Dict[str, Any]:
    """Compute phase-consistency classification.

    Definitions (deterministic):
      - For each phase, consider windows assigned to that phase.
      - dominant_scenario := most frequent scenario_id (tie-break lexicographically)
      - dominant_fraction := count(dominant)/N
      - rel_score_drift := (max(score_total)-min(score_total))/min(score_total) within phase
      - flip_rate := (# of adjacent scenario_id changes)/(N-1) after sorting by window_id

    Classification:
      - PHASE-CONSISTENT if dominant_fraction >= dominant_fraction_green AND rel_score_drift <= max_rel_score_drift_green
      - PHASE-DRIFTING if not consistent AND flip_rate <= max_flip_rate_yellow
      - PHASE-BREAKING otherwise

    Notes:
      - window ordering is by window_id (stable), which is deterministic given the window library generator.
    """
    if per_window_df.empty:
        return {"ok": False, "error": "per_window_df empty"}

    df = assign_windows_to_phases(per_window_df, phases)
    out_phases: List[Dict[str, Any]] = []

    for ph in [p.get("phase") for p in phases.get("phases", [])]:
        ph = str(ph)
        dph = df[df["phase"] == ph].copy()
        if dph.empty:
            out_phases.append({"phase": ph, "ok": False, "error": "no windows assigned"})
            continue

        dph = dph.sort_values(["window_id"], kind="mergesort")
        scen = dph["scenario_id"].astype(str).tolist()
        # dominant scenario with deterministic tie-break
        vc = dph["scenario_id"].astype(str).value_counts()
        max_count = int(vc.max())
        dom_candidates = sorted([k for k, v in vc.items() if int(v) == max_count])
        dominant_scenario = dom_candidates[0]
        dominant_fraction = float(max_count) / float(len(dph))

        scores = dph["score_total"].astype(float)
        smin = float(scores.min())
        smax = float(scores.max())
        rel_drift = float((smax - smin) / smin) if smin > 0 else float("inf")

        flips = 0
        for i in range(1, len(scen)):
            if scen[i] != scen[i-1]:
                flips += 1
        flip_rate = float(flips) / float(max(1, len(scen)-1))

        if (dominant_fraction >= dominant_fraction_green) and (rel_drift <= max_rel_score_drift_green):
            label = "PHASE-CONSISTENT"
        elif flip_rate <= max_flip_rate_yellow:
            label = "PHASE-DRIFTING"
        else:
            label = "PHASE-BREAKING"

        out_phases.append({
            "phase": ph,
            "ok": True,
            "n_windows": int(len(dph)),
            "dominant_scenario_id": dominant_scenario,
            "dominant_fraction": dominant_fraction,
            "relative_score_drift": rel_drift,
            "flip_rate": flip_rate,
            "label": label,
            "thresholds": {
                "dominant_fraction_green": float(dominant_fraction_green),
                "max_rel_score_drift_green": float(max_rel_score_drift_green),
                "max_flip_rate_yellow": float(max_flip_rate_yellow),
            },
        })

    # global label: worst across phases (breaking > drifting > consistent)
    order = {"PHASE-BREAKING": 2, "PHASE-DRIFTING": 1, "PHASE-CONSISTENT": 0}
    labels = [p.get("label") for p in out_phases if p.get("ok")]
    global_label = None
    if labels:
        global_label = sorted(labels, key=lambda x: order.get(str(x), 99), reverse=True)[0]

    return {"ok": True, "method": "phase_midpoint_assignment", "global_label": global_label, "phases": out_phases}
