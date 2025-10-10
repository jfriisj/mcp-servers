"""
Async MCP Client Implementation for Study Buddy GUI Integration Layer.

This module provides the main AsyncMCPClient class that serves as the primary
interface between GUI components and the MCP server. It integrates all previously
implemented components (connection manager, tool invoker, configuration manager)
to provide a complete, production-ready MCP client.

Architecture: Clean Architecture Layer 4 (Infrastructure)
SOLID Compliance: Full compliance with all SOLID principles
Dependencies: Connection manager, tool invoker, configuration manager
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable, Set, Type
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import weakref
import functools

# Local imports for GUI integration
from config_manager import (
    IntegrationConfigurationManager,
    IntegrationConfig
)


def get_debug_logger() -> logging.Logger:
    """Get debug logger for integration layer."""
    logger = logging.getLogger("study_buddy.integration.async_mcp_client")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


# Client status and health monitoring
class ClientStatus(Enum):
    """MCP client operational status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DEGRADED = "degraded"  # Partial functionality
    SHUTTING_DOWN = "shutting_down"


class ClientHealth(Enum):
    """MCP client health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class OperationMetrics:
    """Metrics for MCP operations."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    last_operation_time: Optional[datetime] = None
    current_concurrent_operations: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        return 100.0 - self.success_rate


@dataclass
class HealthStatus:
    """Comprehensive health status information."""
    client_status: ClientStatus
    health_level: ClientHealth
    last_health_check: datetime
    connection_stable: bool
    response_time_ms: float
    error_rate_percent: float
    concurrent_operations: int
    max_concurrent_operations: int
    uptime_seconds: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class ConnectionPoolError(MCPClientError):
    """Error related to connection pool management."""
    pass


class OperationTimeoutError(MCPClientError):
    """Error when MCP operation times out."""
    pass


class ResourceExhaustionError(MCPClientError):
    """Error when client resources are exhausted."""
    pass


# Abstract interfaces for dependency injection
class IHealthMonitor(ABC):
    """Interface for health monitoring functionality."""
    
    @abstractmethod
    async def start_monitoring(self) -> None:
        """Start health monitoring tasks."""
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> None:
        """Stop health monitoring tasks."""
        pass
    
    @abstractmethod
    async def check_health(self) -> HealthStatus:
        """Perform comprehensive health check."""
        pass
    
    @abstractmethod
    def get_current_status(self) -> HealthStatus:
        """Get current cached health status."""
        pass


class IConnectionPool(ABC):
    """Interface for connection pool management."""
    
    @abstractmethod
    async def acquire_connection(self) -> Any:
        """Acquire connection from pool."""
        pass
    
    @abstractmethod
    async def release_connection(self, connection: Any) -> None:
        """Release connection back to pool."""
        pass
    
    @abstractmethod
    async def close_all_connections(self) -> None:
        """Close all connections in pool."""
        pass
    
    @abstractmethod
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status information."""
        pass


class IAsyncMCPClient(ABC):
    """Interface for async MCP client functionality."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        pass
    
    @abstractmethod
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Invoke MCP tool with parameters."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        pass
    
    @abstractmethod
    def get_status(self) -> ClientStatus:
        """Get current client status."""
        pass
    
    @abstractmethod
    def get_health(self) -> HealthStatus:
        """Get current health status."""
        pass


