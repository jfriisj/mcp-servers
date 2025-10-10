#!/usr/bin/env python3
"""
Production-Ready Tkinter Example with Study Buddy MCP Integration

This example demonstrates a complete Tkinter application with proper MCP integration,
comprehensive error handling, progress tracking, and production best practices.

Features:
- Non-blocking MCP operations with background threading
- Real-time progress tracking and status updates  
- Comprehensive error handling and automatic recovery
- Connection health monitoring with visual indicators
- Proper resource cleanup and memory management
- Production-ready configuration management

Usage:
    python tkinter_example.py

Requirements:
    - Python 3.8+
    - tkinter (usually included)
    - Study Buddy MCP server running
"""

import asyncio
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict, Any, Optional, Callable

# Import MCP integration layer
try:
    from gui.integration import (
        MCPClient, 
        ConfigManager, 
        MCPConnectionError,
        ConnectionState,
        OperationProgress
    )
except ImportError as e:
    print(f"❌ Failed to import MCP integration layer: {e}")
    print("💡 Ensure you're running this from the project root directory")
    exit(1)


class MCPIntegrationManager:
    """
    Reusable MCP integration manager for GUI applications.
    
    Handles MCP client lifecycle, error recovery, and event management
    with proper threading for GUI applications.
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.client = None
        self.is_initialized = False
        
        # Event callbacks
        self._connection_callbacks = []
        self._progress_callbacks = []
        self._error_callbacks = []
        
        # Threading
        self._mcp_thread = None
        self._event_loop = None
        self._shutdown_event = threading.Event()
    
    async def initialize(self) -> bool:
        """Initialize MCP client and establish connection"""
        try:
            print("🔧 Initializing MCP client...")
            
            # Create client with configuration
            self.client = MCPClient(self.config)
            
            # Set up event handlers
            self.client.add_connection_listener(self._on_connection_change)
            self.client.add_error_listener(self._on_error)
            
            # Attempt connection
            print("🔌 Connecting to MCP server...")
            success = await self.client.connect()
            
            if success:
                self.is_initialized = True
                print("✅ MCP integration initialized successfully")
                self._notify_connection_callbacks(ConnectionState.CONNECTED)
            else:
                print("❌ Failed to connect to MCP server")
                self._notify_connection_callbacks(ConnectionState.ERROR)
            
            return success
            
        except Exception as e:
            print(f"❌ MCP initialization error: {e}")
            self._notify_error_callbacks(e, {"context": "initialization"})
            return False
    
    async def shutdown(self):
        """Gracefully shutdown MCP integration"""
        print("🔌 Shutting down MCP integration...")
        
        self.is_initialized = False
        
        if self.client:
            try:
                await self.client.disconnect()
                print("✅ MCP client disconnected successfully")
            except Exception as e:
                print(f"⚠️ Error during MCP shutdown: {e}")
        
        self._shutdown_event.set()
    
    def start_background_thread(self):
        """Start background thread for MCP operations"""
        if self._mcp_thread and self._mcp_thread.is_alive():
            return
        
        self._mcp_thread = threading.Thread(
            target=self._run_event_loop,
            name="MCPIntegrationThread",
            daemon=True
        )
        self._mcp_thread.start()
    
    def _run_event_loop(self):
        """Run async event loop in background thread"""
        try:
            # Create new event loop for this thread
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            
            # Initialize MCP client
            init_success = self._event_loop.run_until_complete(self.initialize())
            
            if not init_success:
                return
            
            # Keep event loop running until shutdown
            while not self._shutdown_event.is_set():
                try:
                    # Process any pending coroutines
                    self._event_loop.run_until_complete(asyncio.sleep(0.1))
                except Exception as e:
                    print(f"Event loop error: {e}")
                    
        except Exception as e:
            print(f"❌ Background thread error: {e}")
        finally:
            # Cleanup
            if self._event_loop and not self._event_loop.is_closed():
                self._event_loop.run_until_complete(self.shutdown())
                self._event_loop.close()
    
    def execute_async_operation(self, coro, callback: Optional[Callable] = None):
        """Execute async MCP operation from main thread"""
        if not self._event_loop or not self.is_initialized:
            if callback:
                callback({"success": False, "error": "MCP not initialized"})
            return
        
        def operation_wrapper():
            try:
                # Schedule coroutine in the MCP event loop
                future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
                result = future.result(timeout=60)  # 60 second timeout
                
                if callback:
                    callback(result)
                    
            except Exception as e:
                error_result = {"success": False, "error": str(e)}
                if callback:
                    callback(error_result)
        
        # Run operation in separate thread to avoid blocking GUI
        threading.Thread(target=operation_wrapper, daemon=True).start()
    
    # Event Management
    def add_connection_callback(self, callback):
        """Add callback for connection state changes"""
        self._connection_callbacks.append(callback)
    
    def add_progress_callback(self, callback):
        """Add callback for operation progress"""
        self._progress_callbacks.append(callback)
    
    def add_error_callback(self, callback):
        """Add callback for error events"""
        self._error_callbacks.append(callback)
    
    def _on_connection_change(self, state: ConnectionState):
        """Handle MCP connection state changes"""
        self._notify_connection_callbacks(state)
    
    def _on_error(self, error: Exception, context: dict):
        """Handle MCP errors"""
        self._notify_error_callbacks(error, context)
    
    def _notify_connection_callbacks(self, state: ConnectionState):
        """Notify all connection callbacks"""
        for callback in self._connection_callbacks:
            try:
                callback(state)
            except Exception as e:
                print(f"Connection callback error: {e}")
    
    def _notify_progress_callbacks(self, operation: str, progress: OperationProgress):
        """Notify all progress callbacks"""
        for callback in self._progress_callbacks:
            try:
                callback(operation, progress)
            except Exception as e:
                print(f"Progress callback error: {e}")
    
    def _notify_error_callbacks(self, error: Exception, context: dict):
        """Notify all error callbacks"""
        for callback in self._error_callbacks:
            try:
                callback(error, context)
            except Exception as e:
                print(f"Error callback error: {e}")


class StudyBuddyTkinterApp:
    """
    Production-ready Tkinter application with Study Buddy MCP integration.
    
    Demonstrates best practices for:
    - Non-blocking MCP operations
    - Comprehensive error handling  
    - Real-time progress tracking
    - Connection health monitoring
    - Resource cleanup
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.mcp_manager = None
        
        # UI state variables
        self.connection_status = tk.StringVar(value="Disconnected")
        self.progress_text = tk.StringVar(value="")
        self.progress_value = tk.DoubleVar(value=0.0)
        
        # Application state
        self.is_shutting_down = False
        
        self.setup_window()
        self.setup_ui()
        self.setup_mcp_integration()
    
    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Study Buddy - Document Manager")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Handle window close properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def setup_ui(self):
        """Set up the user interface with comprehensive controls"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # === Status Section ===
        status_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection status indicator
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.connection_status,
            font=("TkDefaultFont", 10, "bold")
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Health check button
        self.health_btn = ttk.Button(
            status_frame,
            text="Health Check",
            command=self.check_health,
            state="disabled"
        )
        self.health_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Reconnect button
        self.reconnect_btn = ttk.Button(
            status_frame,
            text="Reconnect",
            command=self.reconnect,
            state="disabled"
        )
        self.reconnect_btn.grid(row=0, column=2, padx=(5, 0))
        
        # === Controls Section ===
        controls_frame = ttk.LabelFrame(main_frame, text="Document Operations", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Upload button
        self.upload_btn = ttk.Button(
            controls_frame,
            text="📤 Upload Document",
            command=self.upload_document,
            state="disabled"
        )
        self.upload_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Refresh button  
        self.refresh_btn = ttk.Button(
            controls_frame,
            text="🔄 Refresh List",
            command=self.refresh_documents,
            state="disabled"
        )
        self.refresh_btn.grid(row=0, column=1, padx=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        search_label = ttk.Label(controls_frame, text="Search:")
        search_label.grid(row=0, column=2, padx=(20, 5))
        
        self.search_entry = ttk.Entry(
            controls_frame,
            textvariable=self.search_var,
            width=20,
            state="disabled"
        )
        self.search_entry.grid(row=0, column=3, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_documents())
        
        # Search button
        self.search_btn = ttk.Button(
            controls_frame,
            text="🔍 Search",
            command=self.search_documents,
            state="disabled"
        )
        self.search_btn.grid(row=0, column=4, padx=(5, 0))
        
        # === Progress Section ===
        progress_frame = ttk.LabelFrame(main_frame, text="Operation Progress", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress text
        self.progress_label = ttk.Label(
            progress_frame,
            textvariable=self.progress_text,
            foreground="blue"
        )
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_value,
            mode="determinate",
            length=400
        )
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # === Documents Section ===
        docs_frame = ttk.LabelFrame(main_frame, text="Documents", padding="10")
        docs_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        docs_frame.columnconfigure(0, weight=1)
        docs_frame.rowconfigure(0, weight=1)
        
        # Documents treeview with scrollbars
        tree_frame = ttk.Frame(docs_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview
        columns = ("Title", "Type", "Pages", "Words", "Status", "Upload Date")
        self.docs_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Configure column headings and widths
        column_configs = {
            "Title": (200, tk.W),
            "Type": (60, tk.CENTER),
            "Pages": (60, tk.CENTER),
            "Words": (80, tk.CENTER),
            "Status": (80, tk.CENTER),
            "Upload Date": (120, tk.CENTER)
        }
        
        for col, (width, anchor) in column_configs.items():
            self.docs_tree.heading(col, text=col)
            self.docs_tree.column(col, width=width, anchor=anchor)
        
        self.docs_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.docs_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.docs_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.docs_tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.docs_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Context menu for documents
        self.setup_context_menu()
        
        # === Statistics Section ===
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="Ready - No documents loaded",
            foreground="gray"
        )
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
    
    def setup_context_menu(self):
        """Set up context menu for document tree"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self.view_document_details)
        self.context_menu.add_command(label="Index Document", command=self.index_selected_document)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Document", command=self.delete_selected_document)
        
        # Bind right-click to show context menu
        self.docs_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu at cursor position"""
        # Select item under cursor
        item = self.docs_tree.identify_row(event.y)
        if item:
            self.docs_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def setup_mcp_integration(self):
        """Set up MCP integration with proper configuration"""
        try:
            # Create configuration - adjust paths as needed
            config = ConfigManager({
                "server_path": "mcp-server/main.py",
                "timeout": 60,
                "retry_attempts": 3,
                "log_level": "INFO",
                "min_connections": 2,
                "max_connections": 5
            })
            
            # Create integration manager
            self.mcp_manager = MCPIntegrationManager(config)
            
            # Set up event callbacks
            self.mcp_manager.add_connection_callback(self.on_connection_change)
            self.mcp_manager.add_progress_callback(self.on_progress_update)
            self.mcp_manager.add_error_callback(self.on_mcp_error)
            
            # Start background MCP thread
            self.mcp_manager.start_background_thread()
            
            # Update UI to show initialization
            self.update_connection_status(ConnectionState.CONNECTING)
            
        except Exception as e:
            self.show_error("MCP Setup Error", f"Failed to set up MCP integration: {e}")
    
    # === Event Handlers ===
    
    def on_connection_change(self, state: ConnectionState):
        """Handle MCP connection state changes (called from background thread)"""
        # Schedule UI update on main thread
        self.root.after(0, lambda: self.update_connection_status(state))
    
    def on_progress_update(self, operation: str, progress: OperationProgress):
        """Handle operation progress updates (called from background thread)"""
        # Schedule UI update on main thread
        self.root.after(0, lambda: self.update_progress(operation, progress))
    
    def on_mcp_error(self, error: Exception, context: dict):
        """Handle MCP errors (called from background thread)"""
        # Schedule UI update on main thread
        error_msg = f"MCP Error: {error}\\nContext: {context}"
        self.root.after(0, lambda: self.show_error("MCP Error", error_msg))
    
    def update_connection_status(self, state: ConnectionState):
        """Update UI connection status (called on main thread)"""
        status_configs = {
            ConnectionState.CONNECTED: ("Connected ✅", "green", True),
            ConnectionState.CONNECTING: ("Connecting... 🔄", "blue", False),
            ConnectionState.RECONNECTING: ("Reconnecting... 🔄", "orange", False),
            ConnectionState.ERROR: ("Disconnected ❌", "red", False),
            ConnectionState.DEGRADED: ("Connected (Degraded) ⚠️", "orange", True),
            ConnectionState.DISCONNECTED: ("Disconnected", "gray", False)
        }
        
        status_text, color, enabled = status_configs.get(state, ("Unknown", "black", False))
        
        # Update status label
        self.connection_status.set(status_text)
        self.status_label.configure(foreground=color)
        
        # Update button states
        buttons = [
            self.upload_btn, self.refresh_btn, self.search_btn,
            self.health_btn, self.search_entry
        ]
        
        button_state = "normal" if enabled else "disabled"
        for button in buttons:
            button.configure(state=button_state)
        
        # Update reconnect button (opposite state)
        self.reconnect_btn.configure(state="normal" if not enabled else "disabled")
        
        # Auto-refresh documents when connected
        if state == ConnectionState.CONNECTED:
            self.refresh_documents()
    
    def update_progress(self, operation: str, progress: OperationProgress):
        """Update progress display (called on main thread)"""
        progress_text = f"{operation}: {progress.current_step}"
        self.progress_text.set(progress_text)
        self.progress_value.set(progress.progress_percent)
        
        # Clear progress when complete
        if progress.progress_percent >= 100:
            self.root.after(2000, self.clear_progress)  # Clear after 2 seconds
    
    def clear_progress(self):
        """Clear progress display"""
        self.progress_text.set("")
        self.progress_value.set(0)
    
    # === MCP Operations ===
    
    def upload_document(self):
        """Handle document upload with file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Document to Upload",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Markdown files", "*.md"),
                ("PowerPoint files", "*.pptx"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        def upload_callback(result):
            self.root.after(0, lambda: self.handle_upload_result(result, file_path))
        
        # Create progress callback
        def progress_callback(progress):
            self.root.after(0, lambda: self.update_progress("Upload Document", progress))
        
        # Execute upload operation
        upload_coro = self.mcp_manager.client.upload_document(
            file_path=file_path,
            progress_callback=progress_callback
        )
        
        self.mcp_manager.execute_async_operation(upload_coro, upload_callback)
    
    def handle_upload_result(self, result, file_path):
        """Handle upload operation result"""
        if result.get("success"):
            doc_id = result.get("data", {}).get("document_id")
            title = result.get("data", {}).get("title", os.path.basename(file_path))
            
            messagebox.showinfo(
                "Upload Successful",
                f"Document uploaded successfully!\\n\\nTitle: {title}\\nDocument ID: {doc_id}"
            )
            
            # Refresh document list
            self.refresh_documents()
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Upload Failed", f"Failed to upload document:\\n{error_msg}")
    
    def refresh_documents(self):
        """Refresh the documents list"""
        def refresh_callback(result):
            self.root.after(0, lambda: self.handle_documents_result(result))
        
        if self.mcp_manager and self.mcp_manager.is_initialized:
            list_coro = self.mcp_manager.client.list_documents()
            self.mcp_manager.execute_async_operation(list_coro, refresh_callback)
    
    def search_documents(self):
        """Search documents based on query"""
        query = self.search_var.get().strip()
        if not query:
            self.refresh_documents()  # Show all documents if no query
            return
        
        def search_callback(result):
            self.root.after(0, lambda: self.handle_search_result(result))
        
        if self.mcp_manager and self.mcp_manager.is_initialized:
            search_coro = self.mcp_manager.client.search_documents(query)
            self.mcp_manager.execute_async_operation(search_coro, search_callback)
    
    def handle_documents_result(self, result):
        """Handle documents list result"""
        # Clear existing items
        for item in self.docs_tree.get_children():
            self.docs_tree.delete(item)
        
        if result.get("success"):
            documents = result.get("data", {}).get("documents", [])
            
            for doc in documents:
                # Format upload date
                upload_date = doc.get("upload_date", "")
                if upload_date:
                    try:
                        # Parse and format date
                        date_obj = datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
                        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = upload_date[:10]  # Just date part
                else:
                    formatted_date = "Unknown"
                
                # Status indicator
                status_parts = []
                if doc.get("indexed"):
                    status_parts.append("📚 Indexed")
                if doc.get("summarized"):
                    status_parts.append("📝 Summarized")
                status = " ".join(status_parts) if status_parts else "📄 Uploaded"
                
                # Insert document row
                self.docs_tree.insert("", "end", values=(
                    doc.get("title", "Untitled"),
                    doc.get("file_type", "").upper(),
                    doc.get("total_pages", "N/A"),
                    f"{doc.get('total_words', 0):,}",
                    status,
                    formatted_date
                ))
            
            # Update statistics
            total_docs = len(documents)
            indexed_docs = sum(1 for doc in documents if doc.get("indexed"))
            total_words = sum(doc.get("total_words", 0) for doc in documents)
            
            stats_text = f"Total: {total_docs} documents, {indexed_docs} indexed, {total_words:,} words"
            self.stats_label.configure(text=stats_text, foreground="black")
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Load Error", f"Failed to load documents:\\n{error_msg}")
            self.stats_label.configure(text="Error loading documents", foreground="red")
    
    def handle_search_result(self, result):
        """Handle search results"""
        # Clear existing items
        for item in self.docs_tree.get_children():
            self.docs_tree.delete(item)
        
        if result.get("success"):
            search_results = result.get("data", {}).get("results", [])
            total_results = result.get("data", {}).get("total_results", 0)
            
            for item in search_results:
                # Extract document info from search result
                doc_id = item.get("document_id")
                title = item.get("title", "Untitled")
                file_type = item.get("file_type", "").upper()
                relevance = item.get("relevance_score", 0)
                excerpt = item.get("match_excerpt", "")
                
                # Add search-specific information
                title_with_score = f"{title} (Score: {relevance:.2f})"
                
                self.docs_tree.insert("", "end", values=(
                    title_with_score,
                    file_type,
                    "-",  # Pages not available in search results
                    "-",  # Words not available in search results
                    "🔍 Match",
                    excerpt[:50] + "..." if len(excerpt) > 50 else excerpt
                ))
            
            # Update statistics for search
            query = self.search_var.get()
            stats_text = f"Search '{query}': {len(search_results)} results (of {total_results} total matches)"
            self.stats_label.configure(text=stats_text, foreground="blue")
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Search Error", f"Search failed:\\n{error_msg}")
    
    def check_health(self):
        """Check MCP server health"""
        def health_callback(result):
            self.root.after(0, lambda: self.show_health_result(result))
        
        if self.mcp_manager and self.mcp_manager.is_initialized:
            health_coro = self.mcp_manager.client.get_health_status()
            self.mcp_manager.execute_async_operation(health_coro, health_callback)
    
    def show_health_result(self, result):
        """Display health check results"""
        if hasattr(result, 'is_connected'):  # ConnectionHealth object
            health = result
            
            status = "Healthy ✅" if health.is_connected else "Unhealthy ❌"
            
            health_info = f"""Connection Health Status
            
Status: {status}
State: {health.connection_state.value}
Uptime: {health.uptime_seconds:.1f} seconds
Total Operations: {health.total_operations}
Error Count: {health.error_count}
Error Rate: {health.error_rate:.1f}%
Active Operations: {health.active_operations}"""
            
            if health.round_trip_time_ms:
                health_info += f"\\nResponse Time: {health.round_trip_time_ms:.1f}ms"
            
            messagebox.showinfo("Health Check", health_info)
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Health Check Failed", f"Health check failed:\\n{error_msg}")
    
    def reconnect(self):
        """Reconnect to MCP server"""
        if self.mcp_manager:
            # Restart the integration manager
            self.update_connection_status(ConnectionState.CONNECTING)
            self.mcp_manager.start_background_thread()
    
    # === Context Menu Operations ===
    
    def view_document_details(self):
        """View details of selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            return
        
        # Get document info from tree
        values = self.docs_tree.item(selection[0])["values"]
        if not values:
            return
        
        title, file_type, pages, words, status, date = values
        
        details = f"""Document Details
        
Title: {title}
Type: {file_type}
Pages: {pages}
Words: {words}
Status: {status}
Upload Date: {date}"""
        
        messagebox.showinfo("Document Details", details)
    
    def index_selected_document(self):
        """Index the selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            return
        
        # This would require getting document ID from the selection
        # For now, show placeholder
        messagebox.showinfo("Index Document", "Document indexing functionality would be implemented here.")
    
    def delete_selected_document(self):
        """Delete the selected document"""
        selection = self.docs_tree.selection()
        if not selection:
            return
        
        values = self.docs_tree.item(selection[0])["values"]
        title = values[0] if values else "Selected document"
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{title}'?"):
            # This would require getting document ID from the selection
            # For now, show placeholder
            messagebox.showinfo("Delete Document", "Document deletion functionality would be implemented here.")
    
    # === Utility Methods ===
    
    def show_error(self, title: str, message: str):
        """Show error message to user"""
        messagebox.showerror(title, message)
    
    def on_window_close(self):
        """Handle application window close"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        
        try:
            # Shutdown MCP integration
            if self.mcp_manager:
                # Signal shutdown to background thread
                self.mcp_manager._shutdown_event.set()
                
                # Wait briefly for cleanup
                if self.mcp_manager._mcp_thread and self.mcp_manager._mcp_thread.is_alive():
                    self.mcp_manager._mcp_thread.join(timeout=2.0)
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")
        finally:
            # Destroy window
            self.root.destroy()
    
    def run(self):
        """Start the application"""
        print("🚀 Starting Study Buddy Tkinter Application...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\n🛑 Application interrupted by user")
        except Exception as e:
            print(f"❌ Application error: {e}")
        finally:
            print("👋 Application shutdown complete")


def main():
    """Main application entry point"""
    print("=" * 60)
    print("Study Buddy - Tkinter Example with MCP Integration")
    print("=" * 60)
    
    # Check if MCP server is likely available
    mcp_server_paths = [
        "mcp-server/main.py",
        "../mcp-server/main.py",
        "../../mcp-server/main.py"
    ]
    
    server_found = False
    for path in mcp_server_paths:
        if os.path.exists(path):
            print(f"✅ Found MCP server at: {path}")
            server_found = True
            break
    
    if not server_found:
        print("⚠️ MCP server not found at expected locations:")
        for path in mcp_server_paths:
            print(f"   - {path}")
        print("💡 Make sure the MCP server is available and adjust the path in the code")
    
    try:
        # Create and run application
        app = StudyBuddyTkinterApp()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()