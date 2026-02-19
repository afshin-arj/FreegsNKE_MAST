# Machine configuration: MAST (placeholder)

This directory is intended to hold **machine authority inputs** required to run FreeGSNKE for MAST, in particular:

- Probe geometry (required for synthetic diagnostics)
  - `probe_geometry.json` (preferred) OR
  - `flux_loops.csv` / `pickup_coils.csv` OR
  - a Python module exporting geometry

Run:

```bash
mast-freegsnke geom-template --machine machine_configs/MAST
```

…then replace template values with authoritative metrology.
