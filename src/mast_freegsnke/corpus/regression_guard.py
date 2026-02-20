from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from ..util import write_json


def regression_guard(delta_path: Path, out_path: Path,
                     max_red_increase: int = 0,
                     max_median_degradation_increase: float = 0.0,
                     max_physics_red_increase: int = 0,
                     max_physics_median_violation_increase: float = 0.0,
                     max_mfe_red_increase: int = 0,
                     max_mfe_median_worst_rel_deg_increase: float = 0.0) -> Dict[str, Any]:
    """Deterministic regression guard for compare-run outputs.

    v6 adds optional checks on physics-consistency deltas if present.
    """
    delta_path = Path(delta_path)
    out_path = Path(out_path)

    delta = json.loads(delta_path.read_text(encoding="utf-8"))
    rd = (delta.get("relative_degradation") or {})
    tierA = delta.get("tier_counts_A") or {}
    tierB = delta.get("tier_counts_B") or {}

    redA = int(tierA.get("RED", 0))
    redB = int(tierB.get("RED", 0))
    red_increase = redB - redA

    medA = rd.get("median_A")
    medB = rd.get("median_B")
    med_increase = None
    if (medA is not None) and (medB is not None):
        med_increase = float(medB) - float(medA)

    ok = True
    reasons = []

    if red_increase > max_red_increase:
        ok = False
        reasons.append(f"RED tier increase {red_increase} > {max_red_increase}")

    if (med_increase is not None) and (med_increase > max_median_degradation_increase):
        ok = False
        reasons.append(f"Median relative degradation increase {med_increase} > {max_median_degradation_increase}")

    # v6 physics checks (optional)
    phy = delta.get("physics")
    if phy is not None:
        phyA = phy.get("tier_counts_A") or {}
        phyB = phy.get("tier_counts_B") or {}
        preA = int(phyA.get("PHYSICS-RED", 0))
        preB = int(phyB.get("PHYSICS-RED", 0))
        pre_increase = preB - preA
        if pre_increase > max_physics_red_increase:
            ok = False
            reasons.append(f"PHYSICS-RED tier increase {pre_increase} > {max_physics_red_increase}")

        mv = phy.get("max_violation") or {}
        mva = mv.get("median_A")
        mvb = mv.get("median_B")
        mv_inc = None
        if (mva is not None) and (mvb is not None):
            mv_inc = float(mvb) - float(mva)
        if (mv_inc is not None) and (mv_inc > max_physics_median_violation_increase):
            ok = False
            reasons.append(f"Median physics max-violation increase {mv_inc} > {max_physics_median_violation_increase}")


    # v7 model-form checks (optional)
    mfe = delta.get("model_form")
    if mfe is not None:
        mfeA = mfe.get("tier_counts_A") or {}
        mfeB = mfe.get("tier_counts_B") or {}
        mredA = int(mfeA.get("MFE-RED", 0))
        mredB = int(mfeB.get("MFE-RED", 0))
        mred_inc = mredB - mredA
        if mred_inc > max_mfe_red_increase:
            ok = False
            reasons.append(f"MFE-RED tier increase {mred_inc} > {max_mfe_red_increase}")

        wrd = mfe.get("worst_relative_degradation") or {}
        mva = wrd.get("median_A")
        mvb = wrd.get("median_B")
        mv_inc = None
        if (mva is not None) and (mvb is not None):
            mv_inc = float(mvb) - float(mva)
        if (mv_inc is not None) and (mv_inc > max_mfe_median_worst_rel_deg_increase):
            ok = False
            reasons.append(f"Median MFE worst-relative-degradation increase {mv_inc} > {max_mfe_median_worst_rel_deg_increase}")

    result = {
        "schema_version": "v7.0.0",
        "ok": ok,
        "reasons": reasons,
        "inputs": {
            "delta_scorecards": str(delta_path),
        },
        "thresholds": {
            "max_red_increase": max_red_increase,
            "max_median_degradation_increase": max_median_degradation_increase,
            "max_physics_red_increase": max_physics_red_increase,
            "max_physics_median_violation_increase": max_physics_median_violation_increase,
            "max_mfe_red_increase": max_mfe_red_increase,
            "max_mfe_median_worst_rel_deg_increase": max_mfe_median_worst_rel_deg_increase,
        }
    }
    write_json(out_path, result)
    return result
