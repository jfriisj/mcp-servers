#!/usr/bin/env python3
"""
Production-Ready PyQt Example with Study Buddy MCP Integration

This example demonstrates a professional PyQt application with proper MCP integration,
multi-threading, comprehensive error handling, and modern UI design.

Features:
- Modern PyQt6 interface with professional styling
- Proper multi-threading with QThread for MCP operations
- Real-time progress tracking with animated progress bars
- Comprehensive error handling with user-friendly messages
- Connection health monitoring with visual indicators
- Memory-efficient large dataset handling
- Professional UI patterns and accessibility features

Usage:
    python pyqt_example.py

Requirements:
    - Python 3.8+
    - PyQt6 (pip install PyQt6)
    - Study Buddy MCP server running
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QMessageBox, QFileDialog,
    QGroupBox, QFrame, QSplitter, QTextEdit, QTabWidget, QComboBox,
    QCheckBox, QSpinBox, QSlider, QScrollArea, QToolBar, QSystemTrayIcon
)
from PyQt6.QtCore import (
    QThread, pyqtSignal, QTimer, Qt, QPropertyAnimation, QEasingCurve,
    QRect, QEvent, QObject, QMutex, QWaitCondition
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QFont, QColor, QPalette, QAction,
    QMovie, QTextCharFormat, QTextCursor
)

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
    print("💡 Ensure you're running this from the project root directory")
    sys.exit(1)


class MCPWorkerThread(QThread):
    """
    Background worker thread for MCP operations.
    
    Handles all async MCP operations in a separate thread to prevent
    GUI freezing and provide responsive user experience.
    """
    
    # Signals for communication with main thread
    connection_changed = pyqtSignal(str)  # ConnectionState as string
    progress_updated = pyqtSignal(str, dict)  # operation, progress_data
    operation_completed = pyqtSignal(str, dict)  # operation_type, result
    error_occurred = pyqtSignal(str, str, dict)  # error_type, message, context
    health_updated = pyqtSignal(dict)  # health_data
    
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.client = None
        self.event_loop = None
        self.is_running = False
        
        # Thread synchronization
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        
        # Operation queue
        self.operation_queue = []
        self.current_operation = None
    
    def run(self):
        """Main thread execution loop"""
        try:
            # Create new event loop for this thread
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            # Initialize MCP client
            self.is_running = True
            self.event_loop.run_until_complete(self.initialize_mcp())
            
            # Main event loop
            while self.is_running:
                try:
                    # Process operation queue
                    self.process_operations()
                    
                    # Run event loop for short periods
                    self.event_loop.run_until_complete(asyncio.sleep(0.1))
                    
                except Exception as e:
                    self.error_occurred.emit("EventLoop", str(e), {"thread": "MCPWorkerThread"})
                    
        except Exception as e:
            self.error_occurred.emit("ThreadError", str(e), {"thread_initialization": True})
        finally:
            # Cleanup
            if self.event_loop and not self.event_loop.is_closed():
                self.event_loop.run_until_complete(self.cleanup())
                self.event_loop.close()
    
    async def initialize_mcp(self):
        """Initialize MCP client and establish connection"""
        try:
            self.connection_changed.emit("CONNECTING")
            
            # Create MCP client
            self.client = MCPClient(self.config)
            
            # Set up event handlers
            self.client.add_connection_listener(self.on_connection_change)
            self.client.add_error_listener(self.on_mcp_error)
            
            # Attempt connection
            success = await self.client.connect()
            
            if success:
                self.connection_changed.emit("CONNECTED")
                
                # Start health monitoring
                self.start_health_monitoring()
            else:
                self.connection_changed.emit("ERROR")
                
        except Exception as e:
            self.error_occurred.emit("Initialization", str(e), {"mcp_client": True})
            self.connection_changed.emit("ERROR")
    
    async def cleanup(self):
        """Cleanup MCP resources"""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    def stop_thread(self):
        """Stop the worker thread"""
        self.is_running = False
        
        # Wake up any waiting operations
        self.mutex.lock()
        self.wait_condition.wakeAll()
        self.mutex.unlock()
    
    def queue_operation(self, operation_type: str, **kwargs):
        """Queue an MCP operation for execution"""
        operation = {
            "type": operation_type,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        }
        
        self.mutex.lock()
        try:
            self.operation_queue.append(operation)
            self.wait_condition.wakeOne()
        finally:
            self.mutex.unlock()
    
    def process_operations(self):
        """Process queued operations"""
        self.mutex.lock()
        try:
            if not self.operation_queue:
                return
            
            operation = self.operation_queue.pop(0)
        finally:
            self.mutex.unlock()
        
        # Execute operation
        self.current_operation = operation
        
        try:
            operation_type = operation["type"]
            kwargs = operation["kwargs"]
            
            if operation_type == "upload_document":
                coro = self.execute_upload_document(**kwargs)
            elif operation_type == "list_documents":
                coro = self.execute_list_documents(**kwargs)
            elif operation_type == "search_documents":
                coro = self.execute_search_documents(**kwargs)
            elif operation_type == "index_document":
                coro = self.execute_index_document(**kwargs)
            elif operation_type == "delete_document":
                coro = self.execute_delete_document(**kwargs)
            elif operation_type == "health_check":
                coro = self.execute_health_check(**kwargs)
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            # Execute the coroutine
            if self.event_loop and self.client:
                result = self.event_loop.run_until_complete(coro)
                self.operation_completed.emit(operation_type, result)
                
        except Exception as e:
            error_context = {
                "operation": operation,
                "client_state": "connected" if self.client else "disconnected"
            }
            self.error_occurred.emit("Operation", str(e), error_context)
        finally:
            self.current_operation = None
    
    # === MCP Operation Methods ===
    
    async def execute_upload_document(self, file_path: str, **kwargs):
        """Execute document upload operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            def progress_callback(progress):
                progress_data = {
                    "current_step": progress.current_step,
                    "progress_percent": progress.progress_percent,
                    "estimated_time_remaining": getattr(progress, 'estimated_time_remaining', None)
                }
                self.progress_updated.emit("upload_document", progress_data)
            
            result = await self.client.upload_document(
                file_path=file_path,
                progress_callback=progress_callback,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_list_documents(self, filters=None, **kwargs):
        """Execute list documents operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            result = await self.client.list_documents(filters=filters, **kwargs)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_search_documents(self, query: str, **kwargs):
        """Execute search documents operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            result = await self.client.search_documents(query=query, **kwargs)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_index_document(self, document_id: int, strategy: str = "auto", **kwargs):
        """Execute document indexing operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            def progress_callback(progress):
                progress_data = {
                    "current_step": progress.current_step,
                    "progress_percent": progress.progress_percent,
                    "chunks_created": getattr(progress, 'chunks_created', 0)
                }
                self.progress_updated.emit("index_document", progress_data)
            
            result = await self.client.index_document(
                document_id=document_id,
                strategy=strategy,
                progress_callback=progress_callback,
                **kwargs
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_delete_document(self, document_id: int, **kwargs):
        """Execute document deletion operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            result = await self.client.delete_document(document_id=document_id, **kwargs)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_health_check(self, **kwargs):
        """Execute health check operation"""
        if not self.client:
            return {"success": False, "error": "MCP client not initialized"}
        
        try:
            health = await self.client.get_health_status(**kwargs)
            
            # Convert health object to dictionary for signal transmission
            health_data = {
                "is_connected": health.is_connected,
                "connection_state": health.connection_state.value,
                "uptime_seconds": health.uptime_seconds,
                "total_operations": health.total_operations,
                "error_count": health.error_count,
                "error_rate": health.error_rate,
                "active_operations": health.active_operations,
                "round_trip_time_ms": getattr(health, 'round_trip_time_ms', None)
            }
            
            return {"success": True, "health": health_data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start_health_monitoring(self):
        """Start periodic health monitoring"""
        # Queue initial health check
        self.queue_operation("health_check")
        
        # Set up timer for periodic checks (every 30 seconds)
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(lambda: self.queue_operation("health_check"))
        self.health_timer.start(30000)  # 30 seconds
    
    def on_connection_change(self, state: ConnectionState):
        """Handle connection state changes"""
        self.connection_changed.emit(state.value)
    
    def on_mcp_error(self, error: Exception, context: dict):
        """Handle MCP errors"""
        self.error_occurred.emit("MCP", str(error), context)


class AnimatedProgressBar(QProgressBar):
    """Custom progress bar with smooth animations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        
        # Animation for smooth progress updates
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(300)  # 300ms animation
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setAnimatedValue(self, value):
        """Set progress value with animation"""
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()


class ConnectionStatusWidget(QWidget):
    """Custom widget for displaying connection status with visual indicators"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connection_state = "DISCONNECTED"
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Status indicator (colored circle)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                background-color: #808080;
            }
        """)
        
        # Status text
        self.status_text = QLabel("Disconnected")
        self.status_text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_text)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, state: str):
        """Update connection status display"""
        self.connection_state = state
        
        status_configs = {
            "CONNECTED": ("#4CAF50", "Connected ✅"),
            "CONNECTING": ("#2196F3", "Connecting... 🔄"),
            "RECONNECTING": ("#FF9800", "Reconnecting... 🔄"),
            "ERROR": ("#F44336", "Error ❌"),
            "DEGRADED": ("#FF9800", "Degraded ⚠️"),
            "DISCONNECTED": ("#808080", "Disconnected")
        }
        
        color, text = status_configs.get(state, ("#808080", "Unknown"))
        
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                border-radius: 8px;
                background-color: {color};
            }}
        """)
        
        self.status_text.setText(text)
        self.status_text.setStyleSheet(f"color: {color};")


