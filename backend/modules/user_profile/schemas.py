"""Response shapes for the User Profile module endpoints."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PortfolioItem(BaseModel):
    ticker: str
    shares: float
    price: float
    market_value: float
    sector: Optional[str] = None
    industry: Optional[str] = None


class UserPortfolioResponse(BaseModel):
    username: str
    portfolio_items: List[PortfolioItem]
    total_market_value: float
    total_positions: int


class TickerSuggestion(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None


class TickerSearchResponse(BaseModel):
    suggestions: List[TickerSuggestion]


class PortfolioMutationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    updated_items: Optional[int] = None
    new_items: Optional[int] = None
    total_items: Optional[int] = None