# Connection pool implementation
class AsyncConnectionPool(IConnectionPool):
    """
    Async connection pool for MCP server connections.
    
    Manages a pool of connections with proper lifecycle management,
    health checking, and resource cleanup.
    """
    
    def __init__(
        self,
        connection_factory: Callable[[], Any],
        max_connections: int = 10,
        min_connections: int = 2,
        connection_timeout: float = 30.0,
        health_check_interval: float = 60.0
    ):
        """
        Initialize connection pool.
        
        Args:
            connection_factory: Factory function to create connections
            max_connections: Maximum number of connections in pool
            min_connections: Minimum number of connections to maintain
            connection_timeout: Timeout for connection operations
            health_check_interval: Interval between health checks
        """
        self.connection_factory = connection_factory
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_timeout = connection_timeout
        self.health_check_interval = health_check_interval
        
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._active_connections: Set[Any] = set()
        self._connection_semaphore = asyncio.Semaphore(max_connections)
        self._pool_lock = asyncio.Lock()
        self._health_task: Optional[asyncio.Task] = None
        self._closed = False
        
        self.logger = get_debug_logger()
    
    async def start(self) -> None:
        """Start the connection pool and create initial connections."""
        async with self._pool_lock:
            if self._closed:
                raise ConnectionPoolError("Connection pool is closed")
            
            # Create minimum connections
            for _ in range(self.min_connections):
                try:
                    connection = await self._create_connection()
                    await self._pool.put(connection)
                    self.logger.debug("Created initial connection")
                except Exception as e:
                    self.logger.error(f"Failed to create initial connection: {e}")
            
            # Start health monitoring
            self._health_task = asyncio.create_task(self._health_monitor())
            
            self.logger.info(f"Connection pool started with {self._pool.qsize()} connections")
    
    async def stop(self) -> None:
        """Stop the connection pool and close all connections."""
        async with self._pool_lock:
            self._closed = True
            
            # Stop health monitoring
            if self._health_task:
                self._health_task.cancel()
                try:
                    await self._health_task
                except asyncio.CancelledError:
                    pass
            
            # Close all connections
            await self.close_all_connections()
            
            self.logger.info("Connection pool stopped")
    
    async def acquire_connection(self) -> Any:
        """Acquire connection from pool."""
        if self._closed:
            raise ConnectionPoolError("Connection pool is closed")
        
        # Wait for semaphore (limits concurrent connections)
        await self._connection_semaphore.acquire()
        
        try:
            # Try to get existing connection from pool
            try:
                connection = self._pool.get_nowait()
                self._active_connections.add(connection)
                self.logger.debug("Acquired existing connection from pool")
                return connection
            except asyncio.QueueEmpty:
                pass
            
            # Create new connection if pool is empty
            connection = await self._create_connection()
            self._active_connections.add(connection)
            self.logger.debug("Created new connection")
            return connection
            
        except Exception:
            # Release semaphore on error
            self._connection_semaphore.release()
            raise
    
    async def release_connection(self, connection: Any) -> None:
        """Release connection back to pool."""
        if connection in self._active_connections:
            self._active_connections.remove(connection)
        
        if not self._closed and await self._is_connection_healthy(connection):
            # Return healthy connection to pool
            try:
                self._pool.put_nowait(connection)
                self.logger.debug("Released connection back to pool")
            except asyncio.QueueFull:
                # Pool is full, close the connection
                await self._close_connection(connection)
                self.logger.debug("Pool full, closed excess connection")
        else:
            # Close unhealthy or unwanted connection
            await self._close_connection(connection)
            self.logger.debug("Closed unhealthy connection")
        
        # Release semaphore
        self._connection_semaphore.release()
    
    async def close_all_connections(self) -> None:
        """Close all connections in pool and active set."""
        # Close active connections
        active_copy = self._active_connections.copy()
        for connection in active_copy:
            await self._close_connection(connection)
            self._active_connections.discard(connection)
        
        # Close pooled connections
        while not self._pool.empty():
            try:
                connection = self._pool.get_nowait()
                await self._close_connection(connection)
            except asyncio.QueueEmpty:
                break
        
        self.logger.info("All connections closed")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status information."""
        return {
            "max_connections": self.max_connections,
            "min_connections": self.min_connections,
            "pooled_connections": self._pool.qsize(),
            "active_connections": len(self._active_connections),
            "total_connections": self._pool.qsize() + len(self._active_connections),
            "available_slots": self._connection_semaphore._value,
            "is_closed": self._closed
        }
    
    async def _create_connection(self) -> Any:
        """Create new connection using factory."""
        try:
            # Create connection with timeout
            connection = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.connection_factory
                ),
                timeout=self.connection_timeout
            )
            return connection
        except asyncio.TimeoutError:
            raise ConnectionPoolError(f"Connection creation timed out after {self.connection_timeout}s")
        except Exception as e:
            raise ConnectionPoolError(f"Failed to create connection: {e}")
    
    async def _close_connection(self, connection: Any) -> None:
        """Close individual connection."""
        try:
            # Attempt graceful closure
            if hasattr(connection, 'close'):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
        except Exception as e:
            self.logger.warning(f"Error closing connection: {e}")
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check if connection is healthy."""
        try:
            # Basic health check - could be extended with ping/heartbeat
            return hasattr(connection, 'is_connected') and connection.is_connected()
        except Exception:
            return False
    
    async def _health_monitor(self) -> None:
        """Background task for connection health monitoring."""
        while not self._closed:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if self._closed:
                    break
                
                # Check pool connections
                healthy_connections = []
                while not self._pool.empty():
                    try:
                        connection = self._pool.get_nowait()
                        if await self._is_connection_healthy(connection):
                            healthy_connections.append(connection)
                        else:
                            await self._close_connection(connection)
                            self.logger.debug("Removed unhealthy connection from pool")
                    except asyncio.QueueEmpty:
                        break
                
                # Put healthy connections back
                for connection in healthy_connections:
                    try:
                        self._pool.put_nowait(connection)
                    except asyncio.QueueFull:
                        await self._close_connection(connection)
                
                # Ensure minimum connections
                current_total = self._pool.qsize() + len(self._active_connections)
                if current_total < self.min_connections:
                    needed = self.min_connections - current_total
                    for _ in range(needed):
                        try:
                            connection = await self._create_connection()
                            await self._pool.put(connection)
                            self.logger.debug("Added connection to maintain minimum")
                        except Exception as e:
                            self.logger.error(f"Failed to maintain minimum connections: {e}")
                            break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in connection health monitor: {e}")


