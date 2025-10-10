"""
Mock MCP Client for Testing - Study Buddy Integration Layer.

This module provides a comprehensive mock implementation of the AsyncMCPClient
for testing GUI components without requiring a real MCP server connection.
Supports configurable responses, error simulation, and testing utilities.

Architecture: Clean Architecture Layer 4 (Infrastructure) - Testing Infrastructure
SOLID Compliance: Full compliance with interface segregation and dependency inversion
Purpose: Enable comprehensive testing of GUI components with realistic MCP client behavior
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Callable, Union, Set
)
from unittest.mock import Mock
import logging as std_logging
import random
import uuid
from pathlib import Path

# Import the real interfaces for compatibility
try:
    from .async_mcp_client import (
        IAsyncMCPClient, ClientStatus, ClientHealth, HealthStatus,
        MCPClientError, OperationMetrics
    )
except ImportError:
    # Fallback definitions for standalone testing
    from abc import ABC, abstractmethod
    from enum import Enum
    
    class ClientStatus(Enum):
        """MCP client operational status."""
        DISCONNECTED = "disconnected"
        CONNECTING = "connecting"
        CONNECTED = "connected"
        ERROR = "error"
        DEGRADED = "degraded"
        SHUTTING_DOWN = "shutting_down"
    
    class ClientHealth(Enum):
        """MCP client health status."""
        HEALTHY = "healthy"
        WARNING = "warning"
        CRITICAL = "critical"
        UNKNOWN = "unknown"
    
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
    
    @dataclass
    class OperationMetrics:
        """Metrics for MCP operations."""
        total_operations: int = 0
        successful_operations: int = 0
        failed_operations: int = 0
        average_response_time_ms: float = 0.0
    
    class MCPClientError(Exception):
        """Base exception for MCP client errors."""
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


# ============================================================================
# MOCK CONFIGURATION AND BEHAVIOR
# ============================================================================

class MockBehavior(Enum):
    """Mock client behavior modes."""
    NORMAL = "normal"                    # Normal successful responses
    SLOW = "slow"                       # Slow responses (high latency)
    INTERMITTENT_ERRORS = "intermittent" # Random errors occasionally
    ALWAYS_FAIL = "always_fail"         # Always return errors
    CONNECTION_ISSUES = "connection"     # Connection problems
    TIMEOUT = "timeout"                 # Operations timeout
    DEGRADED = "degraded"               # Partial functionality


class ErrorType(Enum):
    """Types of errors to simulate."""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    TOOL_NOT_FOUND = "tool_not_found"
    INVALID_PARAMETERS = "invalid_parameters"
    SERVER_ERROR = "server_error"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"


@dataclass
class MockResponse:
    """Configured response for mock client."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    delay_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        if self.success:
            return self.data or {}
        else:
            return {
                "error": self.error or "Mock error",
                "code": self.error_code or "MOCK_ERROR"
            }


@dataclass
class MockConfiguration:
    """Configuration for mock client behavior."""
    
    # Response configuration
    default_tool_responses: Dict[str, MockResponse] = field(default_factory=dict)
    tool_list_response: List[Dict[str, Any]] = field(default_factory=list)
    
    # Behavior settings
    behavior_mode: MockBehavior = MockBehavior.NORMAL
    error_probability: float = 0.0  # 0.0 to 1.0
    latency_min_ms: float = 10.0
    latency_max_ms: float = 100.0
    
    # Connection settings
    connection_success_rate: float = 1.0
    max_concurrent_operations: int = 10
    
    # Error simulation
    simulated_errors: List[ErrorType] = field(default_factory=list)
    error_messages: Dict[ErrorType, str] = field(default_factory=lambda: {
        ErrorType.CONNECTION_ERROR: "Mock connection failed",
        ErrorType.TIMEOUT_ERROR: "Mock operation timed out",
        ErrorType.TOOL_NOT_FOUND: "Mock tool not found",
        ErrorType.INVALID_PARAMETERS: "Mock invalid parameters",
        ErrorType.SERVER_ERROR: "Mock server error",
        ErrorType.PERMISSION_DENIED: "Mock permission denied",
        ErrorType.RATE_LIMITED: "Mock rate limited"
    })
    
    # Performance simulation
    simulate_performance_degradation: bool = False
    cpu_usage_percent: float = 50.0
    memory_usage_mb: float = 100.0


