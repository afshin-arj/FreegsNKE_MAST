from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import pandas as pd

def _load_descriptor(scenario_dir: Path) -> Dict[str, Any] | None:
    p = scenario_dir / "descriptor.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def sensitivity_attribution(rob_root: Path, top_k: int = 8) -> Dict[str, Any]:
    """Build a deterministic sensitivity attribution ledger.

    Inputs:
      rob_root = <run>/robustness_v4

    Method:
      - Iterate all windows/<window_id>/aggregated_metrics.csv
      - For each window, compute baseline=min(score_total)
      - For each family, compute worst_family=max(score_total) and rel_degradation=(worst_family-baseline)/baseline
      - Aggregate across windows:
          * per_family: worst_overall, mean_rel_degradation, count_windows_where_dominant
      - Identify top_k worst scenarios globally by score_total (tie-break by scenario_id)

    Returns a JSON-serializable dict.
    """
    windows_dir = rob_root / "windows"
    if not windows_dir.exists():
        return {"ok": False, "error": "windows directory missing", "path": str(windows_dir)}

    per_family_rows: List[Dict[str, Any]] = []
    worst_scenarios: List[Tuple[float, str, str]] = []  # (score_total, scenario_id, window_id)

    for wdir in sorted([p for p in windows_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
        agg = wdir / "aggregated_metrics.csv"
        if not agg.exists():
            continue
        df = pd.read_csv(agg)
        if df.empty:
            continue
        df = df.sort_values(["score_total", "scenario_id"], kind="mergesort")
        baseline = float(df["score_total"].min())
        if baseline <= 0:
            continue

        # worst scenarios list
        dfw = df.sort_values(["score_total", "scenario_id"], ascending=[False, True], kind="mergesort")
        for _, r in dfw.head(top_k).iterrows():
            worst_scenarios.append((float(r["score_total"]), str(r["scenario_id"]), str(wdir.name)))

        # per-family degradation within this window
        fams = sorted(set(df["family"].astype(str).tolist()))
        worst_by_family = {}
        for fam in fams:
            dff = df[df["family"].astype(str) == fam]
            if dff.empty:
                continue
            worst = float(dff["score_total"].max())
            worst_by_family[fam] = worst

        if not worst_by_family:
            continue
        # dominant family: largest relative degradation (tie-break lexicographically)
        dom = sorted(worst_by_family.items(), key=lambda kv: ((kv[1]-baseline)/baseline, kv[0]), reverse=True)[0][0]

        for fam, worst in worst_by_family.items():
            rel = float((worst - baseline) / baseline)
            per_family_rows.append({
                "window_id": str(wdir.name),
                "family": str(fam),
                "baseline_score_total": baseline,
                "worst_family_score_total": worst,
                "relative_degradation": rel,
                "is_dominant_in_window": bool(fam == dom),
            })

    if not per_family_rows:
        return {"ok": False, "error": "no aggregated metrics found"}

    dff = pd.DataFrame(per_family_rows)
    fam_summary = []
    for fam in sorted(dff["family"].unique().tolist()):
        sub = dff[dff["family"] == fam]
        fam_summary.append({
            "family": fam,
            "n_windows": int(sub["window_id"].nunique()),
            "worst_relative_degradation": float(sub["relative_degradation"].max()),
            "mean_relative_degradation": float(sub["relative_degradation"].mean()),
            "dominant_count": int(sub["is_dominant_in_window"].sum()),
        })
    fam_summary = sorted(fam_summary, key=lambda x: (x["worst_relative_degradation"], x["family"]), reverse=True)

    # global top worst scenarios
    worst_scenarios_sorted = sorted(worst_scenarios, key=lambda t: (t[0], t[1], t[2]), reverse=True)[:top_k]
    top_damage = []
    for score, sid, wid in worst_scenarios_sorted:
        sdir = windows_dir / wid / "scenarios" / sid
        desc = _load_descriptor(sdir)
        top_damage.append({
            "window_id": wid,
            "scenario_id": sid,
            "score_total": float(score),
            "descriptor": desc,
        })

    return {
        "ok": True,
        "method": "family_worstcase_relative_degradation",
        "per_family_summary": fam_summary,
        "top_damage_scenarios": top_damage,
    }

def dominant_failure_modes_markdown(attrib: Dict[str, Any]) -> str:
    if not attrib.get("ok"):
        return "# Dominant Failure Modes\n\nNo attribution available.\n"
    lines = ["# Dominant Failure Modes", ""]
    lines.append("## Families ranked by worst-case relative degradation")
    lines.append("")
    for row in attrib.get("per_family_summary", [])[:10]:
        lines.append(f"- **{row['family']}**: worst={row['worst_relative_degradation']:.3f}, mean={row['mean_relative_degradation']:.3f}, dominant_windows={row['dominant_count']}")
    lines.append("")
    lines.append("## Top damage scenarios (global)")
    lines.append("")
    for s in attrib.get("top_damage_scenarios", [])[:10]:
        lines.append(f"- window `{s['window_id']}` scenario `{s['scenario_id']}` score_total={s['score_total']}")
    lines.append("")
    return "\n".join(lines)
