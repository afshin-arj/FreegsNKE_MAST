# Example: v5 Cross-shot Atlas + Comparator

This example assumes you have already produced per-shot runs and executed:

- `mast-freegsnke robustness-run --run runs/shot_<N>`
- `mast-freegsnke robustness-pack --run runs/shot_<N>` (optional)

## 1) Build a corpus index

```bash
mast-freegsnke corpus-build --runs runs/shot_30201 runs/shot_30202 --out corpora/demo_corpus
```

Outputs:

- `corpora/demo_corpus/corpus_manifest.json`
- `corpora/demo_corpus/shot_index.csv`

## 2) Build an atlas

```bash
mast-freegsnke atlas-build --corpus corpora/demo_corpus
```

Outputs:

- `corpora/demo_corpus/atlas/atlas_metrics.csv`
- `corpora/demo_corpus/atlas/atlas_summary.json`
- `corpora/demo_corpus/atlas/plots/`

## 3) Compare two atlases (A/B)

```bash
mast-freegsnke compare-run --A corpora/corpus_A/atlas --B corpora/corpus_B/atlas --out compare/A_vs_B
```

Outputs:

- `compare/A_vs_B/paired_metrics.csv`
- `compare/A_vs_B/delta_scorecards.json`
- `compare/A_vs_B/delta_summary.md`

## 4) Regression guard

```bash
mast-freegsnke regression-guard --delta compare/A_vs_B/delta_scorecards.json --out compare/A_vs_B/regression_guard.json \
  --max-red-increase 0 --max-median-degradation-increase 0.0
```

A non-zero exit code indicates a guarded regression.
