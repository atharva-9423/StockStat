from __future__ import annotations

from .base import MarketDataProvider


def get_provider(name: str = "investing") -> MarketDataProvider:
    key = (name or "investing").lower()
    if key == "yahoo":
        from .yahoo import YahooFinanceProvider
        return YahooFinanceProvider()
    if key in ("investing", "investing.com", "investgo"):
        from .investing import InvestingComProvider
        return InvestingComProvider()
    raise ValueError(f"Unknown data provider: {name}")
