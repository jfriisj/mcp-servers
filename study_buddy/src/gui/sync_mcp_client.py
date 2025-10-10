"""
Synchronous MCP Client interface for GUI components.

This module provides a synchronous wrapper around the async MCP client
to simplify integration with tkinter GUI components which run synchronously.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

# Import from the same GUI package
from .mcp_client import AsyncMCPClient, MCPResponse, ConnectionConfig


class SyncMCPClient:
    """
    Synchronous wrapper for AsyncMCPClient.
    
    Provides blocking interface for GUI components that cannot handle
    async operations directly. Uses a dedicated thread pool and event
    loop to execute async operations.
    
    This follows the Adapter pattern, converting async interface to sync
    while maintaining the same error handling and functionality.
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self._async_client = AsyncMCPClient(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mcp-client")
        self.logger = logging.getLogger(__name__)
        
        # Start background event loop
        self._start_event_loop()
    
    def _start_event_loop(self) -> None:
        """Start background event loop for async operations."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # Wait for loop to be ready
        while self._loop is None:
            threading.Event().wait(0.01)
    
    def _run_async(self, coro) -> Any:
        """Run async coroutine in background thread and return result."""
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30.0)  # 30 second timeout
    
    def connect(self) -> bool:
        """Establish connection to MCP server."""
        try:
            return self._run_async(self._async_client.connect())
        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            self._run_async(self._async_client.disconnect())
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        try:
            return self._run_async(self._async_client.is_connected())
        except Exception as e:
            self.logger.error(f"Failed to check connection: {str(e)}")
            return False
    
    def call_tool(
        self, 
        tool_name: str, 
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """Call MCP tool synchronously."""
        try:
            return self._run_async(
                self._async_client.call_tool(tool_name, parameters, timeout)
            )
        except Exception as e:
            self.logger.error(f"Failed to call tool '{tool_name}': {str(e)}")
            return MCPResponse(
                success=False,
                error=f"Client error: {str(e)}",
                error_code="CLIENT_ERROR"
            )
    
    # Progress tracking tools
    def get_reading_progress(self, document_id: str) -> MCPResponse:
        """Get reading progress for a document."""
        return self.call_tool("get_reading_progress", {"document_id": document_id})
    
    def update_reading_progress(self, document_id: str, pages_read: int, total_pages: Optional[int] = None) -> MCPResponse:
        """Update reading progress for a document."""
        params = {"document_id": document_id, "pages_read": pages_read}
        if total_pages is not None:
            params["total_pages"] = total_pages
        return self.call_tool("update_reading_progress", params)
    
    def create_reading_progress(self, document_id: str, total_pages: int) -> MCPResponse:
        """Create new reading progress record."""
        return self.call_tool("create_reading_progress", {
            "document_id": document_id,
            "total_pages": total_pages
        })
    
    def delete_reading_progress(self, document_id: str) -> MCPResponse:
        """Delete reading progress record."""
        return self.call_tool("delete_reading_progress", {"document_id": document_id})
    
    def get_progress_analytics(self, document_id: Optional[str] = None) -> MCPResponse:
        """Get progress analytics."""
        params = {}
        if document_id:
            params["document_id"] = document_id
        return self.call_tool("get_progress_analytics", params)
    
    # Session management tools
    def start_study_session(self, document_id: str, session_type: str = "reading") -> MCPResponse:
        """Start a new study session."""
        return self.call_tool("start_study_session", {
            "document_id": document_id,
            "session_type": session_type
        })
    
    def pause_study_session(self, session_id: int) -> MCPResponse:
        """Pause an active study session."""
        return self.call_tool("pause_study_session", {"session_id": session_id})
    
    def resume_study_session(self, session_id: int) -> MCPResponse:
        """Resume a paused study session."""
        return self.call_tool("resume_study_session", {"session_id": session_id})
    
    def end_study_session(self, session_id: int, notes: Optional[str] = None) -> MCPResponse:
        """End an active study session."""
        params: Dict[str, Any] = {"session_id": session_id}
        if notes:
            params["notes"] = notes
        return self.call_tool("end_study_session", params)
    
    def get_active_session(self, document_id: Optional[str] = None) -> MCPResponse:
        """Get currently active session."""
        params: Dict[str, Any] = {}
        if document_id:
            params["document_id"] = document_id
        return self.call_tool("get_active_session", params)
    
    def list_study_sessions(self, document_id: Optional[str] = None, limit: int = 20) -> MCPResponse:
        """List study sessions."""
        params: Dict[str, Any] = {"limit": limit}
        if document_id:
            params["document_id"] = document_id
        return self.call_tool("list_study_sessions", params)
    
    def get_study_session_details(self, session_id: int) -> MCPResponse:
        """Get detailed information about a study session."""
        return self.call_tool("get_study_session_details", {"session_id": session_id})
    
    def get_session_analytics(self, document_id: Optional[str] = None, days: int = 30) -> MCPResponse:
        """Get session analytics."""
        params: Dict[str, Any] = {"days": days}
        if document_id:
            params["document_id"] = document_id
        return self.call_tool("get_session_analytics", params)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.disconnect()
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._executor.shutdown(wait=True)
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()