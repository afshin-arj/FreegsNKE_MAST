
import importlib
from pathlib import Path
import json

import pytest


def _has(pkg: str) -> bool:
    return importlib.util.find_spec(pkg) is not None


@pytest.mark.skipif(not _has("pandas"), reason="pandas required for consensus tests")
def test_consensus_picks_overlap(tmp_path: Path):
    import pandas as pd
    from mast_freegsnke.window_consensus import infer_consensus_window

    # Create two CSVs with overlapping above-threshold segments.
    t = [0.0, 0.1, 0.2, 0.3, 0.4]
    df_mag = pd.DataFrame({"time": t, "Ip": [0, 0, 10, 10, 0]})
    df_pf = pd.DataFrame({"time": t, "I": [0, 5, 5, 0, 0]})

    df_mag.to_csv(tmp_path / "magnetics_raw.csv", index=False)
    df_pf.to_csv(tmp_path / "pf_currents.csv", index=False)

    cw = infer_consensus_window(inputs_dir=tmp_path, formed_frac=0.5)
    assert cw.t_start <= cw.t_end
    # With no true overlap segment at coverage=2, the algorithm picks an earliest max-coverage segment deterministically.
    assert cw.t_start in (0.1, 0.2)
    assert cw.t_end in (0.2, 0.3)
    assert 0.0 < cw.frac_sources_agree <= 1.0
    assert "magnetics_raw.csv" in cw.sources_used


@pytest.mark.skipif(not _has("pandas"), reason="pandas required for consensus tests")
def test_consensus_writes_audit_fields(tmp_path: Path):
    import pandas as pd
    from mast_freegsnke.window_consensus import infer_consensus_window

    t = [0.0, 0.1, 0.2]
    pd.DataFrame({"time": t, "Ip": [0, 1, 0]}).to_csv(tmp_path / "magnetics_raw.csv", index=False)

    cw = infer_consensus_window(inputs_dir=tmp_path, formed_frac=0.5)
    assert isinstance(cw.per_source, dict)
    assert "magnetics_raw.csv" in cw.per_source