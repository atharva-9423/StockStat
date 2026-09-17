from __future__ import annotations

import logging
from datetime import datetime
from functools import lru_cache

import pandas as pd

from .base import MarketDataProvider, SymbolInfo
from .registry import STOCK_REGISTRY, NIFTY_INVESTING_PAIR_ID

log = logging.getLogger(__name__)


def _to_investing_date(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d%m%Y")


class InvestingComProvider(MarketDataProvider):
    provider_name = "Investing.com (third-party, not an official NSE feed)"


    def search_symbol(self, query: str) -> list[SymbolInfo]:
        q = (query or "").strip().lower().rstrip(".ns")
        if not q:
            return []
        results: list[SymbolInfo] = []
        for entry in STOCK_REGISTRY:
            hay = " ".join([entry["name"].lower(), entry["symbol"].lower()] + entry["aliases"])
            if q in hay or q.replace(" ", "") in hay.replace(" ", ""):
                results.append(SymbolInfo(symbol=entry["symbol"], name=entry["name"],
                                          exchange=entry["exchange"],
                                          investing_pair_id=str(entry.get("investing_pair_id") or "")))
        normalised = q.upper().replace(" ", "")
        if not normalised.endswith(".NS") and normalised:
            normalised += ".NS"
        if normalised and all(r.symbol != normalised for r in results):
            for entry in STOCK_REGISTRY:
                if entry["symbol"] == normalised:
                    results.insert(0, SymbolInfo(symbol=entry["symbol"], name=entry["name"],
                                                exchange=entry["exchange"],
                                                investing_pair_id=str(entry.get("investing_pair_id") or "")))

        known_pairs = {r.investing_pair_id for r in results if r.investing_pair_id}
        for hit in self._search_live_all(query):
            if hit.investing_pair_id and hit.investing_pair_id in known_pairs:
                continue
            if hit.investing_pair_id:
                known_pairs.add(hit.investing_pair_id)
            results.append(hit)
        return results[:15]

    @staticmethod
    def _search_live_all(query: str, limit: int = 12) -> list[SymbolInfo]:
        from investgo import get_pair_id

        q = (query or "").strip()
        if len(q) < 2:
            return []
        try:
            df = get_pair_id(q, display_mode="all")
        except Exception as exc:
            log.warning("investing.com live search failed for %r: %s", q, exc)
            return []
        if df is None or getattr(df, "empty", True):
            return []
        rows = []
        ql = q.lower()
        for _, row in df.iterrows():
            try:
                ticker = str(row.get("Ticker", "")).strip()
                desc = str(row.get("Description", "")).strip()
                exch = str(row.get("Exchange", "")).strip()
                pair = str(row.get("pair_id", "")).strip()
            except Exception:
                continue
            if not ticker or not pair or not desc:
                continue
            exact = int(ticker.lower() == ql)
            equity = int("equity" in exch.lower())
            rows.append((exact, equity, SymbolInfo(symbol=ticker, name=desc,
                                                  exchange=exch or "Investing.com",
                                                  investing_pair_id=pair)))
        rows.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return [r[2] for r in rows[:limit]]


    @staticmethod
    def get_instrument_meta(pair_id: str) -> dict:
        from investgo import get_info

        try:
            info = get_info(str(pair_id))
            row = info.iloc[0]
            meta = {"name": str(row.get("name", "") or ""),
                    "exchange": str(row.get("exchange", "") or ""),
                    "currency": str(row.get("currency", "") or "INR").upper()}
            return meta
        except Exception as exc:
            log.warning("investing.com info lookup failed for pair %s: %s", pair_id, exc)
            return {}


    def _pair_id_for_symbol(self, symbol: str) -> str:
        for entry in STOCK_REGISTRY:
            if entry["symbol"] == symbol and entry.get("investing_pair_id"):
                return str(entry["investing_pair_id"])

        return self._search_pair_id_live(symbol)

    @staticmethod
    @lru_cache(maxsize=64)
    def _search_pair_id_live(symbol: str) -> str:
        from investgo import get_pair_id

        base = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
        if not base:
            raise ValueError(f"Unknown symbol for Investing.com: {symbol!r}")
        try:
            df = get_pair_id(base, display_mode="all")
        except Exception as exc:
            raise ValueError(f"No Investing.com listing found for {symbol}.") from exc
        if df is None or getattr(df, "empty", True):
            raise ValueError(f"No Investing.com listing found for {symbol}.")

        for _, row in df.iterrows():
            exch = str(row.get("Exchange", "")).upper()
            desc = str(row.get("Description", ""))
            if "NSE" in exch:
                return str(row["pair_id"])
        for _, row in df.iterrows():
            if "NSE" in str(row.get("Description", "")).upper():
                return str(row["pair_id"])
        return str(df.iloc[0]["pair_id"])


    def _download(self, pair_id: str, start: str, end_inclusive: str) -> pd.DataFrame:
        from investgo import get_historical_prices

        raw = get_historical_prices(str(pair_id), _to_investing_date(start), _to_investing_date(end_inclusive))
        if raw is None or raw.empty:
            return pd.DataFrame()
        df = raw.copy()
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df.sort_index()
        rename = {"price": "Close", "open": "Open", "high": "High", "low": "Low", "vol": "Volume"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        df["Date"] = df.index

        lo, hi = pd.Timestamp(start), pd.Timestamp(end_inclusive) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        df = df[(df["Date"] >= lo) & (df["Date"] <= hi)]
        df["Date"] = df["Date"].dt.tz_localize(None) if df["Date"].dt.tz is not None else df["Date"]
        keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        out = df[keep].reset_index(drop=True)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        return out

    def get_historical_data(self, symbol: str, start: str, end_inclusive: str,
                              pair_id: str | None = None) -> pd.DataFrame:
        try:
            pid = (pair_id or "").strip() or self._pair_id_for_symbol(symbol)
            return self._download(pid, start, end_inclusive)
        except ValueError:
            raise
        except Exception as exc:
            log.exception("investing.com download failed for %s: %s", symbol, exc)
            raise RuntimeError("Market data could not be retrieved. Please try again in a moment.")

    def get_index_data(self, start: str, end_inclusive: str) -> pd.DataFrame:
        try:
            return self._download(NIFTY_INVESTING_PAIR_ID, start, end_inclusive)
        except Exception as exc:
            log.exception("investing.com index download failed: %s", exc)
            raise RuntimeError("Market data could not be retrieved. Please try again in a moment.")
