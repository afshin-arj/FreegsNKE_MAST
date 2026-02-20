import json
from pathlib import Path

import pandas as pd

from mast_freegsnke.corpus.corpus_build import build_corpus
from mast_freegsnke.corpus.atlas import build_atlas
from mast_freegsnke.corpus.compare import compare_atlases
from mast_freegsnke.corpus.regression_guard import regression_guard

def _write_run(tmp: Path, shot: int, tier: str, rel: float, fam: str, phase_label: str):
    run = tmp / f"runs/shot_{shot}"
    rob = run / "robustness_v4"
    rob.mkdir(parents=True, exist_ok=True)

    # Required files for corpus indexing
    pd.DataFrame([
        {"window_id":"w00","t_start":0.48,"t_end":0.50,"scenario_id":"S0","score_total":10.0,"tier":tier},
    ]).to_csv(rob / "per_window_summary.csv", index=False)

    (rob / "global_robust_choice.json").write_text(json.dumps({"scenario_id":"S0","score_total":10.0}, indent=2, sort_keys=True))
    (rob / "stability_scorecard.json").write_text(json.dumps({"tier":tier,"relative_degradation":rel}, indent=2, sort_keys=True))
    (rob / "phase_consistency_scorecard.json").write_text(json.dumps({"global_label":phase_label}, indent=2, sort_keys=True))
    (rob / "sensitivity_attribution.json").write_text(json.dumps({"dominant_family":fam}, indent=2, sort_keys=True))
    (rob / "plots_manifest.json").write_text(json.dumps({"plots":[]}, indent=2, sort_keys=True))
    return run

def test_v5_corpus_atlas_compare_guard(tmp_path: Path):
    runA1 = _write_run(tmp_path, 1, tier="GREEN", rel=0.02, fam="window", phase_label="PHASE-CONSISTENT")
    runA2 = _write_run(tmp_path, 2, tier="YELLOW", rel=0.10, fam="diagnostic_subset", phase_label="PHASE-DRIFTING")

    corpusA = build_corpus([runA1, runA2], tmp_path / "corpusA")
    atlasA = build_atlas(corpusA)

    # make B worse deterministically
    runB1 = _write_run(tmp_path, 1, tier="YELLOW", rel=0.12, fam="window", phase_label="PHASE-DRIFTING")
    runB2 = _write_run(tmp_path, 2, tier="RED", rel=0.30, fam="contract_scale", phase_label="PHASE-BREAKING")
    corpusB = build_corpus([runB1, runB2], tmp_path / "corpusB")
    atlasB = build_atlas(corpusB)

    comp = compare_atlases(atlasA, atlasB, tmp_path / "compare")
    delta = json.loads((Path(comp) / "delta_scorecards.json").read_text())
    assert delta["n_paired"] == 2

    guard_out = tmp_path / "guard.json"
    res = regression_guard(Path(comp) / "delta_scorecards.json", guard_out, max_red_increase=0, max_median_degradation_increase=0.0)
    assert res["ok"] is False