# ============================================================================
# MOCK OPERATION TRACKING
# ============================================================================

@dataclass
class MockOperationRecord:
    """Record of a mock operation for testing assertions."""
    operation_id: str
    operation_type: str  # "connect", "disconnect", "invoke_tool", "list_tools"
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    response: Optional[Dict[str, Any]] = None


class OperationTracker:
    """Tracks mock operations for test assertions."""
    
    def __init__(self):
        """Initialize operation tracker."""
        self.operations: List[MockOperationRecord] = []
        self._operation_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
    
    def record_operation(self, record: MockOperationRecord) -> None:
        """Record an operation."""
        self.operations.append(record)
        
        # Update counters
        op_key = f"{record.operation_type}:{record.tool_name or 'N/A'}"
        self._operation_counts[op_key] = self._operation_counts.get(op_key, 0) + 1
        
        if not record.success:
            self._error_counts[op_key] = self._error_counts.get(op_key, 0) + 1
    
    def get_operation_count(self, operation_type: str, tool_name: Optional[str] = None) -> int:
        """Get count of operations."""
        op_key = f"{operation_type}:{tool_name or 'N/A'}"
        return self._operation_counts.get(op_key, 0)
    
    def get_error_count(self, operation_type: str, tool_name: Optional[str] = None) -> int:
        """Get count of errors."""
        op_key = f"{operation_type}:{tool_name or 'N/A'}"
        return self._error_counts.get(op_key, 0)
    
    def get_last_operation(self, operation_type: Optional[str] = None) -> Optional[MockOperationRecord]:
        """Get the last operation, optionally filtered by type."""
        filtered_ops = [
            op for op in self.operations 
            if operation_type is None or op.operation_type == operation_type
        ]
        return filtered_ops[-1] if filtered_ops else None
    
    def clear(self) -> None:
        """Clear all operation history."""
        self.operations.clear()
        self._operation_counts.clear()
        self._error_counts.clear()


# ============================================================================
# MOCK MCP CLIENT IMPLEMENTATION
# ============================================================================

