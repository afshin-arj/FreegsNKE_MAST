from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import hashlib

def sha256_file(path: Path, chunk_bytes: int = 1024 * 1024) -> str:
    """Compute SHA256 of a file deterministically."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_bytes)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def run_cmd(cmd: List[str]) -> Tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

def looks_like_exists_s5cmd_ls(output: str) -> bool:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return False
    if all(ln.upper().startswith("ERROR") for ln in lines):
        return False
    return True
