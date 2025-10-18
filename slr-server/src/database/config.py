"""
Database configuration detector and multi-database support utilities.
Detects PostgreSQL configuration and provides guidance for setup.
"""

import os
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management and detection."""
    
    @staticmethod
    def detect_database_type() -> str:
        """
        Detect which database type to use based on environment variables.
        
        Returns:
            Database type: 'sqlite' or 'postgresql'
        """
        # Check for explicit database type
        db_type = os.getenv("DATABASE_TYPE", "").lower()
        if db_type in ["postgresql", "postgres"]:
            return "postgresql"
            
        # Check for PostgreSQL connection parameters
        if (os.getenv("POSTGRES_HOST") or 
            os.getenv("DATABASE_URL") or 
            os.getenv("POSTGRES_USER")):
            return "postgresql"
            
        # Default to SQLite
        return "sqlite"
    
    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        """
        Get database configuration based on environment variables.
        
        Returns:
            Database configuration dictionary
        """
        db_type = DatabaseConfig.detect_database_type()
        
        if db_type == "postgresql":
            return {
                "type": "postgresql",
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "slr_server"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
            }
        else:
            return {
                "type": "sqlite",
                "path": os.getenv("DATABASE_PATH", "database/slr_database.db")
            }
    
    @staticmethod
    def check_postgresql_availability() -> bool:
        """
        Check if PostgreSQL is configured and available.
        
        Returns:
            True if PostgreSQL is available, False otherwise
        """
        config = DatabaseConfig.get_database_config()
        if config["type"] != "postgresql":
            return False
            
        try:
            import psycopg2
            
            # Try to connect
            conn = psycopg2.connect(
                host=config["host"],
                port=config["port"], 
                database=config["database"],
                user=config["user"],
                password=config["password"],
                connect_timeout=5
            )
            conn.close()
            return True
            
        except ImportError:
            logger.warning("PostgreSQL configured but psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.warning(f"PostgreSQL configured but connection failed: {e}")
            return False
    
    @staticmethod
    def get_setup_guide() -> str:
        """
        Get setup guidance based on current configuration.
        
        Returns:
            Setup guidance text
        """
        config = DatabaseConfig.get_database_config()
        db_type = config["type"]
        
        if db_type == "postgresql":
            if DatabaseConfig.check_postgresql_availability():
                return f"""
✅ PostgreSQL Configuration Detected and Working

Database: {config['database']}
Host: {config['host']}:{config['port']}
User: {config['user']}

PostgreSQL will be used for enhanced performance with large datasets.
Tables will be created automatically on first use.
"""
            else:
                return f"""
⚠️  PostgreSQL Configuration Detected but Not Available

Configuration found:
- Host: {config['host']}:{config['port']}
- Database: {config['database']}
- User: {config['user']}

Setup required:
1. Install PostgreSQL: pip install psycopg2-binary
2. Ensure PostgreSQL server is running
3. Create database: CREATE DATABASE {config['database']};
4. Grant permissions to user

Falling back to SQLite for now.
"""
        else:
            return f"""
✅ SQLite Configuration (Default)

Database file: {config['path']}

SQLite provides excellent performance for development and single-user scenarios.
For large projects with multiple users, consider PostgreSQL configuration:

Environment variables for PostgreSQL:
- DATABASE_TYPE=postgresql
- POSTGRES_HOST=your-host
- POSTGRES_DB=slr_server
- POSTGRES_USER=your-user
- POSTGRES_PASSWORD=your-password
"""
    
    @staticmethod
    def log_configuration():
        """Log current database configuration."""
        config = DatabaseConfig.get_database_config()
        guide = DatabaseConfig.get_setup_guide()
        
        logger.info("Database Configuration:")
        logger.info(guide)
        
        return config


# For backward compatibility and easy access
def get_database_path() -> str:
    """Get database path for SQLite or connection string for PostgreSQL."""
    config = DatabaseConfig.get_database_config()
    
    if config["type"] == "postgresql":
        # Return a connection identifier that existing code can use
        return f"postgresql://{config['user']}@{config['host']}:{config['port']}/{config['database']}"
    else:
        return config["path"]