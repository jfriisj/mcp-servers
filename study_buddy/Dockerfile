# =============================================================================
# Study Buddy MCP Server - Native Prompts Only
# =============================================================================
# This Dockerfile packages only the Study Buddy MCP server with native prompts
# for document processing and analysis. No GUI, no extra APIs - just the MCP server.
#
# Usage:
#   docker build -t study-buddy-mcp .
#   docker run -p 3000:3000 -v ./data:/data study-buddy-mcp
#
# Components included:
#   - MCP Server with Native Prompts (document processing and analysis)
#   - SQLite Database (document storage)
#   - Document Parsers (PDF, DOCX, PPTX, Markdown)
# =============================================================================

FROM python:3.12-slim AS base

# =============================================================================
# Base Stage - System Dependencies (MCP Server Only)
# =============================================================================

# Install minimal system dependencies for MCP server
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core system
    sqlite3 libsqlite3-dev \
    gcc g++ libc6-dev libffi-dev \
    ca-certificates \
    # Process management (tini not available in slim, use dumb-init)
    # Additional utilities
    curl wget \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -g 1000 studybuddy && \
    useradd -u 1000 -g studybuddy -m -s /bin/bash studybuddy

# Create application directories
RUN mkdir -p /app /data && \
    chmod 755 /app && \
    chmod 750 /data && \
    chown -R studybuddy:studybuddy /app /data

WORKDIR /app

# =============================================================================
# Dependencies Stage - MCP Server Python Packages
# =============================================================================

FROM base AS dependencies

# Install build dependencies temporarily
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libc6-dev libffi-dev libssl-dev python3-dev make \
    && rm -rf /var/lib/apt/lists/*

# Create requirements file for MCP server only
COPY --chown=studybuddy:studybuddy <<'EOF' ./requirements.txt
# MCP Framework
mcp>=1.0.0

# Document Processing
PyPDF2>=3.0.1
python-docx>=1.1.0
python-pptx>=0.6.23
markdown>=3.5.2

# Additional utilities
pydantic>=2.5.0
typing-extensions>=4.8.0
EOF

# Install Python dependencies (MCP server only)
RUN pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Clean up build dependencies
RUN apt-get remove -y gcc g++ libc6-dev libffi-dev libssl-dev python3-dev make && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /pip-cache /tmp/*

# Verify MCP server dependencies only
RUN python -c "import mcp, sqlite3; print('✅ MCP server dependencies verified')"

# =============================================================================
# MCP Server Build Stage
# =============================================================================

FROM dependencies AS build

# Copy MCP server source code
COPY --chown=studybuddy:studybuddy src/ ./src/

# Set Python path for MCP server
ENV PYTHONPATH=/app/src:/app/mcp-server/src
ENV PYTHONDONTWRITEBYTECODE=1

# Create MCP server executable script
RUN echo '#!/bin/bash\ncd /app && python src/study_buddy/server/main.py "$@"' > /usr/local/bin/mcp-server && \
    chmod +x /usr/local/bin/mcp-server

# =============================================================================
# Production Stage - MCP Server Only
# =============================================================================

FROM base AS production

# Copy Python installation from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=dependencies /usr/local/bin/ /usr/local/bin/

# Copy built MCP server from build stage
COPY --from=build --chown=studybuddy:studybuddy /app/ /app/

# Create simple MCP server startup script
RUN printf '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Study Buddy MCP Server Starting..."\n\
echo "📊 Components: MCP Server with Native Prompts + SQLite Database"\n\
echo "🗄️ Database: ${STUDY_BUDDY_DB_PATH:-/app/study_buddy.db}"\n\
\n\
# Ensure data directory exists\n\
mkdir -p /data /app\n\
\n\
# Set database path (use internal path by default to avoid volume issues)\n\
export STUDY_BUDDY_DB_PATH="${STUDY_BUDDY_DB_PATH:-/app/study_buddy.db}"\n\
\n\
# Set Python path for MCP server\n\
export PYTHONPATH="/app/src:/app/mcp-server/src:$PYTHONPATH"\n\
\n\
# Start MCP server (it handles database initialization automatically)\n\
echo "✅ Starting Study Buddy MCP Server..."\n\
cd /app\n\
exec python src/study_buddy/server/main.py\n' > /app/startup.sh

RUN chmod +x /app/startup.sh && chown studybuddy:studybuddy /app/startup.sh

# Create health check script
COPY --chown=studybuddy:studybuddy <<'EOF' /app/healthcheck.sh
#!/bin/bash

# Check if MCP server process is running
if ! pgrep -f "python.*server.py" > /dev/null; then
    echo "❌ MCP server not running"
    exit 1
fi

# Check database exists and is accessible
if [ ! -f "${STUDY_BUDDY_DB_PATH:-/data/study_buddy.db}" ]; then
    echo "❌ Database not found"
    exit 1
fi

echo "✅ MCP server healthy"
exit 0
EOF

RUN chmod +x /app/healthcheck.sh

# Switch to application user
USER studybuddy

# Final verification - check MCP server dependencies only
RUN python -c "import mcp, sqlite3; print('✅ MCP server dependencies verified')"

# Configure port for MCP server
EXPOSE 3000

# Configure volumes
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Direct command execution (no init system needed for simple MCP server)
ENTRYPOINT ["/app/startup.sh"]

# =============================================================================
# Build Information and Metadata
# =============================================================================

LABEL maintainer="Study Buddy Team"
LABEL description="Study Buddy MCP Server with Native Prompts - Document Processing and Analysis"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/jfriisj/study-buddy"
LABEL org.opencontainers.image.description="Lightweight Study Buddy MCP server with native prompts for document processing, chunking, and analysis workflows"
LABEL org.opencontainers.image.licenses="MIT"

# Usage information
LABEL usage="docker run -p 3000:3000 -v ./data:/data study-buddy-mcp"
LABEL components="MCP Server with Native Prompts, SQLite Database, Document Parsers (PDF/DOCX/PPTX/MD)"

# Container size estimate: ~150MB (lightweight!)
# - Python 3.12-slim base: ~45MB
# - System dependencies: ~15MB  
# - Python MCP dependencies: ~60MB
# - Application code: ~10MB
# - Total: ~130MB (optimized for MCP server only)