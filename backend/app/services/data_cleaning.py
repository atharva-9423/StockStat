from __future__ import annotations

import pandas as pd

REQUIRED = ["Date", "Open", "High", "Low", "Close", "Volume"]


def clean_ohlcv(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        raise ValueError("No historical data was available for this stock during the selected period.")
    df = raw.copy()

    df.columns = [str(c).strip() for c in df.columns]
    lower = {c.lower(): c for c in df.columns}
    for req in REQUIRED:
        if req not in df.columns and req.lower() in lower:
            df = df.rename(columns={lower[req.lower()]: req})
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Market data is missing required columns: {', '.join(missing)}.")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Close"])
    df["Volume"] = df["Volume"].fillna(0)

    df = df.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
    if df.empty:
        raise ValueError("No valid trading observations remain after data cleaning.")
    if (df["Close"] <= 0).any():
        raise ValueError("Market data contains non-positive closing prices; cannot analyse.")
    return df[REQUIRED]
