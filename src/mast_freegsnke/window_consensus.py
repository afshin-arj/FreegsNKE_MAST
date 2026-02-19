
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import math

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore

from .windowing import TimeWindow, _find_time_column, _pick_ip_column


@dataclass(frozen=True)
class ConsensusWindow:
    t_start: float
    t_end: float
    sources_used: List[str]
    frac_sources_agree: float
    method: str
    notes: List[str]
    per_source: Dict[str, Dict[str, object]]


def _require_pandas() -> None:
    if pd is None:
        raise RuntimeError("pandas required for consensus. Install optional deps: pip install -e '.[zarr]'")


def _finite(x: float) -> bool:
    return x is not None and not (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))


def _infer_window_for_file(csv_path: Path, label: str, formed_frac: float) -> Optional[TimeWindow]:
    """Infer a TimeWindow from a specific CSV file deterministically.

    For magnetics files, prefer an Ip-like column; otherwise, pick the column with largest abs-span.
    """
    if not csv_path.exists():
        return None
    _require_pandas()
    df = pd.read_csv(csv_path)
    if df.shape[0] < 3 or df.shape[1] < 2:
        return None

    tcol = _find_time_column(list(df.columns))
    cols = [c for c in df.columns if c != tcol]
    if not cols:
        return None

    # Choose signal column
    sig_col: Optional[str] = None
    if "magnetics" in label:
        sig_col = _pick_ip_column(cols)
    if sig_col is None:
        # largest abs-span proxy
        best_c = None
        best_span = -1.0
        for c in cols:
            try:
                y = df[c].astype(float)
                span = float(y.abs().max() - y.abs().min())
                if _finite(span) and span > best_span:
                    best_span = span
                    best_c = c
            except Exception:
                continue
        sig_col = best_c

    if sig_col is None:
        return None

    t = df[tcol].astype(float).to_list()
    y = df[sig_col].astype(float).to_list()

    # threshold = formed_frac * max(abs(y))
    ay = [abs(v) for v in y if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not ay:
        return None
    ymax = max(ay)
    thr = formed_frac * ymax
    idx = [i for i, v in enumerate(y) if v is not None and not (isinstance(v, float) and math.isnan(v)) and abs(v) >= thr]
    if not idx:
        # fallback to full extent
        return TimeWindow(
            t_start=float(min(t)),
            t_end=float(max(t)),
            source=label,
            signal_column=sig_col,
            threshold=None,
            note="consensus_fallback_full_extent_no_samples_above_threshold",
        )
    i0, i1 = idx[0], idx[-1]
    return TimeWindow(t_start=float(t[i0]), t_end=float(t[i1]), source=label, signal_column=sig_col, threshold=float(thr))


def _best_covered_segment(intervals: List[Tuple[float, float]]) -> Tuple[float, float, int]:
    """Pick a segment with maximal coverage count using endpoint grid.

    Deterministic:
      - consider all unique boundaries
      - score midpoints by number of intervals covering them
      - choose segment with max count, then max length, then earliest start
    """
    bounds: List[float] = sorted({b for iv in intervals for b in iv})
    if len(bounds) < 2:
        # degenerate
        t0 = bounds[0] if bounds else 0.0
        return (t0, t0, 0)

    best = (bounds[0], bounds[1], -1, -1.0)  # (start,end,count,length)
    for a, b in zip(bounds[:-1], bounds[1:]):
        if not (b > a):
            continue
        mid = 0.5 * (a + b)
        count = sum(1 for (s, e) in intervals if s <= mid <= e)
        length = b - a
        cand = (a, b, count, length)
        if cand[2] > best[2]:
            best = cand
        elif cand[2] == best[2]:
            if cand[3] > best[3]:
                best = cand
            elif cand[3] == best[3] and cand[0] < best[0]:
                best = cand

    return (float(best[0]), float(best[1]), int(best[2]))


def infer_consensus_window(inputs_dir: Path, formed_frac: float) -> ConsensusWindow:
    """Compute a formed-plasma window consensus from multiple extracted signals.

    Sources attempted (in deterministic order):
      - magnetics_raw.csv
      - magnetics.csv
      - pf_active_raw.csv
      - pf_currents.csv

    Outputs both the chosen consensus segment and per-source windows for audit.
    """
    _require_pandas()

    candidates = [
        ("magnetics_raw.csv", inputs_dir / "magnetics_raw.csv"),
        ("magnetics.csv", inputs_dir / "magnetics.csv"),
        ("pf_active_raw.csv", inputs_dir / "pf_active_raw.csv"),
        ("pf_currents.csv", inputs_dir / "pf_currents.csv"),
    ]

    per: Dict[str, Dict[str, object]] = {}
    intervals: List[Tuple[float, float]] = []
    used_labels: List[str] = []

    for label, path in candidates:
        tw = _infer_window_for_file(path, label=label, formed_frac=formed_frac)
        if tw is None:
            continue
        per[label] = tw.__dict__
        # sanitize ordering
        t0, t1 = float(min(tw.t_start, tw.t_end)), float(max(tw.t_start, tw.t_end))
        intervals.append((t0, t1))
        used_labels.append(label)

    if not intervals:
        raise FileNotFoundError(f"No usable CSVs found for consensus in {inputs_dir}")

    seg0, seg1, count = _best_covered_segment(intervals)
    notes: List[str] = []
    method = "endpoint_grid_max_coverage"

    if count <= 0:
        # fallback: intersection if any, else first source window
        s0 = max(s for s, _ in intervals)
        s1 = min(e for _, e in intervals)
        if s1 > s0:
            seg0, seg1 = float(s0), float(s1)
            count = len(intervals)
            method = "hard_intersection_fallback"
            notes.append("used_full_intersection")
        else:
            seg0, seg1 = intervals[0]
            count = 1
            method = "first_source_fallback"
            notes.append("no_overlapping_segment_found")

    frac = float(count) / float(len(intervals)) if intervals else 0.0

    return ConsensusWindow(
        t_start=float(seg0),
        t_end=float(seg1),
        sources_used=used_labels,
        frac_sources_agree=float(frac),
        method=method,
        notes=notes,
        per_source=per,
    )
