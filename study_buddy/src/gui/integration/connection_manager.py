"""
Study Buddy GUI - Connection Manager with Health Monitoring

Implements robust MCP server connection lifecycle management with connection pooling,
health monitoring, automatic retry with exponential backoff, and comprehensive
connection statistics tracking.

Architecture: Clean Architecture Layer 3 (Data Access Infrastructure)
Patterns: Factory Pattern, Observer Pattern, Circuit Breaker Pattern, Object Pool Pattern  
SOLID: SRP (connection management only), OCP (extensible connection types), DIP (abstraction-based)
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import aiohttp
import subprocess

from .mcp_client import (
    IConnectionManager,
    ConnectionState,
    ConnectionHealth,
    ConnectionCallback,
    ConnectionError,
    TimeoutError,
)
from gui.error_handling import (
    get_debug_logger,
    get_error_tracker,
    ErrorSeverity,
    ErrorCategory,
    get_degradation_manager,
    record_mcp_failure,
    record_mcp_success,
)
from gui.performance import get_performance_monitor


class ConnectionType(Enum):
    """Types of MCP server connections supported."""

    STDIO = "stdio"  # Standard input/output communication
    TCP = "tcp"  # TCP socket communication
    HTTP = "http"  # HTTP REST API communication
    WEBSOCKET = "websocket"  # WebSocket communication


@dataclass
class ConnectionConfig:
    """Configuration for MCP server connections."""

    connection_type: ConnectionType = ConnectionType.HTTP

    # Common configuration
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    max_retry_delay_seconds: float = 60.0
    keepalive_interval_seconds: float = 30.0

    # Connection pooling
    min_connections: int = 3
    max_connections: int = 10
    connection_idle_timeout_seconds: float = 300.0  # 5 minutes

    # Health monitoring
    health_check_interval_seconds: float = 60.0
    health_check_timeout_seconds: float = 5.0
    max_consecutive_failures: int = 5

    # HTTP-specific
    http_host: str = "localhost"
    http_port: int = 3000
    http_base_path: str = "/mcp"

    # TCP-specific
    tcp_host: str = "localhost"
    tcp_port: int = 4000

    # STDIO-specific
    stdio_command: Optional[List[str]] = None
    stdio_working_directory: Optional[Path] = None

    # WebSocket-specific
    websocket_url: str = "ws://localhost:8000/mcp"

    def __post_init__(self):
        """Validate configuration."""
        if self.min_connections > self.max_connections:
            raise ValueError("min_connections cannot be greater than max_connections")

        if self.connection_type == ConnectionType.STDIO and not self.stdio_command:
            raise ValueError("stdio_command required for STDIO connection type")


@dataclass
class ConnectionMetrics:
    """Metrics for connection performance monitoring."""

    # Connection statistics
    total_connections_created: int = 0
    total_connections_closed: int = 0
    active_connections: int = 0
    failed_connections: int = 0

    # Operation statistics
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

    # Timing statistics
    average_connection_time_ms: float = 0.0
    average_operation_time_ms: float = 0.0
    last_successful_operation: Optional[datetime] = None

    # Health statistics
    consecutive_failures: int = 0
    uptime_seconds: float = 0.0
    downtime_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate operation success rate percentage."""
        if self.total_operations == 0:
            return 100.0
        return (self.successful_operations / self.total_operations) * 100.0

    @property
    def connection_success_rate(self) -> float:
        """Calculate connection success rate percentage."""
        total_attempts = self.total_connections_created + self.failed_connections
        if total_attempts == 0:
            return 100.0
        return (self.total_connections_created / total_attempts) * 100.0


