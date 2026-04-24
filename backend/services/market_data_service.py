"""Market data access layer.

This service owns the raw OHLCV pipeline: pulling historical bars from IBKR,
persisting them to Postgres, and reading back close series / log returns for
downstream analytics. It has no opinion on portfolios, users, or risk metrics --
keep it that way.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from database.models.ticker_data import TickerData
from services.ibkr_service import IBKRService


_DATE_PATTERNS = ["%Y%m%d", "%Y-%m-%d", "%Y%m%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]


def _parse_ibkr_date(date_str: str):
    for pat in _DATE_PATTERNS:
        try:
            return datetime.strptime(date_str, pat).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")


class MarketDataService:
    """Reads and writes TickerData. Thin; all math stays in analytics layers."""

    def __init__(self, ibkr_service: IBKRService):
        self.ibkr_service = ibkr_service

    # ------------------------------------------------------------------
    # Write path: IBKR -> DB
    # ------------------------------------------------------------------
    def fetch_and_store_historical_data(self, db: Session, symbol: str) -> bool:
        """Fetch historical OHLCV from IBKR and persist new rows idempotently."""
        try:
            if not self.ibkr_service.connect():
                print(f"Failed to connect to IBKR for {symbol}")
                return False

            historical_data = self.ibkr_service.get_historical_data(symbol)
            if not historical_data:
                print(f"No historical data received for {symbol}")
                return False

            # Skip bars that are already present for this ticker
            dates_to_check = [_parse_ibkr_date(bar["date"]) for bar in historical_data]
            existing_dates = {
                d[0]
                for d in db.query(TickerData.date)
                .filter(
                    TickerData.ticker_symbol == symbol,
                    TickerData.date.in_(dates_to_check),
                )
                .all()
            }

            for bar in historical_data:
                date_obj = _parse_ibkr_date(bar["date"])
                if date_obj in existing_dates:
                    continue
                db.add(
                    TickerData(
                        ticker_symbol=symbol,
                        date=date_obj,
                        open_price=bar["open"],
                        close_price=bar["close"],
                        high_price=bar["high"],
                        low_price=bar["low"],
                        volume=bar["volume"],
                    )
                )

            db.commit()
            print(f"Successfully stored historical data for {symbol}")
            return True
        except Exception as e:
            print(f"Error fetching/storing data for {symbol}: {e}")
            return False
        finally:
            self.ibkr_service.disconnect()

    def inject_sample_data(self, db: Session, symbol: str, seed: Optional[int] = None) -> bool:
        """Seed synthetic OHLCV (used for local-only smoke testing)."""
        try:
            if seed is not None:
                np.random.seed(seed)

            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == symbol).count()
            if existing_count > 0:
                print(f"{symbol}: Already has {existing_count} records")
                return True

            base_price = 100.0
            current_price = base_price
            data_points = []

            start_date = datetime(2016, 1, 1)
            end_date = datetime.now()
            current_date = start_date

            while current_date <= end_date:
                if current_date.weekday() < 5:
                    daily_return = np.random.normal(0, 0.02)
                    current_price *= (1 + daily_return)
                    open_price = current_price * (1 + np.random.normal(0, 0.01))
                    high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.015)))
                    low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.015)))
                    volume = int(np.random.normal(1_000_000, 500_000))
                    data_points.append(
                        {
                            "ticker_symbol": symbol,
                            "date": current_date.date(),
                            "open_price": round(open_price, 2),
                            "close_price": round(current_price, 2),
                            "high_price": round(high_price, 2),
                            "low_price": round(low_price, 2),
                            "volume": max(volume, 100_000),
                        }
                    )
                current_date += timedelta(days=1)

            for data_point in data_points:
                db.add(TickerData(**data_point))
            db.commit()
            print(f"[ok] Added {len(data_points)} sample records for {symbol}")
            return True
        except Exception as e:
            print(f"Error injecting sample data for {symbol}: {e}")
            db.rollback()
            return False

    # ------------------------------------------------------------------
    # Read path: DB -> (dates, prices/returns)
    # ------------------------------------------------------------------
    def get_close_series(self, db: Session, symbol: str) -> Tuple[List, np.ndarray]:
        """Return (dates, closes) ascending; filter NaN and non-positive prices."""
        rows = (
            db.query(TickerData)
            .filter(TickerData.ticker_symbol == symbol)
            .order_by(TickerData.date)
            .all()
        )
        if not rows:
            if symbol != "PORTFOLIO":
                print(f"Debug: No TickerData found for {symbol}")
            return [], np.array([])
        dates = [r.date for r in rows]
        closes = np.array([float(r.close_price) for r in rows], dtype=float)
        mask = np.isfinite(closes) & (closes > 0)
        dates = [d for d, m in zip(dates, mask) if m]
        closes = closes[mask]
        print(
            f"Debug: {symbol} - Found {len(dates)} valid data points, "
            f"first: {dates[0] if dates else 'N/A'}, last: {dates[-1] if dates else 'N/A'}"
        )
        return dates, closes

    @staticmethod
    def log_returns_from_series(dates, closes) -> Tuple[List, np.ndarray]:
        """Return (ret_dates, log_returns); ret_dates = dates[1:]."""
        if len(closes) < 2:
            return [], np.array([])
        rets = np.diff(np.log(closes))
        return dates[1:], rets

    def get_returns_between_dates(
        self, db: Session, symbol: str, start_d: date, end_d: date
    ) -> Tuple[List, np.ndarray]:
        """Return (dates, log_returns) in [start_d, end_d]; may be empty."""
        rows = (
            db.query(TickerData)
            .filter(
                TickerData.ticker_symbol == symbol,
                TickerData.date >= start_d,
                TickerData.date <= end_d,
            )
            .order_by(TickerData.date)
            .all()
        )
        if len(rows) < 2:
            return [], np.array([])
        dts = [r.date for r in rows]
        closes = np.array([float(r.close_price) for r in rows], dtype=float)
        return self.log_returns_from_series(dts, closes)
