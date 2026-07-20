FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY shared ./shared
COPY services ./services

# Create directories for imports and audio
RUN mkdir -p /app/imports /app/audio

# Expose port
EXPOSE 8000

# Run the application using gunicorn for production
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000"]