#!/usr/bin/env python3
"""
Initialize the SLR database schema

This script creates all necessary tables in the database.
Run this before running any tests or using the MCP server.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager


def initialize_database(db_path: str = "database/slr_database.db"):
    """Initialize the database with all tables"""
    print("=" * 80)
    print("Initializing SLR Database Schema")
    print("=" * 80)
    print()
    
    # Resolve path
    db_file = Path(db_path)
    print(f"Database file: {db_file.absolute()}")
    print()
    
    # Create database directory if needed
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    print("1️⃣ Connecting to database...")
    db = DatabaseConnection(str(db_file))
    print(f"✅ Connected to: {db_file}")
    print()
    
    # Initialize schema
    print("2️⃣ Creating database schema...")
    schema_manager = SchemaManager(db)
    schema_manager.initialize_schema()
    print("✅ Schema created successfully")
    print()
    
    # List created tables
    print("3️⃣ Verifying tables...")
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Created {len(tables)} tables:")
    for table in tables:
        cursor = db.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   ✅ {table} ({count} rows)")
    print()
    
    print("=" * 80)
    print("✅ Database initialization complete!")
    print("=" * 80)
    print()
    print("You can now run the Phase 2 manual test:")
    print("  python test_phase2_manual.py")
    print()


if __name__ == "__main__":
    initialize_database()
