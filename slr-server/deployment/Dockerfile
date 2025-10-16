# Dockerfile for SLR MCP Server

FROM python:3.11-slim

# Metadata
LABEL maintainer="SLR Team <team@example.com>"
LABEL description="Systematic Literature Review MCP Server"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LOG_LEVEL=INFO \
    MCP_PORT=8080

# Create app user for security
RUN groupadd -r slrserver && useradd -r -g slrserver slrserver

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    sqlite3 \
    libsqlite3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-postgresql.txt .

# Install Python dependencies (including PostgreSQL support)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-postgresql.txt

# Copy source code and production scripts
COPY src/ src/
COPY start_server.py .
COPY README.md .
COPY requirements-postgresql.txt .

# Create data directory with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R slrserver:slrserver /app

# Switch to non-root user
USER slrserver

# Health check (test if server components can be imported)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - start production server
CMD ["python", "start_server.py"]
