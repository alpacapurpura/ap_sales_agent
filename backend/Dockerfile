# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for building python packages
# (gcc, libpq-dev for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.11-slim as final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime system dependencies only
# (libpq5 is needed for psycopg2 at runtime, but we don't need gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Create cache directories and set permissions
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser
RUN mkdir -p /tmp/fastembed_cache && chown -R appuser:appuser /tmp/fastembed_cache && chmod 777 /tmp/fastembed_cache

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
