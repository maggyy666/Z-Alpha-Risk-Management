FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install poetry and Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main

# Copy backend code
COPY backend/ ./backend/

# Copy frontend code
COPY frontend/ ./frontend/

# Install frontend dependencies
WORKDIR /app/frontend
RUN npm install

# Create startup script
WORKDIR /app
RUN echo '#!/bin/bash\n\
cd /app/backend && poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 &\n\
cd /app/frontend && npm start\n\
wait' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 3000 8000

# Start both services
CMD ["/app/start.sh"]
