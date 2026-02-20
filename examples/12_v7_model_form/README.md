# Example 12 — v7.0.0 Model-Form / Forward Checks

Prerequisite:
- Completed `robustness-run` output: `runs/shot_<N>/robustness_v4/`
- Completed `physics-audit-run` output (v6): `runs/shot_<N>/robustness_v4/physics_audit/`

## 1) Run model-form audit (CV splits + forward checks + tier)

```bash
mast-freegsnke model-form-run --run runs/shot_<N>
```

Outputs:
- `runs/shot_<N>/robustness_v4/model_form/cv_splits.json`
- `runs/shot_<N>/robustness_v4/model_form/forward_checks.csv`
- `runs/shot_<N>/robustness_v4/model_form/model_form_scorecard.json`
- `runs/shot_<N>/robustness_v4/model_form/model_form_summary.md`

## 2) Build Consistency Triangle reviewer pack

```bash
mast-freegsnke consistency-pack --run runs/shot_<N>
```

Creates:
- `runs/shot_<N>/CONSISTENCY_TRIANGLE_REVIEWER_PACK/`
