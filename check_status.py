"""Check status of all components."""

import json
import logging
import os
import sqlite3

import requests

logger = logging.getLogger(__name__)


def check_backend():
    logger.info("Checking backend...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("Backend is running")
            return True
        logger.error("Backend is not responding properly")
        return False
    except requests.exceptions.RequestException:
        logger.error("Backend is not running")
        return False


def check_frontend():
    logger.info("Checking frontend...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            logger.info("Frontend is running")
            return True
        logger.error("Frontend is not responding properly")
        return False
    except requests.exceptions.RequestException:
        logger.error("Frontend is not running")
        return False


def check_database():
    logger.info("Checking database...")
    try:
        if not os.path.exists("portfolio.db"):
            logger.error("Database file not found")
            return False

        conn = sqlite3.connect("portfolio.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info("Database tables: %s", ", ".join(tables))

        cursor.execute("SELECT COUNT(*) FROM ticker_data;")
        total_records = cursor.fetchone()[0]
        logger.info("Total records: %s", total_records)

        cursor.execute("SELECT COUNT(DISTINCT ticker_symbol) FROM ticker_data;")
        total_tickers = cursor.fetchone()[0]
        logger.info("Total tickers: %s", total_tickers)

        cursor.execute("SELECT MIN(date), MAX(date) FROM ticker_data;")
        min_date, max_date = cursor.fetchone()
        logger.info("Date range: %s to %s", min_date, max_date)

        conn.close()
        return True
    except Exception as e:
        logger.error("Database error: %s", e)
        return False


def test_endpoints():
    logger.info("Testing endpoints...")

    endpoints = [
        ("/concentration-risk-data?username=admin", "Concentration Risk"),
        ("/factor-exposure-data?username=admin", "Factor Exposure"),
        ("/volatility-data?username=admin", "Volatility Data"),
        ("/risk-scoring?username=admin", "Risk Scoring"),
        ("/stress-testing?username=admin", "Stress Testing"),
    ]

    all_ok = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    logger.error("%s: %s", name, data["error"])
                    all_ok = False
                else:
                    logger.info("%s: OK", name)
            else:
                logger.error("%s: HTTP %s", name, response.status_code)
                all_ok = False

        except requests.exceptions.RequestException as e:
            logger.error("%s: Connection error - %s", name, e)
            all_ok = False
        except json.JSONDecodeError:
            logger.error("%s: Invalid JSON response", name)
            all_ok = False

    return all_ok


def main():
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("=" * 60)
    logger.info("Z-ALPHA SECURITIES - STATUS CHECK")
    logger.info("=" * 60)

    backend_ok = check_backend()
    frontend_ok = check_frontend()
    database_ok = check_database()

    endpoints_ok = test_endpoints() if backend_ok else False

    logger.info("=" * 60)
    logger.info("STATUS SUMMARY")
    logger.info("=" * 60)
    logger.info("Backend: %s", "OK" if backend_ok else "FAILED")
    logger.info("Frontend: %s", "OK" if frontend_ok else "FAILED")
    logger.info("Database: %s", "OK" if database_ok else "FAILED")
    logger.info("Endpoints: %s", "OK" if endpoints_ok else "FAILED")

    if all([backend_ok, frontend_ok, database_ok, endpoints_ok]):
        logger.info("Everything is working correctly")
        logger.info("Open http://localhost:3000 to use the dashboard")
    else:
        logger.warning("Some components are not working properly")
        logger.warning("Run 'python start_all.py' to restart everything")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
