# Z-Alpha Securities - Risk Management System

## Prerequisites

1. **Python 3.11** - [Download here](https://python.org/downloads/)
   * *Note: Python 3.11 is strictly required due to Interactive Brokers (IBKR) API limitations.*
2. **Node.js 20+** - [Download here](https://nodejs.org/)
   * *Note: Node.js 20+ is required for the frontend dependencies (e.g., react-router v7).*
3. **Docker Desktop** - [Download here](https://docker.com/products/docker-desktop)
4. **TWS (Trader Workstation)** - [Download here](https://www.interactivebrokers.com/]
   * *Ensure TWS is installed and running for live data connectivity.*
5. **Poetry** - [Install via pipx or official site](https://python-poetry.org/docs/)

## Quick Start

1. **Configure Environment Variables**
   Copy the example environment file and fill in your credentials:
   ```bash
   cp .config.env.example .env
   ```
   Edit `.env` to set your desired passwords and `AUTH_SECRET`.

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**
   **Windows (PowerShell):**
   ```powershell
   .venv/Scripts/activate.ps1
   ```
   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. **Run the Application**
   ```bash
   python start_all.py
   ```
   This script will:
   - Build and start all Docker containers (PostgreSQL, Backend, Frontend).
   - Seed the database with the configured admin and user accounts.
   - Launch the application.

## Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Default Login Credentials
The system creates two default users on first run. **Passwords must be configured in your `.env` file** before starting the application.

**Admin User:**
- Username: `admin@zalpha`
- Password: *(Set in `.env` as `ADMIN_PASSWORD`)*

**Analyst User:**
- Username: `user@zalpha`
- Password: *(Set in `.env` as `USER_PASSWORD`)*

## Environment Configuration (`.env`)
The application relies on a `.env` file for all sensitive configuration. Copy `.config.env.example` to `.env` and update the following:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database credentials.
- `IBKR_HOST`, `IBKR_PORT`: TWS connection settings (`127.0.0.1` + `7496` for live, `7497` for paper).
- `ADMIN_PASSWORD`, `USER_PASSWORD`: Must be at least 8 characters.
- `AUTH_SECRET`: Generate a secure random string using: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

>  **Note**: `.env` is automatically gitignored. Never commit it to version control.

## Troubleshooting
- Ensure **Docker Desktop** is running.
- Ensure **TWS** is running and connected.
- Ensure ports **3000** and **8000** are free.
- If issues persist, stop Docker containers with:
  ```bash
  docker compose down
  ```
- Make sure your virtual environment is activated before running `python start_all.py`.
- Verify that `.env` exists and contains valid values.
- **Windows Users**: If you encounter `UnicodeDecodeError` during startup, ensure your terminal supports UTF-8 or update `start_all.py` to handle encoding explicitly.