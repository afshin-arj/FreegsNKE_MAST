from __future__ import annotations
from dataclasses import dataclass
import requests

@dataclass
class MastAppClient:
    base_url: str
    timeout_s: float = 15.0

    def _get(self, path: str) -> requests.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        return requests.get(url, timeout=self.timeout_s)

    def shot_exists(self, shot: int) -> bool:
        r = self._get(f"shots/{shot}")
        if r.status_code == 200:
            return True
        r2 = self._get("shots")
        if r2.status_code != 200:
            return False
        try:
            data = r2.json()
        except Exception:
            return False
        if isinstance(data, list):
            for s in data:
                if s == shot:
                    return True
                if isinstance(s, dict) and int(s.get("shot", -1)) == shot:
                    return True
        return False
