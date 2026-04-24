#!/usr/bin/env python3
"""Complete database setup: create schema, seed users, import portfolios, fetch market data."""

import json
import logging
import os
import sys
from typing import List

sys.path.append(os.path.dirname(__file__))

from database.database import Base, SessionLocal, engine
from database.models.portfolio import Portfolio
from database.models.ticker import TickerInfo
from database.models.ticker_data import TickerData
from database.models.user import User
from logging_config import setup_logging
from services.data_service import DataService

logger = logging.getLogger(__name__)


def check_required_modules():
    logger.info("Checking required modules...")
    required_modules = ["sqlalchemy", "requests", "numpy", "pandas"]
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    if missing_modules:
        logger.error("Missing required modules: %s", missing_modules)
        logger.error("Install them with: pip install %s", " ".join(missing_modules))
        return False
    logger.info("All required modules found")
    return True


def check_database_connection():
    """Verify Postgres is reachable via SQLAlchemy engine."""
    logger.info("Checking database connection...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
        return True
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        return False


def drop_all_tables():
    """Drop all tables for a clean re-seed. Volume wipe is handled by start_all."""
    logger.info("Dropping existing tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables dropped")
        return True
    except Exception as e:
        logger.error("Error dropping tables: %s", e)
        return False


def create_database_tables():
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error("Error creating database tables: %s", e)
        return False


SEED_USERS = [
    {
        "slot": "ADMIN",
        "default_username": "admin",
        "default_email": "admin@zalpha.local",
        "portfolio_fixture": "admin_portfolio.json",
    },
    {
        "slot": "USER",
        "default_username": "user",
        "default_email": "user@zalpha.local",
        "portfolio_fixture": "user_portfolio.json",
    },
]


def _read_seed_credentials(slot: str, default_username: str, default_email: str) -> dict:
    """Read {SLOT}_USERNAME / {SLOT}_EMAIL / {SLOT}_PASSWORD from env.
    Username/email fall back to sane defaults; password has no default and must be set."""
    username = os.environ.get(f"{slot}_USERNAME", default_username)
    email = os.environ.get(f"{slot}_EMAIL", default_email)
    password = os.environ.get(f"{slot}_PASSWORD")
    if not password:
        raise RuntimeError(
            f"{slot}_PASSWORD is not set. Copy config.env.example to .env and set a password."
        )
    if len(password) < 8:
        raise RuntimeError(f"{slot}_PASSWORD must be at least 8 characters.")
    return {"username": username, "email": email, "password": password}


def seed_users(db) -> dict:
    """Create admin + user from env (idempotent). Returns {slot: User} map."""
    from auth.passwords import hash_password

    logger.info("Seeding users from environment...")
    created = {}
    for entry in SEED_USERS:
        slot = entry["slot"]
        creds = _read_seed_credentials(slot, entry["default_username"], entry["default_email"])

        user = db.query(User).filter(User.username == creds["username"]).first()
        if user:
            logger.info("  %s: user '%s' already exists -- skipping", slot, creds["username"])
        else:
            user = User(
                username=creds["username"],
                email=creds["email"],
                password_hash=hash_password(creds["password"]),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("  %s: created user '%s' (id=%s)", slot, creds["username"], user.id)
        created[slot] = user
    return created


def _resolve_fixture_path(filename: str) -> str:
    """Locate a fixture file whether script runs from project root or backend/."""
    candidates = [f"../data/{filename}", f"data/{filename}"]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def get_tickers_from_fixture(fixture_filename: str) -> List[str]:
    """Return list of ticker symbols from a portfolio fixture file."""
    portfolio_file = _resolve_fixture_path(fixture_filename)
    try:
        if not os.path.exists(portfolio_file):
            logger.error("Portfolio fixture %s not found", portfolio_file)
            return []
        with open(portfolio_file, "r") as f:
            portfolio_data = json.load(f)
        if not isinstance(portfolio_data, list):
            logger.error("Invalid portfolio format in %s: expected list", portfolio_file)
            return []
        return [item.get("ticker") for item in portfolio_data if "ticker" in item]
    except Exception as e:
        logger.error("Error reading %s: %s", portfolio_file, e)
        return []


def import_portfolio_from_file(db, user, portfolio_file: str):
    try:
        if not os.path.exists(portfolio_file):
            logger.error("Portfolio file %s not found", portfolio_file)
            return False

        with open(portfolio_file, "r") as f:
            portfolio_data = json.load(f)

        if not isinstance(portfolio_data, list):
            logger.error("Invalid portfolio format: expected list of ticker objects")
            return False

        added_count = 0
        for item in portfolio_data:
            if "ticker" not in item or "shares" not in item:
                logger.warning("Invalid portfolio item: missing ticker or shares")
                continue

            ticker = item["ticker"]
            shares = int(item["shares"])

            existing = db.query(Portfolio).filter(
                Portfolio.user_id == user.id,
                Portfolio.ticker_symbol == ticker,
            ).first()

            if not existing:
                db.add(Portfolio(user_id=user.id, ticker_symbol=ticker, shares=shares))
                added_count += 1

        db.commit()
        logger.info(
            "Imported portfolio for %s with %s tickers from %s",
            user.username, added_count, portfolio_file,
        )
        return True
    except Exception as e:
        logger.error("Error importing portfolio for %s: %s", user.username, e)
        db.rollback()
        return False


def setup_portfolio(db, user, fixture_filename: str):
    """Import a portfolio fixture file into the DB for the given user."""
    logger.info("Setting up portfolio for %s from %s...", user.username, fixture_filename)
    portfolio_file = _resolve_fixture_path(fixture_filename)
    return import_portfolio_from_file(db, user, portfolio_file)


def generate_ticker_data(db, data_service, ticker):
    """Fetch real historical data from IBKR for a ticker. Reuses the caller's
    DataService so the underlying IBKRService keeps its client_id counter
    monotonically increasing -- otherwise every ticker reconnects with id
    1001 and TWS rejects with Error 326 (client id already in use)."""
    logger.info("Fetching real data for %s from IBKR", ticker)
    return data_service.fetch_and_store_historical_data(db, ticker)


def generate_historical_data(db, data_service, tickers, data_type):
    logger.info("Generating historical data for %s...", data_type)

    try:
        success_count = 0
        for ticker in tickers:
            try:
                existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
                if existing_count == 0:
                    generate_ticker_data(db, data_service, ticker)
                    logger.info("Generated data for %s", ticker)
                    success_count += 1
                else:
                    logger.info("%s: already has %s records", ticker, existing_count)
                    success_count += 1

                try:
                    info = data_service._ensure_ticker_info(db, ticker)
                    if info:
                        logger.info(
                            "Ticker info for %s: sector=%s, industry=%s",
                            ticker, info.sector, info.industry,
                        )
                    else:
                        logger.warning("No ticker info for %s", ticker)
                except Exception as e:
                    logger.error("Error ensuring ticker info for %s: %s", ticker, e)

            except Exception as e:
                logger.error("Error generating data for %s: %s", ticker, e)

        logger.info("Successfully processed %s/%s %s", success_count, len(tickers), data_type)
        return True
    except Exception as e:
        logger.error("Error generating historical data: %s", e)
        return False


def fetch_fundamental_data(db, data_service, tickers):
    """Fetch fundamental data for tickers from IBKR."""
    logger.info("Fetching fundamental data for tickers...")

    try:
        logger.info("Connecting to IBKR...")
        if not data_service.ibkr_service.connect():
            logger.error("Failed to connect to IBKR -- skipping fundamental data")
            return False

        success_count = 0
        for ticker in tickers:
            try:
                logger.info("Fetching data for %s...", ticker)
                fundamental_data = data_service.ibkr_service.get_fundamentals(ticker)
                info = data_service._ensure_ticker_info(db, ticker, preloaded=fundamental_data)

                if info:
                    success_count += 1
                    logger.info("Successfully processed %s", ticker)
                else:
                    logger.warning("Failed to process %s", ticker)

            except Exception as e:
                logger.error("Error processing %s: %s", ticker, e)
                continue

        logger.info("Successfully processed %s/%s tickers", success_count, len(tickers))
        return True

    except Exception as e:
        logger.error("Error in fetch_fundamental_data: %s", e)
        return False
    finally:
        data_service.ibkr_service.disconnect()
        logger.info("Disconnected from IBKR")


def show_database_summary(db, admin_user):
    logger.info("Database summary...")

    try:
        total_tickers = db.query(TickerData.ticker_symbol).distinct().count()
        total_records = db.query(TickerData).count()
        portfolio_count = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).count()
        ticker_info_count = db.query(TickerInfo).count()

        logger.info("Total tickers: %s", total_tickers)
        logger.info("Total records: %s", total_records)
        logger.info("Portfolio items: %s", portfolio_count)
        logger.info("Ticker info records: %s", ticker_info_count)

        date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
        if date_range:
            logger.info("Date range: %s to %s", date_range[0][0], date_range[-1][0])

        return True
    except Exception as e:
        logger.error("Error showing database summary: %s", e)
        return False


def setup_database():
    logger.info("Starting complete database setup...")
    logger.info("Using real market data from IBKR TWS")

    if not check_required_modules():
        return False
    if not check_database_connection():
        return False
    if not drop_all_tables():
        return False
    if not create_database_tables():
        return False

    db = SessionLocal()
    try:
        try:
            users_by_slot = seed_users(db)
        except RuntimeError as e:
            logger.error("User seeding failed: %s", e)
            return False

        for entry in SEED_USERS:
            user = users_by_slot[entry["slot"]]
            if not setup_portfolio(db, user, entry["portfolio_fixture"]):
                return False

        data_service = DataService()

        all_tickers = set()
        for entry in SEED_USERS:
            all_tickers.update(get_tickers_from_fixture(entry["portfolio_fixture"]))

        static_tickers = ["SPY", "MTUM", "IWM", "VLUE", "QUAL"]
        all_tickers.update(static_tickers)

        logger.info("Total unique tickers to process: %s", len(all_tickers))
        logger.info("Tickers: %s", sorted(all_tickers))

        if not generate_historical_data(db, data_service, list(all_tickers), "all tickers"):
            return False

        if not fetch_fundamental_data(db, data_service, list(all_tickers)):
            logger.warning("Some fundamental data may be missing")

        if not show_database_summary(db, users_by_slot["ADMIN"]):
            return False

        logger.info("Database setup completed successfully")
        return True

    except Exception as e:
        logger.exception("Error during database setup: %s", e)
        return False
    finally:
        db.close()


def main():
    setup_logging()
    logger.info("=" * 60)
    logger.info("Z-ALPHA SECURITIES - DATABASE SETUP")
    logger.info("=" * 60)

    success = setup_database()

    if success:
        logger.info("Setup completed successfully")
        logger.info("You can now run the application with: python start_all.py")
    else:
        logger.error("Setup failed -- check the log messages above")

    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
