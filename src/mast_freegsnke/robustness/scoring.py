from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np
import pandas as pd

from ..diagnostic_contracts import DiagnosticContract, load_contracts
from ..metrics import compare_timeseries

@dataclass(frozen=True)
class ScoreSummary:
    ok: bool
    n_contracts: int
    n_scored: int
    score_total: float
    errors: List[str]

def _score_from_metrics(per_contract: List[Dict[str, Any]]) -> float:
    # Deterministic scalarization: mean RMS across scored contracts.
    rms = [float(d["rms"]) for d in per_contract if "rms" in d]
    if not rms:
        return float("inf")
    return float(np.mean(rms))

def score_contracts_in_window(
    contracts: List[DiagnosticContract],
    t_start: float,
    t_end: float,
) -> Tuple[ScoreSummary, List[Dict[str, Any]]]:
    """
    Compute residual metrics between exp and syn, but restricted to a time window.

    Deterministic:
    - filter exp samples to [t_start, t_end]
    - interpolate syn to filtered exp timebase
    - apply sign/scale per contract before compare (already encoded in DiagnosticContract)
    - scalar score_total = mean(rms) across scored contracts
    """
    per_contract: List[Dict[str, Any]] = []
    errors: List[str] = []

    for c in contracts:
        try:
            exp = pd.read_csv(c.exp.csv)
            syn = pd.read_csv(c.syn.csv)
            if c.exp.time_col not in exp.columns or c.exp.value_col not in exp.columns:
                raise ValueError("experimental columns missing")
            if c.syn.time_col not in syn.columns or c.syn.value_col not in syn.columns:
                raise ValueError("synthetic columns missing")

            t_exp = exp[c.exp.time_col].to_numpy(dtype=float)
            y_exp = c.exp.apply(exp[c.exp.value_col].to_numpy(dtype=float))

            mask = np.isfinite(t_exp) & np.isfinite(y_exp) & (t_exp >= float(t_start)) & (t_exp <= float(t_end))
            t_exp2 = t_exp[mask]
            y_exp2 = y_exp[mask]
            if t_exp2.size < 3:
                raise ValueError("insufficient experimental points in window after filtering")

            t_syn = syn[c.syn.time_col].to_numpy(dtype=float)
            y_syn = c.syn.apply(syn[c.syn.value_col].to_numpy(dtype=float))

            # local interp (stable)
            order = np.argsort(t_syn)
            y_syn_i = np.interp(t_exp2, t_syn[order], y_syn[order])

            r = y_exp2 - y_syn_i
            rms = float(np.sqrt(np.mean(r**2)))
            mae = float(np.mean(np.abs(r)))
            max_abs = float(np.max(np.abs(r)))

            per_contract.append({
                "name": c.name,
                "dtype": c.dtype,
                "units": c.units,
                "n": int(r.size),
                "rms": rms,
                "mae": mae,
                "max_abs": max_abs,
            })
        except Exception as e:
            errors.append(f"{c.name}: {e}")

    score_total = _score_from_metrics(per_contract)
    return ScoreSummary(
        ok=(len(errors) == 0 and len(per_contract) > 0),
        n_contracts=len(contracts),
        n_scored=len(per_contract),
        score_total=score_total,
        errors=errors,
    ), per_contract
