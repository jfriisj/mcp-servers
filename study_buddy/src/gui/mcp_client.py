"""
MCP Client Foundation for Study Buddy GUI Application.

This module provides the abstract MCP client interface and async implementation
for communicating with the Study Buddy MCP Server. It handles connection pooling,
retry logic, and comprehensive error handling following Clean Architecture principles.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import aiohttp
import time


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
    
    Encapsulates all MCP tool responses with consistent structure
    for error handling and result processing.
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
    """MCP connection configuration settings."""
    host: str = "localhost"
    port: int = 3000
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 10.0
    connection_pool_size: int = 5
    keepalive_interval: float = 30.0


class MCPConnectionError(Exception):
    """Exception raised for MCP connection issues."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error


class MCPTimeoutError(MCPConnectionError):
    """Exception raised for MCP operation timeouts."""
    pass


class MCPServerError(MCPConnectionError):
    """Exception raised for MCP server-side errors."""
    pass


class MCPClient(ABC):
    """
    Abstract MCP Client interface.
    
    Defines the contract for MCP protocol communication following
    Dependency Inversion Principle. All GUI components depend on
    this abstraction rather than concrete implementations.
    
    This interface ensures:
    - Consistent error handling across all MCP operations
    - Testability through mock implementations
    - Future extensibility for different MCP transport layers
    - Proper separation of concerns between GUI and protocol layers
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if client is connected to MCP server."""
        pass
    
    @abstractmethod
    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """
        Call an MCP tool with parameters.
        
        Args:
            tool_name: Name of the MCP tool to call
            parameters: Tool parameters dictionary
            timeout: Optional timeout override
            
        Returns:
            MCPResponse with tool execution result
            
        Raises:
            MCPConnectionError: If not connected or connection fails
            MCPTimeoutError: If operation times out
            MCPServerError: If server returns an error
        """
        pass
    
    @abstractmethod
    def add_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """
        Add callback for connection state changes.
        
        Args:
            callback: Function to call with new ConnectionState
        """
        pass
    
    @abstractmethod
    def remove_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Remove connection state change callback."""
        pass
    
    # Document Management Tools
    @abstractmethod
    async def upload_document(self, file_path: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> MCPResponse:
        """Upload and parse a document."""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: int) -> MCPResponse:
        """Retrieve document by ID."""
        pass
    
    @abstractmethod
    async def list_documents(self, filters: Optional[Dict[str, Any]] = None, limit: int = 20) -> MCPResponse:
        """List documents with optional filters."""
        pass
    
    @abstractmethod
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20) -> MCPResponse:
        """Search documents using full-text search."""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: int) -> MCPResponse:
        """Delete a document and all related data."""
        pass
    
    # Document Structure Tools
    @abstractmethod
    async def index_document(self, document_id: int, strategy: str = "auto") -> MCPResponse:
        """Create chunks from document."""
        pass
    
    @abstractmethod
    async def get_document_structure(self, document_id: int) -> MCPResponse:
        """Get document structure (chunks/chapters)."""
        pass
    
    @abstractmethod
    async def get_chunk_content(self, chunk_id: int) -> MCPResponse:
        """Retrieve specific chunk text content."""
        pass
    
    # Summary Management Tools
    @abstractmethod
    async def get_summary(self, chunk_id: Optional[int] = None, document_id: Optional[int] = None, summary_type: str = "standard") -> MCPResponse:
        """Retrieve existing summary."""
        pass
    
    @abstractmethod
    async def save_summary(
        self, 
        summary_content: str, 
        summary_type: str = "standard",
        chunk_id: Optional[int] = None, 
        document_id: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> MCPResponse:
        """Store AI-generated summary."""
        pass
    
    @abstractmethod
    async def list_summaries(self, document_id: Optional[int] = None, chunk_id: Optional[int] = None) -> MCPResponse:
        """List summaries for document or chunk."""
        pass


class ConnectionManager:
    """
    Manages MCP server connection lifecycle and health monitoring.
    
    Handles connection pooling, automatic reconnection, and health checks
    following Single Responsibility Principle.
    """
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_activity = datetime.now()
        self.reconnect_attempts = 0
        self.logger = logging.getLogger(__name__)
        self.connection_listeners: List[Callable[[ConnectionState], None]] = []
        self._keepalive_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        try:
            self._set_state(ConnectionState.CONNECTING)
            
            # Create aiohttp session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                keepalive_timeout=self.config.keepalive_interval
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Test connection with health check
            health_response = await self._health_check()
            
            if health_response:
                self._set_state(ConnectionState.CONNECTED)
                self.reconnect_attempts = 0
                self.last_activity = datetime.now()
                
                # Start keepalive task
                self._keepalive_task = asyncio.create_task(self._keepalive_loop())
                
                self.logger.info(f"Connected to MCP server at {self.config.host}:{self.config.port}")
                return True
            else:
                await self.disconnect()
                self._set_state(ConnectionState.ERROR)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {str(e)}")
            await self.disconnect()
            self._set_state(ConnectionState.ERROR)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        self._set_state(ConnectionState.DISCONNECTED)
        
        # Cancel keepalive task
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        
        # Close session
        if self.session and not self.session.closed:
            await self.session.close()
        
        self.session = None
        self.logger.info("Disconnected from MCP server")
    
    async def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return (
            self.state == ConnectionState.CONNECTED and
            self.session is not None and 
            not self.session.closed
        )
    
    async def _health_check(self) -> bool:
        """Perform health check against MCP server."""
        try:
            if self.session is None:
                return False
            url = f"http://{self.config.host}:{self.config.port}/health"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {str(e)}")
            return False
    
    async def _keepalive_loop(self) -> None:
        """Background task for connection keepalive."""
        while await self.is_connected():
            try:
                await asyncio.sleep(self.config.keepalive_interval)
                
                # Check if connection is still healthy
                if not await self._health_check():
                    self.logger.warning("Keepalive health check failed, attempting reconnection")
                    await self._attempt_reconnection()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Keepalive error: {str(e)}")
                await self._attempt_reconnection()
    
    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to MCP server."""
        self._set_state(ConnectionState.RECONNECTING)
        
        while self.reconnect_attempts < self.config.max_retries:
            self.reconnect_attempts += 1
            
            # Calculate exponential backoff delay
            delay = min(
                self.config.retry_delay * (2 ** (self.reconnect_attempts - 1)),
                self.config.max_retry_delay
            )
            
            self.logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.config.max_retries} in {delay}s")
            await asyncio.sleep(delay)
            
            if await self.connect():
                return
        
        # All reconnection attempts failed
        self.logger.error("All reconnection attempts failed")
        self._set_state(ConnectionState.ERROR)
    
    def _set_state(self, new_state: ConnectionState) -> None:
        """Set connection state and notify listeners."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.debug(f"Connection state changed: {old_state} -> {new_state}")
            
            # Notify all listeners
            for listener in self.connection_listeners:
                try:
                    listener(new_state)
                except Exception as e:
                    self.logger.error(f"Connection listener error: {str(e)}")
    
    def add_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Add connection state change listener."""
        if callback not in self.connection_listeners:
            self.connection_listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Remove connection state change listener."""
        if callback in self.connection_listeners:
            self.connection_listeners.remove(callback)


class AsyncMCPClient(MCPClient):
    """
    Asynchronous MCP Client implementation.
    
    Provides robust MCP server communication with:
    - Connection pooling and management
    - Automatic retry logic with exponential backoff
    - Comprehensive error handling and recovery
    - Performance monitoring and timeout management
    - Event-driven connection state management
    
    This implementation follows Clean Architecture Layer 1 principles:
    - Depends only on abstractions (MCPClient interface)
    - Handles external protocol concerns
    - Provides clean interface for GUI components
    - Isolates network and protocol complexities
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.connection_manager = ConnectionManager(self.config)
        self.logger = logging.getLogger(__name__)
        self._operation_stats: Dict[str, List[float]] = {}
    
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        return await self.connection_manager.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        await self.connection_manager.disconnect()
    
    async def is_connected(self) -> bool:
        """Check if client is connected to MCP server."""
        return await self.connection_manager.is_connected()
    
    def add_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Add callback for connection state changes."""
        self.connection_manager.add_listener(callback)
    
    def remove_connection_listener(self, callback: Callable[[ConnectionState], None]) -> None:
        """Remove connection state change callback."""
        self.connection_manager.remove_listener(callback)
    
    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """
        Call an MCP tool with comprehensive error handling and retry logic.
        
        Args:
            tool_name: Name of the MCP tool to call
            parameters: Tool parameters dictionary
            timeout: Optional timeout override
            
        Returns:
            MCPResponse with tool execution result
            
        Raises:
            MCPConnectionError: If not connected or connection fails
            MCPTimeoutError: If operation times out
            MCPServerError: If server returns an error
        """
        if not await self.is_connected():
            raise MCPConnectionError("Not connected to MCP server")
        
        start_time = time.time()
        operation_timeout = timeout or self.config.timeout
        
        try:
            # Prepare request payload
            payload = {
                "tool": tool_name,
                "parameters": parameters or {}
            }
            
            # Make request with retry logic
            for attempt in range(self.config.max_retries + 1):
                try:
                    url = f"http://{self.config.host}:{self.config.port}/mcp/call"
                    
                    if self.connection_manager.session is None:
                        raise MCPConnectionError("Session not initialized")
                    
                    async with self.connection_manager.session.post(
                        url, 
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=operation_timeout)
                    ) as response:
                        
                        execution_time = (time.time() - start_time) * 1000
                        
                        # Track operation performance
                        self._record_operation_time(tool_name, execution_time)
                        
                        # Parse response
                        if response.content_type == 'application/json':
                            data = await response.json()
                        else:
                            data = {"raw_response": await response.text()}
                        
                        # Handle different response status codes
                        if response.status == 200:
                            return MCPResponse(
                                success=True,
                                data=data,
                                execution_time_ms=execution_time
                            )
                        elif response.status == 400:
                            return MCPResponse(
                                success=False,
                                error=data.get("error", "Bad request"),
                                error_code="BAD_REQUEST",
                                execution_time_ms=execution_time
                            )
                        elif response.status == 404:
                            return MCPResponse(
                                success=False,
                                error=f"Tool '{tool_name}' not found",
                                error_code="TOOL_NOT_FOUND",
                                execution_time_ms=execution_time
                            )
                        elif response.status >= 500:
                            # Server error - retry
                            if attempt < self.config.max_retries:
                                retry_delay = self.config.retry_delay * (2 ** attempt)
                                self.logger.warning(f"Server error (status {response.status}), retrying in {retry_delay}s")
                                await asyncio.sleep(retry_delay)
                                continue
                            else:
                                raise MCPServerError(
                                    f"Server error: {response.status}",
                                    error_code="SERVER_ERROR"
                                )
                        else:
                            return MCPResponse(
                                success=False,
                                error=f"Unexpected response status: {response.status}",
                                error_code="UNEXPECTED_STATUS",
                                execution_time_ms=execution_time
                            )
                
                except asyncio.TimeoutError:
                    if attempt < self.config.max_retries:
                        self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                        continue
                    else:
                        raise MCPTimeoutError(
                            f"Operation '{tool_name}' timed out after {operation_timeout}s",
                            error_code="TIMEOUT"
                        )
                
                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries:
                        retry_delay = self.config.retry_delay * (2 ** attempt)
                        self.logger.warning(f"Connection error: {str(e)}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise MCPConnectionError(
                            f"Connection error: {str(e)}",
                            error_code="CONNECTION_ERROR",
                            original_error=e
                        )
            
            # This should never be reached, but add return for type safety
            return MCPResponse(
                success=False,
                error="All retry attempts exhausted",
                error_code="RETRY_EXHAUSTED"
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            if isinstance(e, (MCPConnectionError, MCPTimeoutError, MCPServerError)):
                raise
            else:
                self.logger.error(f"Unexpected error calling tool '{tool_name}': {str(e)}")
                raise MCPConnectionError(
                    f"Unexpected error: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    original_error=e
                )
    
    def _record_operation_time(self, tool_name: str, execution_time_ms: float) -> None:
        """Record operation execution time for performance monitoring."""
        if tool_name not in self._operation_stats:
            self._operation_stats[tool_name] = []
        
        stats = self._operation_stats[tool_name]
        stats.append(execution_time_ms)
        
        # Keep only last 100 measurements
        if len(stats) > 100:
            stats.pop(0)
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all operations."""
        stats = {}
        
        for tool_name, times in self._operation_stats.items():
            if times:
                stats[tool_name] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "last_ms": times[-1]
                }
        
        return stats
    
    # Document Management Tool Implementations
    async def upload_document(self, file_path: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> MCPResponse:
        """Upload and parse a document."""
        parameters: Dict[str, Any] = {"file_path": file_path}
        if title:
            parameters["title"] = title
        if tags:
            parameters["tags"] = tags
        
        return await self.call_tool("upload_document", parameters)
    
    async def get_document(self, document_id: int) -> MCPResponse:
        """Retrieve document by ID."""
        return await self.call_tool("get_document", {"document_id": document_id})
    
    async def list_documents(self, filters: Optional[Dict[str, Any]] = None, limit: int = 20) -> MCPResponse:
        """List documents with optional filters."""
        parameters: Dict[str, Any] = {"limit": limit}
        if filters:
            parameters["filters"] = filters
        
        return await self.call_tool("list_documents", parameters)
    
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20) -> MCPResponse:
        """Search documents using full-text search."""
        parameters: Dict[str, Any] = {"query": query, "limit": limit}
        if filters:
            parameters["filters"] = filters
        
        return await self.call_tool("search_documents", parameters)
    
    async def delete_document(self, document_id: int) -> MCPResponse:
        """Delete a document and all related data."""
        return await self.call_tool("delete_document", {"document_id": document_id})
    
    # Document Structure Tool Implementations
    async def index_document(self, document_id: int, strategy: str = "auto") -> MCPResponse:
        """Create chunks from document."""
        return await self.call_tool("index_document", {
            "document_id": document_id,
            "strategy": strategy
        })
    
    async def get_document_structure(self, document_id: int) -> MCPResponse:
        """Get document structure (chunks/chapters)."""
        return await self.call_tool("get_document_structure", {"document_id": document_id})
    
    async def get_chunk_content(self, chunk_id: int) -> MCPResponse:
        """Retrieve specific chunk text content."""
        return await self.call_tool("get_chunk_content", {"chunk_id": chunk_id})
    
    # Summary Management Tool Implementations
    async def get_summary(self, chunk_id: Optional[int] = None, document_id: Optional[int] = None, summary_type: str = "standard") -> MCPResponse:
        """Retrieve existing summary."""
        parameters: Dict[str, Any] = {"summary_type": summary_type}
        if chunk_id is not None:
            parameters["chunk_id"] = chunk_id
        if document_id is not None:
            parameters["document_id"] = document_id
        
        return await self.call_tool("get_summary", parameters)
    
    async def save_summary(
        self, 
        summary_content: str, 
        summary_type: str = "standard",
        chunk_id: Optional[int] = None, 
        document_id: Optional[int] = None,
        model_name: Optional[str] = None
    ) -> MCPResponse:
        """Store AI-generated summary."""
        parameters: Dict[str, Any] = {
            "summary_content": summary_content,
            "summary_type": summary_type
        }
        if chunk_id is not None:
            parameters["chunk_id"] = chunk_id
        if document_id is not None:
            parameters["document_id"] = document_id
        if model_name:
            parameters["model_name"] = model_name
        
        return await self.call_tool("save_summary", parameters)
    
    async def list_summaries(self, document_id: Optional[int] = None, chunk_id: Optional[int] = None) -> MCPResponse:
        """List summaries for document or chunk."""
        parameters: Dict[str, Any] = {}
        if document_id is not None:
            parameters["document_id"] = document_id
        if chunk_id is not None:
            parameters["chunk_id"] = chunk_id
        
        return await self.call_tool("list_summaries", parameters)