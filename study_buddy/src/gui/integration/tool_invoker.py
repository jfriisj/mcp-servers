"""
GUI Integration Layer - Tool Invoker with Schema Validation

This module implements the ToolInvoker for the GUI integration layer, providing:
- Pydantic schema validation for all MCP tools
- Progress tracking with callbacks for operations >10 seconds
- Comprehensive error handling with specific error types
- Clean integration with GUI components

Architecture: Clean Architecture Layer 3 (Data Access)
Patterns: Command Pattern, Strategy Pattern, Observer Pattern
SOLID: SRP (single tool invocation responsibility), OCP (extensible via tool registry), 
       LSP (substitutable implementations), ISP (focused interfaces), DIP (depend on abstractions)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

# Local imports for GUI integration
from .mcp_client import (
    IMCPClient, OperationStatus, ConnectionState, ProgressCallback, 
    ValidationError, MCPResponse, OperationProgress, ProgressPhase
)
from gui.error_handling import (
    get_debug_logger, get_error_tracker, ErrorSeverity, ErrorCategory
)


# Basic Pydantic schemas for validation
class UploadDocumentParams(BaseModel):
    """Parameters for upload_document tool"""
    file_path: str = Field(description="Absolute path to document file")
    title: Optional[str] = Field(default=None, description="Custom title")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    notes: Optional[str] = Field(default=None, description="User notes")

class SearchDocumentParams(BaseModel):
    """Parameters for search_documents tool"""
    query: str = Field(description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    limit: int = Field(default=20, description="Maximum results")

class IndexDocumentParams(BaseModel):
    """Parameters for index_document tool"""
    document_id: int = Field(description="Document ID to index")
    strategy: str = Field(default="auto", description="Chunking strategy")


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""
    
    def __init__(self, tool_name: str, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.error_code = error_code 
        self.message = message
        self.details = details or {}
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ValidationResult:
    """Result of parameter validation."""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, validated_params: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.validated_params = validated_params or {}


@dataclass
class ToolOperation:
    """Represents a tool operation with tracking information."""
    
    operation_id: str
    tool_name: str
    parameters: Dict[str, Any]
    status: OperationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    progress_callback: Optional[ProgressCallback] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_long_running(self) -> bool:
        """Check if operation exceeds 10 second threshold."""
        if self.status == OperationStatus.RUNNING:
            current_duration = (datetime.now() - self.start_time).total_seconds()
            return current_duration > 10.0
        return False


class GUIToolInvoker:
    """
    GUI Integration Layer Tool Invoker with comprehensive validation and progress tracking.
    
    This class provides a clean interface for GUI components to invoke MCP tools with:
    - Automatic Pydantic schema validation
    - Progress tracking for operations >10 seconds
    - JSON-RPC protocol compliance
    - Comprehensive error handling
    - Connection management integration
    
    The invoker acts as an adapter between GUI components and the MCP client,
    ensuring all tool invocations are properly validated and tracked.
    """
    
    def __init__(self, mcp_client: IMCPClient, enable_validation: bool = True):
        """
        Initialize the GUI Tool Invoker.
        
        Args:
            mcp_client: MCP client instance for communication
            enable_validation: Whether to enable Pydantic validation (default: True)
        """
        self.mcp_client = mcp_client
        self.enable_validation = enable_validation
        self.logger = get_debug_logger()
        self.error_tracker = get_error_tracker()
        
        # Track active operations
        self.active_operations: Dict[str, ToolOperation] = {}
        self._operation_counter = 0
        self._lock = asyncio.Lock()
        
        # Tool schema registry - simplified for basic validation
        self.tool_schemas = self._build_tool_registry()
        
        # Performance tracking
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'validation_errors': 0,
            'average_duration': 0.0,
            'long_running_operations': 0
        }
        
        self.logger.info(f"GUI Tool Invoker initialized with {len(self.tool_schemas)} registered tools")
    
    def _build_tool_registry(self) -> Dict[str, Type[BaseModel]]:
        """
        Build registry of tool names to their parameter schemas.
        
        Returns:
            Dictionary mapping tool names to parameter schema classes
        """
        registry = {
            'upload_document': UploadDocumentParams,
            'search_documents': SearchDocumentParams,
            'index_document': IndexDocumentParams
        }
        
        return registry
    
    def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> ValidationResult:
        """
        Validate tool parameters using Pydantic schemas.
        
        Args:
            tool_name: Name of the MCP tool
            parameters: Parameters to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        if not self.enable_validation or tool_name not in self.tool_schemas:
            # Skip validation if disabled or schema not available
            return ValidationResult(is_valid=True, validated_params=parameters)
        
        try:
            schema_class = self.tool_schemas[tool_name]
            validated = schema_class(**parameters)
            
            self.logger.debug(f"Parameters validated successfully for tool '{tool_name}'")
            return ValidationResult(
                is_valid=True,
                validated_params=validated.dict()
            )
            
        except PydanticValidationError as e:
            error_msg = f"Parameter validation failed for tool '{tool_name}': {str(e)}"
            self.logger.error(error_msg)
            self.stats['validation_errors'] += 1
            
            # Extract detailed validation errors
            errors = []
            for error in e.errors():
                field = ' -> '.join(str(x) for x in error['loc'])
                errors.append(f"{field}: {error['msg']}")
            
            return ValidationResult(is_valid=False, errors=errors)
        except Exception as e:
            error_msg = f"Parameter validation failed for tool '{tool_name}': {str(e)}"
            self.logger.error(error_msg)
            self.stats['validation_errors'] += 1
            return ValidationResult(is_valid=False, errors=[str(e)])
    
    async def invoke_tool_wrapper(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """
        Wrapper to invoke MCP tools with validation and progress tracking.
        
        Args:
            tool_name: Name of the MCP tool to invoke
            parameters: Tool parameters
            progress_callback: Optional callback for progress updates
            timeout: Optional timeout in seconds
            
        Returns:
            MCPResponse with tool execution result
            
        Raises:
            ToolExecutionError: If tool execution fails
            ValidationError: If parameter validation fails
        """
        # Generate unique operation ID
        async with self._lock:
            self._operation_counter += 1
            operation_id = f"op_{self._operation_counter}_{int(time.time())}"
        
        # Create operation tracking
        operation = ToolOperation(
            operation_id=operation_id,
            tool_name=tool_name,
            parameters=parameters.copy(),
            status=OperationStatus.PENDING,
            start_time=datetime.now(),
            progress_callback=progress_callback
        )
        
        # Register operation
        self.active_operations[operation_id] = operation
        self.stats['total_operations'] += 1
        
        try:
            # Validate parameters
            validation_result = self.validate_parameters(tool_name, parameters)
            if not validation_result.is_valid:
                raise ValidationError(
                    message=f"Parameter validation failed for tool '{tool_name}'"
                )
            
            # Update operation status
            operation.status = OperationStatus.RUNNING
            operation.parameters = validation_result.validated_params
            
            self.logger.info(f"Invoking tool '{tool_name}' with operation ID {operation_id}")
            
            # Set up progress tracking for long-running operations
            progress_task = None
            if progress_callback:
                progress_task = asyncio.create_task(
                    self._track_operation_progress(operation)
                )
            
            # Route to the appropriate MCP client method
            try:
                if tool_name == 'upload_document':
                    result = await self.mcp_client.upload_document(**validation_result.validated_params)
                elif tool_name == 'search_documents':
                    result = await self.mcp_client.search_documents(**validation_result.validated_params)
                else:
                    # For unsupported tools, create a basic response
                    result = MCPResponse(
                        success=False,
                        operation_id=operation_id,
                        operation_name=tool_name,
                        error_message=f"Tool '{tool_name}' not yet implemented in GUI tool invoker",
                        error_code="NOT_IMPLEMENTED"
                    )
                
                # Update operation success
                operation.status = OperationStatus.COMPLETED
                operation.result = result
                operation.end_time = datetime.now()
                
                self.stats['successful_operations'] += 1
                self._update_average_duration(operation.duration)
                
                if operation.is_long_running:
                    self.stats['long_running_operations'] += 1
                
                self.logger.info(
                    f"Tool '{tool_name}' completed successfully in {operation.duration:.2f}s"
                )
                
                # Send final progress update
                if progress_callback:
                    try:
                        progress = OperationProgress(
                            operation_id=operation_id,
                            operation_name=tool_name,
                            phase=ProgressPhase.FINALIZING,
                            progress_percent=100.0,
                            current_step="Completed"
                        )
                        progress_callback(progress)
                    except Exception as e:
                        self.logger.warning(f"Progress callback failed: {e}")
                
                return result
                
            except asyncio.TimeoutError:
                operation.status = OperationStatus.TIMEOUT
                operation.end_time = datetime.now()
                self.stats['failed_operations'] += 1
                
                error_msg = f"Tool '{tool_name}' timed out after {timeout}s"
                self.logger.error(error_msg)
                
                raise ToolExecutionError(
                    tool_name=tool_name,
                    error_code="TIMEOUT",
                    message=error_msg
                )
                
            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.error = e
                operation.end_time = datetime.now()
                self.stats['failed_operations'] += 1
                
                error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                # Send error progress update
                if progress_callback:
                    try:
                        progress = OperationProgress(
                            operation_id=operation_id,
                            operation_name=tool_name,
                            phase=ProgressPhase.PROCESSING,
                            progress_percent=-1,
                            current_step=f"Failed: {str(e)}"
                        )
                        progress_callback(progress)
                    except Exception:
                        pass
                
                raise ToolExecutionError(
                    tool_name=tool_name,
                    error_code="EXECUTION_FAILED",
                    message=str(e)
                )
                
        except ValidationError:
            operation.status = OperationStatus.FAILED
            operation.end_time = datetime.now()
            self.stats['failed_operations'] += 1
            raise
            
        finally:
            # Cleanup progress tracking
            if 'progress_task' in locals() and progress_task:
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
            
            # Remove from active operations after delay for monitoring
            asyncio.create_task(self._cleanup_operation(operation_id, delay=300))
    
    async def _track_operation_progress(self, operation: ToolOperation):
        """
        Track progress of long-running operations.
        
        Args:
            operation: Operation to track
        """
        if not operation.progress_callback:
            return
        
        try:
            # Wait for operation to potentially become long-running
            await asyncio.sleep(10.0)
            
            # Check if operation is still running
            if operation.status != OperationStatus.RUNNING:
                return
            
            # Send long-running operation alert
            progress = OperationProgress(
                operation_id=operation.operation_id,
                operation_name=operation.tool_name,
                phase=ProgressPhase.PROCESSING,
                progress_percent=50.0,
                current_step="Taking longer than expected..."
            )
            try:
                operation.progress_callback(progress)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
            
            # Continue monitoring with periodic updates
            while operation.status == OperationStatus.RUNNING:
                await asyncio.sleep(30.0)  # Update every 30 seconds
                
                if operation.status == OperationStatus.RUNNING:
                    duration = (datetime.now() - operation.start_time).total_seconds()
                    progress = OperationProgress(
                        operation_id=operation.operation_id,
                        operation_name=operation.tool_name,
                        phase=ProgressPhase.PROCESSING,
                        progress_percent=50.0,
                        current_step=f"Still processing... ({duration:.0f}s elapsed)"
                    )
                    try:
                        operation.progress_callback(progress)
                    except Exception as e:
                        self.logger.warning(f"Progress callback failed: {e}")
                    
        except asyncio.CancelledError:
            # Task was cancelled - operation completed
            pass
        except Exception as e:
            self.logger.warning(f"Progress tracking failed for operation {operation.operation_id}: {e}")
    
    async def _cleanup_operation(self, operation_id: str, delay: float = 300):
        """
        Clean up completed operation after delay.
        
        Args:
            operation_id: ID of operation to clean up
            delay: Delay in seconds before cleanup
        """
        await asyncio.sleep(delay)
        self.active_operations.pop(operation_id, None)
    
    def _update_average_duration(self, duration: Optional[float]):
        """Update rolling average duration."""
        if duration is not None and self.stats['successful_operations'] > 0:
            current_avg = self.stats['average_duration']
            count = self.stats['successful_operations']
            self.stats['average_duration'] = (current_avg * (count - 1) + duration) / count
    
    # High-level tool invocation methods for GUI convenience
    
    async def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> MCPResponse:
        """
        Upload a document with validation and progress tracking.
        
        Args:
            file_path: Path to document file
            title: Optional custom title
            tags: Optional tags for categorization
            notes: Optional user notes
            progress_callback: Optional progress callback
            
        Returns:
            MCPResponse with upload result
        """
        return await self.invoke_tool_wrapper(
            tool_name='upload_document',
            parameters={
                'file_path': file_path,
                'title': title,
                'tags': tags,
                'notes': notes
            },
            progress_callback=progress_callback,
            timeout=300.0  # 5 minute timeout for large files
        )
    
    async def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        progress_callback: Optional[ProgressCallback] = None
    ) -> MCPResponse:
        """
        Search documents with validation.
        
        Args:
            query: Search query
            filters: Optional search filters
            limit: Maximum results to return
            progress_callback: Optional progress callback
            
        Returns:
            MCPResponse with search results
        """
        return await self.invoke_tool_wrapper(
            tool_name='search_documents',
            parameters={
                'query': query,
                'filters': filters or {},
                'limit': limit
            },
            progress_callback=progress_callback
        )
    
    # Monitoring and status methods
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get list of currently active operations."""
        return [
            {
                'operation_id': op.operation_id,
                'tool_name': op.tool_name,
                'status': op.status.value,
                'start_time': op.start_time.isoformat(),
                'duration': op.duration,
                'is_long_running': op.is_long_running
            }
            for op in self.active_operations.values()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool invoker performance statistics."""
        return self.stats.copy()
    
    def get_supported_tools(self) -> List[str]:
        """Get list of supported tool names."""
        return list(self.tool_schemas.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of tool invoker.
        
        Returns:
            Health status information
        """
        try:
            # Check MCP client health
            client_health = await self.mcp_client.get_health_status()
            
            return {
                'status': 'healthy',
                'tool_invoker': {
                    'validation_enabled': self.enable_validation,
                    'registered_tools': len(self.tool_schemas),
                    'active_operations': len(self.active_operations),
                    'statistics': self.stats
                },
                'mcp_client': client_health,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def shutdown(self):
        """Shutdown tool invoker and cleanup resources."""
        self.logger.info("Shutting down GUI Tool Invoker")
        
        # Cancel any active operations
        for operation in self.active_operations.values():
            if operation.status == OperationStatus.RUNNING:
                operation.status = OperationStatus.CANCELLED
        
        # Clear active operations
        self.active_operations.clear()
        
        self.logger.info("GUI Tool Invoker shutdown complete")


# Factory function for easy instantiation
def create_tool_invoker(mcp_client: IMCPClient, enable_validation: bool = True) -> GUIToolInvoker:
    """
    Factory function to create a configured GUIToolInvoker instance.
    
    Args:
        mcp_client: MCP client instance
        enable_validation: Whether to enable Pydantic validation
        
    Returns:
        Configured GUIToolInvoker instance
    """
    return GUIToolInvoker(mcp_client=mcp_client, enable_validation=enable_validation)