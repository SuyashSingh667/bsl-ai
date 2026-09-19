FROM python:3.11-slim

# Install system dependencies (ffmpeg, git, build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared assets, docs, and configurations
COPY spatial_impact/ ./spatial_impact/
COPY rag_documents/ ./rag_documents/
COPY verification_questions.json .

# Copy backend code into /app/backend
COPY backend/ ./backend/

# Also copy backend files directly into /app so it works with either rootDir
COPY backend/app/ ./app/

# Ensure upload directories exist in both possible working directories
RUN mkdir -p /app/backend/data/audio /app/backend/data/photos /app/data/audio /app/data/photos

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app/backend:/app

# Start Uvicorn bound to 0.0.0.0
CMD ["sh", "-c", "cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
