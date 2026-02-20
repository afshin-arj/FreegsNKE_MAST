from __future__ import annotations

from pathlib import Path
import shutil
import json

def build_robustness_reviewer_pack(run_dir: Path, out_dir: Path | None = None) -> Path:
    """
    Build a self-contained robustness reviewer pack from an already computed robustness_v4 directory.
    """
    run_dir = run_dir.resolve()
    rob = run_dir / "robustness_v4"
    if not rob.exists():
        raise FileNotFoundError(f"robustness_v4 not found in run_dir: {rob}")

    out = out_dir.resolve() if out_dir is not None else (rob / "ROBUSTNESS_REVIEWER_PACK")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # copy key artifacts
    for name in [
        "window_library.json",
        "phase_timeline.json",
        "per_window_summary.csv",
        "continuity_metrics.csv",
        "global_robust_choice.json",
        "robust_summary.md",
        # v4.1 additions
        "phase_consistency_scorecard.json",
        "phase_consistency_summary.md",
        "sensitivity_attribution.json",
        "dominant_failure_modes.md",
        "plots_manifest.json",
    ]:
        src = rob / name
        if src.exists():
            shutil.copy2(src, out / name)

    # copy per-window essentials
    wsrc = rob / "windows"
    if wsrc.exists():
        shutil.copytree(wsrc, out / "windows", dirs_exist_ok=True)

    # copy plots if present
    psrc = rob / "plots"
    if psrc.exists():
        shutil.copytree(psrc, out / "plots", dirs_exist_ok=True)

    return out
