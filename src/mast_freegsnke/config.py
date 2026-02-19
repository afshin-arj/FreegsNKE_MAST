from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

@dataclass(frozen=True)
class AppConfig:
    mastapp_base_url: str
    required_groups: List[str]
    level2_s3_prefix: str
    s5cmd_path: str
    runs_dir: Path
    cache_dir: Path
    formed_plasma_frac: float
    s3_layout_patterns: List[str]
    allow_missing_geometry: bool

    # Optional: execute FreeGSNKE scripts after generating a run folder.
    execute_freegsnke: bool
    # one of: none | inverse | forward | both
    freegsnke_run_mode: str
    # Optional python interpreter path for FreeGSNKE environment; defaults to current interpreter.
    freegsnke_python: Optional[str]

    # Optional residual comparison configuration.
    # Each entry is a dict contract that describes how to compare experimental vs synthetic traces.
    diagnostics_compare: List[Dict[str, Any]]

    # Optional: path to diagnostic contracts authority JSON.
    diagnostic_contracts_path: Optional[str]
    # Optional: path to PF/coil mapping authority JSON.
    coil_map_path: Optional[str]
    # Enable contract-driven extraction + residual metrics (requires contracts).
    enable_contract_metrics: bool

    @staticmethod
    def load(path: Path) -> "AppConfig":
        obj = json.loads(path.read_text())
        return AppConfig(
            mastapp_base_url=str(obj.get("mastapp_base_url", "https://mastapp.site/json")).rstrip("/"),
            required_groups=list(obj.get("required_groups", ["pf_active", "magnetics"])),
            level2_s3_prefix=str(obj.get("level2_s3_prefix", "")),
            s5cmd_path=str(obj.get("s5cmd_path", "s5cmd")),
            runs_dir=Path(obj.get("runs_dir", "runs")),
            cache_dir=Path(obj.get("cache_dir", "data_cache")),
            formed_plasma_frac=float(obj.get("formed_plasma_frac", 0.80)),
            allow_missing_geometry=bool(obj.get("allow_missing_geometry", False)),
            execute_freegsnke=bool(obj.get("execute_freegsnke", False)),
            freegsnke_run_mode=str(obj.get("freegsnke_run_mode", "none")).lower(),
            freegsnke_python=(str(obj["freegsnke_python"]) if obj.get("freegsnke_python") else None),
            diagnostics_compare=list(obj.get("diagnostics_compare", [])),
            diagnostic_contracts_path=(str(obj["diagnostic_contracts_path"]) if obj.get("diagnostic_contracts_path") else None),
            coil_map_path=(str(obj["coil_map_path"]) if obj.get("coil_map_path") else None),
            enable_contract_metrics=bool(obj.get("enable_contract_metrics", False)),
            s3_layout_patterns=list(obj.get("s3_layout_patterns", [
                "{prefix}/{group}/shot_{shot}.zarr",
                "{prefix}/shot_{shot}/{group}.zarr",
                "{prefix}/shot_{shot}_{group}.zarr",
            ])),
        )
