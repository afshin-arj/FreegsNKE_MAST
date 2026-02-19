from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple
from .schema import WindowDef

def generate_window_library(
    t_start: float,
    t_end: float,
    dt_grid: Sequence[float] = (-0.02, -0.01, 0.0, 0.01, 0.02),
    expand_grid: Sequence[float] = (0.0, 0.01),
) -> List[WindowDef]:
    """
    Deterministically generate a small multi-window library around a baseline window.

    Rules:
    - shift both endpoints by dt in dt_grid
    - optionally expand by 'expand' on both sides
    - drop any windows with t_end <= t_start
    - stable ordering: (dt, expand)
    """
    windows: List[WindowDef] = []
    for dt in dt_grid:
        for ex in expand_grid:
            ts = float(t_start + dt - ex)
            te = float(t_end + dt + ex)
            if te <= ts:
                continue
            wid = f"w_dt{dt:+.4f}_ex{ex:.4f}"
            windows.append(WindowDef(window_id=wid, t_start=ts, t_end=te, note="baseline-shift-expand"))
    return windows
