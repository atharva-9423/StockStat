from __future__ import annotations

import numpy as np
from scipy import stats


def regress_on_trading_day(close: list[float] | np.ndarray) -> dict:
    y = np.asarray(close, dtype=float)
    n = y.size
    if n < 3:
        raise ValueError("There aren't enough valid observations to fit a regression line (need ≥ 3).")
    x = np.arange(1, n + 1, dtype=float)
    res = stats.linregress(x, y)
    slope, intercept = float(res.slope), float(res.intercept)
    r = float(res.rvalue)
    r2 = float(res.rvalue ** 2)
    yhat = intercept + slope * x

    se = float(np.sqrt(np.sum((y - yhat) ** 2) / (n - 2))) if n > 2 else float("nan")
    return {
        "n": int(n), "slope": slope, "intercept": intercept,
        "equation": f"Y = {intercept:.4f} + {slope:.4f}·X",
        "r": r, "r_squared": r2,
        "p_value_slope": float(res.pvalue), "std_err_slope": float(res.stderr),
        "std_err_estimate": se,
        "x_def": "X = trading-day number (first observation = 1)",
        "y_def": "Y = closing price (INR)",
        "fitted": yhat.tolist(),
    }
