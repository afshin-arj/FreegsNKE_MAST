from __future__ import annotations

from pathlib import Path
import json

from mast_freegsnke.physics_audit.schema import PhysicsAuditConfig
from mast_freegsnke.physics_audit.audit import run_physics_audit


def _write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))


def test_v6_physics_audit_smoke(tmp_path: Path):
    # Create minimal run structure with robustness_v4 artifacts expected by the audit.
    run_dir = tmp_path / "runs" / "shot_99999"
    rob = run_dir / "robustness_v4"
    windows = rob / "windows"

    # phase timeline
    _write_json(rob / "phase_timeline.json", {
        "phases": [{"name": "flat", "start": 0.1, "end": 0.2}]
    })

    # one window
    w0 = windows / "window_000"
    w0.mkdir(parents=True, exist_ok=True)

    # stability scorecard + robust choice
    _write_json(w0 / "stability_scorecard.json", {"relative_degradation": 0.02})
    _write_json(w0 / "robust_choice.json", {"score_total": 0.5, "delta_score_prev": 0.0})

    cfg = PhysicsAuditConfig(physics_green=0.05, physics_yellow=0.15, primary_metric="score_total", zero_timestamp_mode=True)
    sc = run_physics_audit(run_dir, cfg)

    out = rob / "physics_audit"
    assert (out / "physics_consistency_scorecard.json").exists()
    assert (out / "physics_consistency_summary.md").exists()
    assert (out / "per_window_physics.csv").exists()
    assert sc.tier in ["PHYSICS-GREEN", "PHYSICS-YELLOW", "PHYSICS-RED"]
    # With small violations, should be green
    assert sc.tier == "PHYSICS-GREEN"
