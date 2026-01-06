FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Install package in editable mode
RUN pip install --no-cache-dir -e .

# Default entrypoint (can be overridden in docker-compose)
ENTRYPOINT ["python", "tools/run_demo.py"]
