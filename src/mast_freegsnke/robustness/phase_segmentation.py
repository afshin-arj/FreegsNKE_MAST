from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any
import json
from .schema import WindowDef

def segment_phases_from_window(win: WindowDef, pre: float = 0.02, post: float = 0.02) -> Dict[str, Any]:
    """
    Deterministic 3-phase segmentation derived only from the chosen baseline window.

    This is deliberately *data-independent* (no ML, no hidden fitting):
      - ramp_up: [t_start-pre, t_start]
      - flat_top: [t_start, t_end]
      - ramp_down: [t_end, t_end+post]

    Times are not clipped to available data (that is validated downstream by scenario execution).
    """
    t0 = float(win.t_start)
    t1 = float(win.t_end)
    return {
        "method": "window_derived_three_phase",
        "parameters": {"pre": float(pre), "post": float(post)},
        "phases": [
            {"phase": "ramp_up", "t_start": t0 - float(pre), "t_end": t0},
            {"phase": "flat_top", "t_start": t0, "t_end": t1},
            {"phase": "ramp_down", "t_start": t1, "t_end": t1 + float(post)},
        ],
    }
