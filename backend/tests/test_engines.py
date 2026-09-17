import numpy as np
import pandas as pd
from app.services.statistics import describe
from app.services.regression import regress_on_trading_day
from app.services.probability import weekly_direction_probability
from app.services.hypothesis import one_sample_t_test
from app.services.data_cleaning import clean_ohlcv


def test_describe_known_values():
    s = pd.Series([1, 2, 3, 4, 5])
    d = describe(s)
    assert d["n"] == 5
    assert abs(d["mean"] - 3.0) < 1e-9
    assert abs(d["median"] - 3.0) < 1e-9
    assert abs(d["variance_sample"] - 2.5) < 1e-9
    assert abs(d["std_sample"] - np.sqrt(2.5)) < 1e-9
    assert abs(d["cv_percent"] - (np.sqrt(2.5) / 3 * 100)) < 1e-9
    assert d["q1"] == 2.0 and d["q3"] == 4.0 and d["iqr"] == 2.0


def test_regression_known_line():

    y = np.array([5, 8, 11, 14, 17], dtype=float)
    r = regress_on_trading_day(y)
    assert abs(r["slope"] - 3.0) < 1e-9
    assert abs(r["intercept"] - 2.0) < 1e-9
    assert abs(r["r_squared"] - 1.0) < 1e-9


def test_probability_counts():

    p = weekly_direction_probability(np.arange(1, 21, dtype=float), horizon=5)
    assert p["observations"] == 15
    assert p["positive"] == 15 and p["negative"] == 0
    assert abs(p["p_positive"] - 1.0) < 1e-12


def test_hypothesis_decision():
    x = np.array([10, 10, 10, 10, 11], dtype=float)
    h = one_sample_t_test(x, mu0=10.0, alpha=0.05)
    assert h["n"] == 5 and h["df"] == 4
    assert 0 <= h["p_value"] <= 1
    assert h["decision"] in ("Reject H0", "Fail to reject H0")


def test_cleaning_sorts_dedupes():
    raw = pd.DataFrame({
        "Date": ["2025-04-03", "2025-04-01", "2025-04-01"],
        "Open": [1, 1, 1], "High": [2, 2, 2], "Low": [1, 1, 1],
        "Close": [10, 9, 9], "Volume": [100, 100, 100]})
    df = clean_ohlcv(raw)
    assert len(df) == 2
    assert df["Date"].is_monotonic_increasing
    assert df["Date"].is_unique


def test_cleaning_rejects_empty():
    import pytest
    with pytest.raises(ValueError):
        clean_ohlcv(pd.DataFrame())
