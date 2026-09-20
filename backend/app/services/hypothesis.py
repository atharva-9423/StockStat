from __future__ import annotations

import numpy as np
from scipy import stats


def one_sample_t_test(close: list[float] | np.ndarray, mu0: float, alpha: float = 0.05,
                      alternative: str = "two-sided") -> dict:
    x = np.asarray(close, dtype=float)
    x = x[~np.isnan(x)]
    n = int(x.size)
    if n < 2:
        raise ValueError("There aren't enough valid observations to perform this statistical test.")
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError("alternative must be two-sided, greater or less.")
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    se = std / np.sqrt(n)
    t_stat = (mean - mu0) / se if se != 0 else float("nan")
    res = stats.ttest_1samp(x, popmean=mu0, alternative=alternative)
    p = float(res.pvalue)
    df = n - 1
    if alternative == "two-sided":
        crit = float(stats.t.ppf(1 - alpha / 2, df))
        reject = bool(p < alpha)
    elif alternative == "greater":
        crit = float(stats.t.ppf(1 - alpha, df))
        reject = bool(p < alpha)
    else:
        crit = float(stats.t.ppf(alpha, df))
        reject = bool(p < alpha)
    return {
        "n": n, "sample_mean": mean, "sample_std": std, "mu0": float(mu0),
        "alpha": float(alpha), "alternative": alternative,
        "t_statistic": float(t_stat), "p_value": p,
        "critical_value": crit, "df": int(df),
        "reject_null": reject,
        "decision": "Reject H0" if reject else "Fail to reject H0",
    }
