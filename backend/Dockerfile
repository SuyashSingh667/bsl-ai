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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY . .

# Ensure upload directories exist
RUN mkdir -p data/audio data/photos

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Start Uvicorn bound to 0.0.0.0
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