class MockMCPClient(IAsyncMCPClient):
    """
    Comprehensive mock MCP client for testing GUI components.
    
    Features:
    - Configurable responses for any tool
    - Error simulation with various error types
    - Performance and latency simulation
    - Operation tracking for test assertions
    - Realistic connection lifecycle simulation
    - Health status and metrics simulation
    
    This mock implements the exact same interface as AsyncMCPClient,
    allowing it to be used as a drop-in replacement for testing.
    """
    
    def __init__(
        self, 
        config: Optional[MockConfiguration] = None,
        logger: Optional[std_logging.Logger] = None
    ):
        """
        Initialize MockMCPClient.
        
        Args:
            config: Mock configuration settings
            logger: Optional logger for debugging
        """
        self.config = config or MockConfiguration()
        self.logger = logger or self._create_logger()
        
        # Client state
        self._status = ClientStatus.DISCONNECTED
        self._health = ClientHealth.HEALTHY
        self._connected_at: Optional[datetime] = None
        self._operation_count = 0
        self._error_count = 0
        
        # Operation tracking
        self.tracker = OperationTracker()
        self._active_operations: Set[str] = set()
        self._operation_semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
        
        # Metrics simulation
        self._metrics = OperationMetrics()
        self._response_times: List[float] = []
        
        # Connection simulation
        self._connection_stable = True
        self._last_health_check = datetime.now()
        
        self.logger.info("MockMCPClient initialized", extra={
            "behavior_mode": self.config.behavior_mode.value,
            "error_probability": self.config.error_probability
        })
    
    def _create_logger(self) -> std_logging.Logger:
        """Create logger for mock client."""
        logger = std_logging.getLogger("study_buddy.integration.mock_mcp_client")
        if not logger.handlers:
            handler = std_logging.StreamHandler()
            formatter = std_logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(std_logging.DEBUG)
        return logger
    
    async def connect(self) -> bool:
        """Simulate connection to MCP server."""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.logger.info("Mock connecting to MCP server", extra={"operation_id": operation_id})
            
            # Simulate connection latency
            await self._simulate_latency()
            
            # Check if connection should fail
            if not self._should_connection_succeed():
                self._status = ClientStatus.ERROR
                error_msg = "Mock connection failed"
                
                # Record failed operation
                record = MockOperationRecord(
                    operation_id=operation_id,
                    operation_type="connect",
                    duration_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error=error_msg
                )
                self.tracker.record_operation(record)
                
                raise MCPClientError(error_msg)
            
            # Successful connection
            self._status = ClientStatus.CONNECTED
            self._connected_at = datetime.now()
            self._connection_stable = True
            
            # Record successful operation
            record = MockOperationRecord(
                operation_id=operation_id,
                operation_type="connect",
                duration_ms=(time.time() - start_time) * 1000,
                success=True
            )
            self.tracker.record_operation(record)
            
            self.logger.info("Mock connected successfully", extra={"operation_id": operation_id})
            return True
            
        except Exception as e:
            self._status = ClientStatus.ERROR
            self.logger.error(f"Mock connection failed: {e}", extra={"operation_id": operation_id})
            raise
    
    async def disconnect(self) -> None:
        """Simulate disconnection from MCP server."""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info("Mock disconnecting from MCP server", extra={"operation_id": operation_id})
        
        # Simulate disconnection latency
        await asyncio.sleep(0.01)  # Quick disconnection
        
        self._status = ClientStatus.DISCONNECTED
        self._connected_at = None
        
        # Record operation
        record = MockOperationRecord(
            operation_id=operation_id,
            operation_type="disconnect",
            duration_ms=(time.time() - start_time) * 1000,
            success=True
        )
        self.tracker.record_operation(record)
        
        self.logger.info("Mock disconnected successfully", extra={"operation_id": operation_id})
    
    async def invoke_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Simulate tool invocation with configurable responses."""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info(
            f"Mock invoking tool: {tool_name}", 
            extra={
                "operation_id": operation_id,
                "tool_name": tool_name,
                "parameters": parameters
            }
        )
        
        # Check connection status
        if self._status != ClientStatus.CONNECTED:
            raise MCPClientError("Mock client not connected")
        
        # Limit concurrent operations
        async with self._operation_semaphore:
            self._active_operations.add(operation_id)
            
            try:
                # Simulate operation latency
                await self._simulate_latency()
                
                # Check for timeout simulation
                if timeout and self.config.behavior_mode == MockBehavior.TIMEOUT:
                    await asyncio.sleep(timeout + 1)  # Force timeout
                
                # Check if operation should fail
                error = await self._should_operation_fail(tool_name)
                if error:
                    self._error_count += 1
                    
                    # Record failed operation
                    record = MockOperationRecord(
                        operation_id=operation_id,
                        operation_type="invoke_tool",
                        tool_name=tool_name,
                        parameters=parameters,
                        duration_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error=error
                    )
                    self.tracker.record_operation(record)
                    
                    raise MCPClientError(error)
                
                # Get configured response or generate default
                response = self._get_tool_response(tool_name, parameters)
                self._operation_count += 1
                
                # Track response time
                duration_ms = (time.time() - start_time) * 1000
                self._response_times.append(duration_ms)
                
                # Record successful operation
                record = MockOperationRecord(
                    operation_id=operation_id,
                    operation_type="invoke_tool",
                    tool_name=tool_name,
                    parameters=parameters,
                    duration_ms=duration_ms,
                    success=True,
                    response=response
                )
                self.tracker.record_operation(record)
                
                self.logger.info(
                    f"Mock tool invocation successful: {tool_name}",
                    extra={
                        "operation_id": operation_id,
                        "duration_ms": duration_ms
                    }
                )
                
                return response
                
            finally:
                self._active_operations.discard(operation_id)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Simulate listing available tools."""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info("Mock listing tools", extra={"operation_id": operation_id})
        
        # Check connection status
        if self._status != ClientStatus.CONNECTED:
            raise MCPClientError("Mock client not connected")
        
        # Simulate latency
        await self._simulate_latency()
        
        # Get configured tool list or generate default
        tools = self.config.tool_list_response or self._get_default_tools()
        
        # Record operation
        record = MockOperationRecord(
            operation_id=operation_id,
            operation_type="list_tools",
            duration_ms=(time.time() - start_time) * 1000,
            success=True,
            response={"tools": tools}
        )
        self.tracker.record_operation(record)
        
        self.logger.info(
            f"Mock tool listing successful: {len(tools)} tools",
            extra={"operation_id": operation_id, "tool_count": len(tools)}
        )
        
        return tools
    
    def get_status(self) -> ClientStatus:
        """Get current client status."""
        return self._status
    
    def get_health(self) -> HealthStatus:
        """Get comprehensive health status."""
        now = datetime.now()
        uptime = (now - self._connected_at).total_seconds() if self._connected_at else 0.0
        
        # Calculate metrics
        avg_response_time = (
            sum(self._response_times[-100:]) / len(self._response_times[-100:])
            if self._response_times else 0.0
        )
        
        error_rate = (
            (self._error_count / max(self._operation_count, 1)) * 100
            if self._operation_count > 0 else 0.0
        )
        
        # Determine health level
        health_level = ClientHealth.HEALTHY
        issues = []
        recommendations = []
        
        if error_rate > 10.0:
            health_level = ClientHealth.WARNING
            issues.append(f"High error rate: {error_rate:.1f}%")
            recommendations.append("Check tool parameters and server configuration")
        
        if avg_response_time > 1000:  # > 1 second
            health_level = ClientHealth.WARNING
            issues.append(f"High response time: {avg_response_time:.1f}ms")
            recommendations.append("Check network connection and server performance")
        
        if not self._connection_stable:
            health_level = ClientHealth.CRITICAL
            issues.append("Connection instability detected")
            recommendations.append("Restart client connection")
        
        return HealthStatus(
            client_status=self._status,
            health_level=health_level,
            last_health_check=now,
            connection_stable=self._connection_stable,
            response_time_ms=avg_response_time,
            error_rate_percent=error_rate,
            concurrent_operations=len(self._active_operations),
            max_concurrent_operations=self.config.max_concurrent_operations,
            uptime_seconds=uptime,
            issues=issues,
            recommendations=recommendations
        )
    
    # ========================================================================
    # MOCK-SPECIFIC METHODS FOR TESTING
    # ========================================================================
    
    def configure_tool_response(
        self, 
        tool_name: str, 
        response: MockResponse
    ) -> None:
        """Configure response for a specific tool."""
        self.config.default_tool_responses[tool_name] = response
        self.logger.debug(f"Configured mock response for tool: {tool_name}")
    
    def configure_error_simulation(
        self, 
        error_types: List[ErrorType], 
        probability: float = 0.1
    ) -> None:
        """Configure error simulation."""
        self.config.simulated_errors = error_types
        self.config.error_probability = probability
        self.logger.debug(f"Configured error simulation: {error_types} at {probability:.2%}")
    
    def set_behavior_mode(self, mode: MockBehavior) -> None:
        """Set mock behavior mode."""
        self.config.behavior_mode = mode
        self.logger.debug(f"Set behavior mode: {mode.value}")
    
    def simulate_connection_failure(self) -> None:
        """Simulate connection failure."""
        self._connection_stable = False
        self._status = ClientStatus.ERROR
        self.logger.debug("Simulated connection failure")
    
    def simulate_performance_degradation(
        self, 
        latency_multiplier: float = 3.0
    ) -> None:
        """Simulate performance degradation."""
        self.config.latency_min_ms *= latency_multiplier
        self.config.latency_max_ms *= latency_multiplier
        self.config.simulate_performance_degradation = True
        self.logger.debug(f"Simulated performance degradation: {latency_multiplier}x latency")
    
    def reset_state(self) -> None:
        """Reset mock client to initial state."""
        self._status = ClientStatus.DISCONNECTED
        self._health = ClientHealth.HEALTHY
        self._connected_at = None
        self._operation_count = 0
        self._error_count = 0
        self._connection_stable = True
        self._response_times.clear()
        self._active_operations.clear()
        self.tracker.clear()
        self.logger.debug("Mock client state reset")
    
    def get_operation_tracker(self) -> OperationTracker:
        """Get operation tracker for test assertions."""
        return self.tracker
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get mock client metrics."""
        return {
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "active_operations": len(self._active_operations),
            "average_response_time_ms": (
                sum(self._response_times) / len(self._response_times)
                if self._response_times else 0.0
            ),
            "error_rate_percent": (
                (self._error_count / max(self._operation_count, 1)) * 100
                if self._operation_count > 0 else 0.0
            )
        }
    
    # ========================================================================
    # INTERNAL HELPER METHODS
    # ========================================================================
    
    async def _simulate_latency(self) -> None:
        """Simulate network latency based on configuration."""
        if self.config.behavior_mode == MockBehavior.SLOW:
            # Slow mode: multiply latency
            min_ms = self.config.latency_min_ms * 5
            max_ms = self.config.latency_max_ms * 5
        else:
            min_ms = self.config.latency_min_ms
            max_ms = self.config.latency_max_ms
        
        latency_ms = random.uniform(min_ms, max_ms)
        await asyncio.sleep(latency_ms / 1000.0)
    
    def _should_connection_succeed(self) -> bool:
        """Determine if connection should succeed based on configuration."""
        if self.config.behavior_mode == MockBehavior.ALWAYS_FAIL:
            return False
        elif self.config.behavior_mode == MockBehavior.CONNECTION_ISSUES:
            return random.random() < self.config.connection_success_rate
        else:
            return random.random() < self.config.connection_success_rate
    
    async def _should_operation_fail(self, tool_name: str) -> Optional[str]:
        """Determine if operation should fail and return error message."""
        # Always fail mode
        if self.config.behavior_mode == MockBehavior.ALWAYS_FAIL:
            return self._get_random_error_message()
        
        # Intermittent errors mode
        if self.config.behavior_mode == MockBehavior.INTERMITTENT_ERRORS:
            if random.random() < self.config.error_probability:
                return self._get_random_error_message()
        
        # Timeout mode
        if self.config.behavior_mode == MockBehavior.TIMEOUT:
            return "Operation timed out"
        
        # Check configured error simulation
        if (self.config.simulated_errors and 
            random.random() < self.config.error_probability):
            error_type = random.choice(self.config.simulated_errors)
            return self.config.error_messages.get(error_type, "Simulated error")
        
        return None
    
    def _get_random_error_message(self) -> str:
        """Get a random error message."""
        error_types = list(ErrorType)
        error_type = random.choice(error_types)
        return self.config.error_messages.get(error_type, "Random mock error")
    
    def _get_tool_response(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get configured or default response for tool."""
        # Check for configured response
        if tool_name in self.config.default_tool_responses:
            mock_response = self.config.default_tool_responses[tool_name]
            return mock_response.to_dict()
        
        # Generate default response based on tool name
        return self._generate_default_response(tool_name, parameters)
    
    def _generate_default_response(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default response for tool."""
        # Common MCP tools and their typical responses
        if "upload" in tool_name.lower():
            return {
                "success": True,
                "document_id": random.randint(1, 1000),
                "title": f"Mock Document {random.randint(1, 100)}",
                "file_type": "pdf",
                "total_pages": random.randint(10, 500),
                "message": "Mock document uploaded successfully"
            }
        
        elif "list" in tool_name.lower():
            return {
                "success": True,
                "total": random.randint(0, 10),
                "documents": [
                    {
                        "id": i,
                        "title": f"Mock Document {i}",
                        "file_type": random.choice(["pdf", "docx", "md"]),
                        "upload_date": datetime.now().isoformat()
                    }
                    for i in range(random.randint(0, 5))
                ]
            }
        
        elif "search" in tool_name.lower():
            return {
                "success": True,
                "total_results": random.randint(0, 20),
                "results": [
                    {
                        "document_id": random.randint(1, 100),
                        "title": f"Mock Result {i}",
                        "relevance_score": random.uniform(0.5, 1.0),
                        "excerpt": f"Mock search result excerpt {i}"
                    }
                    for i in range(random.randint(0, 5))
                ]
            }
        
        else:
            # Generic success response
            return {
                "success": True,
                "message": f"Mock {tool_name} executed successfully",
                "data": {
                    "mock_result": True,
                    "parameters_received": parameters,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _get_default_tools(self) -> List[Dict[str, Any]]:
        """Get default list of mock tools."""
        return [
            {
                "name": "upload_document",
                "description": "Mock upload document tool",
                "parameters": {
                    "file_path": {"type": "string", "required": True},
                    "title": {"type": "string", "required": False}
                }
            },
            {
                "name": "list_documents",
                "description": "Mock list documents tool", 
                "parameters": {
                    "filters": {"type": "object", "required": False}
                }
            },
            {
                "name": "search_documents",
                "description": "Mock search documents tool",
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "required": False}
                }
            },
            {
                "name": "get_document",
                "description": "Mock get document tool",
                "parameters": {
                    "document_id": {"type": "integer", "required": True}
                }
            },
            {
                "name": "delete_document", 
                "description": "Mock delete document tool",
                "parameters": {
                    "document_id": {"type": "integer", "required": True}
                }
            }
        ]


# ============================================================================
# TESTING UTILITIES
# ============================================================================

class MockClientBuilder:
    """Builder for creating configured MockMCPClient instances."""
    
    def __init__(self):
        """Initialize builder."""
        self._config = MockConfiguration()
        self._logger: Optional[std_logging.Logger] = None
    
    def with_behavior(self, behavior: MockBehavior) -> 'MockClientBuilder':
        """Set behavior mode."""
        self._config.behavior_mode = behavior
        return self
    
    def with_error_simulation(
        self, 
        error_types: List[ErrorType], 
        probability: float = 0.1
    ) -> 'MockClientBuilder':
        """Configure error simulation."""
        self._config.simulated_errors = error_types
        self._config.error_probability = probability
        return self
    
    def with_latency(self, min_ms: float, max_ms: float) -> 'MockClientBuilder':
        """Configure latency simulation."""
        self._config.latency_min_ms = min_ms
        self._config.latency_max_ms = max_ms
        return self
    
    def with_tool_response(
        self, 
        tool_name: str, 
        response: MockResponse
    ) -> 'MockClientBuilder':
        """Configure tool response."""
        self._config.default_tool_responses[tool_name] = response
        return self
    
    def with_tools(self, tools: List[Dict[str, Any]]) -> 'MockClientBuilder':
        """Configure available tools."""
        self._config.tool_list_response = tools
        return self
    
    def with_logger(self, logger: std_logging.Logger) -> 'MockClientBuilder':
        """Set logger."""
        self._logger = logger
        return self
    
    def build(self) -> MockMCPClient:
        """Build configured mock client."""
        return MockMCPClient(config=self._config, logger=self._logger)


# ============================================================================
# PREDEFINED MOCK CLIENTS
# ============================================================================

def create_normal_mock_client() -> MockMCPClient:
    """Create mock client with normal behavior."""
    return MockClientBuilder().with_behavior(MockBehavior.NORMAL).build()


def create_slow_mock_client() -> MockMCPClient:
    """Create mock client with slow responses."""
    return (MockClientBuilder()
            .with_behavior(MockBehavior.SLOW)
            .with_latency(500, 2000)
            .build())


def create_error_prone_mock_client() -> MockMCPClient:
    """Create mock client that frequently errors."""
    return (MockClientBuilder()
            .with_behavior(MockBehavior.INTERMITTENT_ERRORS)
            .with_error_simulation([
                ErrorType.CONNECTION_ERROR,
                ErrorType.TIMEOUT_ERROR,
                ErrorType.SERVER_ERROR
            ], probability=0.3)
            .build())


def create_failing_mock_client() -> MockMCPClient:
    """Create mock client that always fails."""
    return MockClientBuilder().with_behavior(MockBehavior.ALWAYS_FAIL).build()


def create_connection_issues_mock_client() -> MockMCPClient:
    """Create mock client with connection problems."""
    return (MockClientBuilder()
            .with_behavior(MockBehavior.CONNECTION_ISSUES)
            .build())


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def _test_mock_client():
    """Test mock client functionality."""
    print("🧪 Testing Mock MCP Client...")
    
    async def run_tests():
        print("\n📝 Testing normal behavior:")
        client = create_normal_mock_client()
        
        # Test connection
        await client.connect()
        print(f"Status after connect: {client.get_status().value}")
        
        # Test tool listing
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")
        
        # Test tool invocation
        result = await client.invoke_tool("upload_document", {"file_path": "/test/file.pdf"})
        print(f"Upload result: {result.get('success', False)}")
        
        # Check metrics
        metrics = client.get_metrics()
        print(f"Operations: {metrics['operation_count']}, Errors: {metrics['error_count']}")
        
        # Test disconnect
        await client.disconnect()
        print(f"Status after disconnect: {client.get_status().value}")
        
        print("\n❌ Testing error simulation:")
        error_client = create_error_prone_mock_client()
        await error_client.connect()
        
        # Try operations that may fail
        success_count = 0
        for i in range(5):
            try:
                await error_client.invoke_tool("test_tool", {})
                success_count += 1
            except MCPClientError:
                pass
        
        print(f"Succeeded {success_count}/5 operations (expected some failures)")
        
        await error_client.disconnect()
        
        print("\n🎉 Mock client tests completed!")
    
    # Run async tests
    asyncio.run(run_tests())


if __name__ == "__main__":
    _test_mock_client()