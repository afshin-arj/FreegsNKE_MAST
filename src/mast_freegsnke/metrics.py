from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # headless
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

from .diagnostic_contracts import DiagnosticContract


@dataclass(frozen=True)
class ResidualMetric:
    name: str
    n: int
    rms: float
    mae: float
    max_abs: float


def _interp_to(t_ref: np.ndarray, t: np.ndarray, y: np.ndarray) -> np.ndarray:
    order = np.argsort(t)
    return np.interp(t_ref, t[order], y[order])


def compare_timeseries(
    exp_csv: Path,
    syn_csv: Path,
    time_col: str,
    value_col: str,
    name: Optional[str] = None,
) -> ResidualMetric:
    """Compute simple residual metrics between experimental and synthetic traces.

    Deterministic contract:
    - Compare on the experimental timebase by linear interpolation of synthetic trace.
    - Ignore NaNs in experimental.
    """
    exp = pd.read_csv(exp_csv)
    syn = pd.read_csv(syn_csv)

    t_exp = exp[time_col].to_numpy(dtype=float)
    y_exp = exp[value_col].to_numpy(dtype=float)
    t_syn = syn[time_col].to_numpy(dtype=float)
    y_syn = syn[value_col].to_numpy(dtype=float)

    mask = np.isfinite(t_exp) & np.isfinite(y_exp)
    t_exp = t_exp[mask]
    y_exp = y_exp[mask]
    if t_exp.size == 0:
        raise ValueError(f"No finite samples in experimental trace for {value_col}")

    y_syn_i = _interp_to(t_exp, t_syn, y_syn)
    r = y_syn_i - y_exp
    r = r[np.isfinite(r)]
    if r.size == 0:
        raise ValueError(f"No finite residual samples for {value_col}")

    return ResidualMetric(
        name=name or value_col,
        n=int(r.size),
        rms=float(np.sqrt(np.mean(r * r))),
        mae=float(np.mean(np.abs(r))),
        max_abs=float(np.max(np.abs(r))),
    )


def run_residual_contracts(run_dir: Path, contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run residual comparisons defined by deterministic contracts.

    Contract schema (each entry):
      {
        "name": "psi_loop_01" (optional),
        "exp_csv": "inputs/flux_loop_01.csv",
        "syn_csv": "outputs/flux_loop_01_synth.csv",
        "time_col": "time",
        "value_col": "psi"
      }
    """
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for c in contracts:
        try:
            exp_csv = (run_dir / str(c["exp_csv"]))
            syn_csv = (run_dir / str(c["syn_csv"]))
            if not exp_csv.exists() or not syn_csv.exists():
                raise FileNotFoundError(f"Missing exp/syn CSV: {exp_csv} or {syn_csv}")
            m = compare_timeseries(
                exp_csv=exp_csv,
                syn_csv=syn_csv,
                time_col=str(c.get("time_col", "time")),
                value_col=str(c["value_col"]),
                name=str(c.get("name", c.get("value_col", "trace"))),
            )
            results.append(m.__dict__)
        except Exception as e:
            errors.append({"contract": c, "error": str(e), "type": type(e).__name__})

    return {
        "n_contracts": int(len(contracts)),
        "n_ok": int(len(results)),
        "n_failed": int(len(errors)),
        "metrics": results,
        "errors": errors,
    }


def write_metrics(run_dir: Path, payload: Dict[str, Any]) -> Path:
    out = run_dir / "reconstruction_metrics.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return out



def compare_from_contracts(run_dir: Path, contracts: List[DiagnosticContract]) -> Dict[str, Any]:
    """
    Compute residual metrics for all contracts, writing residual CSVs and a summary JSON.

    Deterministic rules:
      - Interpolate synthetic to experimental timebase (linear).
      - Apply sign/scale per contract BEFORE comparison.
      - Drop NaNs in experimental.
    """
    out_dir = run_dir / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)

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

            t_syn = syn[c.syn.time_col].to_numpy(dtype=float)
            y_syn = c.syn.apply(syn[c.syn.value_col].to_numpy(dtype=float))

            mask = np.isfinite(t_exp) & np.isfinite(y_exp)
            t_exp2 = t_exp[mask]
            y_exp2 = y_exp[mask]
            if t_exp2.size < 3:
                raise ValueError("insufficient experimental points after NaN filtering")

            y_syn_i = _interp_to(t_exp2, t_syn, y_syn)
            r = y_exp2 - y_syn_i

            met = ResidualMetric(
                name=c.name,
                n=int(r.size),
                rms=float(np.sqrt(np.mean(r**2))),
                mae=float(np.mean(np.abs(r))),
                max_abs=float(np.max(np.abs(r))),
            )

            res_df = pd.DataFrame({"time": t_exp2, "exp": y_exp2, "syn": y_syn_i, "residual": r})
            res_path = out_dir / f"residual_{c.name}.csv"
            res_df.to_csv(res_path, index=False)

            # Deterministic plot artifacts (best-effort; do not block scoring).
            if _HAS_MPL:
                try:
                    rep_dir = run_dir / "report" / "key_plots"
                    rep_dir.mkdir(parents=True, exist_ok=True)

                    # exp vs syn
                    fig = plt.figure()
                    plt.plot(t_exp2, y_exp2, label="exp")
                    plt.plot(t_exp2, y_syn_i, label="syn")
                    plt.xlabel("time [s]")
                    plt.ylabel(f"{c.name} [{c.units}]")
                    plt.legend()
                    fig.savefig(rep_dir / f"{c.name}_exp_vs_syn.png", dpi=150, bbox_inches="tight")
                    plt.close(fig)

                    # residual
                    fig2 = plt.figure()
                    plt.plot(t_exp2, r)
                    plt.xlabel("time [s]")
                    plt.ylabel(f"residual [{c.units}]")
                    fig2.savefig(rep_dir / f"{c.name}_residual.png", dpi=150, bbox_inches="tight")
                    plt.close(fig2)
                except Exception:
                    pass

            per_contract.append({
                "name": c.name,
                "dtype": c.dtype,
                "units": c.units,
                "n": met.n,
                "rms": met.rms,
                "mae": met.mae,
                "max_abs": met.max_abs,
                "residual_csv": str(res_path),
            })
        except Exception as e:
            errors.append(f"{c.name}: {e}")

    summary = {
        "ok": len(errors) == 0,
        "n_contracts": len(contracts),
        "n_scored": len(per_contract),
        "errors": errors,
        "per_contract": per_contract,
    }
    out_path = out_dir / "reconstruction_metrics.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary