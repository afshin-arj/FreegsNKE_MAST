
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from .diagnostic_contracts import DiagnosticContract


@dataclass(frozen=True)
class SyntheticExtractResult:
    ok: bool
    written: List[str]
    errors: List[str]


def extract_synthetic_by_contracts(
    run_dir: Path,
    contracts: List[DiagnosticContract],
) -> SyntheticExtractResult:
    """
    Deterministic synthetic extraction step.

    This does NOT assume any specific FreeGSNKE output format. Instead:
      - Each contract defines the synthetic CSV and columns to use.
      - We copy/normalize those columns into run_dir/synthetic/<dtype>.csv and per-contract residual files later.

    Output convention:
      run_dir/synthetic/synthetic_<dtype>.csv with columns: time, <contract.name>, ...
      Multiple contracts with same dtype are merged by outer join on time (deterministic sort).
    """
    out_dir = run_dir / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)

    errors: List[str] = []
    written: List[str] = []

    # group contracts by dtype
    by_dtype: Dict[str, List[DiagnosticContract]] = {}
    for c in contracts:
        by_dtype.setdefault(c.dtype, []).append(c)

    for dtype, cs in by_dtype.items():
        frames: List[pd.DataFrame] = []
        for c in cs:
            try:
                syn = pd.read_csv(c.syn.csv)
                if c.syn.time_col not in syn.columns:
                    raise ValueError(f"missing time_col '{c.syn.time_col}'")
                if c.syn.value_col not in syn.columns:
                    raise ValueError(f"missing value_col '{c.syn.value_col}'")
                df = syn[[c.syn.time_col, c.syn.value_col]].copy()
                df.rename(columns={c.syn.time_col: "time", c.syn.value_col: c.name}, inplace=True)
                df[c.name] = c.syn.apply(df[c.name].astype(float))
                frames.append(df)
            except Exception as e:
                errors.append(f"{c.name}: cannot read synthetic trace from {c.syn.csv}: {e}")

        if not frames:
            continue

        # Deterministic merge on time
        merged = frames[0].sort_values("time")
        for df in frames[1:]:
            merged = pd.merge(merged, df.sort_values("time"), on="time", how="outer", sort=True)

        out_path = out_dir / f"synthetic_{dtype}.csv"
        merged.sort_values("time").to_csv(out_path, index=False)
        written.append(str(out_path))

    return SyntheticExtractResult(ok=(len(errors) == 0), written=written, errors=errors)
