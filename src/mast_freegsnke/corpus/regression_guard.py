from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from ..util import write_json

def regression_guard(
    delta_scorecards_path: Path,
    out_path: Path,
    max_red_increase: int = 0,
    max_median_degradation_increase: float = 0.0,
) -> Dict[str, Any]:
    """Deterministic regression guard for certified comparisons.

    Flags RED if:
      - RED tier count increases by more than max_red_increase, OR
      - median relative degradation increases by more than max_median_degradation_increase.
    """
    delta = json.loads(Path(delta_scorecards_path).read_text())
    tierA = delta.get("tier_counts_A", {})
    tierB = delta.get("tier_counts_B", {})
    redA = int(tierA.get("RED", 0))
    redB = int(tierB.get("RED", 0))
    red_increase = redB - redA

    rd = delta.get("relative_degradation", {})
    medA = rd.get("median_A")
    medB = rd.get("median_B")
    med_increase = None
    if (medA is not None) and (medB is not None):
        med_increase = float(medB) - float(medA)

    ok = True
    reasons = []
    if red_increase > int(max_red_increase):
        ok = False
        reasons.append(f"RED tier increase {red_increase} > {max_red_increase}")
    if med_increase is not None and med_increase > float(max_median_degradation_increase):
        ok = False
        reasons.append(f"median relative degradation increase {med_increase} > {max_median_degradation_increase}")

    out = {
        "schema_version": "v5.0.0",
        "ok": ok,
        "reasons": reasons,
        "red_increase": red_increase,
        "median_degradation_increase": med_increase,
        "thresholds": {
            "max_red_increase": int(max_red_increase),
            "max_median_degradation_increase": float(max_median_degradation_increase),
        },
    }
    write_json(Path(out_path), out)
    return out
