"""
Consistency Triangle Reviewer Pack (v7.0.0)
Bundles: robustness_v4 + physics_audit (v6) + model_form (v7)
Hash-locked pack manifest.

© 2026 Afshin Arjhangmehr
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import json
import hashlib
import shutil

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)

def build_consistency_triangle_pack(run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    rob = run_dir / "robustness_v4"
    phys = rob / "physics_audit"
    mf = rob / "model_form"
    if not rob.exists():
        raise FileNotFoundError(f"Missing robustness_v4: {rob}")
    if not phys.exists():
        raise FileNotFoundError(f"Missing physics_audit outputs: {phys} (run physics-audit-run)")
    if not mf.exists():
        raise FileNotFoundError(f"Missing model_form outputs: {mf} (run model-form-run)")

    pack = run_dir / "CONSISTENCY_TRIANGLE_REVIEWER_PACK"
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, str]] = []

    def copy_tree(src: Path, dst: Path, include_names: List[str] | None = None):
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(src)
            if include_names is not None and rel.name not in include_names and not any(str(rel).startswith(n + "/") for n in include_names):
                continue
            outp = dst / rel
            outp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, outp)
            manifest.append({"path": str(outp.relative_to(pack)), "sha256": _sha256_file(outp)})

    copy_tree(rob, pack / "robustness", include_names=None)
    copy_tree(phys, pack / "physics_audit", include_names=None)
    copy_tree(mf, pack / "model_form", include_names=None)

    # deterministic narrative stub
    evidence = []
    evidence.append("# Consistency Triangle Evidence (v7.0.0)\n\n")
    evidence.append("This pack bundles three orthogonal audit axes:\n\n")
    evidence.append("1. Robustness under perturbations (v4/v5)\n")
    evidence.append("2. Physics-closure consistency (v6)\n")
    evidence.append("3. Model-form / holdout forward checks (v7)\n\n")
    evidence.append("Interpretation guidance:\n\n")
    evidence.append("- robust+physics-green but MFE-red => consistently wrong risk\n")
    evidence.append("- robust-red but MFE-green => sensitive but predictive\n")
    evidence.append("- physics-red => closure violation: investigate assumptions/contracts\n")
    (pack / "EVIDENCE.md").write_text("".join(evidence), encoding="utf-8")
    manifest.append({"path": "EVIDENCE.md", "sha256": _sha256_file(pack / "EVIDENCE.md")})

    _write_json(pack / "pack_manifest.json", {"schema_version": "v7.0.0", "files": manifest})
    return pack
