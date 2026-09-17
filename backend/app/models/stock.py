from __future__ import annotations
import re
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str
    investing_pair_id: str | None = None


class AnalyzeRequest(BaseModel):
    symbol: str = Field(description="Ticker, e.g. AMBUJACEM.NS (registry) or any Investing.com ticker")
    start: str = "2025-04-01"
    end: str = "2026-03-31"
    price_field: Literal["Close"] = "Close"
    mu0: float | None = None
    alpha: float = 0.05
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"
    investing_pair_id: str | None = Field(default=None, description="Exact Investing.com pair id from search results")
    stock_name: str | None = Field(default=None, description="Display name hint from search results")

    @field_validator("start", "end")
    @classmethod
    def _valid_day(cls, v: str) -> str:
        if not v or not _DATE_RE.match(v):
            raise ValueError("Dates must be YYYY-MM-DD.")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid calendar date: {v}.")
        return v

    @model_validator(mode="after")
    def _ordered(self):
        if self.start > self.end:
            raise ValueError("Start date must be on or before end date.")
        return self


class HypothesisRequest(BaseModel):
    analysis_id: str
    mu0: float
    alpha: float = 0.05
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"
