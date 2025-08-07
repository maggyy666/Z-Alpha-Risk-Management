# Z-Alpha Securities - Risk Management System

## Prerequisites

1. **Python 3.11+** - [Download here](https://python.org/downloads/)
2. **Docker Desktop** - [Download here](https://docker.com/products/docker-desktop)

## Quick Start

```bash
python start_all.py
```

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

- Make sure Docker Desktop is running
- Ports 3000 and 8000 must be free
- If stuck, run: `docker compose down` then try again