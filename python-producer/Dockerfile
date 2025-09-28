FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  gcc \
  libxml2-dev \
  libxslt-dev \
  libffi-dev \
  libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies as root (system-wide)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user with UID/GID 1001
RUN groupadd -g 1001 appuser && \
  useradd -r -u 1001 -g appuser appuser

# Create logs and cache directories and ensure proper permissions
RUN mkdir -p /app/logs /app/cache && \
  chown -R appuser:appuser /app && \
  chmod -R 775 /app

# Switch to non-root user
USER appuser

# Expose port (if needed for health checks)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "main.py"]
