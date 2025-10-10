"""
Core Interfaces for Study Buddy Application

These interfaces define the fundamental contracts for core system components.
All concrete implementations should implement these interfaces to ensure
proper dependency inversion and testability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncContextManager
from pathlib import Path
import logging


class ILogger(ABC):
    """Interface for logging operations."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management operations."""
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    def load_configuration(self, source: Union[str, Path, Dict]) -> None:
        """Load configuration from source."""
        pass
    
    @abstractmethod
    def save_configuration(self, target: Union[str, Path]) -> None:
        """Save configuration to target."""
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate current configuration."""
        pass


class ISecurityManager(ABC):
    """Interface for security operations."""
    
    @abstractmethod
    def validate_input(self, input_data: str, validation_type: str) -> bool:
        """Validate input data for security."""
        pass
    
    @abstractmethod
    def sanitize_data(self, data: Any) -> Any:
        """Sanitize data for safe processing."""
        pass
    
    @abstractmethod
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for action on resource."""
        pass
    
    @abstractmethod
    def encrypt_data(self, data: bytes, key: Optional[str] = None) -> bytes:
        """Encrypt sensitive data."""
        pass
    
    @abstractmethod
    def decrypt_data(self, encrypted_data: bytes, key: Optional[str] = None) -> bytes:
        """Decrypt sensitive data."""
        pass


class IStorageProvider(ABC):
    """Interface for data storage operations."""
    
    @abstractmethod
    async def store(self, key: str, data: Any) -> bool:
        """Store data with given key."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data by key."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete data by key."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix filter."""
        pass


class IDocumentProcessor(ABC):
    """Interface for document processing operations."""
    
    @abstractmethod
    async def process_document(self, file_path: Path, document_id: str) -> Dict[str, Any]:
        """Process a document and return metadata."""
        pass
    
    @abstractmethod
    async def extract_text(self, file_path: Path) -> str:
        """Extract text content from document."""
        pass
    
    @abstractmethod
    async def chunk_document(self, text: str, strategy: str = "auto") -> List[Dict[str, Any]]:
        """Chunk document into smaller pieces."""
        pass
    
    @abstractmethod
    async def analyze_document(self, text: str) -> Dict[str, Any]:
        """Analyze document and return insights."""
        pass


class IMCPClient(ABC):
    """Interface for MCP client operations."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish MCP connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close MCP connection."""
        pass
    
    @abstractmethod
    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool with given parameters."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """Get client health status."""
        pass


class IContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def register_singleton(self, interface: type, implementation: type) -> None:
        """Register a singleton service."""
        pass
    
    @abstractmethod
    def register_transient(self, interface: type, implementation: type) -> None:
        """Register a transient service."""
        pass
    
    @abstractmethod
    def register_factory(self, interface: type, factory_func: callable) -> None:
        """Register a factory function for creating instances."""
        pass
    
    @abstractmethod
    def resolve(self, interface: type) -> Any:
        """Resolve an instance of the given interface."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform container health check."""
        pass