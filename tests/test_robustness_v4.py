from mast_freegsnke.robustness.schema import ScenarioDescriptor, WindowDef
from mast_freegsnke.robustness.window_library import generate_window_library

def test_scenario_id_deterministic():
    s1 = ScenarioDescriptor(family="window", window_id="w0", name="baseline", params={"a": 1, "b": 2})
    s2 = ScenarioDescriptor(family="window", window_id="w0", name="baseline", params={"b": 2, "a": 1})
    assert s1.scenario_id() == s2.scenario_id()

def test_window_library_finite():
    wins = generate_window_library(0.5, 0.6, dt_grid=(-0.01, 0.0, 0.01), expand_grid=(0.0, 0.01))
    assert len(wins) == 6
    assert all(w.t_end > w.t_start for w in wins)
