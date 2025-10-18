# Configuration - Requirements

Alternative and development dependencies for the SLR server.

## Files

### `dev-requirements.txt`
Development dependencies including:
- **Linting**: pylint, ruff, black
- **Type Checking**: mypy
- **Testing**: pytest, pytest-cov
- **Documentation**: sphinx
- **Utilities**: ipython

**Installation**:
```bash
pip install -r config/requirements/dev-requirements.txt
```

### `requirements-postgresql.txt`
PostgreSQL-specific dependencies (alternative to SQLite):
- PostgreSQL driver (psycopg2)
- SQLAlchemy PostgreSQL support

**Installation**:
```bash
pip install -r config/requirements/requirements-postgresql.txt
```

---

## Main Requirements

The main `requirements.txt` at repository root contains:
- Core dependencies
- MCP server packages
- PDF processing
- Database access
- Logging and utilities

---

## Usage Examples

### Development Setup
```bash
# Install main dependencies
pip install -r requirements.txt

# Add development tools
pip install -r config/requirements/dev-requirements.txt
```

### PostgreSQL Setup
```bash
# Install main dependencies
pip install -r requirements.txt

# Add PostgreSQL support
pip install -r config/requirements/requirements-postgresql.txt
```

### Production Setup
```bash
# Just install main requirements
pip install -r requirements.txt
```

---

## Adding New Requirements

1. For development tools: Add to `dev-requirements.txt`
2. For database alternatives: Add to `requirements-postgresql.txt` (or create new file)
3. For core features: Add to main `requirements.txt` at repository root

