"""
Corpus-level Closure Atlas Builder (v6.0.0)
Aggregates physics audit outputs across a corpus, stratified by available regime bins.
Deterministic, hash-locked.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import hashlib
import pandas as pd

def _read_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def build_closure_atlas(corpus_dir: Path, out: Optional[Path] = None) -> Path:
    corpus_dir = Path(corpus_dir)
    if out is None:
        out = corpus_dir / "atlas" / "closure_atlas"
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    idx = corpus_dir / "shot_index.csv"
    if not idx.exists():
        raise FileNotFoundError(f"Missing corpus index: {idx}")
    df_idx = pd.read_csv(idx)

    records: List[Dict[str, Any]] = []
    for _, r in df_idx.iterrows():
        run_dir = Path(r["run_dir"])
        shot = int(r.get("shot", -1))
        phys = run_dir / r.get("robustness_subdir", "robustness_v4") / "physics_audit" / "physics_consistency_scorecard.json"
        if not phys.exists():
            # allow corpus even if some shots not audited; skip
            continue
        sc = _read_json(phys)
        records.append({
            "shot": shot,
            "run_dir": str(run_dir),
            "tier": sc.get("tier"),
            "max_violation": sc.get("max_violation"),
            "primary_metric": sc.get("primary_metric"),
            "config_hash": sc.get("config_hash"),
        })

    df = pd.DataFrame(records)
    metrics_csv = out / "closure_atlas_metrics.csv"
    df.to_csv(metrics_csv, index=False)

    # summary
    tier_counts = df["tier"].value_counts(dropna=False).to_dict() if not df.empty else {}
    summary = {
        "n_shots": int(len(df)),
        "tier_counts": tier_counts,
        "max_violation_quantiles": {
            "p50": float(df["max_violation"].quantile(0.50)) if not df.empty else None,
            "p75": float(df["max_violation"].quantile(0.75)) if not df.empty else None,
            "p95": float(df["max_violation"].quantile(0.95)) if not df.empty else None,
        },
    }
    _write_json(out / "closure_atlas_summary.json", summary)

    manifest = {
        "files": [
            {"path": "closure_atlas_metrics.csv", "sha256": _sha256_file(metrics_csv)},
            {"path": "closure_atlas_summary.json", "sha256": _sha256_file(out / "closure_atlas_summary.json")},
        ]
    }
    _write_json(out / "closure_atlas_manifest.json", manifest)
    return out
