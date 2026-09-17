from __future__ import annotations

import numpy as np
import pandas as pd


def describe(series: pd.Series) -> dict:
    x = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
    n = int(x.size)
    if n == 0:
        raise ValueError("There aren't enough valid observations to perform this statistical test.")
    mean = float(np.mean(x))
    median = float(np.median(x))

    vals, counts = np.unique(x, return_counts=True)
    mode = float(vals[int(np.argmax(counts))])
    mode_count = int(counts.max())
    vmin, vmax = float(np.min(x)), float(np.max(x))
    rng = vmax - vmin
    var_sample = float(np.var(x, ddof=1)) if n > 1 else 0.0
    std_sample = float(np.std(x, ddof=1)) if n > 1 else 0.0
    q1, q2, q3 = (float(v) for v in np.percentile(x, [25, 50, 75]))
    iqr = q3 - q1
    cv = (std_sample / mean * 100.0) if mean != 0 else float("nan")
    return {
        "n": n, "mean": mean, "median": median, "mode": mode, "mode_count": mode_count,
        "min": vmin, "max": vmax, "range": float(rng),
        "variance_sample": var_sample, "std_sample": std_sample,
        "variance_population": float(np.var(x, ddof=0)),
        "std_population": float(np.std(x, ddof=0)),
        "q1": q1, "q2": q2, "q3": q3, "iqr": float(iqr),
        "cv_percent": float(cv),
        "method": "sample statistics (ddof=1) — academic sample convention",
    }
