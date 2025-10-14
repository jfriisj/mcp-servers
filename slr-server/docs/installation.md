# Installation Guide - SLR MCP Server

Complete installation and setup guide for the Systematic Literature Review MCP Server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [MCP Integration](#mcp-integration)
5. [Database Setup](#database-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites {#prerequisites}

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space minimum
- **Network**: Internet connection for package downloads

### Required Software

- **Python 3.8+** with pip
- **Git** (for development installation)
- **VS Code** (for MCP integration)
- **SQLite 3** (usually included with Python)

### Development Prerequisites

For development installations, you'll also need:
- **Node.js 16+** (for VS Code MCP extension)
- **Docker** (optional, for containerized deployment)

## Installation Methods {#installation-methods}

### Method 1: Quick Install (Recommended)

```bash
# Create virtual environment
python -m venv slr-server-env

# Activate virtual environment
# On Windows:
slr-server-env\Scripts\activate
# On macOS/Linux:
source slr-server-env/bin/activate

# Clone repository
git clone https://github.com/your-org/mcp-servers.git
cd mcp-servers/slr-server

# Install package
pip install -e .
```

### Method 2: From PyPI (When Available)

```bash
# Install from PyPI
pip install slr-mcp-server

# Verify installation
slr-mcp-server --version
```

### Method 3: Docker Installation

```bash
# Pull Docker image
docker pull your-org/slr-mcp-server:latest

# Run container
docker run -d \
  --name slr-server \
  -p 8080:8080 \
  -v /path/to/data:/data \
  your-org/slr-mcp-server:latest
```

### Method 4: Development Installation

```bash
# Clone repository
git clone https://github.com/your-org/mcp-servers.git
cd mcp-servers/slr-server

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Configuration {#configuration}

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database configuration
DATABASE_PATH=./slr_database.db
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30

# Server configuration
MCP_PORT=8080
LOG_LEVEL=INFO
MAX_PAPERS_PER_ANALYSIS=100

# Performance settings
ENABLE_CACHING=true
CACHE_SIZE_MB=256
WORKER_PROCESSES=4

# API keys (if needed)
OPENAI_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here
```

### Configuration File

Create `config/server.yaml`:

```yaml
server:
  host: localhost
  port: 8080
  debug: false
  
database:
  path: "./slr_database.db"
  pool_size: 20
  timeout: 30
  enable_wal: true

processing:
  max_papers_per_batch: 50
  chunk_size: 512
  max_workers: 4
  
quality_assessment:
  default_framework: "prisma"
  require_dual_review: true
  inter_rater_threshold: 0.6

citation_analysis:
  max_depth: 3
  cache_results: true
  update_frequency: "weekly"
```

## MCP Integration {#mcp-integration}

### VS Code Setup

1. **Install MCP Extension**:
   ```bash
   code --install-extension mcp-extension
   ```

2. **Create MCP Configuration**:
   
   Create or update `.vscode/mcp.json`:
   ```json
   {
     "mcpServers": {
       "slr-server": {
         "command": "python",
         "args": ["-m", "slr_server"],
         "cwd": "/path/to/slr-server",
         "env": {
           "DATABASE_PATH": "./slr_database.db",
           "LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

3. **Verify Integration**:
   - Open VS Code
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type "MCP: Connect to Server"
   - Select "slr-server"
   - Verify connection in MCP panel

### Claude Desktop Integration

1. **Locate Configuration File**:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add Server Configuration**:
   ```json
   {
     "mcpServers": {
       "slr-server": {
         "command": "python",
         "args": ["-m", "slr_server", "--mcp-mode"],
         "cwd": "/path/to/slr-server",
         "env": {
           "DATABASE_PATH": "./slr_database.db"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

### Custom MCP Client

```python
import asyncio
from mcp_client import MCPClient

async def connect_to_slr_server():
    client = MCPClient()
    await client.connect("slr-server", {
        "command": "python",
        "args": ["-m", "slr_server"],
        "cwd": "/path/to/slr-server"
    })
    
    # Test connection
    tools = await client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    return client

# Usage
client = asyncio.run(connect_to_slr_server())
```

## Database Setup {#database-setup}

### Automatic Setup

The database is created automatically on first run:

```bash
# Run server to create database
python -m slr_server --init-db
```

### Manual Database Creation

```bash
# Create database manually
python -c "
from slr_server.database.schema import create_tables
create_tables('./slr_database.db')
print('Database created successfully')
"
```

### Database Migration

```bash
# Run migrations
python -m slr_server --migrate

# Check migration status
python -m slr_server --migration-status
```

### Custom Database Path

```bash
# Use custom database location
python -m slr_server --database-path /custom/path/slr.db
```

### Database Optimization

```bash
# Optimize database performance
python -m slr_server --optimize-db

# Backup database
python -m slr_server --backup-db backup_$(date +%Y%m%d).db

# Restore from backup
python -m slr_server --restore-db backup_20231014.db
```

## Verification {#verification}

### Basic Verification

```bash
# Check installation
python -m slr_server --version

# Verify dependencies
python -m slr_server --check-deps

# Test database connection
python -m slr_server --test-db
```

### MCP Integration Test

```bash
# Test MCP server
python -c "
import asyncio
from slr_server.server import SLRMCPServer

async def test():
    server = SLRMCPServer()
    tools = await server.list_tools()
    print(f'Available tools: {len(tools)}')
    print(f'Tool names: {[t.name for t in tools]}')

asyncio.run(test())
"
```

### Functional Testing

```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Test with sample paper
python -c "
import asyncio
from slr_server.mcp_handler import SLRMCPHandler

async def test_upload():
    handler = SLRMCPHandler()
    
    # This would require actual paper file
    # result = await handler.upload_paper('/path/to/sample.pdf')
    # print(f'Upload successful: {result.success}')
    
    print('Handler initialized successfully')

asyncio.run(test_upload())
"
```

## Troubleshooting {#troubleshooting}

### Common Issues

#### Issue 1: Python Version Incompatibility

**Symptoms:**
```
ImportError: This package requires Python 3.8 or higher
```

**Solution:**
```bash
# Check Python version
python --version

# Install correct version
# On Windows (using chocolatey):
choco install python --version=3.11.0

# On macOS (using homebrew):
brew install python@3.11

# On Linux (Ubuntu):
sudo apt update
sudo apt install python3.11
```

#### Issue 2: Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'slr_database.db'
```

**Solution:**
```bash
# Fix database permissions
chmod 664 slr_database.db
chown $USER:$USER slr_database.db

# Or create in user directory
mkdir -p ~/.local/share/slr-server
export DATABASE_PATH="$HOME/.local/share/slr-server/slr_database.db"
```

#### Issue 3: MCP Connection Failed

**Symptoms:**
- VS Code shows "MCP Server Error"
- Claude Desktop can't connect to server

**Solution:**
```bash
# Test server standalone
python -m slr_server --test-mode

# Check logs
tail -f ~/.local/share/slr-server/logs/server.log

# Verify configuration
python -c "
import json
with open('.vscode/mcp.json') as f:
    config = json.load(f)
    print('MCP Config:', json.dumps(config, indent=2))
"
```

#### Issue 4: Database Lock Errors

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Check for stale connections
lsof slr_database.db  # On macOS/Linux
# Or kill existing processes:
pkill -f "slr_server"

# Reset database if necessary
mv slr_database.db slr_database.db.backup
python -m slr_server --init-db
```

#### Issue 5: Memory Issues

**Symptoms:**
- Server crashes with large papers
- "Out of memory" errors

**Solution:**
```bash
# Increase memory limits
export PYTHONMEMORY=4096
export MAX_PAPERS_PER_ANALYSIS=10

# Use chunking for large files
python -m slr_server --enable-chunking --chunk-size 256
```

### Performance Tuning

#### For Large Datasets

```bash
# Optimize for large reviews
export DATABASE_CACHE_SIZE=100000
export ENABLE_PARALLEL_PROCESSING=true
export MAX_WORKER_PROCESSES=8

# Use SSD for database
mv slr_database.db /ssd/path/slr_database.db
ln -s /ssd/path/slr_database.db ./slr_database.db
```

#### For Development

```bash
# Enable debug mode
export LOG_LEVEL=DEBUG
export FLASK_DEBUG=true

# Use faster database settings
export DATABASE_SYNCHRONOUS=OFF
export DATABASE_JOURNAL_MODE=MEMORY
```

### Log Analysis

```bash
# View recent logs
tail -f ~/.local/share/slr-server/logs/server.log

# Search for errors
grep -i error ~/.local/share/slr-server/logs/server.log

# Analyze performance
grep -i "processing_time" ~/.local/share/slr-server/logs/server.log | \
  awk '{print $NF}' | sort -n | tail -10
```

### Recovery Procedures

#### Database Recovery

```bash
# Check database integrity
sqlite3 slr_database.db "PRAGMA integrity_check;"

# Repair database
sqlite3 slr_database.db "VACUUM;"

# Restore from backup
cp slr_database.db.backup slr_database.db
python -m slr_server --verify-db
```

#### Configuration Reset

```bash
# Reset to defaults
rm -f config/server.yaml
rm -f .env
python -m slr_server --create-default-config

# Verify configuration
python -m slr_server --validate-config
```

## Security Considerations

### File Permissions

```bash
# Secure database
chmod 600 slr_database.db

# Secure configuration
chmod 600 .env
chmod 600 config/server.yaml
```

### Network Security

```bash
# Bind to localhost only
export MCP_HOST=127.0.0.1

# Use HTTPS in production
export USE_TLS=true
export TLS_CERT_PATH=/path/to/cert.pem
export TLS_KEY_PATH=/path/to/key.pem
```

### API Key Management

```bash
# Store API keys securely
export OPENAI_API_KEY=$(security find-generic-password -s openai -w)  # macOS
export ANTHROPIC_API_KEY=$(pass show anthropic/api_key)  # Linux with pass
```

## Next Steps

After successful installation:

1. **Read the [Research Guide](research-guide.md)** for academic usage
2. **Review [API Reference](api-reference.md)** for technical details
3. **Try [Example Workflows](example-workflows.md)** for practical examples
4. **Join the community** on [GitHub Discussions](https://github.com/your-org/mcp-servers/discussions)

## Support

- **Documentation**: [Full Documentation](./README.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/mcp-servers/issues)
- **Community**: [GitHub Discussions](https://github.com/your-org/mcp-servers/discussions)
- **Email**: support@your-org.com

---

*Last updated: October 14, 2023*