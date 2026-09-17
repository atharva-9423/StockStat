from __future__ import annotations

import numpy as np


def weekly_direction_probability(close: list[float] | np.ndarray, horizon: int = 5) -> dict:
    p = np.asarray(close, dtype=float)
    n = p.size
    if n <= horizon:
        raise ValueError("There aren't enough valid observations to estimate weekly probabilities.")
    base = p[:-horizon]
    fwd = p[horizon:]
    rets = (fwd - base) / base
    valid = rets[~np.isnan(rets)]
    m = int(valid.size)
    pos = int(np.sum(valid > 0))
    neg = int(np.sum(valid < 0))
    flat = int(np.sum(valid == 0))
    return {
        "horizon_trading_days": horizon,
        "observations": m,
        "positive": pos, "negative": neg, "flat": flat,
        "p_positive": float(pos / m) if m else float("nan"),
        "p_negative": float(neg / m) if m else float("nan"),
        "p_flat": float(flat / m) if m else float("nan"),
        "mean_weekly_return": float(np.mean(valid)) if m else float("nan"),
        "method": "P(increase) = (# positive 5-trading-day returns) / (# valid 5-trading-day observations). Historical estimate only — not a prediction.",
    }
