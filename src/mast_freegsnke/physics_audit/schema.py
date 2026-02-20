"""
Schemas for physics audit artifacts.
Deterministic, hash-friendly JSON structures.
© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
import json
import hashlib

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class PhysicsAuditConfig:
    # Thresholds for tiering
    physics_green: float = 0.05   # max normalized violation
    physics_yellow: float = 0.15
    # Which metric to treat as primary (if multiple exist)
    primary_metric: str = "score_total"
    # Whether to ignore timestamps when hashing packs
    zero_timestamp_mode: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())

@dataclass(frozen=True)
class ResidualBudget:
    # All values should be non-negative and dimensionless (normalized)
    buckets: Dict[str, float]
    total: float
    sanity_ok: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())

@dataclass(frozen=True)
class ClosureTestResult:
    name: str
    value: float                  # normalized [0, +inf)
    threshold_green: float
    threshold_yellow: float
    tier: str                      # PHYSICS-GREEN/YELLOW/RED
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class PhysicsScorecard:
    tier: str
    max_violation: float
    primary_metric: str
    per_test: List[ClosureTestResult]
    residual_budget: ResidualBudget
    config_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "max_violation": self.max_violation,
            "primary_metric": self.primary_metric,
            "per_test": [t.to_dict() for t in self.per_test],
            "residual_budget": self.residual_budget.to_dict(),
            "config_hash": self.config_hash,
        }

    def to_canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def hash(self) -> str:
        return sha256_text(self.to_canonical_json())
