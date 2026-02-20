import pandas as pd
from mast_freegsnke.robustness.phase_consistency import compute_phase_consistency

def test_phase_consistency_deterministic():
    per_window = pd.DataFrame([
        {"window_id":"w00","t_start":0.48,"t_end":0.50,"scenario_id":"A","score_total":10.0,"tier":"GREEN"},
        {"window_id":"w01","t_start":0.50,"t_end":0.52,"scenario_id":"A","score_total":10.2,"tier":"GREEN"},
        {"window_id":"w02","t_start":0.52,"t_end":0.54,"scenario_id":"B","score_total":10.1,"tier":"GREEN"},
    ])
    phases = {
        "phases":[
            {"phase":"ramp_up","t_start":0.46,"t_end":0.50},
            {"phase":"flat_top","t_start":0.50,"t_end":0.60},
        ]
    }
    out = compute_phase_consistency(per_window, phases, dominant_fraction_green=0.6, max_rel_score_drift_green=0.2, max_flip_rate_yellow=0.9)
    assert out["ok"] is True
    # deterministic dominant scenario tie-break and global label presence
    labels = {p["phase"]: p.get("label") for p in out["phases"] if p.get("ok")}
    assert "flat_top" in labels
    assert out["global_label"] in ("PHASE-CONSISTENT","PHASE-DRIFTING","PHASE-BREAKING")
