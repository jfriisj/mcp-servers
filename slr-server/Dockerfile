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
    DATABASE_PATH=/app/data/slr_database.db \
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code
COPY src/ src/
COPY tests/ tests/
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install -e .

# Create data directory with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R slrserver:slrserver /app

# Switch to non-root user
USER slrserver

# Health check (test if server can start)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.main import SLRMCPServer; print('Server can be imported')" || exit 1

# Default command
CMD ["python", "-m", "src.main"]
