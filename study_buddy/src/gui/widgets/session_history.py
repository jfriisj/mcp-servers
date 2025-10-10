"""
Session History Widget for Study Buddy MCP Server.

This module provides the SessionHistoryWidget class which displays
a list of past study sessions with filtering and detailed view capabilities.
"""

from typing import Optional, Dict, Any, List
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from ..sync_mcp_client import SyncMCPClient


class SessionHistoryWidget:
    """
    A GUI widget that displays session history with filtering and details.
    
    This widget follows the Single Responsibility Principle by focusing solely
    on session history display and management. It depends on abstractions
    (SyncMCPClient) following the Dependency Inversion Principle.
    """
    
    def __init__(self, parent: tk.Widget, mcp_client: SyncMCPClient):
        """
        Initialize the SessionHistoryWidget.
        
        Args:
            parent: The parent tkinter widget
            mcp_client: The MCP client for backend interactions
        """
        self._mcp_client = mcp_client
        self._sessions_data: List[Dict[str, Any]] = []
        self._selected_session: Optional[Dict[str, Any]] = None
        
        # Create main frame
        self._frame = ttk.LabelFrame(parent, text="Session History", padding="10")
        
        # Initialize UI components
        self._setup_ui()
        
        # Load initial session data
        self._load_sessions()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Control frame for filters and buttons
        self._control_frame = ttk.Frame(self._frame)
        self._control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Document filter
        ttk.Label(self._control_frame, text="Document Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self._document_filter_var = tk.StringVar()
        self._document_filter_entry = ttk.Entry(
            self._control_frame, 
            textvariable=self._document_filter_var, 
            width=25
        )
        self._document_filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Date range filter
        ttk.Label(self._control_frame, text="Days:").pack(side=tk.LEFT, padx=(0, 5))
        self._days_var = tk.StringVar(value="30")
        self._days_combo = ttk.Combobox(
            self._control_frame,
            textvariable=self._days_var,
            values=["7", "14", "30", "90", "365", "All"],
            state="readonly",
            width=8
        )
        self._days_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter button
        self._filter_button = ttk.Button(
            self._control_frame,
            text="Filter",
            command=self._apply_filters
        )
        self._filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh button
        self._refresh_button = ttk.Button(
            self._control_frame,
            text="Refresh",
            command=self._load_sessions
        )
        self._refresh_button.pack(side=tk.RIGHT)
        
        # Export button
        self._export_button = ttk.Button(
            self._control_frame,
            text="Export",
            command=self._export_sessions
        )
        self._export_button.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Main content frame with paned window
        self._content_frame = ttk.PanedWindow(self._frame, orient=tk.HORIZONTAL)
        self._content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left pane: Session list
        self._list_frame = ttk.Frame(self._content_frame)
        self._content_frame.add(self._list_frame, weight=2)
        
        # Right pane: Session details
        self._details_frame = ttk.Frame(self._content_frame)
        self._content_frame.add(self._details_frame, weight=1)
        
        # Setup session list
        self._setup_session_list()
        
        # Setup session details
        self._setup_session_details()
    
    def _setup_session_list(self) -> None:
        """Set up the session list treeview."""
        # Session list label
        ttk.Label(self._list_frame, text="Study Sessions", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Create treeview for session list
        self._sessions_tree = ttk.Treeview(
            self._list_frame,
            columns=("date", "duration", "type", "document", "status"),
            show="tree headings",
            height=12
        )
        
        # Configure columns
        self._sessions_tree.heading("#0", text="ID")
        self._sessions_tree.heading("date", text="Date")
        self._sessions_tree.heading("duration", text="Duration")
        self._sessions_tree.heading("type", text="Type")
        self._sessions_tree.heading("document", text="Document")
        self._sessions_tree.heading("status", text="Status")
        
        # Configure column widths
        self._sessions_tree.column("#0", width=50, minwidth=50)
        self._sessions_tree.column("date", width=120, minwidth=100)
        self._sessions_tree.column("duration", width=80, minwidth=70)
        self._sessions_tree.column("type", width=80, minwidth=70)
        self._sessions_tree.column("document", width=150, minwidth=100)
        self._sessions_tree.column("status", width=80, minwidth=70)
        
        # Bind selection event
        self._sessions_tree.bind("<<TreeviewSelect>>", self._on_session_select)
        self._sessions_tree.bind("<Double-1>", self._on_session_double_click)
        
        # Pack treeview with scrollbars
        self._sessions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        self._tree_v_scroll = ttk.Scrollbar(self._list_frame, orient=tk.VERTICAL, command=self._sessions_tree.yview)
        self._tree_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._sessions_tree.config(yscrollcommand=self._tree_v_scroll.set)
        
        # Horizontal scrollbar
        self._tree_h_scroll = ttk.Scrollbar(self._list_frame, orient=tk.HORIZONTAL, command=self._sessions_tree.xview)
        self._tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self._sessions_tree.config(xscrollcommand=self._tree_h_scroll.set)
    
    def _setup_session_details(self) -> None:
        """Set up the session details panel."""
        # Details label
        ttk.Label(self._details_frame, text="Session Details", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Details content frame with scrollbar
        self._details_canvas = tk.Canvas(self._details_frame)
        self._details_scroll = ttk.Scrollbar(self._details_frame, orient=tk.VERTICAL, command=self._details_canvas.yview)
        self._details_content = ttk.Frame(self._details_canvas)
        
        # Configure scrollable canvas
        self._details_content.bind(
            "<Configure>",
            lambda e: self._details_canvas.configure(scrollregion=self._details_canvas.bbox("all"))
        )
        
        self._details_canvas.create_window((0, 0), window=self._details_content, anchor="nw")
        self._details_canvas.configure(yscrollcommand=self._details_scroll.set)
        
        # Pack canvas and scrollbar
        self._details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Setup details fields
        self._setup_detail_fields()
        
        # Initially show "No session selected"
        self._show_no_selection()
    
    def _setup_detail_fields(self) -> None:
        """Set up the detail fields in the details panel."""
        # Session ID
        self._id_label = ttk.Label(self._details_content, text="Session ID:")
        self._id_label.grid(row=0, column=0, sticky="nw", pady=(0, 5))
        self._id_value = ttk.Label(self._details_content, text="-", font=("Arial", 10, "bold"))
        self._id_value.grid(row=0, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Document
        self._doc_label = ttk.Label(self._details_content, text="Document:")
        self._doc_label.grid(row=1, column=0, sticky="nw", pady=(0, 5))
        self._doc_value = ttk.Label(self._details_content, text="-", wraplength=200)
        self._doc_value.grid(row=1, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Session type
        self._type_label = ttk.Label(self._details_content, text="Type:")
        self._type_label.grid(row=2, column=0, sticky="nw", pady=(0, 5))
        self._type_value = ttk.Label(self._details_content, text="-")
        self._type_value.grid(row=2, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Start time
        self._start_label = ttk.Label(self._details_content, text="Started:")
        self._start_label.grid(row=3, column=0, sticky="nw", pady=(0, 5))
        self._start_value = ttk.Label(self._details_content, text="-")
        self._start_value.grid(row=3, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # End time
        self._end_label = ttk.Label(self._details_content, text="Ended:")
        self._end_label.grid(row=4, column=0, sticky="nw", pady=(0, 5))
        self._end_value = ttk.Label(self._details_content, text="-")
        self._end_value.grid(row=4, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Duration
        self._duration_label = ttk.Label(self._details_content, text="Duration:")
        self._duration_label.grid(row=5, column=0, sticky="nw", pady=(0, 5))
        self._duration_value = ttk.Label(self._details_content, text="-", font=("Arial", 10, "bold"))
        self._duration_value.grid(row=5, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Status
        self._status_label = ttk.Label(self._details_content, text="Status:")
        self._status_label.grid(row=6, column=0, sticky="nw", pady=(0, 10))
        self._status_value = ttk.Label(self._details_content, text="-")
        self._status_value.grid(row=6, column=1, sticky="nw", padx=(10, 0), pady=(0, 10))
        
        # Focus score
        self._focus_label = ttk.Label(self._details_content, text="Focus Score:")
        self._focus_label.grid(row=7, column=0, sticky="nw", pady=(0, 5))
        self._focus_value = ttk.Label(self._details_content, text="-")
        self._focus_value.grid(row=7, column=1, sticky="nw", padx=(10, 0), pady=(0, 5))
        
        # Pauses
        self._pauses_label = ttk.Label(self._details_content, text="Pauses:")
        self._pauses_label.grid(row=8, column=0, sticky="nw", pady=(0, 10))
        self._pauses_value = ttk.Label(self._details_content, text="-")
        self._pauses_value.grid(row=8, column=1, sticky="nw", padx=(10, 0), pady=(0, 10))
        
        # Notes section
        self._notes_label = ttk.Label(self._details_content, text="Notes:")
        self._notes_label.grid(row=9, column=0, columnspan=2, sticky="nw", pady=(0, 5))
        
        self._notes_text = tk.Text(
            self._details_content, 
            height=6, 
            width=30, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg="#f0f0f0"
        )
        self._notes_text.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Action buttons
        self._actions_frame = ttk.Frame(self._details_content)
        self._actions_frame.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self._view_button = ttk.Button(
            self._actions_frame,
            text="View Full Details",
            command=self._view_full_details,
            state=tk.DISABLED
        )
        self._view_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        self._delete_button = ttk.Button(
            self._actions_frame,
            text="Delete Session",
            command=self._delete_session,
            state=tk.DISABLED
        )
        self._delete_button.pack(side=tk.TOP, fill=tk.X)
        
        # Configure grid weights
        self._details_content.columnconfigure(1, weight=1)
    
    def _load_sessions(self) -> None:
        """Load study sessions from the server."""
        try:
            document_filter = self._document_filter_var.get().strip() or None
            days_str = self._days_var.get()
            limit = 1000 if days_str == "All" else 100
            
            result = self._mcp_client.list_study_sessions(document_filter, limit)
            
            if result.success and result.data:
                self._sessions_data = result.data.get("sessions", [])
                self._populate_session_tree()
            else:
                self._sessions_data = []
                self._populate_session_tree()
                if not result.success:
                    messagebox.showerror("Error", result.error or "Failed to load sessions")
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error loading sessions: {str(e)}")
    
    def _apply_filters(self) -> None:
        """Apply filters and reload sessions."""
        self._load_sessions()
    
    def _populate_session_tree(self) -> None:
        """Populate the session tree with data."""
        # Clear existing items
        for item in self._sessions_tree.get_children():
            self._sessions_tree.delete(item)
        
        # Apply date filter if specified
        sessions_to_show = self._filter_sessions_by_date()
        
        # Add sessions to tree
        for session in sessions_to_show:
            session_id = session.get("id", "N/A")
            date_str = self._format_datetime(session.get("start_time"))
            duration = self._format_duration(session.get("duration", 0))
            session_type = session.get("session_type", "reading").title()
            document_id = session.get("document_id", "Unknown")
            status = session.get("status", "completed").title()
            
            # Truncate document ID if too long
            if len(document_id) > 20:
                document_id = document_id[:17] + "..."
            
            self._sessions_tree.insert(
                "", 
                "end",
                text=str(session_id),
                values=(date_str, duration, session_type, document_id, status)
            )
    
    def _filter_sessions_by_date(self) -> List[Dict[str, Any]]:
        """Filter sessions by the selected date range."""
        days_str = self._days_var.get()
        
        if days_str == "All":
            return self._sessions_data
        
        try:
            days = int(days_str)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            filtered_sessions = []
            for session in self._sessions_data:
                start_time_str = session.get("start_time")
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time >= cutoff_date:
                            filtered_sessions.append(session)
                    except (ValueError, AttributeError):
                        # Include sessions with invalid dates
                        filtered_sessions.append(session)
                else:
                    # Include sessions without start time
                    filtered_sessions.append(session)
            
            return filtered_sessions
        
        except ValueError:
            return self._sessions_data
    
    def _on_session_select(self, event) -> None:
        """Handle session selection in the tree."""
        selection = self._sessions_tree.selection()
        if selection:
            item = selection[0]
            session_id_text = self._sessions_tree.item(item, "text")
            
            try:
                session_id = int(session_id_text)
                # Find session data
                self._selected_session = None
                for session in self._sessions_data:
                    if session.get("id") == session_id:
                        self._selected_session = session
                        break
                
                if self._selected_session:
                    self._display_session_details(self._selected_session)
                else:
                    self._show_no_selection()
            
            except (ValueError, TypeError):
                self._show_no_selection()
        else:
            self._show_no_selection()
    
    def _on_session_double_click(self, event) -> None:
        """Handle double-click on session item."""
        self._view_full_details()
    
    def _display_session_details(self, session: Dict[str, Any]) -> None:
        """Display detailed information for the selected session."""
        # Update all detail fields
        self._id_value.config(text=str(session.get("id", "N/A")))
        self._doc_value.config(text=session.get("document_id", "Unknown"))
        self._type_value.config(text=session.get("session_type", "reading").title())
        
        # Format times
        start_time = self._format_datetime(session.get("start_time"))
        end_time = self._format_datetime(session.get("end_time"))
        self._start_value.config(text=start_time)
        self._end_value.config(text=end_time)
        
        # Duration
        duration = session.get("duration", 0)
        self._duration_value.config(text=self._format_duration(duration))
        
        # Status with color coding
        status = session.get("status", "completed").title()
        self._status_value.config(text=status)
        if status == "Completed":
            self._status_value.config(foreground="green")
        elif status == "Active":
            self._status_value.config(foreground="blue")
        elif status == "Paused":
            self._status_value.config(foreground="orange")
        else:
            self._status_value.config(foreground="red")
        
        # Focus score
        focus_score = session.get("focus_score")
        if focus_score is not None:
            self._focus_value.config(text=f"{focus_score:.1f}")
        else:
            self._focus_value.config(text="N/A")
        
        # Pauses
        pause_count = session.get("pause_count", 0)
        self._pauses_value.config(text=str(pause_count))
        
        # Notes
        notes = session.get("notes", "")
        self._notes_text.config(state=tk.NORMAL)
        self._notes_text.delete(1.0, tk.END)
        if notes:
            self._notes_text.insert(1.0, notes)
        else:
            self._notes_text.insert(1.0, "No notes available.")
        self._notes_text.config(state=tk.DISABLED)
        
        # Enable action buttons
        self._view_button.config(state=tk.NORMAL)
        self._delete_button.config(state=tk.NORMAL)
    
    def _show_no_selection(self) -> None:
        """Show the no selection state."""
        self._id_value.config(text="-")
        self._doc_value.config(text="-")
        self._type_value.config(text="-")
        self._start_value.config(text="-")
        self._end_value.config(text="-")
        self._duration_value.config(text="-")
        self._status_value.config(text="-", foreground="black")
        self._focus_value.config(text="-")
        self._pauses_value.config(text="-")
        
        self._notes_text.config(state=tk.NORMAL)
        self._notes_text.delete(1.0, tk.END)
        self._notes_text.insert(1.0, "Select a session to view details.")
        self._notes_text.config(state=tk.DISABLED)
        
        # Disable action buttons
        self._view_button.config(state=tk.DISABLED)
        self._delete_button.config(state=tk.DISABLED)
        
        self._selected_session = None
    
    def _view_full_details(self) -> None:
        """View full details of the selected session."""
        if not self._selected_session:
            return
        
        session_id = self._selected_session.get("id")
        if not session_id:
            return
        
        try:
            result = self._mcp_client.get_study_session_details(session_id)
            
            if result.success and result.data:
                details = result.data.get("session", {})
                self._show_details_dialog(details)
            else:
                messagebox.showerror("Error", result.error or "Failed to load session details")
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _show_details_dialog(self, details: Dict[str, Any]) -> None:
        """Show a dialog with full session details."""
        dialog = tk.Toplevel()
        dialog.title(f"Session {details.get('id', 'N/A')} - Full Details")
        dialog.geometry("500x400")
        # Make dialog modal to the main window
        dialog.grab_set()
        
        # Create scrollable text widget
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        
        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format and display details
        details_text = self._format_session_details(details)
        text_widget.insert(1.0, details_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        close_button = ttk.Button(dialog, text="Close", command=dialog.destroy)
        close_button.pack(pady=10)
    
    def _format_session_details(self, details: Dict[str, Any]) -> str:
        """Format session details for display."""
        lines = []
        lines.append(f"Session ID: {details.get('id', 'N/A')}")
        lines.append(f"Document: {details.get('document_id', 'Unknown')}")
        lines.append(f"Session Type: {details.get('session_type', 'reading').title()}")
        lines.append("")
        
        lines.append(f"Started: {self._format_datetime(details.get('start_time'))}")
        lines.append(f"Ended: {self._format_datetime(details.get('end_time'))}")
        lines.append(f"Duration: {self._format_duration(details.get('duration', 0))}")
        lines.append(f"Status: {details.get('status', 'completed').title()}")
        lines.append("")
        
        lines.append(f"Focus Score: {details.get('focus_score', 'N/A')}")
        lines.append(f"Pauses: {details.get('pause_count', 0)}")
        lines.append("")
        
        # Progress during session
        progress_data = details.get("progress_data", {})
        if progress_data:
            lines.append("Progress During Session:")
            lines.append(f"  Pages Read: {progress_data.get('pages_read', 0)}")
            lines.append(f"  Time Spent Reading: {self._format_duration(progress_data.get('reading_time', 0))}")
            lines.append("")
        
        # Notes
        notes = details.get("notes", "")
        lines.append("Notes:")
        if notes:
            lines.append(notes)
        else:
            lines.append("No notes available.")
        
        return "\\n".join(lines)
    
    def _delete_session(self) -> None:
        """Delete the selected session."""
        if not self._selected_session:
            return
        
        session_id = self._selected_session.get("id")
        if not session_id:
            return
        
        # Confirm deletion
        response = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete session {session_id}?\\n\\nThis action cannot be undone."
        )
        
        if response:
            try:
                result = self._mcp_client.call_tool("delete_study_session", {"session_id": session_id})
                
                if result.success:
                    messagebox.showinfo("Success", "Session deleted successfully")
                    self._load_sessions()  # Refresh the list
                else:
                    messagebox.showerror("Error", result.error or "Failed to delete session")
            
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _export_sessions(self) -> None:
        """Export sessions to CSV file."""
        if not self._sessions_data:
            messagebox.showwarning("No Data", "No sessions to export")
            return
        
        from tkinter import filedialog
        import csv
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Sessions"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'id', 'document_id', 'session_type', 'start_time', 
                        'end_time', 'duration', 'status', 'focus_score', 
                        'pause_count', 'notes'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for session in self._filter_sessions_by_date():
                        # Format data for CSV
                        row = {
                            'id': session.get('id', ''),
                            'document_id': session.get('document_id', ''),
                            'session_type': session.get('session_type', ''),
                            'start_time': session.get('start_time', ''),
                            'end_time': session.get('end_time', ''),
                            'duration': session.get('duration', 0),
                            'status': session.get('status', ''),
                            'focus_score': session.get('focus_score', ''),
                            'pause_count': session.get('pause_count', 0),
                            'notes': session.get('notes', '')
                        }
                        writer.writerow(row)
                
                messagebox.showinfo("Success", f"Sessions exported to {filename}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export sessions: {str(e)}")
    
    def _format_datetime(self, dt_str: Optional[str]) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return dt_str
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_frame(self) -> ttk.LabelFrame:
        """Get the main frame widget for embedding in parent containers."""
        return self._frame
    
    def refresh(self) -> None:
        """Refresh the session list."""
        self._load_sessions()
    
    def set_document_filter(self, document_id: str) -> None:
        """Set document filter and refresh."""
        self._document_filter_var.set(document_id)
        self._apply_filters()