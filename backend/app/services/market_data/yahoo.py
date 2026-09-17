from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from .base import MarketDataProvider, SymbolInfo
from .registry import STOCK_REGISTRY, NIFTY_SYMBOL

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


class YahooFinanceProvider(MarketDataProvider):
    provider_name = "Yahoo Finance (third-party, not an official NSE feed)"

    def search_symbol(self, query: str) -> list[SymbolInfo]:
        q = (query or "").strip().lower().rstrip(".ns")
        if not q:
            return []
        results: list[SymbolInfo] = []
        for entry in STOCK_REGISTRY:
            hay = " ".join([entry["name"].lower(), entry["symbol"].lower()] + entry["aliases"])
            if q in hay or q.replace(" ", "") in hay.replace(" ", ""):
                results.append(SymbolInfo(symbol=entry["symbol"], name=entry["name"], exchange=entry["exchange"]))

        normalised = q.upper().replace(" ", "")
        if not normalised.endswith(".NS") and normalised:
            normalised += ".NS"
        if normalised and all(r.symbol != normalised for r in results):
            for entry in STOCK_REGISTRY:
                if entry["symbol"] == normalised:
                    results.insert(0, SymbolInfo(symbol=entry["symbol"], name=entry["name"], exchange=entry["exchange"]))
        return results

    def _download(self, symbol: str, start: str, end_inclusive: str) -> pd.DataFrame:

        end_excl = (datetime.strptime(end_inclusive, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        df = yf.download(symbol, start=start, end=end_excl, interval="1d",
                         auto_adjust=False, progress=False, timeout=30)
        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.reset_index()

        first = df.columns[0]
        df = df.rename(columns={first: "Date"})

        rename = {}
        for c in list(df.columns):
            cl = str(c).strip().lower()
            mapping = {"open": "Open", "high": "High", "low": "Low", "close": "Close",
                       "adj close": "Close", "adj_close": "Close", "volume": "Volume", "date": "Date"}
            if cl in mapping:
                rename[c] = mapping[cl]
        df = df.rename(columns=rename)

        df = df.loc[:, ~pd.Index(list(df.columns)).duplicated()]

        df["Date"] = pd.to_datetime(df["Date"], utc=True, errors="coerce").dt.tz_convert(IST).dt.tz_localize(None)
        keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[keep]

    def get_historical_data(self, symbol: str, start: str, end_inclusive: str,
                              pair_id: str | None = None) -> pd.DataFrame:
        try:
            return self._download(symbol, start, end_inclusive)
        except Exception as exc:
            log.exception("yfinance download failed for %s: %s", symbol, exc)
            raise RuntimeError("Market data could not be retrieved. Please try again in a moment.")

    def get_index_data(self, start: str, end_inclusive: str) -> pd.DataFrame:
        return self.get_historical_data(NIFTY_SYMBOL, start, end_inclusive)


def get_provider(name: str = "yahoo") -> MarketDataProvider:

    from .factory import get_provider as factory
    return factory(name)
