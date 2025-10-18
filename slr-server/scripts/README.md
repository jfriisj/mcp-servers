# Scripts Directory

Utility scripts for SLR server management and operations.

## Available Scripts

### `initialize_database.py`
Initializes the SLR database schema with all required tables and indexes.

**Usage**:
```bash
python scripts/initialize_database.py
```

**Purpose**:
- Creates initial database schema
- Sets up all tables for SLR operations
- Creates necessary indexes

---

### `run_phase3_migration.py`
Runs Phase 3 database migration to add project-based paper management.

**Usage**:
```bash
python scripts/run_phase3_migration.py
```

**Purpose**:
- Adds `project_id` column to research_papers table
- Creates indexes for query performance
- Maintains backward compatibility

---

### `validate_phase3.py`
Validates Phase 3 implementation for completeness and correctness.

**Usage**:
```bash
python scripts/validate_phase3.py
```

**Purpose**:
- Verifies all Phase 3 features implemented
- Checks database schema
- Validates handler implementations
- Tests MCP tools registration

---

## Running Scripts

All scripts should be run from the repository root directory:

```bash
cd slr-server
python scripts/<script_name>.py
```

## Creating New Scripts

When adding new utility scripts:
1. Place them in this directory
2. Include docstring and usage comments
3. Add error handling and logging
4. Update this README

