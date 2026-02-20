from __future__ import annotations

from pathlib import Path
import json

from mast_freegsnke.model_form.schema import ModelFormConfig
from mast_freegsnke.model_form.mfe import run_model_form_audit
from mast_freegsnke.model_form.pack import build_consistency_triangle_pack


def _write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True))


def test_v7_model_form_smoke_and_pack(tmp_path: Path):
    run_dir = tmp_path / "runs" / "shot_777"
    rob = run_dir / "robustness_v4"
    windows = rob / "windows" / "window_000"
    windows.mkdir(parents=True, exist_ok=True)

    # minimal robustness + scenarios
    _write_json(rob / "phase_timeline.json", {"phases": [{"name":"flat","start":0.1,"end":0.2}]})
    _write_json(windows / "robust_choice.json", {"score_total": 1.0, "delta_score_prev": 0.0})
    _write_json(windows / "stability_scorecard.json", {"relative_degradation": 0.01})
    # scenario output
    scen = windows / "scenarios" / "diag_LOO_X"
    scen.mkdir(parents=True, exist_ok=True)
    _write_json(scen / "metrics.json", {"score_total": 1.05})

    # minimal physics audit output for pack requirement
    phys = rob / "physics_audit"
    _write_json(phys / "physics_consistency_scorecard.json", {"tier":"PHYSICS-GREEN","max_violation":0.01,"primary_metric":"score_total","config_hash":"x","per_test":[],"residual_budget":{"buckets":{},"total":0.0,"sanity_ok":True,"notes":""}})
    (phys / "physics_consistency_summary.md").write_text("ok")
    (phys / "per_window_physics.csv").write_text("window_id,max_test_violation\nwindow_000,0.0\n")

    # run model-form
    cfg = ModelFormConfig(mfe_green=0.1, mfe_yellow=0.2, primary_metric="score_total", max_splits=4, zero_timestamp_mode=True)
    sc = run_model_form_audit(run_dir, cfg)
    assert (rob / "model_form" / "model_form_scorecard.json").exists()
    assert sc.tier in ["MFE-GREEN","MFE-YELLOW","MFE-RED"]

    # pack
    pack = build_consistency_triangle_pack(run_dir)
    assert (pack / "pack_manifest.json").exists()
    assert (pack / "EVIDENCE.md").exists()
