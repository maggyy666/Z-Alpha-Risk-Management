# Z-Alpha Securities - Risk Management System

## Prerequisites

1. **Python 3.11+** - [Download here](https://python.org/downloads/)
2. **Node.js 18+** - [Download here](https://nodejs.org/)
3. **Docker Desktop** - [Download here](https://docker.com/products/docker-desktop) (optional)

## Quick Start

### Option 1: With Docker (Recommended)
```bash
python start_all.py
```

### Option 2: Without Docker (Development)

#### Backend Setup (One Command)
```bash
cd backend && poetry install && poetry run python setup_database.py && poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup (One Command)
```bash
cd frontend && npm install && npm start
```

#### Frontend Setup on Port 3001 (Manual)
```bash
cd frontend && npm install && PORT=3001 npm start
```

#### Alternative: Separate Commands

**Backend Setup**
```bash
cd backend
poetry install
poetry run python setup_database.py
poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend Setup**
```bash
cd frontend
npm install
npm start
```

#### Access the Application
- Frontend: http://localhost:3000
- Frontend (Alt): http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## What it does

1. Auto-installs Poetry (Python dependency manager)
2. Installs all dependencies
3. Sets up database with sample data
4. Starts Docker containers (frontend + backend)
5. Opens at http://localhost:3000

## Default login
- Username: `admin`
- Password: `admin`

## Troubleshooting

- Make sure Docker Desktop is running (if using Docker)
- Ports 3000, 3001 and 8000 must be free
- If stuck, run: `docker compose down` then try again