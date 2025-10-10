"""
Updated Study Buddy MCP Server Implementation

This is a refactored version of the MCP server that demonstrates SOLID principles
and dependency injection patterns. It addresses the architectural issues identified
in the SOLID analysis.

Key Improvements:
- Dependency Injection: Uses DI container for service management
- Single Responsibility: Each class has one clear purpose  
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..interfaces.core import IConfigurationManager, ILogger, IContainer
from ..container import ContainerBuilder, get_container
from ..core import StandardLogger


class StudyBuddyMCPServer:
    """
    Main MCP Server implementation using dependency injection.
    
    This class demonstrates proper SOLID principles:
    - SRP: Focused only on MCP server coordination
    - OCP: Extensible through dependency injection
    - LSP: Proper interface implementation
    - ISP: Uses focused interfaces
    - DIP: Depends on abstractions (ILogger, IConfigurationManager, etc.)
    """
    
    def __init__(self, database_path: Optional[str] = None, 
                 container: Optional[IContainer] = None):
        """Initialize server with dependency injection."""
        
        # Use provided container or create default
        self.container = container or self._create_default_container()
        
        # Resolve dependencies through container
        self.logger = self.container.resolve(ILogger)
        self.config_manager = self.container.resolve(IConfigurationManager)
        
        # Configure database path
        if database_path:
            self.config_manager.set_value("database_path", database_path)
        
        self.logger.info("StudyBuddyMCPServer initialized with dependency injection")
        
        # Initialize MCP handler (will be created when needed)
        self.mcp_handler = None
    
    def _create_default_container(self) -> IContainer:
        """Create default dependency injection container."""
        return (ContainerBuilder()
                .with_core_services()
                .with_logging()
                .build())
    
    async def _initialize_dependencies(self) -> None:
        """Initialize all service dependencies."""
        try:
            self.logger.info("Initializing service dependencies...")
            
            # Validate configuration
            if not self.config_manager.validate_configuration():
                self.logger.warning("Configuration validation issues detected")
            
            # Initialize MCP handler when implementations are ready
            # self.mcp_handler = self.container.resolve(IMCPHandler)
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {e}")
            raise
    
    async def run(self) -> None:
        """Run the MCP server."""
        try:
            # Initialize dependencies
            await self._initialize_dependencies()
            
            self.logger.info("Starting MCP server...")
            
            # MCP server implementation will go here
            # For now, this is a placeholder that demonstrates the structure
            
            self.logger.info("MCP server started successfully")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get server health status."""
        try:
            container_health = self.container.health_check()
            config_valid = self.config_manager.validate_configuration()
            
            return {
                "status": "healthy" if container_health["healthy"] and config_valid else "unhealthy",
                "container": container_health,
                "configuration": {
                    "valid": config_valid,
                    "database_path": self.config_manager.get_value("database_path", "not_set")
                },
                "services": {
                    "mcp_handler": self.mcp_handler is not None,
                    "logger": self.logger is not None,
                    "config_manager": self.config_manager is not None
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class StudyBuddyServerFactory:
    """Factory for creating StudyBuddyMCPServer instances."""
    
    @staticmethod
    def create_production_server(config_dir: Optional[Path] = None,
                               database_path: Optional[str] = None) -> StudyBuddyMCPServer:
        """Create production-configured server."""
        container = (ContainerBuilder()
                    .with_configuration(config_dir)
                    .with_core_services()
                    .with_business_services()
                    .with_data_services()
                    .with_security()
                    .with_logging("INFO")
                    .build())
        
        return StudyBuddyMCPServer(database_path=database_path, container=container)
    
    @staticmethod
    def create_test_server(database_path: str = ":memory:") -> StudyBuddyMCPServer:
        """Create test-configured server."""
        container = (ContainerBuilder()
                    .with_core_services()
                    .with_logging("DEBUG")
                    .build())
        
        return StudyBuddyMCPServer(database_path=database_path, container=container)
    
    @staticmethod
    def create_development_server(database_path: Optional[str] = None) -> StudyBuddyMCPServer:
        """Create development-configured server."""
        container = (ContainerBuilder()
                    .with_core_services()
                    .with_logging("DEBUG")
                    .build())
        
        return StudyBuddyMCPServer(database_path=database_path, container=container)