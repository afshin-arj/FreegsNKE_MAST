"""
Schemas for deterministic model-form evaluation (v7.0.0).
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import json
import hashlib

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ModelFormConfig:
    mfe_green: float = 0.05
    mfe_yellow: float = 0.15
    primary_metric: str = "score_total"
    max_splits: int = 64
    zero_timestamp_mode: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())

@dataclass(frozen=True)
class CVSplit:
    split_id: str
    kind: str   # loo|family_holdout|phase_holdout (deterministic)
    holdout: List[str]  # diagnostic ids or family tags
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())

@dataclass(frozen=True)
class ForwardCheckRow:
    split_id: str
    window_id: str
    scenario_id: Optional[str]
    metric: str
    baseline_value: Optional[float]
    heldout_value: Optional[float]
    relative_degradation: Optional[float]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ModelFormScorecard:
    tier: str
    worst_relative_degradation: float
    metric: str
    config_hash: str
    n_rows: int
    n_splits: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())