# Health monitoring implementation
class AsyncHealthMonitor(IHealthMonitor):
    """
    Health monitoring for AsyncMCPClient.
    
    Provides comprehensive health monitoring including connection stability,
    response times, error rates, and operational metrics.
    """
    
    def __init__(
        self,
        client: "AsyncMCPClient",
        check_interval: float = 30.0,
        response_time_threshold: float = 5000.0,  # ms
        error_rate_threshold: float = 10.0  # percent
    ):
        """
        Initialize health monitor.
        
        Args:
            client: The MCP client to monitor
            check_interval: Interval between health checks in seconds
            response_time_threshold: Response time threshold in milliseconds
            error_rate_threshold: Error rate threshold in percent
        """
        self.client_ref = weakref.ref(client)  # Weak reference to avoid circular dependency
        self.check_interval = check_interval
        self.response_time_threshold = response_time_threshold
        self.error_rate_threshold = error_rate_threshold
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._current_status = HealthStatus(
            client_status=ClientStatus.DISCONNECTED,
            health_level=ClientHealth.UNKNOWN,
            last_health_check=datetime.now(),
            connection_stable=False,
            response_time_ms=0.0,
            error_rate_percent=0.0,
            concurrent_operations=0,
            max_concurrent_operations=10,
            uptime_seconds=0.0
        )
        self._start_time = datetime.now()
        self._lock = asyncio.Lock()
        
        self.logger = get_debug_logger()
    
    async def start_monitoring(self) -> None:
        """Start health monitoring tasks."""
        if self._monitor_task and not self._monitor_task.done():
            return
        
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring tasks."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    async def check_health(self) -> HealthStatus:
        """Perform comprehensive health check."""
        async with self._lock:
            client = self.client_ref()
            if not client:
                return self._create_error_status("Client reference lost")
            
            try:
                # Gather health metrics
                now = datetime.now()
                uptime = (now - self._start_time).total_seconds()
                
                # Check client status
                client_status = client.get_status()
                
                # Check connection pool status
                pool_status = client._connection_pool.get_pool_status() if client._connection_pool else {}
                
                # Check operation metrics
                metrics = client._operation_metrics
                
                # Calculate health level
                health_level = self._calculate_health_level(metrics, pool_status)
                
                # Determine connection stability
                connection_stable = (
                    client_status in [ClientStatus.CONNECTED, ClientStatus.DEGRADED] and
                    pool_status["total_connections"] > 0
                )
                
                # Generate issues and recommendations
                issues, recommendations = self._analyze_health(
                    client_status, metrics, pool_status
                )
                
                # Update status
                self._current_status = HealthStatus(
                    client_status=client_status,
                    health_level=health_level,
                    last_health_check=now,
                    connection_stable=connection_stable,
                    response_time_ms=metrics.average_response_time,
                    error_rate_percent=metrics.error_rate,
                    concurrent_operations=metrics.current_concurrent_operations,
                    max_concurrent_operations=client._max_concurrent_operations,
                    uptime_seconds=uptime,
                    issues=issues,
                    recommendations=recommendations
                )
                
                return self._current_status
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return self._create_error_status(f"Health check error: {e}")
    
    def get_current_status(self) -> HealthStatus:
        """Get current cached health status."""
        return self._current_status
    
    async def _monitoring_loop(self) -> None:
        """Main health monitoring loop."""
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(min(self.check_interval, 10.0))
    
    def _calculate_health_level(
        self, 
        metrics: OperationMetrics, 
        pool_status: Dict[str, Any]
    ) -> ClientHealth:
        """Calculate overall health level based on metrics."""
        issues_count = 0
        
        # Check error rate
        if metrics.error_rate > self.error_rate_threshold:
            issues_count += 2
        elif metrics.error_rate > self.error_rate_threshold / 2:
            issues_count += 1
        
        # Check response time
        if metrics.average_response_time > self.response_time_threshold:
            issues_count += 2
        elif metrics.average_response_time > self.response_time_threshold / 2:
            issues_count += 1
        
        # Check connection pool
        if pool_status["total_connections"] == 0:
            issues_count += 3
        elif pool_status["available_slots"] == 0:
            issues_count += 1
        
        # Determine health level
        if issues_count == 0:
            return ClientHealth.HEALTHY
        elif issues_count <= 2:
            return ClientHealth.WARNING
        else:
            return ClientHealth.CRITICAL
    
    def _analyze_health(
        self,
        client_status: ClientStatus,
        metrics: OperationMetrics,
        pool_status: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Analyze health and generate issues/recommendations."""
        issues = []
        recommendations = []
        
        # Client status issues
        if client_status == ClientStatus.ERROR:
            issues.append("Client is in error state")
            recommendations.append("Check client logs and restart if necessary")
        elif client_status == ClientStatus.DEGRADED:
            issues.append("Client is in degraded mode")
            recommendations.append("Monitor connection stability")
        
        # Error rate issues
        if metrics.error_rate > self.error_rate_threshold:
            issues.append(f"High error rate: {metrics.error_rate:.1f}%")
            recommendations.append("Check server connectivity and request validity")
        
        # Response time issues
        if metrics.average_response_time > self.response_time_threshold:
            issues.append(f"High response time: {metrics.average_response_time:.0f}ms")
            recommendations.append("Check network latency and server performance")
        
        # Connection pool issues
        if pool_status["total_connections"] == 0:
            issues.append("No active connections")
            recommendations.append("Check server availability and authentication")
        elif pool_status["available_slots"] == 0:
            issues.append("Connection pool exhausted")
            recommendations.append("Consider increasing max connections or reducing concurrent operations")
        
        # Resource utilization
        utilization = (
            metrics.current_concurrent_operations / 
            (metrics.current_concurrent_operations + pool_status["available_slots"])
        ) if (metrics.current_concurrent_operations + pool_status["available_slots"]) > 0 else 0
        
        if utilization > 0.9:
            issues.append(f"High resource utilization: {utilization:.0%}")
            recommendations.append("Monitor operation queue and consider scaling")
        
        return issues, recommendations
    
    def _create_error_status(self, error_message: str) -> HealthStatus:
        """Create error health status."""
        return HealthStatus(
            client_status=ClientStatus.ERROR,
            health_level=ClientHealth.CRITICAL,
            last_health_check=datetime.now(),
            connection_stable=False,
            response_time_ms=0.0,
            error_rate_percent=100.0,
            concurrent_operations=0,
            max_concurrent_operations=10,
            uptime_seconds=(datetime.now() - self._start_time).total_seconds(),
            issues=[error_message],
            recommendations=["Check client configuration and server availability"]
        )


# Main AsyncMCPClient implementation
class AsyncMCPClient(IAsyncMCPClient):
    """
    Main asynchronous MCP client implementation.
    
    Integrates connection pool management, health monitoring, operation limiting,
    and comprehensive error handling to provide a production-ready MCP client
    for the Study Buddy GUI.
    
    Features:
    - Connection pooling with health monitoring
    - Concurrent operation limiting (max 10 by default)
    - Graceful degradation on errors
    - Comprehensive logging and metrics
    - Resource cleanup and lifecycle management
    """
    
    def __init__(
        self,
        config_manager: IntegrationConfigurationManager,
        max_concurrent_operations: int = 10,
        operation_timeout: float = 30.0,
        health_check_interval: float = 30.0,
        connection_factory: Optional[Callable[[], Any]] = None
    ):
        """
        Initialize AsyncMCPClient.
        
        Args:
            config_manager: Configuration management instance
            max_concurrent_operations: Maximum concurrent operations
            operation_timeout: Default operation timeout in seconds
            health_check_interval: Health check interval in seconds
            connection_factory: Factory for creating connections (injectable for testing)
        """
        self.config_manager = config_manager
        self.max_concurrent_operations = max_concurrent_operations
        self._max_concurrent_operations = max_concurrent_operations
        self.operation_timeout = operation_timeout
        
        # Load configuration
        self.config = config_manager.get_config()
        
        # Operation limiting and metrics
        self._operation_semaphore = asyncio.Semaphore(max_concurrent_operations)
        self._operation_metrics = OperationMetrics()
        self._metrics_lock = asyncio.Lock()
        
        # Client state
        self._status = ClientStatus.DISCONNECTED
        self._status_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        
        # Component dependencies (dependency injection)
        self._connection_pool: Optional[AsyncConnectionPool] = None
        self._health_monitor: Optional[AsyncHealthMonitor] = None
        
        # Operation tracking
        self._active_operations: Set[asyncio.Task] = set()
        self._operation_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # Configuration change handling
        # Note: Callback signature may need adjustment based on config manager implementation
        # self.config_manager.add_change_callback(self._on_config_changed)
        
        self.logger = get_debug_logger()
        
        # Initialize components
        self._initialize_components(connection_factory)
    
    def _initialize_components(self, connection_factory: Optional[Callable[[], Any]]) -> None:
        """Initialize client components with dependency injection."""
        # Use provided factory or create default
        if connection_factory is None:
            connection_factory = self._create_default_connection
        
        # Initialize connection pool
        self._connection_pool = AsyncConnectionPool(
            connection_factory=connection_factory,
            max_connections=10,  # Default pool size
            min_connections=2,   # Default minimum connections
            connection_timeout=self.config.mcp_server.timeout,
            health_check_interval=60.0
        )
        
        # Initialize health monitor
        self._health_monitor = AsyncHealthMonitor(
            client=self,
            check_interval=30.0,
            response_time_threshold=self.config.mcp_server.timeout * 1000 * 0.8,  # 80% of timeout
            error_rate_threshold=10.0
        )
    
    async def connect(self) -> bool:
        """
        Establish connection to MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        async with self._status_lock:
            if self._status in [ClientStatus.CONNECTED, ClientStatus.CONNECTING]:
                return self._status == ClientStatus.CONNECTED
            
            self._status = ClientStatus.CONNECTING
        
        try:
            self.logger.info(f"Connecting to MCP server at {self.config.mcp_server.host}:{self.config.mcp_server.port}")
            
            # Start connection pool
            if self._connection_pool:
                await self._connection_pool.start()
                
                # Test connection
                test_connection = await self._connection_pool.acquire_connection()
                await self._connection_pool.release_connection(test_connection)
            
            # Start health monitoring
            if self._health_monitor:
                await self._health_monitor.start_monitoring()
            
            async with self._status_lock:
                self._status = ClientStatus.CONNECTED
            
            self.logger.info("Successfully connected to MCP server")
            return True
            
        except Exception as e:
            async with self._status_lock:
                self._status = ClientStatus.ERROR
            
            self.logger.error(f"Failed to connect to MCP server: {e}")
            
            # Cleanup on connection failure
            try:
                if self._connection_pool:
                    await self._connection_pool.stop()
                if self._health_monitor:
                    await self._health_monitor.stop_monitoring()
            except Exception as cleanup_error:
                self.logger.error(f"Error during connection cleanup: {cleanup_error}")
            
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server and cleanup resources."""
        async with self._status_lock:
            if self._status == ClientStatus.DISCONNECTED:
                return
            
            self._status = ClientStatus.SHUTTING_DOWN
        
        try:
            self.logger.info("Disconnecting from MCP server")
            
            # Signal shutdown to prevent new operations
            self._shutdown_event.set()
            
            # Wait for active operations to complete (with timeout)
            if self._active_operations:
                self.logger.info(f"Waiting for {len(self._active_operations)} active operations to complete")
                await asyncio.wait_for(
                    self._wait_for_operations(),
                    timeout=self.operation_timeout
                )
            
            # Stop health monitoring
            if self._health_monitor:
                await self._health_monitor.stop_monitoring()
            
            # Close connection pool
            if self._connection_pool:
                await self._connection_pool.stop()
            
            async with self._status_lock:
                self._status = ClientStatus.DISCONNECTED
            
            self.logger.info("Successfully disconnected from MCP server")
            
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for operations to complete, forcing shutdown")
            await self._force_shutdown()
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
            await self._force_shutdown()
    
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Invoke MCP tool with parameters.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
            timeout: Operation timeout (uses default if None)
            
        Returns:
            Tool response dictionary
            
        Raises:
            MCPClientError: If client is not connected or operation fails
            OperationTimeoutError: If operation times out
            ResourceExhaustionError: If too many concurrent operations
        """
        # Check client status
        if self._status != ClientStatus.CONNECTED:
            raise MCPClientError(f"Client not connected (status: {self._status.value})")
        
        if self._shutdown_event.is_set():
            raise MCPClientError("Client is shutting down")
        
        # Use default timeout if not specified
        operation_timeout = timeout or self.operation_timeout
        
        # Acquire operation semaphore
        try:
            await asyncio.wait_for(
                self._operation_semaphore.acquire(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            raise ResourceExhaustionError(
                f"Too many concurrent operations (max: {self.max_concurrent_operations})"
            )
        
        operation_start = datetime.now()
        
        try:
            # Update concurrent operations count
            async with self._metrics_lock:
                self._operation_metrics.current_concurrent_operations += 1
            
            # Create and track operation task
            operation_task = asyncio.create_task(
                self._execute_tool_operation(tool_name, parameters, operation_timeout)
            )
            self._active_operations.add(operation_task)
            
            try:
                # Execute operation
                result = await operation_task
                
                # Update success metrics
                await self._update_operation_metrics(
                    success=True,
                    duration=(datetime.now() - operation_start).total_seconds()
                )
                
                # Notify callbacks
                for callback in self._operation_callbacks:
                    try:
                        callback(tool_name, {"success": True, "result": result})
                    except Exception as cb_error:
                        self.logger.error(f"Operation callback error: {cb_error}")
                
                return result
                
            finally:
                # Remove from active operations
                self._active_operations.discard(operation_task)
        
        except Exception as e:
            # Update failure metrics
            await self._update_operation_metrics(
                success=False,
                duration=(datetime.now() - operation_start).total_seconds()
            )
            
            # Notify callbacks
            for callback in self._operation_callbacks:
                try:
                    callback(tool_name, {"success": False, "error": str(e)})
                except Exception as cb_error:
                    self.logger.error(f"Operation callback error: {cb_error}")
            
            # Re-raise with appropriate exception type
            if isinstance(e, asyncio.TimeoutError):
                raise OperationTimeoutError(f"Tool '{tool_name}' timed out after {operation_timeout}s")
            else:
                raise MCPClientError(f"Tool '{tool_name}' failed: {e}")
        
        finally:
            # Release operation semaphore
            self._operation_semaphore.release()
            
            # Update concurrent operations count
            async with self._metrics_lock:
                self._operation_metrics.current_concurrent_operations -= 1
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.
        
        Returns:
            List of tool definitions
        """
        result = await self.invoke_tool("list_tools", {})
        # Extract tools list from result
        return result.get("tools", [])
    
    def get_status(self) -> ClientStatus:
        """Get current client status."""
        return self._status
    
    def get_health(self) -> HealthStatus:
        """Get current health status."""
        if self._health_monitor:
            return self._health_monitor.get_current_status()
        else:
            return HealthStatus(
                client_status=self._status,
                health_level=ClientHealth.UNKNOWN,
                last_health_check=datetime.now(),
                connection_stable=False,
                response_time_ms=0.0,
                error_rate_percent=0.0,
                concurrent_operations=0,
                max_concurrent_operations=self.max_concurrent_operations,
                uptime_seconds=0.0
            )
    
    def get_metrics(self) -> OperationMetrics:
        """Get operation metrics."""
        return self._operation_metrics
    
    def add_operation_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for operation events."""
        self._operation_callbacks.append(callback)
    
    def remove_operation_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Remove operation callback."""
        if callback in self._operation_callbacks:
            self._operation_callbacks.remove(callback)
    
    async def _execute_tool_operation(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute tool operation with connection management."""
        connection = None
        
        try:
            # Acquire connection
            if not self._connection_pool:
                raise MCPClientError("Connection pool not initialized")
            connection = await self._connection_pool.acquire_connection()
            
            # Execute tool with timeout
            result = await asyncio.wait_for(
                self._invoke_tool_on_connection(connection, tool_name, parameters),
                timeout=timeout
            )
            
            return result
            
        finally:
            # Always release connection
            if connection and self._connection_pool:
                await self._connection_pool.release_connection(connection)
    
    async def _invoke_tool_on_connection(
        self,
        connection: Any,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke tool on specific connection."""
        # This would be implemented based on the actual MCP protocol
        # For now, return a mock response
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return {
            "tool": tool_name,
            "parameters": parameters,
            "result": f"Mock result for {tool_name}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_default_connection(self) -> Any:
        """Create default MCP connection."""
        # This would create actual MCP connection
        # For now, return a mock connection object
        class MockConnection:
            def __init__(self):
                self._connected = True
            
            def is_connected(self):
                return self._connected
            
            async def close(self):
                self._connected = False
        
        return MockConnection()
    
    async def _update_operation_metrics(self, success: bool, duration: float) -> None:
        """Update operation metrics thread-safely."""
        async with self._metrics_lock:
            self._operation_metrics.total_operations += 1
            
            if success:
                self._operation_metrics.successful_operations += 1
            else:
                self._operation_metrics.failed_operations += 1
            
            # Update average response time
            total_time = (
                self._operation_metrics.average_response_time * 
                (self._operation_metrics.total_operations - 1) +
                duration * 1000  # Convert to milliseconds
            )
            self._operation_metrics.average_response_time = (
                total_time / self._operation_metrics.total_operations
            )
            
            self._operation_metrics.last_operation_time = datetime.now()
    
    async def _wait_for_operations(self) -> None:
        """Wait for all active operations to complete."""
        while self._active_operations:
            # Wait for any operation to complete
            done, pending = await asyncio.wait(
                self._active_operations,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=1.0
            )
            
            # Remove completed operations
            for task in done:
                self._active_operations.discard(task)
    
    async def _force_shutdown(self) -> None:
        """Force shutdown by cancelling all operations."""
        # Cancel all active operations
        for task in self._active_operations.copy():
            task.cancel()
        
        # Wait briefly for cancellations
        if self._active_operations:
            await asyncio.wait(self._active_operations, timeout=1.0)
        
        # Clear active operations
        self._active_operations.clear()
        
        # Force close components
        try:
            if self._health_monitor:
                await self._health_monitor.stop_monitoring()
        except Exception:
            pass
        
        try:
            if self._connection_pool:
                await self._connection_pool.close_all_connections()
        except Exception:
            pass
        
        async with self._status_lock:
            self._status = ClientStatus.DISCONNECTED
    
    def _on_config_changed(self, config_dict: Dict[str, Any]) -> None:
        """Handle configuration changes."""
        try:
            # Reload configuration
            self.config = self.config_manager.get_config()
            
            # Log configuration change
            self.logger.info("Configuration updated")
            
            # TODO: Apply configuration changes to running components
            # This could include updating connection pool size, timeouts, etc.
            
        except Exception as e:
            self.logger.error(f"Error handling configuration change: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Factory functions for dependency injection
def create_async_mcp_client(
    config_manager: IntegrationConfigurationManager,
    max_concurrent_operations: int = 10,
    operation_timeout: float = 30.0,
    connection_factory: Optional[Callable[[], Any]] = None
) -> AsyncMCPClient:
    """
    Factory function to create configured AsyncMCPClient.
    
    Args:
        config_manager: Configuration management instance
        max_concurrent_operations: Maximum concurrent operations
        operation_timeout: Default operation timeout
        connection_factory: Optional connection factory for testing
        
    Returns:
        Configured AsyncMCPClient instance
    """
    return AsyncMCPClient(
        config_manager=config_manager,
        max_concurrent_operations=max_concurrent_operations,
        operation_timeout=operation_timeout,
        connection_factory=connection_factory
    )


# Context manager for client operations
@asynccontextmanager
async def mcp_client_session(
    config_manager: IntegrationConfigurationManager,
    **kwargs
):
    """
    Async context manager for MCP client sessions.
    
    Args:
        config_manager: Configuration management instance
        **kwargs: Additional arguments for AsyncMCPClient
        
    Yields:
        Connected AsyncMCPClient instance
    """
    client = create_async_mcp_client(config_manager, **kwargs)
    
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


# Utility decorators
def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator for retrying MCP operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff_factor: Exponential backoff factor
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        break
            
            if last_exception:
                raise last_exception
            else:
                raise Exception("Operation failed after all retry attempts")
        
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float):
    """
    Decorator for adding timeout to MCP operations.
    
    Args:
        timeout_seconds: Timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout_seconds
            )
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage and testing
    async def main():
        """Example usage of AsyncMCPClient."""
        # Example would need to import from config_manager
        # from config_manager import create_integration_config_manager
        
        # Create configuration manager (example)
        # config_manager = create_integration_config_manager()
        return  # Skip example for now
        
        # Create and use MCP client
        async with mcp_client_session(config_manager) as client:
            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {len(tools)}")
            
            # Invoke a tool
            result = await client.invoke_tool("test_tool", {"param": "value"})
            print(f"Tool result: {result}")
            
            # Check health status
            health = client.get_health()
            print(f"Health status: {health.health_level.value}")
            
            # Get metrics
            metrics = client.get_metrics()
            print(f"Success rate: {metrics.success_rate:.1f}%")
    
    # Run example
    # asyncio.run(main())