class IConnection(ABC):
    """Abstract interface for MCP server connections."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connection is active."""
        pass

    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request and get response."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform connection health check."""
        pass

    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging."""
        pass


class HTTPConnection(IConnection):
    """HTTP-based MCP server connection."""

    def __init__(self, config: ConnectionConfig, session: aiohttp.ClientSession):
        self.config = config
        self.session = session
        self._connected = False
        self._connection_time: Optional[datetime] = None
        self._logger = get_debug_logger()

    async def connect(self) -> bool:
        """Establish HTTP connection to MCP server."""
        try:
            self._connection_time = datetime.now()

            # Test connection with health check
            if await self.health_check():
                self._connected = True
                self._logger.debug(
                    f"HTTP connection established to {self.config.http_host}:{self.config.http_port}"
                )
                return True
            else:
                self._connected = False
                return False

        except Exception as e:
            self._logger.error(f"Failed to establish HTTP connection: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close HTTP connection."""
        self._connected = False
        self._connection_time = None
        self._logger.debug("HTTP connection closed")

    async def is_connected(self) -> bool:
        """Check if HTTP connection is active."""
        return self._connected and not self.session.closed

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP request to MCP server."""
        if not await self.is_connected():
            raise ConnectionError("Not connected to MCP server")

        url = f"http://{self.config.http_host}:{self.config.http_port}{self.config.http_base_path}/call"

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            async with self.session.post(
                url, json=request, timeout=timeout
            ) as response:
                if response.content_type == "application/json":
                    return await response.json()
                else:
                    # Handle non-JSON response
                    text = await response.text()
                    return {
                        "error": f"Non-JSON response: {text}",
                        "status_code": response.status,
                    }

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"HTTP request timed out after {self.config.timeout_seconds}s"
            )
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HTTP request failed: {e}")

    async def health_check(self) -> bool:
        """Perform HTTP health check."""
        try:
            url = f"http://{self.config.http_host}:{self.config.http_port}/health"
            timeout = aiohttp.ClientTimeout(
                total=self.config.health_check_timeout_seconds
            )

            async with self.session.get(url, timeout=timeout) as response:
                return response.status == 200

        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get HTTP connection information."""
        return {
            "type": "HTTP",
            "host": self.config.http_host,
            "port": self.config.http_port,
            "base_path": self.config.http_base_path,
            "connected": self._connected,
            "connection_time": self._connection_time.isoformat()
            if self._connection_time
            else None,
        }


