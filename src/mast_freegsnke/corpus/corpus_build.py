from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence
import json

from .schema import CorpusEntry, corpus_id
from ..util import write_json, ensure_dir

def build_corpus(
    run_dirs: Sequence[Path],
    out_dir: Path,
    robustness_subdir: str = "robustness_v4",
    extra_metadata: Optional[Dict[str, object]] = None,
) -> Path:
    """Build a deterministic corpus index from completed run directories.

    Parameters
    ----------
    run_dirs:
        Paths like runs/shot_30201
    out_dir:
        Output directory for corpus artifacts.
    robustness_subdir:
        Directory name inside each run directory that contains robustness artifacts.
    extra_metadata:
        Optional user-provided metadata included verbatim (must be JSON-serializable).

    Outputs
    -------
    out_dir/corpus_manifest.json
    out_dir/shot_index.csv
    """
    out_dir = ensure_dir(out_dir.resolve())
    entries: List[CorpusEntry] = [CorpusEntry.from_run_dir(Path(p), robustness_subdir=robustness_subdir) for p in run_dirs]

    cid = corpus_id(entries)
    manifest = {
        "schema_version": "v5.0.0",
        "corpus_id": cid,
        "robustness_subdir": robustness_subdir,
        "n": len(entries),
        "entries": [
            {
                "run_dir": e.run_dir,
                "shot": e.shot,
                "robustness_dir": e.robustness_dir,
                "hashes": e.hashes,
            }
            for e in entries
        ],
    }
    if extra_metadata:
        manifest["metadata"] = extra_metadata

    write_json(out_dir / "corpus_manifest.json", manifest)

    # Deterministic CSV index for human browsing
    import pandas as pd
    rows = []
    for e in sorted(entries, key=lambda x: (x.shot if x.shot is not None else 10**12, x.run_dir)):
        row = {"shot": e.shot, "run_dir": e.run_dir}
        for k, v in sorted(e.hashes.items()):
            row[f"sha256_{k}"] = v
        rows.append(row)
    pd.DataFrame(rows).to_csv(out_dir / "shot_index.csv", index=False)
    return out_dir
