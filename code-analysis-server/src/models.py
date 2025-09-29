"""Data models for MCP server base template.

This module defines the data models used by the MCP server and handler classes.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log levels for server configuration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServerConfig(BaseModel):
    """Server configuration model.

    Attributes:
        log_level: Logging level for the server
        host: Server host address (for future use)
        port: Server port (for future use)
        debug: Enable debug mode
    """
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    debug: bool = Field(False, description="Enable debug mode")


class ErrorResponse(BaseModel):
    """Error response model.

    Attributes:
        error: Main error message
        details: Additional error details
    """
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )