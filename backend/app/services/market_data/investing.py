from __future__ import annotations

"""Investing.com provider.

The old implementation used the third-party ``investgo`` scraper, whose
Investing.com endpoints now return HTTP 403 for every request, which made
every analysis fail with "No historical data was available...".

To keep the app working with zero setup (no API keys) on every PC, this
provider now serves the same real market data through the direct Yahoo
chart/search APIs (see ``yahoo.py``). The class name, ``provider_name`` and
the ``investing_pair_id`` field are kept so existing ``.env`` files
(``DATA_PROVIDER=investing``), saved searches and the frontend keep working
unchanged.
"""

from functools import lru_cache

import pandas as pd

from .base import MarketDataProvider, SymbolInfo
from .registry import STOCK_REGISTRY
from .yahoo import YahooFinanceProvider, _live_search

_YAHOO = YahooFinanceProvider()


class InvestingComProvider(MarketDataProvider):
    provider_name = "Yahoo Finance (third-party, not an official NSE feed)"

    def search_symbol(self, query: str) -> list[SymbolInfo]:
        q = (query or "").strip()
        if not q:
            return []
        ql = q.lower()
        results: list[SymbolInfo] = []
        for entry in STOCK_REGISTRY:
            hay = " ".join([entry["name"].lower(), entry["symbol"].lower()] + entry["aliases"])
            if ql in hay or ql.replace(" ", "") in hay.replace(" ", ""):
                results.append(SymbolInfo(symbol=entry["symbol"], name=entry["name"],
                                          exchange=entry["exchange"],
                                          investing_pair_id=str(entry.get("investing_pair_id") or "")))
        seen = {r.symbol.upper() for r in results}
        try:
            for hit in _live_search(q):
                if hit.symbol.upper() in seen:
                    continue
                seen.add(hit.symbol.upper())
                # Attach a known pair id when the live hit matches the registry.
                pid = ""
                for entry in STOCK_REGISTRY:
                    if entry["symbol"].upper() == hit.symbol.upper():
                        pid = str(entry.get("investing_pair_id") or "")
                        break
                results.append(SymbolInfo(symbol=hit.symbol, name=hit.name,
                                          exchange=hit.exchange, investing_pair_id=pid))
        except Exception:
            pass
        results.sort(key=lambda s: (not s.symbol.upper().endswith(".NS"), s.symbol))
        return results[:15]

    @staticmethod
    def get_instrument_meta(pair_id: str) -> dict:  # kept for backwards compat
        return {}

    def _pair_id_for_symbol(self, symbol: str) -> str:
        for entry in STOCK_REGISTRY:
            if entry["symbol"] == symbol and entry.get("investing_pair_id"):
                return str(entry["investing_pair_id"])
        return ""

    @staticmethod
    @lru_cache(maxsize=64)
    def _search_pair_id_live(symbol: str) -> str:
        return ""

    def _download(self, pair_id: str, start: str, end_inclusive: str) -> pd.DataFrame:  # pragma: no cover
        raise NotImplementedError

    def get_historical_data(self, symbol: str, start: str, end_inclusive: str,
                            pair_id: str | None = None) -> pd.DataFrame:
        # pair_id is accepted for compatibility but the download is by symbol.
        return _YAHOO.get_historical_data(symbol, start, end_inclusive)

    def get_index_data(self, start: str, end_inclusive: str) -> pd.DataFrame:
        return _YAHOO.get_index_data(start, end_inclusive)
