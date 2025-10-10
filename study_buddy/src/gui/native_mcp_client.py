"""
Native MCP Client for Direct Integration.

This module provides a native MCP client that integrates directly with
Study Buddy MCP Server components without HTTP overhead, bypassing the
MCP library issues while maintaining the same interface as AsyncMCPClient.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import our MCP server components directly
import sys
import os

# Import with error handling for development
try:
    from ..server.container import initialize_application
    from ..server.handlers.mcp_handler import MCPHandler
except ImportError as e:
    # Fallback for development/testing
    logging.getLogger(__name__).warning(f"MCP imports failed: {e}")
    initialize_application = None
    MCPHandler = None


class ConnectionState(Enum):
    """MCP connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class MCPResponse:
    """
    Standardized MCP response container.
    
    Compatible with the existing AsyncMCPClient response format.
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass 
class ConnectionConfig:
    """
    Connection configuration for native MCP client.
    
    Maintains compatibility with AsyncMCPClient but uses direct integration.
    """
    database_path: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    enable_logging: bool = True
    
    # Legacy fields for compatibility (not used in native mode)
    host: str = "localhost"
    port: int = 3000


class MCPConnectionError(Exception):
    """MCP connection-related error."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class MCPTimeoutError(Exception):
    """MCP timeout error.""" 
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class MCPServerError(Exception):
    """MCP server error."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class NativeMCPClient:
    """
    Native MCP Client for direct integration.
    
    This client integrates directly with Study Buddy MCP Server components,
    bypassing HTTP and the problematic MCP library while providing the same
    interface as AsyncMCPClient for drop-in compatibility.
    
    Benefits:
    - No HTTP overhead
    - No MCP library type annotation issues  
    - Direct access to server components
    - Better error handling and debugging
    - Maintains same interface for GUI compatibility
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.logger = logging.getLogger(__name__)
        self._connection_state = ConnectionState.DISCONNECTED
        self._connection_listeners: List[Callable[[ConnectionState], None]] = []
        self._operation_stats: Dict[str, List[float]] = {}
        
        # Native components
        self.container = None
        self.mcp_handler = None  # Will be MCPHandler instance when initialized
        self._initialized = False
    
    def _set_connection_state(self, state: ConnectionState) -> None:
        """Update connection state and notify listeners."""
        if self._connection_state != state:
            self._connection_state = state
            for callback in self._connection_listeners:
                try:
                    callback(state)
                except Exception as e:
                    self.logger.error(f"Error in connection listener: {e}")
    
    def add_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Add callback for connection state changes."""
        self._connection_listeners.append(callback)
    
    def remove_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Remove connection state change callback."""
        if callback in self._connection_listeners:
            self._connection_listeners.remove(callback)
    
    async def connect(self) -> bool:
        """
        Initialize native MCP server components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
            
        self._set_connection_state(ConnectionState.CONNECTING)
        
        try:
            self.logger.info("🔧 Initializing native MCP client...")
            
            # Check if imports are available
            if initialize_application is None or MCPHandler is None:
                raise MCPServerError("MCP server components not available. Run from project root.")
            
            # Initialize application container with all dependencies
            self.container = initialize_application(
                database_path=self.config.database_path,
                environment="production"
            )
            
            # Get MCP handler (fully initialized with all services)
            self.mcp_handler = self.container.get_mcp_handler()
            
            # Test initialization with a simple operation
            test_result = self.mcp_handler.list_documents()
            if not isinstance(test_result, dict):
                raise MCPServerError("MCP handler initialization failed")
            
            self._initialized = True
            self._set_connection_state(ConnectionState.CONNECTED)
            
            self.logger.info("✅ Native MCP client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize native MCP client: {e}")
            self._set_connection_state(ConnectionState.ERROR)
            return False
    
    async def disconnect(self) -> None:
        """Cleanup native MCP components."""
        self._set_connection_state(ConnectionState.DISCONNECTED)
        
        if self.container:
            try:
                self.container.close()
                self.logger.info("✅ Native MCP client disconnected")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
            finally:
                self.container = None
                self.mcp_handler = None
                self._initialized = False
    
    async def is_connected(self) -> bool:
        """Check if native client is initialized."""
        return self._initialized and self._connection_state == ConnectionState.CONNECTED
    
    def _record_operation_time(self, operation: str, time_ms: float) -> None:
        """Record operation timing for performance monitoring."""
        if operation not in self._operation_stats:
            self._operation_stats[operation] = []
        
        self._operation_stats[operation].append(time_ms)
        
        # Keep only last 100 operations
        if len(self._operation_stats[operation]) > 100:
            self._operation_stats[operation] = self._operation_stats[operation][-100:]
    
    def get_operation_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for operations."""
        stats = {}
        for op, times in self._operation_stats.items():
            if times:
                stats[op] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "last_ms": times[-1] if times else 0.0
                }
        return stats
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """
        Call MCP tool directly through native handler.
        
        Args:
            tool_name: Name of the MCP tool to call
            parameters: Tool parameters dictionary  
            timeout: Optional timeout (ignored in native mode)
            
        Returns:
            MCPResponse with tool execution result
            
        Raises:
            MCPConnectionError: If not connected
            MCPTimeoutError: If operation times out (future use)
            MCPServerError: If handler returns error
        """
        if not await self.is_connected():
            raise MCPConnectionError("Native MCP client not connected")
        
        if not self.mcp_handler:
            raise MCPConnectionError("MCP handler not initialized")
        
        start_time = time.time()
        
        try:
            # Get handler method
            if not hasattr(self.mcp_handler, tool_name):
                return MCPResponse(
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                    error_code="TOOL_NOT_FOUND",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            handler_method = getattr(self.mcp_handler, tool_name)
            
            # Call handler directly with parameters
            result = handler_method(**(parameters or {}))
            
            execution_time_ms = (time.time() - start_time) * 1000
            self._record_operation_time(tool_name, execution_time_ms)
            
            # Handler already returns properly formatted dict
            if isinstance(result, dict):
                return MCPResponse(
                    success=result.get("success", True),
                    data=result.get("data", result) if result.get("success") else None,
                    error=result.get("error") if not result.get("success") else None,
                    error_code=result.get("error_code") if not result.get("success") else None,
                    execution_time_ms=execution_time_ms
                )
            else:
                # Unexpected result type
                return MCPResponse(
                    success=False,
                    error=f"Handler returned unexpected type: {type(result)}",
                    error_code="HANDLER_ERROR",
                    execution_time_ms=execution_time_ms
                )
                
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            
            return MCPResponse(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR",
                execution_time_ms=execution_time_ms
            )
    
    # Convenience methods for common operations
    async def list_documents(self, **kwargs) -> MCPResponse:
        """List documents."""
        return await self.call_tool("list_documents", kwargs)
    
    async def upload_document(self, file_path: str, **kwargs) -> MCPResponse:
        """Upload document."""
        params = {"file_path": file_path, **kwargs}
        return await self.call_tool("upload_document", params)
    
    async def get_document(self, document_id: int) -> MCPResponse:
        """Get document by ID."""
        return await self.call_tool("get_document", {"document_id": document_id})
    
    async def delete_document(self, document_id: int) -> MCPResponse:
        """Delete document."""
        return await self.call_tool("delete_document", {"document_id": document_id})
    
    async def search_documents(self, query: str, **kwargs) -> MCPResponse:
        """Search documents."""
        params = {"query": query, **kwargs}
        return await self.call_tool("search_documents", params)
    
    async def index_document(self, document_id: int, strategy: str = "auto") -> MCPResponse:
        """Index document."""
        params = {"document_id": document_id, "strategy": strategy}
        return await self.call_tool("index_document", params)
    
    async def get_document_structure(self, document_id: int) -> MCPResponse:
        """Get document structure."""
        return await self.call_tool("get_document_structure", {"document_id": document_id})
    
    async def get_chunk_content(self, chunk_id: int) -> MCPResponse:
        """Get chunk content."""
        return await self.call_tool("get_chunk_content", {"chunk_id": chunk_id})
    
    async def save_summary(self, **kwargs) -> MCPResponse:
        """Save summary."""
        return await self.call_tool("save_summary", kwargs)
    
    async def get_summaries_for_chunk(self, chunk_id: int) -> MCPResponse:
        """Get summaries for chunk.""" 
        return await self.call_tool("get_summaries_for_chunk", {"chunk_id": chunk_id})
    
    async def get_summaries_for_document(self, document_id: int) -> MCPResponse:
        """Get summaries for document."""
        return await self.call_tool("get_summaries_for_document", {"document_id": document_id})


# Compatibility alias
AsyncMCPClient = NativeMCPClient


def create_native_mcp_client(
    database_path: Optional[str] = None,
    **kwargs
) -> NativeMCPClient:
    """
    Factory function for creating native MCP client.
    
    Args:
        database_path: Optional path to database file
        **kwargs: Additional configuration options
        
    Returns:
        Configured NativeMCPClient instance
    """
    config = ConnectionConfig(
        database_path=database_path,
        **kwargs
    )
    return NativeMCPClient(config)