from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple

Family = Literal[
    "window",
    "diagnostic_subset",
    "contract_perturbation",
]

@dataclass(frozen=True)
class WindowDef:
    window_id: str
    t_start: float  # [s]
    t_end: float    # [s]
    note: str = ""

    def to_obj(self) -> Dict[str, Any]:
        return {"window_id": self.window_id, "t_start": float(self.t_start), "t_end": float(self.t_end), "note": self.note}

    def canonical_json(self) -> str:
        return json.dumps(self.to_obj(), sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ScenarioDescriptor:
    family: Family
    window_id: str
    name: str
    params: Dict[str, Any]

    def to_obj(self) -> Dict[str, Any]:
        return {"family": self.family, "window_id": self.window_id, "name": self.name, "params": self.params}

    def canonical_json(self) -> str:
        # separators ensures stable hashing independent of whitespace
        return json.dumps(self.to_obj(), sort_keys=True, separators=(",", ":"))

    def scenario_id(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()[:16]
