# Example 09 — Robustness v4.1 (Phase Consistency + Attribution + Plots)

This example assumes you have already produced a baseline run directory:

- `runs/shot_<N>/` created via `mast-freegsnke run ...`
- baseline window inferred and written to `runs/shot_<N>/inputs/window.json`
- resolved contracts written to `runs/shot_<N>/contracts/diagnostic_contracts.resolved.json`
- (optional) contract-driven scoring enabled during the baseline run

## 1) Run multi-window robustness (v4.x)

```bash
mast-freegsnke robustness-run --run runs/shot_<N> --policy maximin
```

This produces (v4.1 adds extra evidence outputs):

```
runs/shot_<N>/robustness_v4/
  window_library.json
  phase_timeline.json
  per_window_summary.csv
  continuity_metrics.csv
  global_robust_choice.json
  robust_summary.md

  # v4.1 additions
  phase_consistency_scorecard.json
  phase_consistency_summary.md
  sensitivity_attribution.json
  dominant_failure_modes.md
  plots/
  plots_manifest.json
```

## 2) Build the robustness reviewer pack

```bash
mast-freegsnke robustness-pack --run runs/shot_<N>
```

Outputs:

```
runs/shot_<N>/robustness_v4/ROBUSTNESS_REVIEWER_PACK/
  (key JSON/CSV/MD files)
  windows/...
  plots/...
```

## Notes on determinism

- Scenario IDs are computed from canonical JSON (sorted keys).
- Window ordering is deterministic (generator + stable sort).
- Phase assignment is deterministic by window midpoint.
- Plots are generated using a fixed non-interactive backend and fixed DPI.
