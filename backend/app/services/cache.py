from __future__ import annotations

import hashlib
import time
from pathlib import Path

import pandas as pd

from ..config import settings

_mem: dict[str, tuple[float, pd.DataFrame]] = {}


def _key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def get(key: str) -> pd.DataFrame | None:
    item = _mem.get(key)
    if item and (time.time() - item[0] < settings.cache_ttl_seconds):
        return item[1].copy()

    path = Path(settings.cache_dir) / f"{key}.csv"
    if path.exists() and (time.time() - path.stat().st_mtime < settings.cache_ttl_seconds):
        try:
            df = pd.read_csv(path, parse_dates=["Date"])
            _mem[key] = (time.time(), df)
            return df.copy()
        except Exception:
            return None
    return None


def put(key: str, df: pd.DataFrame) -> None:
    _mem[key] = (time.time(), df.copy())
    try:
        Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
        df.to_csv(Path(settings.cache_dir) / f"{key}.csv", index=False)
    except Exception:
        pass


def cache_key(*parts: str) -> str:
    return _key(*parts)
