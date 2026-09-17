from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd


@dataclass
class SymbolInfo:
    symbol: str
    name: str
    exchange: str
    currency: str = "INR"
    investing_pair_id: str | None = None


class MarketDataProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def search_symbol(self, query: str) -> list[SymbolInfo]:
        ...

    @abstractmethod
    def get_historical_data(self, symbol: str, start: str, end_inclusive: str,
                            pair_id: str | None = None) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_index_data(self, start: str, end_inclusive: str) -> pd.DataFrame:
        ...
