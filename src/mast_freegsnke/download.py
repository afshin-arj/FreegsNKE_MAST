from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
import shutil
import subprocess
import json

from .util import run_cmd, looks_like_exists_s5cmd_ls

@dataclass
class BulkDownloader:
    s5cmd_path: str
    level2_s3_prefix: str
    layout_patterns: List[str]

    def _check_s5cmd(self) -> None:
        if shutil.which(self.s5cmd_path) is None:
            raise RuntimeError(f"s5cmd not found on PATH: '{self.s5cmd_path}'. Install s5cmd first.")

    def _render_candidates(self, shot: int, group: str) -> List[str]:
        base = self.level2_s3_prefix.rstrip("/")
        return [pat.format(prefix=base, group=group, shot=shot) for pat in self.layout_patterns]

    def discover_group_path(self, shot: int, group: str) -> str:
        self._check_s5cmd()
        if not self.level2_s3_prefix or "CHANGE_ME" in self.level2_s3_prefix:
            raise RuntimeError("Config 'level2_s3_prefix' is not set. Edit configs/config.json.")
        tried = []
        for cand in self._render_candidates(shot, group):
            probe = cand.rstrip("/") + "/"
            rc, out = run_cmd([self.s5cmd_path, "ls", probe])
            tried.append({"candidate": probe, "rc": rc})
            if rc == 0 and looks_like_exists_s5cmd_ls(out):
                return cand
        msg = f"Could not discover S3 path for group='{group}' shot={shot}. Tried:\n"
        for t in tried:
            msg += f"  - {t['candidate']} (rc={t['rc']})\n"
        raise FileNotFoundError(msg)

    def download_groups(self, shot: int, groups: List[str], cache_dir: Path) -> Path:
        self._check_s5cmd()
        shot_dir = cache_dir / f"shot_{shot}"
        shot_dir.mkdir(parents=True, exist_ok=True)

        resolved: Dict[str, str] = {}
        for g in groups:
            src = self.discover_group_path(shot, g)
            resolved[g] = src
            dst = shot_dir / f"{g}.zarr"
            cmd = [self.s5cmd_path, "sync", src, str(dst)]
            subprocess.run(cmd, check=True)

        (shot_dir / "resolved_s3_paths.json").write_text(json.dumps(resolved, indent=2) + "\n")
        return shot_dir
