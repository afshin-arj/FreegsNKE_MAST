# MAST → FreeGSNKE Pipeline (v0.3.1)

Shot → MastApp REST check → S3 Zarr auto-discovery → bulk download via s5cmd → (optional) extract CSV → generate FreeGSNKE scripts.

Author: © 2026 Afshin Arjhangmehr

## New in v0.4.0
- `mast-freegsnke check --shot <N> --config <cfg>` validates required Level-2 group availability before downloading.

## New in v0.5.0
- Time-window inference written to runs/shot_<N>/inputs/window.json
- Shot-specific machine stub: runs/shot_<N>/machine_stub_freegsnke.py (+ .json)
- `mast-freegsnke window` command to recompute window after a run.

## New in v0.6.0
- Window QC diagnostics: runs/shot_<N>/inputs/window_diagnostics.json + WINDOW_QC_REPORT.txt
- `mast-freegsnke windowqc` command to recompute QC after a run.
- Inverse template now exposes T_START/T_END variables loaded from inputs/window.json.


### Probe geometry (required for synthetic diagnostics)

FAIR-MAST provides magnetic signals but not full probe metrology (orientation vectors, turns, effective area/couplings).
To run FreeGSNKE synthetic diagnostics you must supply probe geometry in your machine directory.
Use `mast-freegsnke geom-template --machine <dir>` to generate placeholders, then fill with authoritative values.
Set `allow_missing_geometry` to `true` only if you want the pipeline to complete without emitting `magnetic_probes.*`.


## v1.1.0: Contract-driven diagnostics
This release adds deterministic diagnostic contracts, synthetic extraction normalization, and coil-map authority validation.
