# Import Test MCP Server Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r importuser && useradd -r -g importuser importuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/importuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/importuser/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY README.md ./
COPY mcp-config-example.json ./

# Copy Docker-specific entry script
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Create directory for analysis projects
RUN mkdir -p /workspace && chown -R importuser:importuser /workspace

# Create directory for output reports
RUN mkdir -p /output && chown -R importuser:importuser /output

# Switch to non-root user
USER importuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV IMPORT_TEST_PROJECT_ROOT=/workspace
ENV IMPORT_TEST_OUTPUT_DIR=/output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python src/main.py --test --project-root /app/src || exit 1

# Expose port for potential HTTP interface (future enhancement)
EXPOSE 8080

# Default entry point
ENTRYPOINT ["./docker-entrypoint.sh"]

# Default command - run in MCP server mode
CMD ["--project-root", "/workspace"]

# Labels for GitHub Container Registry
LABEL org.opencontainers.image.title="Import Test MCP Server"
LABEL org.opencontainers.image.description="MCP server for analyzing Python imports, dependencies, and circular imports"
LABEL org.opencontainers.image.vendor="MCP Servers Collection"
LABEL org.opencontainers.image.source="https://github.com/jfriisj/mcp-servers"
LABEL org.opencontainers.image.documentation="https://github.com/jfriisj/mcp-servers/tree/main/import-test-server"
LABEL org.opencontainers.image.licenses="MIT"