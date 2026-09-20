from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import settings
from .market_data.factory import get_provider
from .market_data.registry import STOCK_REGISTRY, NIFTY_SYMBOL, NIFTY_NAME
from .data_cleaning import clean_ohlcv
from .statistics import describe
from .regression import regress_on_trading_day
from .probability import weekly_direction_probability
from .hypothesis import one_sample_t_test
from . import cache as cache_mod

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")
_STORE: dict[str, dict] = {}


def _resolve_name(symbol: str) -> str:
    for e in STOCK_REGISTRY:
        if e["symbol"] == symbol:
            return e["name"]
    return symbol


def _registry_entry(symbol: str) -> dict | None:
    for e in STOCK_REGISTRY:
        if e["symbol"] == symbol:
            return e
    return None


def run_full_analysis(symbol: str, start: str, end: str, mu0: float | None = None,
                      alpha: float = 0.05, alternative: str = "two-sided",
                      investing_pair_id: str | None = None,
                      stock_name: str | None = None) -> dict:
    provider = get_provider(settings.data_provider)

    ck = cache_mod.cache_key(provider.provider_name, symbol, investing_pair_id or "", start, end)
    ck_n = cache_mod.cache_key(provider.provider_name, NIFTY_SYMBOL, start, end)
    stock_raw = cache_mod.get(ck)
    if stock_raw is None:
        stock_raw = provider.get_historical_data(symbol, start, end, pair_id=investing_pair_id)
        if not stock_raw.empty:
            cache_mod.put(ck, stock_raw)
    nifty_raw = cache_mod.get(ck_n)
    if nifty_raw is None:
        nifty_raw = provider.get_index_data(start, end)
        if not nifty_raw.empty:
            cache_mod.put(ck_n, nifty_raw)

    stock = clean_ohlcv(stock_raw)
    nifty = clean_ohlcv(nifty_raw)

    close = stock["Close"]
    nclose = nifty["Close"]
    stats = describe(close)
    nstats = describe(nclose)
    reg = regress_on_trading_day(close.to_numpy())
    prob = weekly_direction_probability(close.to_numpy())
    h = one_sample_t_test(close.to_numpy(), mu0 if mu0 is not None else stats["mean"],
                           alpha=alpha, alternative=alternative)


    reg_entry = _registry_entry(symbol)
    display_name = reg_entry["name"] if reg_entry else None
    exchange = reg_entry["exchange"] if reg_entry else "Investing.com"
    currency = "INR"
    meta_getter = getattr(provider, "get_instrument_meta", None)
    if reg_entry is None and meta_getter is not None and investing_pair_id:
        try:
            meta = meta_getter(investing_pair_id) or {}
            display_name = meta.get("name") or display_name
            exchange = meta.get("exchange") or exchange
            currency = (meta.get("currency") or currency).upper()
        except Exception:
            log.warning("instrument metadata lookup failed; using fallbacks", exc_info=True)
    if not display_name:
        display_name = (stock_name or "").strip() or symbol


    s_idx = (close / close.iloc[0] * 100).tolist()
    n_idx = (nclose / nclose.iloc[0] * 100).tolist()

    aid = uuid.uuid4().hex[:12]
    bundle = {
        "analysis_id": aid,
        "stock_name": display_name, "symbol": symbol, "exchange": exchange,
        "currency": currency,
        "start": start, "end": end, "price_field": "Close",
        "provider": provider.provider_name,
        "retrieved_at": datetime.now(IST).isoformat(),
        "n": stats["n"], "n_nifty": nstats["n"],
        "last_close": float(close.iloc[-1]),
        "last_date": str(stock["Date"].iloc[-1].date()),
        "statistics": stats, "nifty_statistics": nstats,
        "regression": reg, "probability": prob, "hypothesis": h,
        "hypothesis_params": {"mu0": h["mu0"], "alpha": h["alpha"], "alternative": h["alternative"]},
        "dates": stock["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "close": close.tolist(),
        "nifty_dates": nifty["Date"].dt.strftime("%Y-%m-%d").tolist(),
        "nifty_close": nclose.tolist(),
        "indexed_stock": s_idx, "indexed_nifty": n_idx,
        "records": [
            {"date": d.strftime("%Y-%m-%d"), "open": float(o), "high": float(hh),
             "low": float(ll), "close": float(c), "volume": int(v)}
            for d, o, hh, ll, c, v in zip(stock["Date"], stock["Open"], stock["High"],
                                          stock["Low"], stock["Close"], stock["Volume"])
        ],
        "nifty_records": [
            {"date": d.strftime("%Y-%m-%d"), "open": float(o), "high": float(hh),
             "low": float(ll), "close": float(c), "volume": int(v)}
            for d, o, hh, ll, c, v in zip(nifty["Date"], nifty["Open"], nifty["High"],
                                          nifty["Low"], nifty["Close"], nifty["Volume"])
        ],
    }
    _STORE[aid] = bundle
    return bundle


def get_analysis(aid: str) -> dict | None:
    return _STORE.get(aid)


def rerun_hypothesis(aid: str, mu0: float, alpha: float, alternative: str) -> dict:
    b = _STORE.get(aid)
    if not b:
        raise KeyError("Unknown analysis_id")
    import numpy as np
    h = one_sample_t_test(np.array(b["close"]), mu0, alpha=alpha, alternative=alternative)
    b["hypothesis"] = h
    b["hypothesis_params"] = {"mu0": h["mu0"], "alpha": h["alpha"], "alternative": h["alternative"]}
    return b
