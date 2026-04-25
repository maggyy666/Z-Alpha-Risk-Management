"""Backwards-compatible facade over data access and analytics services.

New code should talk to the composed services directly; this class exists so
the refactor remained a no-op for the HTTP layer (backend/api/main.py).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from database.models.ticker import TickerInfo
from services.analytics.risk_score import RiskScoreAnalytics
from services.cache import TTLCache
from services.ibkr_service import IBKRService
from services.market_data_service import MarketDataService
from services.portfolio_service import PortfolioService
from services.returns_service import ReturnsService
from services.ticker_info_service import TickerInfoService
from utils.json_safe import clean_json_values

logger = logging.getLogger(__name__)


# Shared domain configuration consumed by analytics services.
NORMALIZATION = {
    "HHI_LOW": 0.05,
    "HHI_HIGH": 0.30,
    "VOL_MAX": 0.40,
    "BETA_ABS_MAX": 1.5,
    "FACTOR_L1_MAX": 3.0,
    "STRESS_5PCT_FULLSCORE": 0.10,
}

STRESS_SCENARIOS = [
    {"name": "2018 Q4 Volatility",   "start": date(2018, 10, 1),  "end": date(2018, 12, 24)},
    {"name": "2020 COVID Crash",     "start": date(2020, 2, 20),  "end": date(2020, 3, 23)},
    {"name": "2020 Recovery",        "start": date(2020, 3, 24),  "end": date(2020, 8, 31)},
    {"name": "2022 Inflation Shock", "start": date(2022, 1, 3),   "end": date(2022, 10, 14)},
    {"name": "2015 China Deval",     "start": date(2015, 8, 10),  "end": date(2015, 9, 1)},
]

STRESS_LIMITS = {
    "lookback_regime_days": 60,
    "momentum_window_days": 20,
    "scenario_min_days": 10,
    "scenario_min_weight_coverage": 0.30,
    "clamp_return_abs": 0.40,
}

REGIME_THRESH = {
    "crisis_vol": 0.30,
    "cautious_vol": 0.20,
    "cautious_corr": 0.45,
    "bull_mom": 0.05,
    "bull_vol": 0.18,
    "bull_corr": 0.25,
}


class DataService:
    def __init__(self):
        self.ibkr_service = IBKRService()
        # ETF proxies used for factor exposure regressions.
        self.STATIC_TICKERS = ["SPY", "MTUM", "IWM", "VLUE", "QUAL"]
        self._cache = TTLCache(ttl_seconds=300)

        self._market_data = MarketDataService(self.ibkr_service)
        self._ticker_info = TickerInfoService(self.ibkr_service)
        self._returns = ReturnsService(self._market_data)
        self._portfolios = PortfolioService(self.ibkr_service, self._market_data, self._cache)

        self._a_risk_score = RiskScoreAnalytics(self, NORMALIZATION)

    # Cache
    def _get_cache_key(self, method: str, username: str, **kwargs) -> str:
        return TTLCache.build_key(method, username, **kwargs)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache.set(key, data)

    def _clear_cache(self, pattern: Optional[str] = None) -> None:
        """Clear the request-level TTL cache plus the per-symbol vol forecast cache."""
        from modules.volatility_sizing.service import _vol_cache
        removed = self._cache.clear(pattern)
        vol_n = len(_vol_cache)
        _vol_cache.clear()
        logger.debug("cleared pattern=%r: %d entries; vol cache: %d entries", pattern, removed, vol_n)

    def _clean_json_values(self, obj):
        return clean_json_values(obj)

    # Ticker metadata
    def _ensure_ticker_info(self, db: Session, symbol: str, *, preloaded: Optional[dict] = None) -> Optional[TickerInfo]:
        return self._ticker_info.ensure_ticker_info(db, symbol, preloaded=preloaded)

    def _looks_like_etf(self, symbol: str) -> bool:
        return TickerInfoService.looks_like_etf(symbol)

    def get_all_tickers(self, db: Session, username: str = "admin") -> List[str]:
        """User portfolio plus factor-proxy ETFs, deduplicated."""
        return sorted(set(self.get_user_portfolio_tickers(db, username) + self.STATIC_TICKERS))

    def get_static_tickers(self) -> List[str]:
        return self.STATIC_TICKERS.copy()

    def add_static_ticker(self, symbol: str) -> bool:
        if symbol in self.STATIC_TICKERS:
            return False
        self.STATIC_TICKERS.append(symbol)
        return True

    def remove_static_ticker(self, symbol: str) -> bool:
        if symbol not in self.STATIC_TICKERS:
            return False
        self.STATIC_TICKERS.remove(symbol)
        return True

    # Portfolio CRUD
    def get_user_portfolio_tickers(self, db: Session, username: str = "admin") -> List[str]:
        return self._portfolios.get_user_portfolio_tickers(db, username)

    def add_ticker_to_portfolio(self, db: Session, username: str, ticker: str, shares: int) -> Dict[str, Any]:
        return self._portfolios.add_ticker(db, username, ticker, shares)

    def remove_ticker_from_portfolio(self, db: Session, username: str, ticker: str) -> Dict[str, Any]:
        return self._portfolios.remove_ticker(db, username, ticker)

    def _update_portfolio_json(self, username: str, db: Session) -> None:
        self._portfolios._update_portfolio_json(username, db)

    def search_tickers(self, query: str) -> List[Dict[str, str]]:
        return self._portfolios.search_tickers(query)

    def check_ibkr_connection(self) -> bool:
        return self._portfolios._check_ibkr_connection()

    # Market data
    def fetch_and_store_historical_data(self, db: Session, symbol: str) -> bool:
        return self._market_data.fetch_and_store_historical_data(db, symbol)

    def inject_sample_data(self, db: Session, symbol: str, seed: Optional[int] = None) -> bool:
        return self._market_data.inject_sample_data(db, symbol, seed=seed)

    def _get_close_series(self, db: Session, symbol: str):
        return self._market_data.get_close_series(db, symbol)

    def _log_returns_from_series(self, dates, closes):
        return MarketDataService.log_returns_from_series(dates, closes)

    def _get_returns_between_dates(self, db: Session, symbol: str, start_d: date, end_d: date):
        return self._market_data.get_returns_between_dates(db, symbol, start_d, end_d)

    # Returns alignment
    def _get_return_series_map(self, db: Session, symbols: List[str], lookback_days: int = 120):
        return self._returns.get_return_series_map(db, symbols, lookback_days)

    def _align_on_reference(self, ret_map, symbols, ref_symbol: str = "SPY", min_obs: int = 40):
        return ReturnsService.align_on_reference(ret_map, symbols, ref_symbol=ref_symbol, min_obs=min_obs)

    def _portfolio_series_with_coverage(self, dates, R, weights_map, symbols, min_weight_cov: float = 0.6):
        return ReturnsService.portfolio_series_with_coverage(
            dates, R, weights_map, symbols, min_weight_cov=min_weight_cov
        )

    def _pairwise_corr_nan_safe(self, R: np.ndarray, min_periods: int = 30):
        return ReturnsService.pairwise_corr_nan_safe(R, min_periods=min_periods)

    def _intersect_and_stack(self, ret_map: Dict[str, Any], symbols: List[str]):
        return ReturnsService.intersect_and_stack(ret_map, symbols)

    def _get_common_date_range(self, db: Session, symbols: List[str]) -> Dict[str, Any]:
        return self._returns.get_common_date_range(db, symbols)

    # Volatility/forecast helpers used by RiskScoreAnalytics through this facade.
    # Logic lives in modules/volatility_sizing + modules/forecast_risk; these are shims.
    def calculate_volatility_metrics(
        self, db: Session, symbol: str,
        forecast_model: str = "EWMA (5D)", risk_free_annual: float = 0.0,
    ) -> Dict[str, float]:
        from modules.volatility_sizing.service import calculate_volatility_metrics
        return calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)

    def build_covariance_matrix(
        self, db: Session, tickers: List[str], vol_model: str = "EWMA (5D)"
    ) -> np.ndarray:
        from modules.forecast_risk.service import build_covariance_matrix
        return build_covariance_matrix(self, db, tickers, vol_model)

    # Concentration / risk score
    def get_concentration_risk_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Shim into modules/concentration_risk -- kept on the facade because
        many modules consume portfolio weights through `ds.get_concentration_risk_data`."""
        from modules.concentration_risk import service as concentration_service
        return concentration_service.get_concentration_risk_data(self, db, username)

    def get_risk_scoring(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_risk_score.get_risk_scoring(db, username)

    def _portfolio_snapshot(self, db: Session, username: str = "admin"):
        """Returns ([{ticker, weight_frac, ...}], 1.0) with weights renormalized,
        or ([], 0.0) when there are no positions. Shared by realized_risk and
        stress_testing modules."""
        conc = self.get_concentration_risk_data(db, username)
        if "error" in conc:
            return [], 0.0
        positions = conc["portfolio_data"]
        w_sum = sum(p.get("weight_frac", 0.0) for p in positions)
        if w_sum <= 0:
            return [], 0.0
        for p in positions:
            p["weight_frac"] = float(p["weight_frac"]) / w_sum
        return positions, 1.0

