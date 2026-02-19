# Example 07 — Reviewer Pack Export (v2.0)

## Goal
Export a **self-contained reviewer bundle** from an already completed run folder.

## Prerequisites
You must already have a run directory, e.g.:

- `runs/shot_30201/`

It should contain (at minimum): `manifest.json` and `provenance/manifest_v2.json`.

## Command

```bash
mast-freegsnke reviewer-pack --run runs/shot_30201
```

## Output

Creates:

- `runs/shot_30201/REVIEWER_PACK/`

This folder includes key artifacts for inspection without running the pipeline again:
manifests, provenance hashes, machine authority snapshot, contracts, residual tables, plots, and execution logs (if present).
