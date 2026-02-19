from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .util import write_json


@dataclass(frozen=True)
class MachineStub:
    """A minimal, shot-specific machine stub intended for committing into your repo.

    This is intentionally conservative: it records provenance and placeholder fields that you should
    wire into your FreeGSNKE machine model.
    """
    shot: int
    machine_name: str
    window: Optional[Dict[str, Any]]
    pf_rules: Optional[Dict[str, Any]]
    notes: str


def write_machine_stub(run_dir: Path, shot: int, machine_name: str) -> Path:
    window_path = run_dir / "inputs" / "window.json"
    pf_rules_path = run_dir / "pf_map_rules.json"

    window = None
    if window_path.exists():
        window = __import__("json").loads(window_path.read_text())

    pf_rules = None
    if pf_rules_path.exists():
        pf_rules = __import__("json").loads(pf_rules_path.read_text())

    stub = MachineStub(
        shot=int(shot),
        machine_name=str(machine_name),
        window=window,
        pf_rules=pf_rules,
        notes=(
            "This is a generated stub. Replace placeholders with authoritative geometry, circuit definitions, "
            "and diagnostic mappings for your FreeGSNKE machine model."
        ),
    )

    out_py = run_dir / "machine_stub_freegsnke.py"
    out_json = run_dir / "machine_stub_freegsnke.json"

    # JSON for tooling
    write_json(out_json, {
        "shot": stub.shot,
        "machine_name": stub.machine_name,
        "window": stub.window,
        "pf_rules": stub.pf_rules,
        "notes": stub.notes,
    })

    # Python stub for committing
    out_py.write_text(
        "# Generated machine stub for FreeGSNKE\n"
        "# Author: © 2026 Afshin Arjhangmehr\n\n"
        "from __future__ import annotations\n\n"
        "MACHINE_STUB = " + __import__("json").dumps({
            "shot": stub.shot,
            "machine_name": stub.machine_name,
            "window": stub.window,
            "pf_rules": stub.pf_rules,
            "placeholders": {
                "geometry": "<FILL_ME>",
                "pf_circuits": "<FILL_ME>",
                "flux_loops": "<FILL_ME>",
                "magnetic_probes": "<FILL_ME>",
            },
        }, indent=2) + "\n"
    )

    how = run_dir / "HOW_TO_USE_MACHINE_STUB.txt"
    how.write_text(
        "HOW TO USE MACHINE STUB\n"
        "=======================\n\n"
        "This run folder includes:\n"
        "  - machine_stub_freegsnke.py\n"
        "  - machine_stub_freegsnke.json\n\n"
        "Intended workflow:\n"
        "1) Copy machine_stub_freegsnke.py into your FreeGSNKE machine_configs/ directory\n"
        "   and rename as appropriate (e.g., MAST_shot_30201.py).\n"
        "2) Replace placeholders with your authoritative machine model fields.\n"
        "3) Commit the file to your GitHub repo to make the reconstruction reproducible.\n\n"
        "The stub also captures the inferred time window and PF mapping rules used for this run.\n"
    )

    return out_py
