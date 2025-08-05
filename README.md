# Z-Alpha Securities Dashboard

A comprehensive risk management dashboard for portfolio analysis, featuring real-time data visualization, factor exposure analysis, concentration risk assessment, and stress testing capabilities.

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)
```bash
python start_all.py
```
This will:
- Set up the database with all historical data (2016-2025)
- Start the backend server
- Start the frontend development server
- Open the dashboard at http://localhost:3000

### Option 2: Manual Setup

#### 1. Database Setup
```bash
cd backend
poetry run python setup_database.py
```

#### 2. Start Backend
```bash
cd backend
poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Start Frontend
```bash
cd frontend
npm start
```

## 📊 Features

### Portfolio Analysis
- **Portfolio Summary**: Overview of current positions and performance
- **Realized Risk**: Historical risk metrics and analysis
- **Forecast Risk**: Volatility forecasting with EWMA, GARCH, and E-GARCH models

### Factor Exposure
- **Market Factors**: Real-time beta calculations against SPY
- **Style Factors**: Momentum, Size, Value, and Quality exposures
- **Rolling Analysis**: Dynamic factor exposure over time (2016-2025)
- **Interactive Charts**: Multi-factor visualization with customizable date ranges

### Concentration Risk
- **Position Concentration**: Herfindahl Index, effective positions, top-N concentration
- **Sector Concentration**: Sector allocation analysis with pie charts
- **Market Cap Concentration**: Market cap distribution analysis
- **Risk Scoring**: Composite risk assessment with alerts and recommendations

### Stress Testing
- **Market Regime Analysis**: Volatility, correlation, and momentum analysis
- **Historical Scenarios**: PnL and drawdown analysis for historical crisis periods
- **Risk Scoring**: Multi-factor risk assessment with component analysis

### Volatility-Based Sizing
- **Volatility Forecasting**: EWMA, GARCH, and E-GARCH models
- **Inverse Volatility Weighting**: Portfolio optimization with configurable floors
- **Real-time Updates**: Dynamic weight calculations based on current market conditions

## 🔧 Management Scripts

### Database Setup
```bash
cd backend
poetry run python setup_database.py
```
Creates database, user, portfolio, and generates all historical data (2016-2025).

### Status Check
```bash
python check_status.py
```
Checks the status of all components (backend, frontend, database, endpoints).

### Add Static Tickers
```bash
cd backend
poetry run python add_static_tickers_data.py
```
Adds sample data for ETF tickers (SPY, MTUM, IWM, VLUE, QUAL).

## 📈 Data Sources

### Portfolio Tickers
- AMD, APP, BRK-B, BULL, DOMO, GOOGL, META, QQQM, RDDT, SGOV, SMCI, SNOW, TSLA, ULTY

### Static Tickers (Factor Proxies)
- **SPY**: Market factor proxy
- **MTUM**: Momentum factor proxy
- **IWM**: Size factor proxy
- **VLUE**: Value factor proxy
- **QUAL**: Quality factor proxy

### Historical Data
- **Date Range**: 2016-01-01 to 2025-12-31
- **Frequency**: Daily trading data
- **Records**: ~49,571 total records across 19 tickers
- **Features**: Open, High, Low, Close, Volume

## 🏗️ Architecture

### Backend (FastAPI + SQLAlchemy)
- **Database**: SQLite with portfolio.db
- **API**: RESTful endpoints for all dashboard features
- **Models**: User, Portfolio, TickerData
- **Services**: DataService, IBKRService

### Frontend (React + TypeScript)
- **Framework**: React with TypeScript
- **Charts**: Chart.js with react-chartjs-2
- **Styling**: Custom CSS with responsive design
- **Routing**: React Router for navigation

### Key Components
- **DashboardLayout**: Main layout with navigation
- **ConcentrationRiskPage**: Risk concentration analysis
- **FactorExposurePage**: Factor exposure visualization
- **StressTestingPage**: Stress testing and regime analysis
- **VolatilitySizingPage**: Volatility-based portfolio sizing

## 🔍 API Endpoints

### Core Endpoints
- `GET /concentration-risk-data` - Portfolio concentration analysis
- `GET /factor-exposure-data` - Factor exposure calculations
- `GET /volatility-data` - Volatility metrics and forecasting
- `GET /risk-scoring` - Composite risk assessment
- `GET /stress-testing` - Stress testing and regime analysis

### Management Endpoints
- `GET /health` - Backend health check
- `POST /initialize-portfolio` - Initialize portfolio with sample data
- `POST /fetch-data/{symbol}` - Fetch data for specific symbol

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Node.js 16+
- Poetry (Python package manager)

### Installation
```bash
# Install Python dependencies
poetry install

# Install Node.js dependencies
cd frontend
npm install
```

### Development Commands
```bash
# Backend development
cd backend
poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm start

# Database setup
cd backend
poetry run python setup_database.py

# Status check
python check_status.py
```

## 📊 Dashboard Sections

### 1. Portfolio Summary
- Current positions and weights
- Total market value
- Performance metrics

### 2. Realized Risk
- Historical volatility analysis
- Drawdown analysis
- Risk-adjusted returns

### 3. Forecast Risk
- Volatility forecasting models
- EWMA, GARCH, E-GARCH implementations
- Confidence intervals

### 4. Factor Exposure
- Market beta calculations
- Style factor exposures
- Rolling beta analysis
- Interactive multi-factor charts

### 5. Stress Testing
- Market regime analysis
- Historical scenario testing
- Risk scoring with alerts

### 6. Concentration Risk
- Position concentration metrics
- Sector allocation analysis
- Herfindahl Index calculations
- Risk scoring integration

### 7. Volatility-Based Sizing
- Volatility forecasting
- Inverse volatility weighting
- Portfolio optimization

## 🎯 Key Features

### Real-Time Data
- Live market data integration
- Dynamic portfolio updates
- Real-time risk calculations

### Advanced Analytics
- Multi-factor risk models
- Stress testing scenarios
- Volatility forecasting
- Concentration analysis

### Interactive Visualization
- Responsive charts and graphs
- Customizable date ranges
- Multi-factor overlays
- Real-time updates

### Risk Management
- Comprehensive risk scoring
- Alert system for risk thresholds
- Historical scenario analysis
- Portfolio optimization tools

## 📝 Notes

- All historical data is generated for demonstration purposes
- Factor exposure uses real ETF proxies (SPY, MTUM, IWM, VLUE, QUAL)
- Database includes 10 years of daily data (2016-2025)
- All calculations use log-returns for consistency
- Stress testing includes historical crisis scenarios

## 🚀 Deployment

The application is designed for local development but can be deployed to production with:
- Backend: Any Python hosting (Heroku, AWS, etc.)
- Frontend: Static hosting (Netlify, Vercel, etc.)
- Database: PostgreSQL for production (currently SQLite for development)

---

**Z-Alpha Securities Dashboard** - Professional risk management and portfolio analysis platform. 