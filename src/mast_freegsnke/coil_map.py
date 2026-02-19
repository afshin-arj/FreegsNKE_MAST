
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class CoilMapError(ValueError):
    pass


@dataclass(frozen=True)
class CoilMap:
    """
    Deterministic mapping from experimental PF current columns to FreeGSNKE coil names.

    Schema:
    {
      "version": "1.0",
      "mapping": {
        "exp_column_name": {"coil": "FreeGSNKE_CoilName", "scale": 1.0, "sign": 1}
      }
    }
    """
    mapping: Dict[str, Dict[str, Any]]


def load_coil_map(path: Path) -> CoilMap:
    obj = json.loads(path.read_text())
    if not isinstance(obj, dict):
        raise CoilMapError("coil_map JSON root must be an object")
    mapping = obj.get("mapping", {})
    if not isinstance(mapping, dict):
        raise CoilMapError("'mapping' must be an object")
    return CoilMap(mapping=mapping)


def validate_coil_map(coil_map: CoilMap) -> Dict[str, Any]:
    report: Dict[str, Any] = {"ok": True, "errors": [], "n": len(coil_map.mapping)}
    for exp_col, spec in coil_map.mapping.items():
        if not isinstance(spec, dict):
            report["ok"] = False
            report["errors"].append(f"{exp_col}: mapping spec must be an object")
            continue
        coil = spec.get("coil")
        if not coil or not isinstance(coil, str):
            report["ok"] = False
            report["errors"].append(f"{exp_col}: missing 'coil' string")
        sign = spec.get("sign", 1)
        if sign not in (-1, 1):
            report["ok"] = False
            report["errors"].append(f"{exp_col}: sign must be +1 or -1")
        try:
            float(spec.get("scale", 1.0))
        except Exception:
            report["ok"] = False
            report["errors"].append(f"{exp_col}: scale must be numeric")
    return report


def write_resolved_coil_map(run_dir: Path, coil_map: CoilMap) -> Path:
    out_dir = run_dir / "contracts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "coil_map.resolved.json"
    out_path.write_text(json.dumps({"version": "1.0", "mapping": coil_map.mapping}, indent=2, sort_keys=True))
    return out_path