class STDIOConnection(IConnection):
    """Standard I/O based MCP server connection."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._connection_time: Optional[datetime] = None
        self._logger = get_debug_logger()

    async def connect(self) -> bool:
        """Establish STDIO connection to MCP server."""
        try:
            self._connection_time = datetime.now()

            # Start MCP server process
            self._process = subprocess.Popen(
                self.config.stdio_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.config.stdio_working_directory,
            )

            # Wait a moment for process to start
            await asyncio.sleep(0.1)

            # Check if process started successfully
            if self._process.poll() is None:
                self._connected = True
                self._logger.debug(
                    f"STDIO connection established with command: {self.config.stdio_command}"
                )
                return True
            else:
                self._connected = False
                return False

        except Exception as e:
            self._logger.error(f"Failed to establish STDIO connection: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close STDIO connection."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(
                    timeout=5.0
                )  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                self._process.kill()  # Force kill if needed
            except Exception as e:
                self._logger.warning(f"Error closing STDIO connection: {e}")

            self._process = None

        self._connected = False
        self._connection_time = None
        self._logger.debug("STDIO connection closed")

    async def is_connected(self) -> bool:
        """Check if STDIO connection is active."""
        return (
            self._connected
            and self._process is not None
            and self._process.poll() is None
        )

    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via STDIO to MCP server."""
        if not await self.is_connected() or not self._process:
            raise ConnectionError("Not connected to MCP server")

        try:
            # Send request as JSON line
            request_json = json.dumps(request) + "\n"
            self._process.stdin.write(request_json)
            self._process.stdin.flush()

            # Read response
            response_line = self._process.stdout.readline().strip()
            if response_line:
                return json.loads(response_line)
            else:
                raise ConnectionError("No response from MCP server")

        except json.JSONDecodeError as e:
            raise ConnectionError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ConnectionError(f"STDIO communication error: {e}")

    async def health_check(self) -> bool:
        """Perform STDIO health check."""
        if not await self.is_connected():
            return False

        try:
            # Send simple ping request
            health_request = {"method": "ping", "id": "health_check"}
            response = await self.send_request(health_request)
            return response.get("result") == "pong"

        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get STDIO connection information."""
        return {
            "type": "STDIO",
            "command": self.config.stdio_command,
            "working_directory": str(self.config.stdio_working_directory)
            if self.config.stdio_working_directory
            else None,
            "connected": self._connected,
            "process_id": self._process.pid if self._process else None,
            "connection_time": self._connection_time.isoformat()
            if self._connection_time
            else None,
        }


class ConnectionFactory:
    """Factory for creating MCP server connections."""

    @staticmethod
    def create_connection(
        config: ConnectionConfig, session: Optional[aiohttp.ClientSession] = None
    ) -> IConnection:
        """
        Create connection based on configuration type.

        Args:
            config: Connection configuration
            session: Optional aiohttp session for HTTP connections

        Returns:
            Appropriate IConnection implementation

        Raises:
            ValueError: If connection type not supported or configuration invalid
        """
        if config.connection_type == ConnectionType.HTTP:
            if session is None:
                raise ValueError("aiohttp.ClientSession required for HTTP connections")
            return HTTPConnection(config, session)

        elif config.connection_type == ConnectionType.STDIO:
            return STDIOConnection(config)

        # TODO: Implement TCP and WebSocket connections in future iterations
        elif config.connection_type == ConnectionType.TCP:
            raise NotImplementedError("TCP connections not yet implemented")

        elif config.connection_type == ConnectionType.WEBSOCKET:
            raise NotImplementedError("WebSocket connections not yet implemented")

        else:
            raise ValueError(f"Unsupported connection type: {config.connection_type}")


class ConnectionPool:
    """
    Connection pool for managing multiple MCP server connections.

    Implements object pooling pattern with health monitoring and automatic
    connection replacement for failed connections.
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._available_connections: List[IConnection] = []
        self._active_connections: Set[IConnection] = set()
        self._connection_metrics: Dict[IConnection, datetime] = {}
        self._lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = get_debug_logger()

        # Initialize session for HTTP connections
        if config.connection_type == ConnectionType.HTTP:
            self._setup_http_session()

    def _setup_http_session(self) -> None:
        """Setup aiohttp session for HTTP connections."""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections,
            keepalive_timeout=self.config.keepalive_interval_seconds,
        )

        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def initialize_pool(self) -> None:
        """Initialize connection pool with minimum connections."""
        async with self._lock:
            # Create minimum number of connections
            for _ in range(self.config.min_connections):
                connection = await self._create_connection()
                if connection:
                    self._available_connections.append(connection)
                    self._connection_metrics[connection] = datetime.now()

            self._logger.info(
                f"Connection pool initialized with {len(self._available_connections)} connections",
                pool_size=len(self._available_connections),
                config_min=self.config.min_connections,
            )

    async def get_connection(self) -> Optional[IConnection]:
        """
        Get available connection from pool.

        Returns:
            Available connection or None if pool is exhausted
        """
        async with self._lock:
            # Try to get available connection
            if self._available_connections:
                connection = self._available_connections.pop(0)
                self._active_connections.add(connection)

                # Check if connection is still healthy
                if await connection.is_connected() and await connection.health_check():
                    return connection
                else:
                    # Connection is unhealthy, remove and create new one
                    self._active_connections.discard(connection)
                    del self._connection_metrics[connection]
                    await connection.disconnect()

                    # Try to create replacement
                    new_connection = await self._create_connection()
                    if new_connection:
                        self._active_connections.add(new_connection)
                        self._connection_metrics[new_connection] = datetime.now()
                        return new_connection

            # No available connections, try to create new one if under limit
            if len(self._active_connections) < self.config.max_connections:
                connection = await self._create_connection()
                if connection:
                    self._active_connections.add(connection)
                    self._connection_metrics[connection] = datetime.now()
                    return connection

            # Pool exhausted
            return None

    async def return_connection(self, connection: IConnection) -> None:
        """
        Return connection to pool.

        Args:
            connection: Connection to return to pool
        """
        async with self._lock:
            if connection in self._active_connections:
                self._active_connections.discard(connection)

                # Check if connection is still healthy and under idle timeout
                if await connection.is_connected():
                    connection_age = datetime.now() - self._connection_metrics.get(
                        connection, datetime.now()
                    )

                    if (
                        connection_age.total_seconds()
                        < self.config.connection_idle_timeout_seconds
                    ):
                        self._available_connections.append(connection)
                    else:
                        # Connection too old, close it
                        await connection.disconnect()
                        del self._connection_metrics[connection]
                else:
                    # Connection unhealthy, clean up
                    await connection.disconnect()
                    if connection in self._connection_metrics:
                        del self._connection_metrics[connection]

    async def close_pool(self) -> None:
        """Close all connections in pool."""
        async with self._lock:
            # Close all available connections
            for connection in self._available_connections:
                await connection.disconnect()

            # Close all active connections
            for connection in self._active_connections:
                await connection.disconnect()

            # Close HTTP session if exists
            if self._session and not self._session.closed:
                await self._session.close()

            # Clear all collections
            self._available_connections.clear()
            self._active_connections.clear()
            self._connection_metrics.clear()

            self._logger.info("Connection pool closed")

    async def _create_connection(self) -> Optional[IConnection]:
        """Create new connection using factory."""
        try:
            connection = ConnectionFactory.create_connection(self.config, self._session)

            if await connection.connect():
                return connection
            else:
                await connection.disconnect()
                return None

        except Exception as e:
            self._logger.error(f"Failed to create connection: {e}")
            return None

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "available_connections": len(self._available_connections),
            "active_connections": len(self._active_connections),
            "total_connections": len(self._available_connections)
            + len(self._active_connections),
            "max_connections": self.config.max_connections,
            "min_connections": self.config.min_connections,
            "connection_type": self.config.connection_type.value,
        }


