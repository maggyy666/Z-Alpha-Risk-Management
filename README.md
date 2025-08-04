# Daisy Risk Engine Dashboard

A comprehensive risk management dashboard for portfolio analysis with volatility-based sizing and factor exposure analysis.

## Features

- 📊 **Volatility-Based Sizing**: Calculate portfolio weights using EWMA, GARCH, and E-GARCH models
- 📈 **Real-time Data**: Fetch historical data from IBKR API
- 🎯 **Factor Exposure**: Analyze rolling betas and R-squared values
- 💼 **Portfolio Management**: Manage multiple portfolios with different tickers
- 📱 **Modern UI**: React-based dashboard with interactive charts
- 🔄 **Database Storage**: SQLite database for efficient data management

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- npm or yarn

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Masters
   ```

2. **Install Python dependencies:**
   ```bash
   poetry install
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Initialize the database:**
   ```bash
   poetry run python init_portfolio.py
   ```

5. **Start the backend server:**
   ```bash
   poetry run python main.py
   ```

6. **In a new terminal, start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

7. **Initialize portfolio data:**
   ```bash
   curl -X POST http://localhost:8000/initialize-portfolio
   ```

8. **Access the dashboard:**
   - Open http://localhost:3000
   - Navigate to Volatility Sizing or Factor Exposure

## Project Structure

```
Masters/
├── backend/                 # FastAPI backend
│   ├── database/           # Database models and connection
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic
│   └── main.py            # FastAPI application
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   └── types/         # TypeScript types
│   └── package.json
├── portfolio.db           # SQLite database
└── pyproject.toml        # Poetry configuration
```

## API Endpoints

- `GET /health` - Health check
- `GET /volatility-data` - Get volatility-based sizing data
- `POST /initialize-portfolio` - Initialize portfolio with sample data
- `GET /factor-exposure` - Get factor exposure data

## Database Schema

- `users` - User accounts
- `portfolios` - User portfolios
- `ticker_data` - Historical price data

## Technologies Used

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript, Chart.js
- **Data Analysis**: NumPy, Pandas
- **Package Management**: Poetry (Python), npm (Node.js)

## Development

### Backend Development
```bash
# Run with auto-reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm start
```

### Database Management
```bash
# View database contents
sqlite3 backend/portfolio.db

# Reset database
rm backend/portfolio.db
poetry run python init_portfolio.py
curl -X POST http://localhost:8000/initialize-portfolio
```

## Configuration

The application uses a SQLite database by default. For production, consider:
- PostgreSQL for better performance
- Redis for caching
- Environment variables for configuration

## License

This project is provided as-is for educational and development purposes. 