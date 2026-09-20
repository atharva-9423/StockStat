from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from .base import MarketDataProvider, SymbolInfo
from .registry import STOCK_REGISTRY, NIFTY_SYMBOL

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
_CHART_HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
_SEARCH_HOSTS = ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]


def _http_get_json(url: str, timeout: int = 20, tries: int = 3) -> dict:
    last: Exception | None = None
    for attempt in range(max(1, tries)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001 - retry then raise
            last = exc
            log.warning("HTTP GET failed (attempt %d) %s: %s", attempt + 1, url[:120], exc)
            if attempt + 1 < tries:
                time.sleep(0.6 * (attempt + 1))
    raise RuntimeError("Market data could not be retrieved. Please check your internet and try again in a moment.") from last


def _chart(symbol: str, start: str, end_inclusive: str) -> pd.DataFrame:
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    # Yahoo period2 is exclusive; add one day and a small buffer so the end date is included.
    end_excl = datetime.strptime(end_inclusive, "%Y-%m-%d") + timedelta(days=2)
    p1, p2 = int(start_dt.timestamp()), int(end_excl.timestamp())
    last_err: Exception | None = None
    for host in _CHART_HOSTS:
        url = f"https://{host}/v8/finance/chart/{urllib.parse.quote(symbol)}?period1={p1}&period2={p2}&interval=1d&events=div%7Csplit"
        try:
            payload = _http_get_json(url, timeout=20, tries=3)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
        try:
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                err = (payload.get("chart") or {}).get("error") or {}
                raise ValueError(err.get("description") or f"No data for {symbol}.")
            r0 = result[0]
            stamps = r0.get("timestamp") or []
            quote = (r0.get("indicators") or {}).get("quote") or [{}]
            q0 = quote[0] if quote else {}
            adj = (r0.get("indicators") or {}).get("adjclose") or [{}]
            a0 = adj[0].get("adjclose") if adj and isinstance(adj[0], dict) else None
            rows = []
            for i, ts in enumerate(stamps):
                try:
                    dt = datetime.fromtimestamp(ts, tz=IST).replace(tzinfo=None)
                except Exception:
                    continue
                def _v(key: str):
                    try:
                        v = (q0.get(key) or [])[i]
                        return float(v) if v is not None else None
                    except Exception:
                        return None
                close = _v("close")
                if close is None and a0:
                    try:
                        close = float(a0[i]) if a0[i] is not None else None
                    except Exception:
                        close = None
                rows.append({
                    "Date": dt,
                    "Open": _v("open"), "High": _v("high"),
                    "Low": _v("low"), "Close": close,
                    "Volume": _v("volume") or 0,
                })
            df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
            if df.empty:
                continue
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])
            lo, hi = pd.Timestamp(start), pd.Timestamp(end_inclusive) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            df = df[(df["Date"] >= lo) & (df["Date"] <= hi)]
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=["Close"]).sort_values("Date").reset_index(drop=True)
            if not df.empty:
                return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        except ValueError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            log.warning("Yahoo chart parse failed for %s on %s: %s", symbol, host, exc)
            continue
    if last_err:
        raise RuntimeError("Market data could not be retrieved. Please try again in a moment.") from last_err
    return pd.DataFrame()


def _live_search(query: str, limit: int = 12) -> list[SymbolInfo]:
    out: list[SymbolInfo] = []
    for host in _SEARCH_HOSTS:
        url = f"https://{host}/v1/finance/search?q={urllib.parse.quote(query)}&quotesCount={limit}&newsCount=0"
        try:
            payload = _http_get_json(url, timeout=8, tries=1)
        except Exception:
            continue
        for q in payload.get("quotes") or []:
            try:
                symbol = str(q.get("symbol") or "").strip()
                if not symbol:
                    continue
                name = str(q.get("longname") or q.get("shortname") or symbol).strip()
                exch_disp = str(q.get("exchDisp") or q.get("exchange") or "").strip() or "Yahoo Finance"
                qtype = str(q.get("quoteType") or q.get("typeDisp") or "").upper()
                # Prefer equities / ETFs / indices; skip currencies & commodities noise.
                if qtype in ("CURRENCY", "CRYPTOCURRENCY", "FUTURE", "OPTION"):
                    continue
                out.append(SymbolInfo(symbol=symbol, name=name, exchange=exch_disp))
                if len(out) >= limit:
                    break
            except Exception:
                continue
        if out:
            break
    # Prefer NSE (.NS) listings first for Indian queries.
    out.sort(key=lambda s: (not s.symbol.upper().endswith(".NS"), s.symbol))
    return out[:limit]


class YahooFinanceProvider(MarketDataProvider):
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
                results.append(SymbolInfo(symbol=entry["symbol"], name=entry["name"], exchange=entry["exchange"]))

        normalised = ql.upper().replace(" ", "")
        if normalised and not normalised.endswith((".NS", ".BO")):
            normalised += ".NS"
        if normalised and all(r.symbol != normalised for r in results):
            for entry in STOCK_REGISTRY:
                if entry["symbol"] == normalised:
                    results.insert(0, SymbolInfo(symbol=entry["symbol"], name=entry["name"], exchange=entry["exchange"]))
                    break

        seen = {r.symbol.upper() for r in results}
        try:
            for hit in _live_search(q):
                if hit.symbol.upper() in seen:
                    continue
                seen.add(hit.symbol.upper())
                results.append(hit)
        except Exception as exc:  # noqa: BLE001
            log.warning("Yahoo live search failed for %r: %s", q, exc)

        # Last resort: if the user typed an exact-looking ticker, keep it so analysis can try it.
        if not results and normalised and normalised.replace(".", "").replace("^", "").isalnum():
            results.append(SymbolInfo(symbol=normalised, name=normalised, exchange="NSE (assumed)"))

        # NSE equities first, then everything else, capped at 15.
        results.sort(key=lambda s: (not s.symbol.upper().endswith(".NS"), s.symbol))
        return results[:15]

    def _download(self, symbol: str, start: str, end_inclusive: str) -> pd.DataFrame:
        return _chart(symbol, start, end_inclusive)

    def get_historical_data(self, symbol: str, start: str, end_inclusive: str,
                            pair_id: str | None = None) -> pd.DataFrame:
        try:
            df = self._download(symbol.strip(), start, end_inclusive)
        except ValueError:
            raise
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.exception("Yahoo download failed for %s: %s", symbol, exc)
            raise RuntimeError("Market data could not be retrieved. Please try again in a moment.") from exc
        if df is None or df.empty:
            raise ValueError(f"No historical data was available for {symbol} during {start} to {end_inclusive}.")
        return df

    def get_index_data(self, start: str, end_inclusive: str) -> pd.DataFrame:
        df = self._download(NIFTY_SYMBOL, start, end_inclusive)
        if df is None or df.empty:
            # NIFTY must never sink the whole analysis: fall back to Yahoo's NSE index alias.
            for alias in ("^NSEI", "^CNX200"):
                if alias == NIFTY_SYMBOL:
                    continue
                try:
                    df = self._download(alias, start, end_inclusive)
                    if df is not None and not df.empty:
                        break
                except Exception:
                    continue
        if df is None or df.empty:
            raise ValueError(f"No historical data was available for NIFTY 50 during {start} to {end_inclusive}.")
        return df


def get_provider(name: str = "yahoo") -> MarketDataProvider:
    from .factory import get_provider as factory
    return factory(name)
