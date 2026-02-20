"""
Deterministic CV split generation for model-form evaluation (v7.0.0).
Uses available diagnostic identifiers from robustness artifacts if present.
No randomness.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
import hashlib

from .schema import CVSplit, canonical_json, sha256_text

def _read_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _diag_ids_from_run(run_dir: Path) -> List[str]:
    """Best-effort extraction of diagnostic ids from run artifacts."""
    run_dir = Path(run_dir)
    rob = run_dir / "robustness_v4"

    # Preferred: robustness scenario library describing diagnostic subsets
    # (If present, it may contain 'diagnostics' or 'inclusion_set' fields.)
    lib = rob / "scenario_library.json"
    ids: List[str] = []
    if lib.exists():
        try:
            obj = _read_json(lib)
            for s in obj.get("scenarios", []):
                params = s.get("parameters", {}) if isinstance(s, dict) else {}
                for key in ("diagnostics", "include", "inclusion_set", "diagnostic_ids"):
                    v = params.get(key)
                    if isinstance(v, list):
                        ids.extend([str(x) for x in v])
        except Exception:
            pass

    # Fallback: diagnostic contracts snapshot if present
    for cand in [run_dir / "diagnostic_contracts_snapshot.json", run_dir / "diagnostic_contracts.json"]:
        if cand.exists() and not ids:
            try:
                obj = _read_json(cand)
                # expected: {contracts:[{id:...}]} or dict of id->...
                if isinstance(obj, dict) and "contracts" in obj and isinstance(obj["contracts"], list):
                    ids = [str(c.get("id")) for c in obj["contracts"] if c.get("id")]
                elif isinstance(obj, dict):
                    ids = [str(k) for k in obj.keys()]
            except Exception:
                pass

    ids = sorted({i for i in ids if i and i.lower() != "none"})
    return ids

def generate_cv_splits(run_dir: Path, max_splits: int = 64) -> List[CVSplit]:
    """Generate deterministic CV splits. Currently:
      - leave-one-out over diagnostic ids (loo)
    Additional kinds can be added later without breaking schema.
    """
    diags = _diag_ids_from_run(run_dir)
    splits: List[CVSplit] = []

    for d in diags[:max_splits]:
        sid = f"loo_{d}"
        splits.append(CVSplit(
            split_id=sid,
            kind="loo",
            holdout=[d],
            details={"source": "diagnostic_ids", "diag": d},
        ))

    if not splits:
        splits.append(CVSplit(
            split_id="noop_none_available",
            kind="noop",
            holdout=[],
            details={"reason": "no diagnostic ids found in run artifacts"},
        ))
    return splits