class DocumentTreeWidget(QTreeWidget):
    """Enhanced tree widget for document display with rich formatting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_tree()
    
    def setup_tree(self):
        """Configure tree widget"""
        # Set headers
        headers = ["Title", "Type", "Pages", "Words", "Status", "Upload Date"]
        self.setHeaderLabels(headers)
        
        # Configure columns
        column_widths = [300, 80, 80, 100, 120, 140]
        for i, width in enumerate(column_widths):
            self.setColumnWidth(i, width)
        
        # Enable sorting
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
        # Enable selection
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        
        # Enable alternating row colors
        self.setAlternatingRowColors(True)
        
        # Set font
        font = QFont("Consolas", 10)  # Monospace font for better alignment
        self.setFont(font)
    
    def add_document(self, doc_data: Dict[str, Any]):
        """Add a document to the tree with proper formatting"""
        # Format upload date
        upload_date = doc_data.get("upload_date", "")
        if upload_date:
            try:
                date_obj = datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = upload_date[:10]
        else:
            formatted_date = "Unknown"
        
        # Format status with emojis
        status_parts = []
        if doc_data.get("indexed"):
            status_parts.append("📚 Indexed")
        if doc_data.get("summarized"):
            status_parts.append("📝 Summarized")
        status = " ".join(status_parts) if status_parts else "📄 Uploaded"
        
        # Format word count with thousands separator
        word_count = doc_data.get("total_words", 0)
        formatted_words = f"{word_count:,}" if word_count else "0"
        
        # Create tree item
        item_data = [
            doc_data.get("title", "Untitled"),
            doc_data.get("file_type", "").upper(),
            str(doc_data.get("total_pages", "N/A")),
            formatted_words,
            status,
            formatted_date
        ]
        
        item = QTreeWidgetItem(item_data)
        
        # Store document ID for operations
        item.setData(0, Qt.ItemDataRole.UserRole, doc_data.get("id"))
        
        # Set tooltips
        item.setToolTip(0, f"Document ID: {doc_data.get('id')}\\nFile: {doc_data.get('file_path', 'Unknown')}")
        
        # Color coding based on status
        if doc_data.get("indexed") and doc_data.get("summarized"):
            # Fully processed - green
            for col in range(self.columnCount()):
                item.setBackground(col, QColor(232, 245, 233))
        elif doc_data.get("indexed"):
            # Indexed only - light blue
            for col in range(self.columnCount()):
                item.setBackground(col, QColor(227, 242, 253))
        
        self.addTopLevelItem(item)
    
    def clear_documents(self):
        """Clear all documents from tree"""
        self.clear()
    
    def get_selected_document_id(self) -> Optional[int]:
        """Get the ID of the currently selected document"""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None


class StudyBuddyMainWindow(QMainWindow):
    """
    Main application window with professional PyQt interface.
    
    Features:
    - Modern UI design with proper layout management
    - Comprehensive MCP integration with background threading
    - Real-time progress tracking and status updates
    - Advanced document management capabilities
    - Professional error handling and user feedback
    """
    
    def __init__(self):
        super().__init__()
        
        # Application state
        self.mcp_worker = None
        self.is_shutting_down = False
        
        # UI setup
        self.setup_window()
        self.setup_ui()
        self.setup_mcp_integration()
        self.setup_status_bar()
        self.setup_menu_bar()
        
        # Statistics
        self.document_stats = {
            "total": 0,
            "indexed": 0,
            "summarized": 0,
            "total_words": 0
        }
    
    def setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("Study Buddy - Professional Document Manager")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)
        
        # Set application icon (if available)
        if os.path.exists("assets/icon.png"):
            self.setWindowIcon(QIcon("assets/icon.png"))
    
    def setup_ui(self):
        """Set up the main user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === Top Section: Connection and Controls ===
        top_section = self.create_top_section()
        main_layout.addWidget(top_section)
        
        # === Middle Section: Progress and Operations ===
        progress_section = self.create_progress_section()
        main_layout.addWidget(progress_section)
        
        # === Bottom Section: Documents Display ===
        documents_section = self.create_documents_section()
        main_layout.addWidget(documents_section, 1)  # Take remaining space
    
    def create_top_section(self) -> QWidget:
        """Create top section with connection status and controls"""
        section = QGroupBox("Connection & Controls")
        layout = QGridLayout(section)
        
        # Connection status
        self.connection_widget = ConnectionStatusWidget()
        layout.addWidget(QLabel("Status:"), 0, 0)
        layout.addWidget(self.connection_widget, 0, 1, 1, 2)
        
        # Connection controls
        self.health_check_btn = QPushButton("🏥 Health Check")
        self.health_check_btn.clicked.connect(self.check_health)
        self.health_check_btn.setEnabled(False)
        
        self.reconnect_btn = QPushButton("🔄 Reconnect")
        self.reconnect_btn.clicked.connect(self.reconnect)
        self.reconnect_btn.setEnabled(False)
        
        layout.addWidget(self.health_check_btn, 0, 3)
        layout.addWidget(self.reconnect_btn, 0, 4)
        
        # Document controls
        self.upload_btn = QPushButton("📤 Upload Document")
        self.upload_btn.clicked.connect(self.upload_document)
        self.upload_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.clicked.connect(self.refresh_documents)
        self.refresh_btn.setEnabled(False)
        
        layout.addWidget(self.upload_btn, 1, 0)
        layout.addWidget(self.refresh_btn, 1, 1)
        
        # Search controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents...")
        self.search_input.returnPressed.connect(self.search_documents)
        self.search_input.setEnabled(False)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.search_documents)
        self.search_btn.setEnabled(False)
        
        self.clear_search_btn = QPushButton("❌ Clear")
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setEnabled(False)
        
        layout.addWidget(self.search_input, 1, 2)
        layout.addWidget(self.search_btn, 1, 3)
        layout.addWidget(self.clear_search_btn, 1, 4)
        
        return section
    
    def create_progress_section(self) -> QWidget:
        """Create progress section with animated progress tracking"""
        section = QGroupBox("Operation Progress")
        layout = QVBoxLayout(section)
        
        # Progress text
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("color: #666; font-weight: bold;")
        layout.addWidget(self.progress_label)
        
        # Progress bar with animation
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Operation details (expandable)
        self.operation_details = QTextEdit()
        self.operation_details.setMaximumHeight(100)
        self.operation_details.setVisible(False)
        self.operation_details.setReadOnly(True)
        self.operation_details.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.operation_details)
        
        return section
    
    def create_documents_section(self) -> QWidget:
        """Create documents section with tree view and details"""
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Document tree
        left_section = QGroupBox("Documents")
        left_layout = QVBoxLayout(left_section)
        
        # Document tree
        self.document_tree = DocumentTreeWidget()
        self.document_tree.itemSelectionChanged.connect(self.on_document_selected)
        self.document_tree.itemDoubleClicked.connect(self.view_document_details)
        left_layout.addWidget(self.document_tree)
        
        # Document operations buttons
        operations_layout = QHBoxLayout()
        
        self.index_btn = QPushButton("📚 Index Document")
        self.index_btn.clicked.connect(self.index_selected_document)
        self.index_btn.setEnabled(False)
        
        self.view_btn = QPushButton("👁 View Details")
        self.view_btn.clicked.connect(self.view_document_details)
        self.view_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.delete_selected_document)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: red; }")
        
        operations_layout.addWidget(self.index_btn)
        operations_layout.addWidget(self.view_btn)
        operations_layout.addStretch()
        operations_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(operations_layout)
        
        # Right side: Document details/preview
        right_section = QGroupBox("Document Details")
        right_layout = QVBoxLayout(right_section)
        
        # Details tabs
        self.details_tabs = QTabWidget()
        
        # Info tab
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.details_tabs.addTab(self.info_text, "📄 Info")
        
        # Content preview tab
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.details_tabs.addTab(self.content_text, "📖 Preview")
        
        # Statistics tab
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.details_tabs.addTab(self.stats_text, "📊 Statistics")
        
        right_layout.addWidget(self.details_tabs)
        
        # Add sections to splitter
        splitter.addWidget(left_section)
        splitter.addWidget(right_section)
        splitter.setSizes([600, 400])  # Initial sizes
        
        return splitter
    
    def setup_status_bar(self):
        """Set up status bar with comprehensive information"""
        self.status_bar = self.statusBar()
        
        # Connection status in status bar
        self.status_connection = QLabel("Disconnected")
        self.status_bar.addWidget(self.status_connection)
        
        # Statistics in status bar
        self.status_stats = QLabel("No documents")
        self.status_bar.addPermanentWidget(self.status_stats)
        
        # Memory usage (optional)
        self.status_memory = QLabel("")
        self.status_bar.addPermanentWidget(self.status_memory)
    
    def setup_menu_bar(self):
        """Set up comprehensive menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        upload_action = QAction("📤 &Upload Document...", self)
        upload_action.setShortcut("Ctrl+U")
        upload_action.triggered.connect(self.upload_document)
        file_menu.addAction(upload_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("🔄 &Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_documents)
        view_menu.addAction(refresh_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        health_action = QAction("🏥 &Health Check", self)
        health_action.triggered.connect(self.check_health)
        tools_menu.addAction(health_action)
        
        reconnect_action = QAction("🔄 &Reconnect", self)
        reconnect_action.triggered.connect(self.reconnect)
        tools_menu.addAction(reconnect_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_mcp_integration(self):
        """Set up MCP integration with worker thread"""
        try:
            # Create configuration
            config = ConfigManager({
                "server_path": "mcp-server/main.py",
                "timeout": 60,
                "retry_attempts": 3,
                "log_level": "INFO",
                "min_connections": 2,
                "max_connections": 5
            })
            
            # Create worker thread
            self.mcp_worker = MCPWorkerThread(config)
            
            # Connect signals
            self.mcp_worker.connection_changed.connect(self.on_connection_changed)
            self.mcp_worker.progress_updated.connect(self.on_progress_updated)
            self.mcp_worker.operation_completed.connect(self.on_operation_completed)
            self.mcp_worker.error_occurred.connect(self.on_error_occurred)
            self.mcp_worker.health_updated.connect(self.on_health_updated)
            
            # Start worker thread
            self.mcp_worker.start()
            
        except Exception as e:
            self.show_error("MCP Setup Error", f"Failed to set up MCP integration: {e}")
    
    # === Event Handlers ===
    
    def on_connection_changed(self, state: str):
        """Handle connection state changes"""
        self.connection_widget.update_status(state)
        self.status_connection.setText(f"Connection: {state}")
        
        # Update button states based on connection
        connected = state == "CONNECTED"
        
        buttons = [
            self.upload_btn, self.refresh_btn, self.search_btn,
            self.health_check_btn, self.search_input, self.clear_search_btn
        ]
        
        for button in buttons:
            button.setEnabled(connected)
        
        # Reconnect button opposite state
        self.reconnect_btn.setEnabled(not connected)
        
        # Auto-refresh when connected
        if connected:
            self.refresh_documents()
    
    def on_progress_updated(self, operation: str, progress_data: dict):
        """Handle progress updates"""
        current_step = progress_data.get("current_step", "Processing...")
        progress_percent = progress_data.get("progress_percent", 0)
        
        # Update progress label and bar
        self.progress_label.setText(f"{operation}: {current_step}")
        
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        
        self.progress_bar.setAnimatedValue(int(progress_percent))
        
        # Show operation details if available
        if progress_data.get("estimated_time_remaining"):
            eta = progress_data["estimated_time_remaining"]
            details = f"ETA: {eta:.1f} seconds"
            
            if not self.operation_details.isVisible():
                self.operation_details.setVisible(True)
            
            self.operation_details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {details}")
        
        # Clear progress when complete
        if progress_percent >= 100:
            QTimer.singleShot(2000, self.clear_progress)
    
    def clear_progress(self):
        """Clear progress display"""
        self.progress_label.setText("Ready")
        self.progress_bar.setVisible(False)
        self.operation_details.setVisible(False)
        self.operation_details.clear()
    
    def on_operation_completed(self, operation_type: str, result: dict):
        """Handle completed operations"""
        if operation_type == "upload_document":
            self.handle_upload_result(result)
        elif operation_type == "list_documents":
            self.handle_documents_result(result)
        elif operation_type == "search_documents":
            self.handle_search_result(result)
        elif operation_type == "index_document":
            self.handle_index_result(result)
        elif operation_type == "delete_document":
            self.handle_delete_result(result)
        elif operation_type == "health_check":
            pass  # Health results handled separately
    
    def on_error_occurred(self, error_type: str, message: str, context: dict):
        """Handle errors"""
        self.show_error(f"{error_type} Error", message)
        
        # Log error details
        error_details = f"[{datetime.now().strftime('%H:%M:%S')}] {error_type}: {message}"
        if context:
            error_details += f" Context: {context}"
        
        if not self.operation_details.isVisible():
            self.operation_details.setVisible(True)
        
        self.operation_details.append(error_details)
    
    def on_health_updated(self, health_data: dict):
        """Handle health status updates"""
        # Update memory status if available
        if health_data.get("round_trip_time_ms"):
            rtt = health_data["round_trip_time_ms"]
            self.status_memory.setText(f"RTT: {rtt:.1f}ms")
    
    # === Document Operations ===
    
    def upload_document(self):
        """Handle document upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document to Upload",
            "",
            "Documents (*.pdf *.docx *.md *.pptx *.txt);;All Files (*.*)"
        )
        
        if file_path and self.mcp_worker:
            self.mcp_worker.queue_operation("upload_document", file_path=file_path)
    
    def handle_upload_result(self, result: dict):
        """Handle upload operation result"""
        if result.get("success"):
            doc_data = result.get("data", {})
            doc_id = doc_data.get("document_id")
            title = doc_data.get("title", "Unknown")
            
            QMessageBox.information(
                self,
                "Upload Successful",
                f"Document uploaded successfully!\\n\\nTitle: {title}\\nDocument ID: {doc_id}"
            )
            
            self.refresh_documents()
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Upload Failed", f"Failed to upload document:\\n{error_msg}")
    
    def refresh_documents(self):
        """Refresh documents list"""
        if self.mcp_worker:
            self.mcp_worker.queue_operation("list_documents")
    
    def handle_documents_result(self, result: dict):
        """Handle documents list result"""
        self.document_tree.clear_documents()
        
        if result.get("success"):
            documents = result.get("data", {}).get("documents", [])
            
            for doc in documents:
                self.document_tree.add_document(doc)
            
            # Update statistics
            self.update_document_statistics(documents)
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Load Error", f"Failed to load documents:\\n{error_msg}")
    
    def search_documents(self):
        """Search documents"""
        query = self.search_input.text().strip()
        if query and self.mcp_worker:
            self.mcp_worker.queue_operation("search_documents", query=query)
        elif not query:
            self.refresh_documents()  # Show all if no query
    
    def handle_search_result(self, result: dict):
        """Handle search results"""
        self.document_tree.clear_documents()
        
        if result.get("success"):
            search_results = result.get("data", {}).get("results", [])
            total_results = result.get("data", {}).get("total_results", 0)
            
            # Convert search results to document format for display
            for item in search_results:
                # Create document-like object for tree display
                doc_data = {
                    "id": item.get("document_id"),
                    "title": f"{item.get('title', 'Untitled')} (Score: {item.get('relevance_score', 0):.2f})",
                    "file_type": item.get("file_type", ""),
                    "total_pages": None,  # Not available in search
                    "total_words": None,  # Not available in search
                    "indexed": True,  # Assume indexed if searchable
                    "summarized": False,
                    "upload_date": ""
                }
                
                self.document_tree.add_document(doc_data)
            
            # Update status
            query = self.search_input.text()
            self.status_stats.setText(f"Search '{query}': {len(search_results)} of {total_results} results")
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Search Error", f"Search failed:\\n{error_msg}")
    
    def clear_search(self):
        """Clear search and show all documents"""
        self.search_input.clear()
        self.refresh_documents()
    
    def update_document_statistics(self, documents: List[Dict]):
        """Update document statistics"""
        total = len(documents)
        indexed = sum(1 for doc in documents if doc.get("indexed"))
        summarized = sum(1 for doc in documents if doc.get("summarized"))
        total_words = sum(doc.get("total_words", 0) for doc in documents)
        
        self.document_stats.update({
            "total": total,
            "indexed": indexed,
            "summarized": summarized,
            "total_words": total_words
        })
        
        # Update status bar
        stats_text = f"Documents: {total} total, {indexed} indexed, {summarized} summarized | Words: {total_words:,}"
        self.status_stats.setText(stats_text)
    
    # === Document Selection and Operations ===
    
    def on_document_selected(self):
        """Handle document selection change"""
        selected = self.document_tree.currentItem() is not None
        
        # Enable/disable operation buttons
        self.index_btn.setEnabled(selected)
        self.view_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)
        
        if selected:
            self.update_document_details()
    
    def update_document_details(self):
        """Update document details panel"""
        doc_id = self.document_tree.get_selected_document_id()
        if not doc_id:
            return
        
        # Get document data from tree
        current_item = self.document_tree.currentItem()
        if not current_item:
            return
        
        # Extract data from tree item
        title = current_item.text(0)
        file_type = current_item.text(1)
        pages = current_item.text(2)
        words = current_item.text(3)
        status = current_item.text(4)
        date = current_item.text(5)
        
        # Update info tab
        info_html = f"""
        <h3>📄 {title}</h3>
        <table style="width: 100%; border-collapse: collapse;">
        <tr><td><b>Document ID:</b></td><td>{doc_id}</td></tr>
        <tr><td><b>File Type:</b></td><td>{file_type}</td></tr>
        <tr><td><b>Pages:</b></td><td>{pages}</td></tr>
        <tr><td><b>Words:</b></td><td>{words}</td></tr>
        <tr><td><b>Status:</b></td><td>{status}</td></tr>
        <tr><td><b>Upload Date:</b></td><td>{date}</td></tr>
        </table>
        """
        self.info_text.setHtml(info_html)
        
        # Placeholder for content preview
        self.content_text.setPlainText("Content preview would be loaded here...")
        
        # Placeholder for statistics
        stats_text = f"""Document Statistics
        
Total Characters: ~{int(words.replace(',', '')) * 5 if words != 'N/A' else 0}
Estimated Reading Time: ~{int(words.replace(',', '')) // 200 if words != 'N/A' else 0} minutes
File Type: {file_type}
Processing Status: {status}
        """
        self.stats_text.setPlainText(stats_text)
    
    def view_document_details(self):
        """View detailed document information"""
        doc_id = self.document_tree.get_selected_document_id()
        if not doc_id:
            return
        
        # For now, show current details in a dialog
        current_item = self.document_tree.currentItem()
        if not current_item:
            return
        
        title = current_item.text(0)
        file_type = current_item.text(1)
        pages = current_item.text(2)
        words = current_item.text(3)
        status = current_item.text(4)
        date = current_item.text(5)
        
        details = f"""Document Details
        
Title: {title}
Document ID: {doc_id}
File Type: {file_type}
Pages: {pages}
Words: {words}
Status: {status}
Upload Date: {date}"""
        
        QMessageBox.information(self, "Document Details", details)
    
    def index_selected_document(self):
        """Index the selected document"""
        doc_id = self.document_tree.get_selected_document_id()
        if not doc_id or not self.mcp_worker:
            return
        
        # Ask user for indexing strategy
        strategies = ["auto", "chapter", "section", "heading", "fixed"]
        strategy, ok = QInputDialog.getItem(
            self,
            "Select Indexing Strategy",
            "Choose how to chunk this document:",
            strategies,
            0,
            False
        )
        
        if ok:
            self.mcp_worker.queue_operation("index_document", document_id=doc_id, strategy=strategy)
    
    def handle_index_result(self, result: dict):
        """Handle indexing result"""
        if result.get("success"):
            chunks_created = result.get("data", {}).get("chunks_created", 0)
            QMessageBox.information(
                self,
                "Indexing Complete",
                f"Document indexed successfully!\\n{chunks_created} chunks created."
            )
            self.refresh_documents()
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Indexing Failed", f"Failed to index document:\\n{error_msg}")
    
    def delete_selected_document(self):
        """Delete the selected document"""
        doc_id = self.document_tree.get_selected_document_id()
        if not doc_id:
            return
        
        current_item = self.document_tree.currentItem()
        title = current_item.text(0) if current_item else "Selected document"
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{title}'?\\n\\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes and self.mcp_worker:
            self.mcp_worker.queue_operation("delete_document", document_id=doc_id)
    
    def handle_delete_result(self, result: dict):
        """Handle deletion result"""
        if result.get("success"):
            QMessageBox.information(self, "Delete Successful", "Document deleted successfully.")
            self.refresh_documents()
        else:
            error_msg = result.get("error", "Unknown error")
            self.show_error("Delete Failed", f"Failed to delete document:\\n{error_msg}")
    
    # === Utility Methods ===
    
    def check_health(self):
        """Check MCP server health"""
        if self.mcp_worker:
            self.mcp_worker.queue_operation("health_check")
    
    def reconnect(self):
        """Reconnect to MCP server"""
        if self.mcp_worker:
            # Stop current worker
            self.mcp_worker.stop_thread()
            self.mcp_worker.wait()
            
            # Start new worker
            self.setup_mcp_integration()
    
    def show_error(self, title: str, message: str):
        """Show error message to user"""
        QMessageBox.critical(self, title, message)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Study Buddy - Professional Document Manager</h2>
        <p><b>Version:</b> 1.0</p>
        <p><b>Built with:</b> PyQt6 and Study Buddy MCP Integration</p>
        
        <p>This application demonstrates professional-grade MCP integration with:</p>
        <ul>
        <li>Multi-threaded MCP operations</li>
        <li>Real-time progress tracking</li>
        <li>Comprehensive error handling</li>
        <li>Modern PyQt interface</li>
        </ul>
        
        <p>© 2025 Study Buddy Project</p>
        """
        
        QMessageBox.about(self, "About Study Buddy", about_text)
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.is_shutting_down:
            event.accept()
            return
        
        self.is_shutting_down = True
        
        try:
            # Stop MCP worker thread
            if self.mcp_worker:
                self.mcp_worker.stop_thread()
                self.mcp_worker.wait(5000)  # Wait up to 5 seconds
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            event.accept()


def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Study Buddy")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Study Buddy Project")
    
    print("=" * 60)
    print("Study Buddy - PyQt6 Example with MCP Integration")
    print("=" * 60)
    
    # Check for MCP server
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
        print("⚠️ MCP server not found at expected locations")
    
    try:
        # Create and show main window
        window = StudyBuddyMainWindow()
        window.show()
        
        print("🚀 PyQt application started successfully")
        
        # Run application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Failed to start PyQt application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()