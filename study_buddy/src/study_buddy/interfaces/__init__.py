"""
Study Buddy Interfaces Module

This module contains all the interface definitions for the Study Buddy application.
These interfaces define contracts that concrete implementations must follow,
enabling dependency inversion and making the system more testable and maintainable.

Core Interfaces:
- IMCPClient: MCP client operations
- IConfigurationManager: Configuration management
- ISecurityManager: Security operations
- IStorageProvider: Data storage operations
- IDocumentProcessor: Document processing operations
- ILogger: Logging operations
"""

from .core import (
    IMCPClient,
    IConfigurationManager,
    ISecurityManager,
    IStorageProvider,
    IDocumentProcessor,
    ILogger,
    IContainer
)

from .services import (
    IDocumentService,
    ISearchService,
    ISummaryService,
    IAnalyticsService
)

from .repositories import (
    IDocumentRepository,
    IChunkRepository,
    ISummaryRepository,
    IUserRepository
)

__all__ = [
    # Core interfaces
    "IMCPClient",
    "IConfigurationManager", 
    "ISecurityManager",
    "IStorageProvider",
    "IDocumentProcessor",
    "ILogger",
    "IContainer",
    
    # Service interfaces
    "IDocumentService",
    "ISearchService", 
    "ISummaryService",
    "IAnalyticsService",
    
    # Repository interfaces
    "IDocumentRepository",
    "IChunkRepository",
    "ISummaryRepository",
    "IUserRepository"
]