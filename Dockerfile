# GRC Audit Dashboard — Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create log directory
RUN mkdir -p logs

# Initialise DB and seed on startup
ENV DATABASE_URL="sqlite:///backend/grc.db"
EXPOSE 8501

CMD ["sh", "-c", "python database/seed.py && streamlit run dashboard/app.py \
     --server.port=8501 --server.address=0.0.0.0 \
     --server.headless=true --server.fileWatcherType=none"]
