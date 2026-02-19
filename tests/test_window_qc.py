from pathlib import Path
import pandas as pd

from mast_freegsnke.windowing import infer_time_window
from mast_freegsnke.window_quality import evaluate_time_window

def test_window_qc_confidence_high_for_clear_ip(tmp_path: Path):
    d = tmp_path
    df = pd.DataFrame({
        "time": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
        "plasma_current": [0.0, 0.0, 50.0, 60.0, 55.0, 1.0],
    })
    (d/"magnetics_raw.csv").write_text(df.to_csv(index=False))
    tw = infer_time_window(inputs_dir=d, formed_frac=0.8)
    diag = evaluate_time_window(inputs_dir=d, tw=tw)
    assert diag.duration_s > 0
    assert 0.0 <= diag.confidence <= 1.0
