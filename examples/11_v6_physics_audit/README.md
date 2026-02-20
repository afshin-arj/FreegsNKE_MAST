# Example 11 — v6.0.0 Physics Audit

This example assumes you already have a completed run directory that includes:

- `runs/shot_<N>/robustness_v4/` (from `mast-freegsnke robustness-run`)

## 1) Run physics audit (closure tests + residual budget ledger)

```bash
mast-freegsnke physics-audit-run --run runs/shot_<N> --plots
```

Outputs:
- `runs/shot_<N>/robustness_v4/physics_audit/physics_consistency_scorecard.json`
- `runs/shot_<N>/robustness_v4/physics_audit/per_window_physics.csv`
- `runs/shot_<N>/robustness_v4/physics_audit/plots/` + `plots_manifest.json`

## 2) Build physics audit reviewer pack

```bash
mast-freegsnke physics-audit-pack --run runs/shot_<N>
```

Creates:
- `runs/shot_<N>/PHYSICS_AUDIT_REVIEWER_PACK/`

## 3) Corpus-level closure atlas

```bash
mast-freegsnke closure-atlas-build --corpus corpora/<your_corpus>
```

Creates:
- `<corpus>/atlas/closure_atlas/closure_atlas_metrics.csv`
- `<corpus>/atlas/closure_atlas/closure_atlas_summary.json`
