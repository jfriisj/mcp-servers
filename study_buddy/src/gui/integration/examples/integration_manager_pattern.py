#!/usr/bin/env python3
"""
Integration Manager Pattern Example

This example demonstrates the Integration Manager pattern - a centralized 
component that orchestrates MCP operations, manages connection lifecycle,
handles errors gracefully, and provides a clean interface for GUI applications.

The Integration Manager abstracts away the complexity of MCP operations and
provides a simple, reliable interface that any GUI framework can use.

Key Benefits:
- Framework-agnostic design (works with Tkinter, PyQt, Kivy, etc.)
- Automatic connection recovery and retry logic
- Operation queuing and batching for efficiency
- Comprehensive error handling with user-friendly messages
- Health monitoring and performance metrics
- Thread-safe operations for GUI applications

Usage:
    manager = StudyBuddyIntegrationManager()
    await manager.initialize()
    
    # Upload document
    result = await manager.upload_document("path/to/file.pdf")
    
    # List documents
    documents = await manager.list_documents()

Architecture:
    GUI Application
         ↓
    Integration Manager (This Class)
         ↓
    MCP Client
         ↓
    MCP Server
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Union
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import weakref

# Import MCP integration layer
try:
    from gui.integration import (
        MCPClient, 
        ConfigManager, 
        MCPConnectionError,
        ConnectionState,
        OperationProgress,
        ConnectionHealth
    )
except ImportError as e:
    print(f"❌ Failed to import MCP integration layer: {e}")
    print("💡 This is a template example - imports will work when integration layer is implemented")


class OperationStatus(Enum):
    """Status of an operation"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class OperationType(Enum):
    """Types of MCP operations"""
    UPLOAD_DOCUMENT = "upload_document"
    LIST_DOCUMENTS = "list_documents"
    SEARCH_DOCUMENTS = "search_documents"
    INDEX_DOCUMENT = "index_document"
    DELETE_DOCUMENT = "delete_document"
    GET_DOCUMENT_STRUCTURE = "get_document_structure"
    GET_CHUNK_CONTENT = "get_chunk_content"
    SAVE_SUMMARY = "save_summary"
    HEALTH_CHECK = "health_check"


@dataclass
class OperationRequest:
    """Represents a queued operation request"""
    id: str
    type: OperationType
    parameters: Dict[str, Any]
    callback: Optional[Callable] = None
    progress_callback: Optional[Callable] = None
    priority: int = 0  # Higher number = higher priority
    max_retries: int = 3
    timeout_seconds: int = 60
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: OperationStatus = OperationStatus.PENDING
    retry_count: int = 0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['type'] = self.type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        # Remove non-serializable callbacks
        data.pop('callback', None)
        data.pop('progress_callback', None)
        return data


