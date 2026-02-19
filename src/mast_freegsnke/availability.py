from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

@dataclass(frozen=True)
class GroupAvailability:
    group: str
    exists: bool
    s3_path: Optional[str] = None
    error: Optional[str] = None

def check_groups(
    shot: int,
    groups: List[str],
    discover: Callable[[int, str], str],
) -> Dict[str, GroupAvailability]:
    out: Dict[str, GroupAvailability] = {}
    for g in groups:
        try:
            path = discover(shot, g)
            out[g] = GroupAvailability(group=g, exists=True, s3_path=path, error=None)
        except Exception as e:
            out[g] = GroupAvailability(group=g, exists=False, s3_path=None, error=str(e))
    return out
