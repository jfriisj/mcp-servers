"""
Database package for Study Buddy MCP Server.

This package provides database infrastructure following Clean Architecture
Layer 4 principles with SQLite connection management and schema operations.
"""

from .connection import DatabaseConnection
from .schema import SchemaManager, initialize_database

__all__ = ["DatabaseConnection", "SchemaManager", "initialize_database"]
