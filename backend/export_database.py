"""Export current database to JSON format for easy distribution."""

import json
import logging
import os
import sys
from datetime import date, datetime

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models.historical_data import HistoricalData
from database.models.portfolio import Portfolio
from database.models.ticker import Ticker
from database.models.ticker_data import TickerData
from database.models.user import User

logger = logging.getLogger(__name__)


def serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_users(db: Session):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
        for user in users
    ]


def export_portfolios(db: Session):
    portfolios = db.query(Portfolio).all()
    return [
        {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "ticker_symbol": portfolio.ticker_symbol,
            "shares": portfolio.shares,
            "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
            "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
        }
        for portfolio in portfolios
    ]


def export_tickers(db: Session):
    tickers = db.query(Ticker).all()
    return [
        {
            "id": ticker.id,
            "symbol": ticker.symbol,
            "company_name": ticker.company_name,
            "sector": ticker.sector,
            "market_cap": ticker.market_cap,
            "last_price": ticker.last_price,
            "volume": ticker.volume,
            "created_at": ticker.created_at.isoformat() if ticker.created_at else None,
            "updated_at": ticker.updated_at.isoformat() if ticker.updated_at else None,
        }
        for ticker in tickers
    ]


def export_historical_data(db: Session):
    historical_data = db.query(HistoricalData).all()
    return [
        {
            "id": data.id,
            "ticker_id": data.ticker_id,
            "date": data.date.isoformat() if data.date else None,
            "open_price": data.open_price,
            "close_price": data.close_price,
            "high_price": data.high_price,
            "low_price": data.low_price,
            "volume": data.volume,
            "created_at": data.created_at.isoformat() if data.created_at else None,
        }
        for data in historical_data
    ]


def export_ticker_data(db: Session):
    ticker_data = db.query(TickerData).all()
    return [
        {
            "id": data.id,
            "ticker_symbol": data.ticker_symbol,
            "date": data.date.isoformat() if data.date else None,
            "open_price": data.open_price,
            "close_price": data.close_price,
            "high_price": data.high_price,
            "low_price": data.low_price,
            "volume": data.volume,
            "created_at": data.created_at.isoformat() if data.created_at else None,
        }
        for data in ticker_data
    ]


def get_database_stats(db: Session):
    return {
        "users_count": db.query(User).count(),
        "portfolios_count": db.query(Portfolio).count(),
        "tickers_count": db.query(Ticker).count(),
        "historical_data_count": db.query(HistoricalData).count(),
        "ticker_data_count": db.query(TickerData).count(),
        "export_timestamp": datetime.now().isoformat(),
    }


def export_database():
    logger.info("=" * 60)
    logger.info("Z-ALPHA SECURITIES - DATABASE EXPORT")
    logger.info("=" * 60)

    db_path = "portfolio.db"
    if not os.path.exists(db_path):
        logger.error("Database file %s not found", db_path)
        return False

    logger.info("Exporting database: %s", db_path)

    db = SessionLocal()
    try:
        stats = get_database_stats(db)
        logger.info("Database statistics:")
        logger.info("  Users: %s", stats["users_count"])
        logger.info("  Portfolios: %s", stats["portfolios_count"])
        logger.info("  Tickers: %s", stats["tickers_count"])
        logger.info("  Historical data records: %s", stats["historical_data_count"])
        logger.info("  Ticker data records: %s", stats["ticker_data_count"])

        logger.info("Exporting data...")

        export_data = {
            "metadata": stats,
            "users": export_users(db),
            "portfolios": export_portfolios(db),
            "tickers": export_tickers(db),
            "historical_data": export_historical_data(db),
            "ticker_data": export_ticker_data(db),
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"z_alpha_database_export_{timestamp}.json"

        logger.info("Saving to: %s", output_file)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=serialize_datetime)

        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        total_records = sum(
            len(export_data[k])
            for k in ("users", "portfolios", "tickers", "historical_data", "ticker_data")
        )

        logger.info("=" * 60)
        logger.info("EXPORT COMPLETE")
        logger.info("=" * 60)
        logger.info("Export file: %s", output_file)
        logger.info("File size: %.2f MB", file_size_mb)
        logger.info("Total records exported: %s", total_records)

        standard_name = "z_alpha_sample_database.json"
        with open(standard_name, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=serialize_datetime)

        logger.info("Standard copy created: %s", standard_name)
        return True

    except Exception as e:
        logger.error("Error during export: %s", e)
        return False
    finally:
        db.close()


def main():
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        if not export_database():
            logger.error("Export failed")
            sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
