
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mast_freegsnke.diagnostic_contracts import load_contracts, validate_contracts
from mast_freegsnke.synthetic_extract import extract_synthetic_by_contracts
from mast_freegsnke.metrics import compare_from_contracts
from mast_freegsnke.coil_map import load_coil_map, validate_coil_map


def test_contracts_and_metrics_roundtrip(tmp_path: Path) -> None:
    # Create synthetic experimental and synthetic CSVs
    exp_csv = tmp_path / "exp.csv"
    syn_csv = tmp_path / "syn.csv"

    t = np.linspace(0.0, 1.0, 11)
    y = np.sin(2*np.pi*t)
    pd.DataFrame({"time": t, "sig": y}).to_csv(exp_csv, index=False)
    # synthetic slightly off
    pd.DataFrame({"time": t, "sig": y + 0.1}).to_csv(syn_csv, index=False)

    contracts_json = tmp_path / "contracts.json"
    contracts_json.write_text(json.dumps({
        "version": "1.0",
        "diagnostics": [
            {
                "name": "sig1",
                "dtype": "flux_loop",
                "units": "arb",
                "exp": {"csv": str(exp_csv), "time_col": "time", "value_col": "sig"},
                "syn": {"csv": str(syn_csv), "time_col": "time", "value_col": "sig"},
            }
        ]
    }))

    contracts = load_contracts(contracts_json)
    rep = validate_contracts(contracts, require_files=True)
    assert rep["ok"]

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    syn_res = extract_synthetic_by_contracts(run_dir, contracts)
    assert syn_res.ok
    assert (run_dir / "synthetic" / "synthetic_flux_loop.csv").exists()

    met = compare_from_contracts(run_dir, contracts)
    assert met["n_scored"] == 1
    assert (run_dir / "metrics" / "reconstruction_metrics.json").exists()


def test_coil_map_validate(tmp_path: Path) -> None:
    cm_path = tmp_path / "coil_map.json"
    cm_path.write_text(json.dumps({
        "version": "1.0",
        "mapping": {"A": {"coil": "P2_inner", "scale": 1.0, "sign": 1}}
    }))
    cm = load_coil_map(cm_path)
    rep = validate_coil_map(cm)
    assert rep["ok"]