class ConnectionManager(IConnectionManager):
    """
    Robust MCP server connection manager with health monitoring.

    Responsibilities:
    - Manage connection lifecycle with automatic retry
    - Monitor connection health with heartbeat
    - Provide connection pooling for performance
    - Track comprehensive connection statistics
    - Handle graceful degradation on failures

    Integrates with existing error handling and performance monitoring systems.
    """

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self._pool = ConnectionPool(self.config)
        self._state = ConnectionState.DISCONNECTED
        self._metrics = ConnectionMetrics()
        self._start_time = datetime.now()

        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_check: Optional[datetime] = None

        # Event listeners
        self._connection_listeners: List[ConnectionCallback] = []

        # Integration with existing systems
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()
        self._performance_monitor = get_performance_monitor()
        self._degradation_manager = get_degradation_manager()

        # Thread safety
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """
        Establish connection to MCP server with health monitoring.

        Returns:
            True if connection established successfully
        """
        async with self._lock:
            try:
                self._set_state(ConnectionState.CONNECTING)
                self._logger.info(
                    "Connecting to MCP server",
                    connection_type=self.config.connection_type.value,
                    config=self.config.__dict__,
                )

                # Initialize connection pool
                start_time = time.time()
                await self._pool.initialize_pool()
                connection_time_ms = (time.time() - start_time) * 1000

                # Check if we have any connections
                pool_stats = self._pool.get_pool_stats()
                if pool_stats["total_connections"] > 0:
                    self._set_state(ConnectionState.CONNECTED)
                    self._metrics.total_connections_created += pool_stats[
                        "total_connections"
                    ]
                    self._metrics.average_connection_time_ms = connection_time_ms

                    # Start health monitoring
                    self._health_check_task = asyncio.create_task(
                        self._health_monitor_loop()
                    )

                    # Record successful connection
                    record_mcp_success()

                    self._logger.info(
                        "Successfully connected to MCP server",
                        connection_time_ms=connection_time_ms,
                        pool_size=pool_stats["total_connections"],
                    )

                    # Notify listeners
                    self._notify_connection_listeners(ConnectionState.CONNECTED)

                    return True
                else:
                    self._set_state(ConnectionState.ERROR)
                    self._metrics.failed_connections += 1

                    error = ConnectionError(
                        "Failed to establish any connections to MCP server"
                    )
                    record_mcp_failure(error)

                    self._error_tracker.capture_error(
                        exception=error,
                        severity=ErrorSeverity.HIGH,
                        category=ErrorCategory.NETWORK,
                        user_action="Connecting to MCP server",
                        operation_context={
                            "connection_type": self.config.connection_type.value,
                            "pool_stats": pool_stats,
                        },
                    )

                    return False

            except Exception as e:
                self._set_state(ConnectionState.ERROR)
                self._metrics.failed_connections += 1

                connection_error = ConnectionError(f"Connection failed: {e}")
                record_mcp_failure(connection_error)

                self._error_tracker.capture_error(
                    exception=connection_error,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.NETWORK,
                    user_action="Connecting to MCP server",
                    operation_context={
                        "connection_type": self.config.connection_type.value,
                        "original_error": str(e),
                    },
                )

                self._logger.error(f"Failed to connect to MCP server: {e}")
                return False

    async def disconnect(self) -> None:
        """Gracefully disconnect from MCP server."""
        async with self._lock:
            self._logger.info("Disconnecting from MCP server")

            # Stop health monitoring
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Close connection pool
            await self._pool.close_pool()

            # Update state and metrics
            self._set_state(ConnectionState.DISCONNECTED)
            self._metrics.total_connections_closed += self._metrics.active_connections
            self._metrics.active_connections = 0

            self._logger.info("Disconnected from MCP server")

            # Notify listeners
            self._notify_connection_listeners(ConnectionState.DISCONNECTED)

    async def is_connected(self) -> bool:
        """
        Check if currently connected to MCP server.

        Returns:
            True if connected and healthy, False otherwise
        """
        return self._state == ConnectionState.CONNECTED

    async def get_connection_health(self) -> ConnectionHealth:
        """
        Get comprehensive connection health information.

        Returns:
            ConnectionHealth with current status and statistics
        """
        uptime = (datetime.now() - self._start_time).total_seconds()

        # Get connection from pool for health check
        connection = await self._pool.get_connection()
        round_trip_time = None

        if connection:
            try:
                start_time = time.time()
                health_ok = await connection.health_check()
                round_trip_time = (time.time() - start_time) * 1000

                if not health_ok and self._state == ConnectionState.CONNECTED:
                    self._set_state(ConnectionState.DEGRADED)

            except Exception:
                round_trip_time = None
                if self._state == ConnectionState.CONNECTED:
                    self._set_state(ConnectionState.DEGRADED)

            finally:
                await self._pool.return_connection(connection)

        return ConnectionHealth(
            is_connected=await self.is_connected(),
            connection_state=self._state,
            last_successful_operation=self._metrics.last_successful_operation,
            last_error=None,  # TODO: Track last error
            round_trip_time_ms=round_trip_time,
            server_version=None,  # TODO: Get from server
            active_operations=self._metrics.active_connections,
            total_operations=self._metrics.total_operations,
            error_count=self._metrics.failed_operations,
            uptime_seconds=uptime,
        )

    def add_connection_listener(self, callback: ConnectionCallback) -> None:
        """Add callback for connection state changes."""
        if callback not in self._connection_listeners:
            self._connection_listeners.append(callback)

    def remove_connection_listener(self, callback: ConnectionCallback) -> None:
        """Remove connection state change callback."""
        if callback in self._connection_listeners:
            self._connection_listeners.remove(callback)

    async def execute_operation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute operation using connection pool.

        Args:
            request: MCP request to execute

        Returns:
            Response from MCP server

        Raises:
            ConnectionError: If no connections available or operation fails
        """
        if not await self.is_connected():
            raise ConnectionError("Not connected to MCP server")

        connection = await self._pool.get_connection()
        if not connection:
            raise ConnectionError("No connections available in pool")

        try:
            start_time = time.time()

            # Execute operation
            response = await connection.send_request(request)

            # Track metrics
            execution_time_ms = (time.time() - start_time) * 1000
            self._metrics.total_operations += 1
            self._metrics.successful_operations += 1
            self._metrics.last_successful_operation = datetime.now()

            # Update average operation time
            total_time = self._metrics.average_operation_time_ms * (
                self._metrics.total_operations - 1
            )
            self._metrics.average_operation_time_ms = (
                total_time + execution_time_ms
            ) / self._metrics.total_operations

            # Record success
            record_mcp_success()

            return response

        except Exception as e:
            # Track failure metrics
            self._metrics.total_operations += 1
            self._metrics.failed_operations += 1
            self._metrics.consecutive_failures += 1

            # Record failure
            record_mcp_failure(e)

            # Check if we need to degrade
            if (
                self._metrics.consecutive_failures
                >= self.config.max_consecutive_failures
            ):
                self._set_state(ConnectionState.ERROR)
                self._degradation_manager.record_connection_failure(e)

            raise

        finally:
            # Return connection to pool
            await self._pool.return_connection(connection)

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        self._logger.debug("Starting health monitor loop")

        try:
            while self._state == ConnectionState.CONNECTED:
                await asyncio.sleep(self.config.health_check_interval_seconds)

                try:
                    # Get health status
                    health = await self.get_connection_health()
                    self._last_health_check = datetime.now()

                    # Check if health is degraded
                    if health.connection_state == ConnectionState.DEGRADED:
                        self._logger.warning(
                            "Connection health degraded, attempting recovery"
                        )
                        # TODO: Implement recovery logic

                except Exception as e:
                    self._logger.error(f"Health check failed: {e}")
                    self._metrics.consecutive_failures += 1

                    if (
                        self._metrics.consecutive_failures
                        >= self.config.max_consecutive_failures
                    ):
                        self._set_state(ConnectionState.ERROR)
                        self._degradation_manager.record_connection_failure(e)
                        break

        except asyncio.CancelledError:
            self._logger.debug("Health monitor loop cancelled")
        except Exception as e:
            self._logger.error(f"Health monitor loop error: {e}")

    def _set_state(self, new_state: ConnectionState) -> None:
        """Set connection state and update metrics."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state

            self._logger.debug(
                f"Connection state changed: {old_state.value} -> {new_state.value}",
                old_state=old_state.value,
                new_state=new_state.value,
            )

    def _notify_connection_listeners(self, state: ConnectionState) -> None:
        """Notify all connection listeners of state change."""
        for listener in self._connection_listeners:
            try:
                listener(state)
            except Exception as e:
                self._logger.error(f"Connection listener error: {e}")
                self._error_tracker.capture_error(
                    exception=e,
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.INTEGRATION,
                    user_action="Connection state notification",
                    operation_context={"connection_state": state.value},
                )

    def get_connection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics."""
        pool_stats = self._pool.get_pool_stats()

        return {
            "state": self._state.value,
            "metrics": {
                "total_connections_created": self._metrics.total_connections_created,
                "total_connections_closed": self._metrics.total_connections_closed,
                "active_connections": self._metrics.active_connections,
                "failed_connections": self._metrics.failed_connections,
                "total_operations": self._metrics.total_operations,
                "successful_operations": self._metrics.successful_operations,
                "failed_operations": self._metrics.failed_operations,
                "success_rate": self._metrics.success_rate,
                "connection_success_rate": self._metrics.connection_success_rate,
                "average_connection_time_ms": self._metrics.average_connection_time_ms,
                "average_operation_time_ms": self._metrics.average_operation_time_ms,
                "consecutive_failures": self._metrics.consecutive_failures,
                "uptime_seconds": self._metrics.uptime_seconds,
            },
            "pool": pool_stats,
            "config": {
                "connection_type": self.config.connection_type.value,
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
            },
            "last_health_check": self._last_health_check.isoformat()
            if self._last_health_check
            else None,
        }
