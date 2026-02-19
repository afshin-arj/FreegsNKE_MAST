from __future__ import annotations

from typing import Dict, List, Sequence, Any
from .schema import ScenarioDescriptor, WindowDef
from ..diagnostic_contracts import DiagnosticContract

def generate_scenarios_for_window(
    window: WindowDef,
    contracts: List[DiagnosticContract],
    include_contract_perturbations: bool = True,
    include_leave_one_out: bool = True,
    scale_grid: Sequence[float] = (0.9, 1.0, 1.1),
    allow_sign_toggle: bool = False,
) -> List[ScenarioDescriptor]:
    """
    Deterministic scenario set per window.

    Families:
      - window: baseline scoring under this window
      - diagnostic_subset: leave-one-out (if enabled)
      - contract_perturbation: deterministic scale perturbations (and optional sign toggles)
    """
    out: List[ScenarioDescriptor] = []

    # Window baseline scenario
    out.append(ScenarioDescriptor(
        family="window",
        window_id=window.window_id,
        name="baseline_window_score",
        params={"t_start": window.t_start, "t_end": window.t_end},
    ))

    if include_leave_one_out:
        for c in contracts:
            out.append(ScenarioDescriptor(
                family="diagnostic_subset",
                window_id=window.window_id,
                name=f"leave_out:{c.name}",
                params={"leave_out": c.name},
            ))

    if include_contract_perturbations:
        for c in contracts:
            for s in scale_grid:
                out.append(ScenarioDescriptor(
                    family="contract_perturbation",
                    window_id=window.window_id,
                    name=f"scale_exp:{c.name}:{s:.3f}",
                    params={"target": c.name, "side": "exp", "scale_mul": float(s), "sign_toggle": False},
                ))
                out.append(ScenarioDescriptor(
                    family="contract_perturbation",
                    window_id=window.window_id,
                    name=f"scale_syn:{c.name}:{s:.3f}",
                    params={"target": c.name, "side": "syn", "scale_mul": float(s), "sign_toggle": False},
                ))
            if allow_sign_toggle:
                out.append(ScenarioDescriptor(
                    family="contract_perturbation",
                    window_id=window.window_id,
                    name=f"toggle_sign_exp:{c.name}",
                    params={"target": c.name, "side": "exp", "scale_mul": 1.0, "sign_toggle": True},
                ))
                out.append(ScenarioDescriptor(
                    family="contract_perturbation",
                    window_id=window.window_id,
                    name=f"toggle_sign_syn:{c.name}",
                    params={"target": c.name, "side": "syn", "scale_mul": 1.0, "sign_toggle": True},
                ))

    return out
