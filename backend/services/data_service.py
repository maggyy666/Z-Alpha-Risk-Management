"""DataService facade.

Backwards-compatible API surface for backend.api.main.py. All heavy lifting
lives in composed services:
    * MarketDataService, TickerInfoService, ReturnsService, PortfolioService
    * analytics.{concentration, volatility, factors, realized, regime,
                 risk_score, liquidity}

New code should prefer talking to those services directly; this facade is
kept so the refactor stays a no-op for the HTTP layer.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from database.models.ticker import TickerInfo
from services.analytics.concentration import ConcentrationAnalytics
from services.analytics.factors import FactorAnalytics
from services.analytics.liquidity import LiquidityAnalytics
from services.analytics.realized import RealizedAnalytics
from services.analytics.regime import RegimeAnalytics
from services.analytics.risk_score import RiskScoreAnalytics
from services.analytics.volatility import VolatilityAnalytics, _vol_cache
from services.cache import TTLCache
from services.ibkr_service import IBKRService
from services.market_data_service import MarketDataService
from services.portfolio_service import PortfolioService
from services.returns_service import ReturnsService
from services.ticker_info_service import TickerInfoService
from utils.json_safe import clean_json_values


# ----------------------------------------------------------------------
# Domain configuration (shared between analytics services)
# ----------------------------------------------------------------------
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
        # Static tickers always fetched from IBKR (used as factor-exposure ETF proxies).
        self.STATIC_TICKERS = ["SPY", "MTUM", "IWM", "VLUE", "QUAL"]

        # Shared cache for expensive analytics responses.
        self._cache = TTLCache(ttl_seconds=300)

        # Data-access layer
        self._market_data = MarketDataService(self.ibkr_service)
        self._ticker_info = TickerInfoService(self.ibkr_service)
        self._returns = ReturnsService(self._market_data)
        self._portfolios = PortfolioService(self.ibkr_service, self._market_data, self._cache)

        # Analytics layer (each takes self for cache + cross-analytics composition)
        self._a_concentration = ConcentrationAnalytics(self)
        self._a_volatility = VolatilityAnalytics(self)
        self._a_factors = FactorAnalytics(self)
        self._a_realized = RealizedAnalytics(self)
        self._a_regime = RegimeAnalytics(self, STRESS_SCENARIOS, STRESS_LIMITS, REGIME_THRESH)
        self._a_risk_score = RiskScoreAnalytics(self, NORMALIZATION)
        self._a_liquidity = LiquidityAnalytics(self)

    # ------------------------------------------------------------------
    # Cache facade (analytics services call these through the ds_ref)
    # ------------------------------------------------------------------
    def _get_cache_key(self, method: str, username: str, **kwargs) -> str:
        return TTLCache.build_key(method, username, **kwargs)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache.set(key, data)

    def _clear_cache(self, pattern: Optional[str] = None) -> None:
        removed = self._cache.clear(pattern)
        print(f"[cache] cleared pattern={pattern!r}: {removed} entries")
        vol_n = len(_vol_cache)
        _vol_cache.clear()
        print(f"[cache] cleared global volatility cache ({vol_n} entries)")

    def _clean_json_values(self, obj):
        return clean_json_values(obj)

    # ------------------------------------------------------------------
    # Ticker metadata + static-ticker list
    # ------------------------------------------------------------------
    def _ensure_ticker_info(self, db: Session, symbol: str, *, preloaded: Optional[dict] = None) -> Optional[TickerInfo]:
        return self._ticker_info.ensure_ticker_info(db, symbol, preloaded=preloaded)

    def _looks_like_etf(self, symbol: str) -> bool:
        return TickerInfoService.looks_like_etf(symbol)

    def get_all_tickers(self, db: Session, username: str = "admin") -> List[str]:
        """User portfolio + static ETF proxies, deduplicated."""
        portfolio_tickers = self.get_user_portfolio_tickers(db, username)
        return sorted(set(portfolio_tickers + self.STATIC_TICKERS))

    def get_static_tickers(self) -> List[str]:
        return self.STATIC_TICKERS.copy()

    def add_static_ticker(self, symbol: str) -> bool:
        if symbol not in self.STATIC_TICKERS:
            self.STATIC_TICKERS.append(symbol)
            return True
        return False

    def remove_static_ticker(self, symbol: str) -> bool:
        if symbol in self.STATIC_TICKERS:
            self.STATIC_TICKERS.remove(symbol)
            return True
        return False

    # ------------------------------------------------------------------
    # Portfolio CRUD
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Market data access
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Returns alignment helpers
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Volatility forecast analytics
    # ------------------------------------------------------------------
    def calculate_volatility_metrics(
        self,
        db: Session,
        symbol: str,
        forecast_model: str = "EWMA (5D)",
        risk_free_annual: float = 0.0,
    ) -> Dict[str, float]:
        return self._a_volatility.calculate_volatility_metrics(
            db, symbol, forecast_model, risk_free_annual
        )

    def get_portfolio_volatility_data(
        self,
        db: Session,
        username: str = "admin",
        forecast_model: str = "EWMA (5D)",
        vol_floor_annual_pct: float = 8.0,
        risk_free_annual: float = 0.0,
    ) -> List[Dict[str, Any]]:
        return self._a_volatility.get_portfolio_volatility_data(
            db, username, forecast_model, vol_floor_annual_pct, risk_free_annual
        )

    def build_covariance_matrix(
        self, db: Session, tickers: List[str], vol_model: str = "EWMA (5D)"
    ) -> np.ndarray:
        return self._a_volatility.build_covariance_matrix(db, tickers, vol_model)

    def get_forecast_risk_contribution(
        self,
        db: Session,
        username: str = "admin",
        vol_model: str = "EWMA (5D)",
        tickers: Optional[List[str]] = None,
        include_portfolio_bar: bool = True,
    ) -> Dict[str, Any]:
        return self._a_volatility.get_forecast_risk_contribution(
            db, username, vol_model, tickers, include_portfolio_bar
        )

    def get_forecast_metrics(
        self, db: Session, username: str = "admin", conf_level: float = 0.95
    ) -> Dict[str, Any]:
        return self._a_volatility.get_forecast_metrics(db, username, conf_level)

    def get_rolling_forecast(
        self,
        db: Session,
        tickers: List[str],
        model: str,
        window: int,
        username: str = "admin",
    ) -> Any:
        return self._a_volatility.get_rolling_forecast(db, tickers, model, window, username)

    # ------------------------------------------------------------------
    # Concentration / factors / risk-score / regime / realized / liquidity
    # ------------------------------------------------------------------
    def get_concentration_risk_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_concentration.get_concentration_risk_data(db, username)

    def get_factor_exposure_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_factors.get_factor_exposure_data(db, username)

    def get_latest_factor_exposures(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_factors.get_latest_factor_exposures(db, username)

    def get_risk_scoring(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_risk_score.get_risk_scoring(db, username)

    def get_portfolio_summary(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_risk_score.get_portfolio_summary(db, username)

    def _get_top_risk_contributor(self, forecast_contribution: Dict[str, Any]) -> tuple:
        return RiskScoreAnalytics.get_top_risk_contributor(forecast_contribution)

    def _portfolio_snapshot(self, db: Session, username: str = "admin"):
        return self._a_regime.portfolio_snapshot(db, username)

    def get_market_regime(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_regime.get_market_regime(db, username)

    def get_historical_scenarios(
        self,
        db: Session,
        username: str = "admin",
        scenarios: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return self._a_regime.get_historical_scenarios(db, username, scenarios)

    def get_stress_testing(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_regime.get_stress_testing(db, username)

    def get_realized_metrics(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_realized.get_realized_metrics(db, username)

    def get_rolling_metric(
        self,
        db: Session,
        metric: str = "vol",
        window: int = 21,
        tickers: Optional[List[str]] = None,
        username: str = "admin",
    ) -> Dict[str, Any]:
        return self._a_realized.get_rolling_metric(db, metric, window, tickers, username)

    def _get_sample_realized_metrics(self, portfolio_tickers: List[str]) -> Dict[str, Any]:
        return self._a_realized._get_sample_realized_metrics(portfolio_tickers)

    def get_liquidity_metrics(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_liquidity.get_liquidity_metrics(db, username)

    def get_volume_distribution(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        return self._a_liquidity.get_volume_distribution(db, username)

    def get_liquidity_alerts(self, db: Session, username: str = "admin") -> List[Dict[str, Any]]:
        return self._a_liquidity.get_liquidity_alerts(db, username)
