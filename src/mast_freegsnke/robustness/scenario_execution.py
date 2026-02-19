from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import hashlib

from .schema import ScenarioDescriptor, WindowDef
from .scoring import score_contracts_in_window
from ..diagnostic_contracts import DiagnosticContract

def _apply_subset(contracts: List[DiagnosticContract], leave_out: str) -> List[DiagnosticContract]:
    return [c for c in contracts if c.name != leave_out]

def _apply_contract_perturbation(
    contracts: List[DiagnosticContract],
    target: str,
    side: str,
    scale_mul: float,
    sign_toggle: bool,
) -> List[DiagnosticContract]:
    out: List[DiagnosticContract] = []
    for c in contracts:
        if c.name != target:
            out.append(c)
            continue
        if side == "exp":
            exp = replace(c.exp, scale=float(c.exp.scale) * float(scale_mul), sign=float(-c.exp.sign if sign_toggle else c.exp.sign))
            out.append(replace(c, exp=exp))
        elif side == "syn":
            syn = replace(c.syn, scale=float(c.syn.scale) * float(scale_mul), sign=float(-c.syn.sign if sign_toggle else c.syn.sign))
            out.append(replace(c, syn=syn))
        else:
            raise ValueError(f"invalid side: {side}")
    return out

def run_scenario(
    base_dir: Path,
    window: WindowDef,
    descriptor: ScenarioDescriptor,
    contracts: List[DiagnosticContract],
) -> Dict[str, Any]:
    """
    Execute a scenario deterministically by recomputing residual metrics under:
      - window clipping
      - diagnostic subsets
      - contract perturbations (scale/sign)

    Writes:
      - descriptor.json (canonical)
      - metrics.json (score summary + per_contract metrics)
    """
    sid = descriptor.scenario_id()
    scenario_dir = base_dir / "scenarios" / sid
    scenario_dir.mkdir(parents=True, exist_ok=True)

    # prepare contracts variant
    cset = contracts
    if descriptor.family == "diagnostic_subset":
        cset = _apply_subset(contracts, leave_out=str(descriptor.params["leave_out"]))
    elif descriptor.family == "contract_perturbation":
        cset = _apply_contract_perturbation(
            contracts,
            target=str(descriptor.params["target"]),
            side=str(descriptor.params["side"]),
            scale_mul=float(descriptor.params["scale_mul"]),
            sign_toggle=bool(descriptor.params.get("sign_toggle", False)),
        )

    score, per_contract = score_contracts_in_window(cset, t_start=window.t_start, t_end=window.t_end)
    out = {
        "scenario_id": sid,
        "family": descriptor.family,
        "window_id": descriptor.window_id,
        "name": descriptor.name,
        "params": descriptor.params,
        "score": {
            "ok": score.ok,
            "n_contracts": score.n_contracts,
            "n_scored": score.n_scored,
            "score_total": score.score_total,
            "errors": score.errors,
        },
        "per_contract": per_contract,
    }

    (scenario_dir / "descriptor.json").write_text(descriptor.canonical_json())
    (scenario_dir / "metrics.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    return out
