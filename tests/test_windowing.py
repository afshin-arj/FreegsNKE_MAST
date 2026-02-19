from pathlib import Path
import pandas as pd

from mast_freegsnke.windowing import infer_time_window

def test_infer_time_window_from_ip(tmp_path: Path):
    d = tmp_path
    # synthetic Ip: 0 then rises
    df = pd.DataFrame({
        "time": [0.0, 0.1, 0.2, 0.3, 0.4],
        "plasma_current": [0.0, 0.0, 100.0, 120.0, 10.0],
        "other": [1,2,3,4,5],
    })
    p = d/"magnetics_raw.csv"
    df.to_csv(p, index=False)
    tw = infer_time_window(inputs_dir=d, formed_frac=0.8)
    assert tw.t_start == 0.2
    assert tw.t_end == 0.3