class StudyBuddyIntegrationManager:
    """
    Centralized Integration Manager for Study Buddy MCP operations.
    
    This class provides a high-level, framework-agnostic interface for MCP
    operations with automatic error recovery, connection management, and
    comprehensive monitoring.
    
    Design Patterns Used:
    - Facade Pattern: Simplifies MCP client complexity
    - Observer Pattern: Event notifications for GUI updates
    - Command Pattern: Operation queuing and execution
    - Singleton Pattern: Single point of MCP integration
    - Circuit Breaker Pattern: Automatic failure recovery
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        # Configuration
        self.config = config or self._create_default_config()
        
        # MCP Client
        self.client: Optional[MCPClient] = None
        self.connection_state = ConnectionState.DISCONNECTED
        
        # Operation Management
        self.operation_queue: List[OperationRequest] = []
        self.active_operations: Dict[str, OperationRequest] = {}
        self.completed_operations: Dict[str, OperationRequest] = {}
        self.operation_counter = 0
        
        # Threading
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.background_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="MCPOp")
        self.shutdown_event = threading.Event()
        self.operation_lock = threading.RLock()
        
        # Event Handling
        self.connection_listeners: List[Callable] = []
        self.progress_listeners: List[Callable] = []
        self.error_listeners: List[Callable] = []
        self.operation_listeners: List[Callable] = []
        
        # Health and Performance Monitoring
        self.health_status: Optional[ConnectionHealth] = None
        self.performance_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "retry_operations": 0,
            "average_response_time": 0.0,
            "uptime_start": datetime.now()
        }
        
        # Error Recovery
        self.circuit_breaker_open = False
        self.circuit_breaker_reset_time: Optional[datetime] = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
        # Logging
        self.logger = self._setup_logging()
        
        self.logger.info("StudyBuddyIntegrationManager initialized")
    
    def _create_default_config(self) -> ConfigManager:
        """Create default configuration"""
        return ConfigManager({
            "server_path": "mcp-server/main.py",
            "timeout": 60,
            "retry_attempts": 3,
            "log_level": "INFO",
            "min_connections": 2,
            "max_connections": 5,
            "health_check_interval": 30,
            "operation_timeout": 300,
            "max_queue_size": 100
        })
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the integration manager"""
        logger = logging.getLogger("StudyBuddyIntegration")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # === Lifecycle Management ===
    
    async def initialize(self) -> bool:
        """
        Initialize the integration manager and establish MCP connection.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info("Initializing Integration Manager...")
            
            # Start background event loop
            self._start_background_thread()
            
            # Wait for background thread to be ready
            await asyncio.sleep(0.5)
            
            # Create and configure MCP client
            if not await self._initialize_mcp_client():
                return False
            
            # Start periodic tasks
            self._start_periodic_tasks()
            
            self.logger.info("✅ Integration Manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Integration Manager: {e}")
            self._notify_error_listeners(e, {"context": "initialization"})
            return False
    
    async def shutdown(self):
        """
        Gracefully shutdown the integration manager.
        """
        self.logger.info("Shutting down Integration Manager...")
        
        try:
            # Signal shutdown
            self.shutdown_event.set()
            
            # Cancel pending operations
            await self._cancel_pending_operations()
            
            # Disconnect MCP client
            if self.client:
                await self.client.disconnect()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True, timeout=10)
            
            # Wait for background thread
            if self.background_thread and self.background_thread.is_alive():
                self.background_thread.join(timeout=5)
            
            self.logger.info("✅ Integration Manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"⚠️ Error during shutdown: {e}")
    
    def _start_background_thread(self):
        """Start background thread for async operations"""
        if self.background_thread and self.background_thread.is_alive():
            return
        
        self.background_thread = threading.Thread(
            target=self._run_background_loop,
            name="MCPIntegrationManager",
            daemon=True
        )
        self.background_thread.start()
    
    def _run_background_loop(self):
        """Run background event loop"""
        try:
            # Create event loop for this thread
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            # Run until shutdown
            self.event_loop.run_until_complete(self._background_main_loop())
            
        except Exception as e:
            self.logger.error(f"Background thread error: {e}")
        finally:
            if self.event_loop and not self.event_loop.is_closed():
                self.event_loop.close()
    
    async def _background_main_loop(self):
        """Main loop for background thread"""
        self.logger.info("Background event loop started")
        
        while not self.shutdown_event.is_set():
            try:
                # Process operation queue
                await self._process_operation_queue()
                
                # Health check if needed
                await self._periodic_health_check()
                
                # Circuit breaker recovery check
                self._check_circuit_breaker_recovery()
                
                # Brief pause
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Background loop error: {e}")
                await asyncio.sleep(1)  # Longer pause on error
    
    async def _initialize_mcp_client(self) -> bool:
        """Initialize MCP client with error handling"""
        try:
            self.logger.info("Creating MCP client...")
            
            # Create client
            self.client = MCPClient(self.config)
            
            # Set up event listeners
            self.client.add_connection_listener(self._on_connection_change)
            self.client.add_error_listener(self._on_mcp_error)
            
            # Attempt connection with retries
            for attempt in range(3):
                try:
                    self.logger.info(f"Connection attempt {attempt + 1}/3...")
                    success = await self.client.connect()
                    
                    if success:
                        self.logger.info("✅ MCP client connected successfully")
                        self._update_connection_state(ConnectionState.CONNECTED)
                        return True
                    else:
                        self.logger.warning(f"Connection attempt {attempt + 1} failed")
                        
                except Exception as e:
                    self.logger.warning(f"Connection attempt {attempt + 1} error: {e}")
                
                # Wait before retry
                if attempt < 2:  # Don't wait after final attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # All attempts failed
            self.logger.error("❌ Failed to connect MCP client after 3 attempts")
            self._update_connection_state(ConnectionState.ERROR)
            return False
            
        except Exception as e:
            self.logger.error(f"MCP client initialization error: {e}")
            self._update_connection_state(ConnectionState.ERROR)
            return False
    
    def _start_periodic_tasks(self):
        """Start periodic background tasks"""
        # Health monitoring is handled in the main background loop
        pass
    
    # === Operation Management ===
    
    def queue_operation(
        self, 
        operation_type: OperationType, 
        parameters: Dict[str, Any],
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        priority: int = 0,
        timeout: int = 60
    ) -> str:
        """
        Queue an operation for execution.
        
        Args:
            operation_type: Type of operation to perform
            parameters: Operation parameters
            callback: Callback for operation completion
            progress_callback: Callback for progress updates
            priority: Operation priority (higher = first)
            timeout: Timeout in seconds
            
        Returns:
            str: Operation ID
        """
        with self.operation_lock:
            self.operation_counter += 1
            operation_id = f"op_{self.operation_counter}_{int(time.time())}"
            
            # Check queue size
            if len(self.operation_queue) >= self.config.get("max_queue_size", 100):
                raise RuntimeError("Operation queue is full")
            
            # Create operation request
            request = OperationRequest(
                id=operation_id,
                type=operation_type,
                parameters=parameters,
                callback=callback,
                progress_callback=progress_callback,
                priority=priority,
                timeout_seconds=timeout
            )
            
            # Add to queue (sorted by priority)
            self.operation_queue.append(request)
            self.operation_queue.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info(f"Queued operation: {operation_type.value} (ID: {operation_id})")
            
            return operation_id
    
    async def _process_operation_queue(self):
        """Process pending operations in the queue"""
        if not self.operation_queue or self.circuit_breaker_open:
            return
        
        if not self.client or self.connection_state != ConnectionState.CONNECTED:
            return
        
        with self.operation_lock:
            # Get next operation
            if not self.operation_queue:
                return
            
            request = self.operation_queue.pop(0)
            self.active_operations[request.id] = request
        
        # Execute operation
        await self._execute_operation(request)
    
    async def _execute_operation(self, request: OperationRequest):
        """Execute a single operation with error handling and retries"""
        request.status = OperationStatus.RUNNING
        request.started_at = datetime.now()
        
        self.logger.info(f"Executing operation: {request.type.value} (ID: {request.id})")
        
        try:
            # Update metrics
            self.performance_metrics["total_operations"] += 1
            
            # Execute based on operation type
            result = await self._dispatch_operation(request)
            
            # Operation successful
            request.status = OperationStatus.COMPLETED
            request.completed_at = datetime.now()
            request.result = result
            
            # Update metrics
            self.performance_metrics["successful_operations"] += 1
            self._update_response_time_metric(request)
            
            # Reset circuit breaker on success
            self.consecutive_failures = 0
            self.circuit_breaker_open = False
            
            self.logger.info(f"✅ Operation completed: {request.type.value} (ID: {request.id})")
            
            # Notify completion
            if request.callback:
                try:
                    request.callback(result)
                except Exception as e:
                    self.logger.error(f"Callback error for operation {request.id}: {e}")
            
        except Exception as e:
            # Operation failed
            self.logger.error(f"❌ Operation failed: {request.type.value} (ID: {request.id}) - {e}")
            
            request.error = str(e)
            request.retry_count += 1
            
            # Check if we should retry
            if request.retry_count <= request.max_retries and not self.shutdown_event.is_set():
                self.logger.info(f"🔄 Retrying operation: {request.type.value} (attempt {request.retry_count}/{request.max_retries})")
                
                request.status = OperationStatus.RETRYING
                self.performance_metrics["retry_operations"] += 1
                
                # Re-queue with backoff
                await asyncio.sleep(2 ** request.retry_count)  # Exponential backoff
                
                with self.operation_lock:
                    self.operation_queue.insert(0, request)  # High priority for retries
                
            else:
                # Max retries exceeded
                request.status = OperationStatus.FAILED
                request.completed_at = datetime.now()
                
                # Update metrics
                self.performance_metrics["failed_operations"] += 1
                
                # Circuit breaker logic
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self._open_circuit_breaker()
                
                # Notify error
                self._notify_error_listeners(e, {
                    "operation_id": request.id,
                    "operation_type": request.type.value,
                    "retry_count": request.retry_count
                })
                
                # Notify completion with error
                if request.callback:
                    try:
                        request.callback({"success": False, "error": str(e)})
                    except Exception as callback_error:
                        self.logger.error(f"Callback error for failed operation {request.id}: {callback_error}")
        
        finally:
            # Move to completed operations
            with self.operation_lock:
                self.active_operations.pop(request.id, None)
                self.completed_operations[request.id] = request
                
                # Limit completed operations history
                if len(self.completed_operations) > 1000:
                    # Remove oldest 100 operations
                    oldest_ids = sorted(self.completed_operations.keys())[:100]
                    for old_id in oldest_ids:
                        self.completed_operations.pop(old_id, None)
    
    async def _dispatch_operation(self, request: OperationRequest) -> Dict[str, Any]:
        """Dispatch operation to appropriate handler"""
        operation_type = request.type
        parameters = request.parameters
        
        # Create progress callback wrapper
        def progress_wrapper(progress: OperationProgress):
            if request.progress_callback:
                try:
                    request.progress_callback(progress)
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
        
        # Dispatch based on operation type
        if operation_type == OperationType.UPLOAD_DOCUMENT:
            return await self.client.upload_document(
                progress_callback=progress_wrapper,
                **parameters
            )
        
        elif operation_type == OperationType.LIST_DOCUMENTS:
            return await self.client.list_documents(**parameters)
        
        elif operation_type == OperationType.SEARCH_DOCUMENTS:
            return await self.client.search_documents(**parameters)
        
        elif operation_type == OperationType.INDEX_DOCUMENT:
            return await self.client.index_document(
                progress_callback=progress_wrapper,
                **parameters
            )
        
        elif operation_type == OperationType.DELETE_DOCUMENT:
            return await self.client.delete_document(**parameters)
        
        elif operation_type == OperationType.GET_DOCUMENT_STRUCTURE:
            return await self.client.get_document_structure(**parameters)
        
        elif operation_type == OperationType.GET_CHUNK_CONTENT:
            return await self.client.get_chunk_content(**parameters)
        
        elif operation_type == OperationType.SAVE_SUMMARY:
            return await self.client.save_summary(**parameters)
        
        elif operation_type == OperationType.HEALTH_CHECK:
            health = await self.client.get_health_status()
            self.health_status = health
            return {"success": True, "health": health}
        
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
    
    # === High-Level API Methods ===
    
    def upload_document_async(
        self, 
        file_path: str, 
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Upload document asynchronously.
        
        Args:
            file_path: Path to document file
            callback: Completion callback
            progress_callback: Progress callback
            **kwargs: Additional parameters
            
        Returns:
            str: Operation ID
        """
        parameters = {"file_path": file_path, **kwargs}
        
        return self.queue_operation(
            OperationType.UPLOAD_DOCUMENT,
            parameters,
            callback=callback,
            progress_callback=progress_callback
        )
    
    def list_documents_async(
        self,
        callback: Optional[Callable] = None,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> str:
        """
        List documents asynchronously.
        
        Args:
            callback: Completion callback
            filters: Optional filters
            **kwargs: Additional parameters
            
        Returns:
            str: Operation ID
        """
        parameters = {"filters": filters, **kwargs}
        
        return self.queue_operation(
            OperationType.LIST_DOCUMENTS,
            parameters,
            callback=callback
        )
    
    def search_documents_async(
        self,
        query: str,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Search documents asynchronously.
        
        Args:
            query: Search query
            callback: Completion callback
            **kwargs: Additional parameters
            
        Returns:
            str: Operation ID
        """
        parameters = {"query": query, **kwargs}
        
        return self.queue_operation(
            OperationType.SEARCH_DOCUMENTS,
            parameters,
            callback=callback
        )
    
    def index_document_async(
        self,
        document_id: int,
        strategy: str = "auto",
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Index document asynchronously.
        
        Args:
            document_id: ID of document to index
            strategy: Indexing strategy
            callback: Completion callback
            progress_callback: Progress callback
            **kwargs: Additional parameters
            
        Returns:
            str: Operation ID
        """
        parameters = {
            "document_id": document_id,
            "strategy": strategy,
            **kwargs
        }
        
        return self.queue_operation(
            OperationType.INDEX_DOCUMENT,
            parameters,
            callback=callback,
            progress_callback=progress_callback,
            priority=5  # Higher priority for indexing
        )
    
    def delete_document_async(
        self,
        document_id: int,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Delete document asynchronously.
        
        Args:
            document_id: ID of document to delete
            callback: Completion callback
            **kwargs: Additional parameters
            
        Returns:
            str: Operation ID
        """
        parameters = {"document_id": document_id, **kwargs}
        
        return self.queue_operation(
            OperationType.DELETE_DOCUMENT,
            parameters,
            callback=callback,
            priority=10  # High priority for deletions
        )
    
    # === Synchronous Convenience Methods ===
    
    async def upload_document(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Upload document synchronously"""
        if not self.client:
            raise RuntimeError("MCP client not initialized")
        
        return await self.client.upload_document(file_path=file_path, **kwargs)
    
    async def list_documents(self, filters: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """List documents synchronously"""
        if not self.client:
            raise RuntimeError("MCP client not initialized")
        
        return await self.client.list_documents(filters=filters, **kwargs)
    
    async def search_documents(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search documents synchronously"""
        if not self.client:
            raise RuntimeError("MCP client not initialized")
        
        return await self.client.search_documents(query=query, **kwargs)
    
    # === Circuit Breaker ===
    
    def _open_circuit_breaker(self):
        """Open circuit breaker to prevent cascade failures"""
        self.circuit_breaker_open = True
        self.circuit_breaker_reset_time = datetime.now() + timedelta(minutes=5)
        
        self.logger.warning(f"🔒 Circuit breaker OPEN - too many consecutive failures ({self.consecutive_failures})")
        self._notify_error_listeners(
            Exception("Circuit breaker activated - MCP operations temporarily disabled"),
            {"circuit_breaker": True, "consecutive_failures": self.consecutive_failures}
        )
    
    def _check_circuit_breaker_recovery(self):
        """Check if circuit breaker can be reset"""
        if (self.circuit_breaker_open and 
            self.circuit_breaker_reset_time and 
            datetime.now() >= self.circuit_breaker_reset_time):
            
            self.circuit_breaker_open = False
            self.circuit_breaker_reset_time = None
            self.consecutive_failures = 0
            
            self.logger.info("🔓 Circuit breaker RESET - operations resumed")
    
    # === Health Monitoring ===
    
    async def _periodic_health_check(self):
        """Perform periodic health checks"""
        if not hasattr(self, '_last_health_check'):
            self._last_health_check = datetime.now()
        
        # Check if it's time for health check
        interval = self.config.get("health_check_interval", 30)
        if (datetime.now() - self._last_health_check).seconds < interval:
            return
        
        self._last_health_check = datetime.now()
        
        # Queue health check operation
        self.queue_operation(
            OperationType.HEALTH_CHECK,
            {},
            priority=-1  # Low priority
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        uptime_seconds = (datetime.now() - self.performance_metrics["uptime_start"]).total_seconds()
        
        return {
            **self.performance_metrics,
            "uptime_seconds": uptime_seconds,
            "connection_state": self.connection_state.value if self.connection_state else "unknown",
            "active_operations_count": len(self.active_operations),
            "queued_operations_count": len(self.operation_queue),
            "circuit_breaker_open": self.circuit_breaker_open,
            "consecutive_failures": self.consecutive_failures,
            "health_status": self.health_status.to_dict() if self.health_status else None
        }
    
    def _update_response_time_metric(self, request: OperationRequest):
        """Update average response time metric"""
        if request.started_at and request.completed_at:
            response_time = (request.completed_at - request.started_at).total_seconds()
            
            current_avg = self.performance_metrics["average_response_time"]
            total_ops = self.performance_metrics["successful_operations"]
            
            # Calculate running average
            if total_ops == 1:
                self.performance_metrics["average_response_time"] = response_time
            else:
                self.performance_metrics["average_response_time"] = (
                    (current_avg * (total_ops - 1) + response_time) / total_ops
                )
    
    # === Event Handling ===
    
    def add_connection_listener(self, listener: Callable):
        """Add connection state change listener"""
        self.connection_listeners.append(listener)
    
    def add_progress_listener(self, listener: Callable):
        """Add progress update listener"""
        self.progress_listeners.append(listener)
    
    def add_error_listener(self, listener: Callable):
        """Add error event listener"""
        self.error_listeners.append(listener)
    
    def add_operation_listener(self, listener: Callable):
        """Add operation status change listener"""
        self.operation_listeners.append(listener)
    
    def _update_connection_state(self, state: ConnectionState):
        """Update connection state and notify listeners"""
        self.connection_state = state
        self._notify_connection_listeners(state)
    
    def _notify_connection_listeners(self, state: ConnectionState):
        """Notify connection state change listeners"""
        for listener in self.connection_listeners[:]:  # Copy to avoid modification during iteration
            try:
                listener(state)
            except Exception as e:
                self.logger.error(f"Connection listener error: {e}")
    
    def _notify_progress_listeners(self, operation_id: str, progress: OperationProgress):
        """Notify progress update listeners"""
        for listener in self.progress_listeners[:]:
            try:
                listener(operation_id, progress)
            except Exception as e:
                self.logger.error(f"Progress listener error: {e}")
    
    def _notify_error_listeners(self, error: Exception, context: Dict[str, Any]):
        """Notify error event listeners"""
        for listener in self.error_listeners[:]:
            try:
                listener(error, context)
            except Exception as e:
                self.logger.error(f"Error listener error: {e}")
    
    def _notify_operation_listeners(self, operation: OperationRequest):
        """Notify operation status change listeners"""
        for listener in self.operation_listeners[:]:
            try:
                listener(operation)
            except Exception as e:
                self.logger.error(f"Operation listener error: {e}")
    
    def _on_connection_change(self, state: ConnectionState):
        """Handle MCP client connection changes"""
        self._update_connection_state(state)
    
    def _on_mcp_error(self, error: Exception, context: Dict[str, Any]):
        """Handle MCP client errors"""
        self._notify_error_listeners(error, context)
    
    # === Utility Methods ===
    
    async def _cancel_pending_operations(self):
        """Cancel all pending operations"""
        with self.operation_lock:
            # Cancel queued operations
            for request in self.operation_queue:
                request.status = OperationStatus.CANCELLED
                request.completed_at = datetime.now()
                
                if request.callback:
                    try:
                        request.callback({"success": False, "error": "Operation cancelled due to shutdown"})
                    except:
                        pass
            
            self.operation_queue.clear()
            
            # Cancel active operations
            for request in self.active_operations.values():
                request.status = OperationStatus.CANCELLED
                request.completed_at = datetime.now()
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationRequest]:
        """Get status of an operation by ID"""
        # Check active operations first
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]
        
        # Check completed operations
        if operation_id in self.completed_operations:
            return self.completed_operations[operation_id]
        
        # Check queued operations
        for request in self.operation_queue:
            if request.id == operation_id:
                return request
        
        return None
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a specific operation"""
        with self.operation_lock:
            # Remove from queue if pending
            for i, request in enumerate(self.operation_queue):
                if request.id == operation_id:
                    request.status = OperationStatus.CANCELLED
                    self.operation_queue.pop(i)
                    
                    if request.callback:
                        try:
                            request.callback({"success": False, "error": "Operation cancelled"})
                        except:
                            pass
                    
                    return True
            
            # Cannot cancel active operations (would require more complex cancellation)
            return False
    
    def is_healthy(self) -> bool:
        """Check if the integration manager is healthy"""
        return (
            self.connection_state == ConnectionState.CONNECTED and
            not self.circuit_breaker_open and
            self.client is not None and
            not self.shutdown_event.is_set()
        )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.run(self.shutdown())


# === Usage Examples ===

async def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    # Create and initialize manager
    manager = StudyBuddyIntegrationManager()
    
    try:
        # Initialize
        success = await manager.initialize()
        if not success:
            print("❌ Failed to initialize manager")
            return
        
        print("✅ Manager initialized successfully")
        
        # Upload a document synchronously
        print("📤 Uploading document...")
        result = await manager.upload_document("path/to/document.pdf")
        
        if result.get("success"):
            doc_id = result["data"]["document_id"]
            print(f"✅ Document uploaded with ID: {doc_id}")
            
            # List documents
            docs_result = await manager.list_documents()
            if docs_result.get("success"):
                doc_count = len(docs_result["data"]["documents"])
                print(f"📚 Found {doc_count} documents")
        
        # Get performance metrics
        metrics = manager.get_performance_metrics()
        print(f"📊 Performance: {metrics['successful_operations']} successful operations")
        
    finally:
        # Always shutdown
        await manager.shutdown()


async def example_async_operations():
    """Asynchronous operations example"""
    print("=== Async Operations Example ===")
    
    manager = StudyBuddyIntegrationManager()
    
    try:
        await manager.initialize()
        
        # Define callbacks
        def upload_completed(result):
            if result.get("success"):
                print(f"✅ Upload completed: Document ID {result['data']['document_id']}")
            else:
                print(f"❌ Upload failed: {result.get('error')}")
        
        def upload_progress(progress):
            print(f"📈 Upload progress: {progress.progress_percent}% - {progress.current_step}")
        
        # Queue multiple operations
        op1_id = manager.upload_document_async(
            "document1.pdf",
            callback=upload_completed,
            progress_callback=upload_progress
        )
        
        op2_id = manager.upload_document_async(
            "document2.docx", 
            callback=upload_completed
        )
        
        print(f"Queued operations: {op1_id}, {op2_id}")
        
        # Wait for operations to complete
        while True:
            op1_status = manager.get_operation_status(op1_id)
            op2_status = manager.get_operation_status(op2_id)
            
            if (op1_status.status in [OperationStatus.COMPLETED, OperationStatus.FAILED] and
                op2_status.status in [OperationStatus.COMPLETED, OperationStatus.FAILED]):
                break
            
            await asyncio.sleep(1)
        
        print("🏁 All operations completed")
        
    finally:
        await manager.shutdown()


async def example_error_recovery():
    """Error recovery and resilience example"""
    print("=== Error Recovery Example ===")
    
    # Create manager with custom configuration for testing
    config = ConfigManager({
        "server_path": "nonexistent/server.py",  # Intentionally wrong path
        "timeout": 5,
        "retry_attempts": 2,
        "log_level": "INFO"
    })
    
    manager = StudyBuddyIntegrationManager(config)
    
    # Add error listener
    def on_error(error, context):
        print(f"🚨 Error captured: {error}")
        print(f"   Context: {context}")
    
    manager.add_error_listener(on_error)
    
    # Add connection listener
    def on_connection_change(state):
        print(f"🔌 Connection state: {state.value}")
    
    manager.add_connection_listener(on_connection_change)
    
    try:
        # Try to initialize (will fail)
        success = await manager.initialize()
        print(f"Initialization result: {success}")
        
        # Try operations (should be queued but fail)
        op_id = manager.upload_document_async("test.pdf")
        print(f"Queued operation: {op_id}")
        
        # Wait a bit to see what happens
        await asyncio.sleep(10)
        
        # Check operation status
        status = manager.get_operation_status(op_id)
        if status:
            print(f"Operation status: {status.status.value}")
            if status.error:
                print(f"Operation error: {status.error}")
        
        # Check metrics
        metrics = manager.get_performance_metrics()
        print(f"Metrics: {metrics}")
        
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    """Run examples"""
    print("Study Buddy Integration Manager Examples")
    print("=" * 50)
    
    # Run basic usage example
    asyncio.run(example_basic_usage())
    
    print("\\n")
    
    # Run async operations example
    asyncio.run(example_async_operations())
    
    print("\\n")
    
    # Run error recovery example  
    asyncio.run(example_error_recovery())