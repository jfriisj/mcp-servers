"""
Session Panel Widget for Study Buddy MCP Server.

This module provides the SessionPanelWidget class which manages study sessions
including start, pause, resume, and end operations through MCP tool interactions.
"""

from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import time

from ..sync_mcp_client import SyncMCPClient


class SessionPanelWidget:
    """
    A GUI widget that manages study sessions with timer and controls.
    
    This widget follows the Single Responsibility Principle by focusing solely
    on session management functionality. It depends on abstractions
    (SyncMCPClient) following the Dependency Inversion Principle.
    """
    
    def __init__(self, parent: tk.Widget, mcp_client: SyncMCPClient):
        """
        Initialize the SessionPanelWidget.
        
        Args:
            parent: The parent tkinter widget
            mcp_client: The MCP client for backend interactions
        """
        self._mcp_client = mcp_client
        self._current_document_id: Optional[str] = None
        self._active_session: Optional[Dict[str, Any]] = None
        self._session_start_time: Optional[datetime] = None
        self._paused_time: Optional[datetime] = None
        self._total_paused_duration: int = 0  # seconds
        self._timer_running = False
        self._timer_job: Optional[str] = None
        
        # Create main frame
        self._frame = ttk.LabelFrame(parent, text="Study Session", padding="10")
        
        # Initialize UI components
        self._setup_ui()
        
        # Check for existing active session
        self._check_active_session()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Document selection
        ttk.Label(self._frame, text="Document:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self._document_var = tk.StringVar()
        self._document_entry = ttk.Entry(self._frame, textvariable=self._document_var, width=40)
        self._document_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 10))
        
        # Session timer display
        ttk.Label(self._frame, text="Session Time:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        self._time_var = tk.StringVar(value="00:00:00")
        self._time_label = ttk.Label(self._frame, textvariable=self._time_var, font=("Arial", 14, "bold"))
        self._time_label.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=(0, 10))
        
        # Session status
        self._status_var = tk.StringVar(value="No active session")
        self._status_label = ttk.Label(self._frame, textvariable=self._status_var, foreground="gray")
        self._status_label.grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(0, 10))
        
        # Session type selection
        ttk.Label(self._frame, text="Session Type:").grid(row=2, column=0, sticky="w", pady=(0, 10))
        self._session_type_var = tk.StringVar(value="reading")
        self._session_type_combo = ttk.Combobox(
            self._frame, 
            textvariable=self._session_type_var,
            values=["reading", "studying", "research", "notes"],
            state="readonly",
            width=15
        )
        self._session_type_combo.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(0, 10))
        
        # Control buttons frame
        self._buttons_frame = ttk.Frame(self._frame)
        self._buttons_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        
        # Session control buttons
        self._start_button = ttk.Button(
            self._buttons_frame, 
            text="Start Session", 
            command=self._start_session,
            style="Accent.TButton"
        )
        self._start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self._pause_button = ttk.Button(
            self._buttons_frame, 
            text="Pause", 
            command=self._pause_session,
            state=tk.DISABLED
        )
        self._pause_button.pack(side=tk.LEFT, padx=5)
        
        self._resume_button = ttk.Button(
            self._buttons_frame, 
            text="Resume", 
            command=self._resume_session,
            state=tk.DISABLED
        )
        self._resume_button.pack(side=tk.LEFT, padx=5)
        
        self._end_button = ttk.Button(
            self._buttons_frame, 
            text="End Session", 
            command=self._end_session,
            state=tk.DISABLED
        )
        self._end_button.pack(side=tk.LEFT, padx=5)
        
        # Session notes
        ttk.Label(self._frame, text="Session Notes:").grid(row=4, column=0, sticky="nw", pady=(15, 5))
        self._notes_text = tk.Text(self._frame, height=3, width=50, wrap=tk.WORD)
        self._notes_text.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(5, 0), pady=(15, 0))
        
        # Scrollbar for notes
        self._notes_scroll = ttk.Scrollbar(self._frame, orient=tk.VERTICAL, command=self._notes_text.yview)
        self._notes_text.config(yscrollcommand=self._notes_scroll.set)
        
        # Session statistics (read-only display)
        self._stats_frame = ttk.LabelFrame(self._frame, text="Session Statistics", padding="5")
        self._stats_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(15, 0))
        
        # Configure column weights
        self._frame.columnconfigure(1, weight=1)
        self._stats_frame.columnconfigure(1, weight=1)
        
        self._setup_stats_display()
    
    def _setup_stats_display(self) -> None:
        """Set up the statistics display area."""
        # Today's total time
        ttk.Label(self._stats_frame, text="Today's Total:").grid(row=0, column=0, sticky="w", pady=2)
        self._today_total_var = tk.StringVar(value="0m")
        ttk.Label(self._stats_frame, textvariable=self._today_total_var).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        
        # Sessions today
        ttk.Label(self._stats_frame, text="Sessions Today:").grid(row=0, column=2, sticky="w", padx=(20, 0), pady=2)
        self._sessions_today_var = tk.StringVar(value="0")
        ttk.Label(self._stats_frame, textvariable=self._sessions_today_var).grid(row=0, column=3, sticky="w", padx=(10, 0), pady=2)
        
        # Average session length
        ttk.Label(self._stats_frame, text="Avg Session:").grid(row=1, column=0, sticky="w", pady=2)
        self._avg_session_var = tk.StringVar(value="0m")
        ttk.Label(self._stats_frame, textvariable=self._avg_session_var).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)
        
        # Focus score
        ttk.Label(self._stats_frame, text="Focus Score:").grid(row=1, column=2, sticky="w", padx=(20, 0), pady=2)
        self._focus_score_var = tk.StringVar(value="N/A")
        ttk.Label(self._stats_frame, textvariable=self._focus_score_var).grid(row=1, column=3, sticky="w", padx=(10, 0), pady=2)
    
    def _check_active_session(self) -> None:
        """Check if there's an active session and restore it."""
        try:
            result = self._mcp_client.get_active_session()
            if result.success and result.data and "session" in result.data:
                self._active_session = result.data["session"]
                self._restore_session_state()
        except Exception as e:
            print(f"Error checking active session: {e}")
    
    def _restore_session_state(self) -> None:
        """Restore UI state for an active session."""
        if not self._active_session:
            return
        
        # Set document ID
        self._current_document_id = self._active_session.get("document_id")
        if self._current_document_id:
            self._document_var.set(self._current_document_id)
        
        # Set session type
        session_type = self._active_session.get("session_type", "reading")
        self._session_type_var.set(session_type)
        
        # Update UI state based on session status
        status = self._active_session.get("status", "active")
        if status == "active":
            self._session_start_time = datetime.now()  # Approximate, should get from server
            self._timer_running = True
            self._start_timer()
            self._set_session_controls_state("active")
            self._status_var.set("Session active")
        elif status == "paused":
            self._paused_time = datetime.now()
            self._timer_running = False
            self._set_session_controls_state("paused")
            self._status_var.set("Session paused")
        
        # Load session notes if any
        notes = self._active_session.get("notes", "")
        self._notes_text.delete(1.0, tk.END)
        self._notes_text.insert(1.0, notes)
    
    def _start_session(self) -> None:
        """Start a new study session."""
        document_id = self._document_var.get().strip()
        if not document_id:
            messagebox.showerror("Error", "Please enter a document ID")
            return
        
        session_type = self._session_type_var.get()
        
        try:
            result = self._mcp_client.start_study_session(document_id, session_type)
            
            if result.success:
                self._active_session = result.data.get("session") if result.data else {}
                self._current_document_id = document_id
                self._session_start_time = datetime.now()
                self._total_paused_duration = 0
                self._paused_time = None
                self._timer_running = True
                
                self._start_timer()
                self._set_session_controls_state("active")
                self._status_var.set("Session active")
                
                messagebox.showinfo("Success", "Study session started!")
                self._update_session_stats()
            else:
                error_msg = result.error or "Failed to start session"
                messagebox.showerror("Error", error_msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _pause_session(self) -> None:
        """Pause the current session."""
        if not self._active_session:
            return
        
        session_id = self._active_session.get("id")
        if not session_id:
            messagebox.showerror("Error", "No active session ID")
            return
        
        try:
            result = self._mcp_client.pause_study_session(session_id)
            
            if result.success:
                self._paused_time = datetime.now()
                self._timer_running = False
                self._stop_timer()
                self._set_session_controls_state("paused")
                self._status_var.set("Session paused")
            else:
                error_msg = result.error or "Failed to pause session"
                messagebox.showerror("Error", error_msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _resume_session(self) -> None:
        """Resume the paused session."""
        if not self._active_session:
            return
        
        session_id = self._active_session.get("id")
        if not session_id:
            messagebox.showerror("Error", "No active session ID")
            return
        
        try:
            result = self._mcp_client.resume_study_session(session_id)
            
            if result.success:
                # Add paused duration to total
                if self._paused_time:
                    pause_duration = (datetime.now() - self._paused_time).total_seconds()
                    self._total_paused_duration += int(pause_duration)
                
                self._paused_time = None
                self._timer_running = True
                self._start_timer()
                self._set_session_controls_state("active")
                self._status_var.set("Session active")
            else:
                error_msg = result.error or "Failed to resume session"
                messagebox.showerror("Error", error_msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _end_session(self) -> None:
        """End the current session."""
        if not self._active_session:
            return
        
        session_id = self._active_session.get("id")
        if not session_id:
            messagebox.showerror("Error", "No active session ID")
            return
        
        # Get session notes
        notes = self._notes_text.get(1.0, tk.END).strip()
        
        try:
            result = self._mcp_client.end_study_session(session_id, notes if notes else None)
            
            if result.success:
                self._timer_running = False
                self._stop_timer()
                self._reset_session_state()
                self._set_session_controls_state("inactive")
                self._status_var.set("No active session")
                
                # Show session summary
                session_time = self._format_duration(self._get_session_duration())
                messagebox.showinfo("Session Ended", f"Study session completed!\\nTotal time: {session_time}")
                
                self._update_session_stats()
            else:
                error_msg = result.error or "Failed to end session"
                messagebox.showerror("Error", error_msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _start_timer(self) -> None:
        """Start the session timer."""
        if self._timer_running:
            self._update_timer_display()
            self._timer_job = self._frame.after(1000, self._start_timer)  # Update every second
    
    def _stop_timer(self) -> None:
        """Stop the session timer."""
        if self._timer_job:
            self._frame.after_cancel(self._timer_job)
            self._timer_job = None
    
    def _update_timer_display(self) -> None:
        """Update the timer display."""
        if self._session_start_time:
            duration = self._get_session_duration()
            formatted_time = self._format_duration(duration)
            self._time_var.set(formatted_time)
    
    def _get_session_duration(self) -> int:
        """Get the current session duration in seconds."""
        if not self._session_start_time:
            return 0
        
        if self._timer_running:
            # Active session
            total_duration = (datetime.now() - self._session_start_time).total_seconds()
            return int(total_duration - self._total_paused_duration)
        else:
            # Paused session
            if self._paused_time:
                pause_start_duration = (self._paused_time - self._session_start_time).total_seconds()
                return int(pause_start_duration - self._total_paused_duration)
            return 0
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _set_session_controls_state(self, state: str) -> None:
        """Set the state of session control buttons."""
        if state == "inactive":
            self._start_button.config(state=tk.NORMAL)
            self._pause_button.config(state=tk.DISABLED)
            self._resume_button.config(state=tk.DISABLED)
            self._end_button.config(state=tk.DISABLED)
            self._session_type_combo.config(state="readonly")
            self._document_entry.config(state=tk.NORMAL)
        elif state == "active":
            self._start_button.config(state=tk.DISABLED)
            self._pause_button.config(state=tk.NORMAL)
            self._resume_button.config(state=tk.DISABLED)
            self._end_button.config(state=tk.NORMAL)
            self._session_type_combo.config(state=tk.DISABLED)
            self._document_entry.config(state=tk.DISABLED)
        elif state == "paused":
            self._start_button.config(state=tk.DISABLED)
            self._pause_button.config(state=tk.DISABLED)
            self._resume_button.config(state=tk.NORMAL)
            self._end_button.config(state=tk.NORMAL)
            self._session_type_combo.config(state=tk.DISABLED)
            self._document_entry.config(state=tk.DISABLED)
    
    def _reset_session_state(self) -> None:
        """Reset session state after ending."""
        self._active_session = None
        self._session_start_time = None
        self._paused_time = None
        self._total_paused_duration = 0
        self._current_document_id = None
        self._time_var.set("00:00:00")
        self._notes_text.delete(1.0, tk.END)
    
    def _update_session_stats(self) -> None:
        """Update session statistics display."""
        try:
            # Get session analytics for today
            result = self._mcp_client.get_session_analytics(days=1)
            
            if result.success and result.data:
                analytics = result.data.get("analytics", {})
                
                # Update today's statistics
                today_total = analytics.get("total_session_time", 0)
                sessions_count = analytics.get("session_count", 0)
                avg_session = analytics.get("average_session_duration", 0)
                focus_score = analytics.get("average_focus_score")
                
                self._today_total_var.set(self._format_duration_short(today_total))
                self._sessions_today_var.set(str(sessions_count))
                self._avg_session_var.set(self._format_duration_short(avg_session))
                
                if focus_score is not None:
                    self._focus_score_var.set(f"{focus_score:.1f}")
                else:
                    self._focus_score_var.set("N/A")
        
        except Exception as e:
            print(f"Error updating session stats: {e}")
    
    def _format_duration_short(self, seconds: int) -> str:
        """Format duration for statistics display (e.g., '2h 30m')."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    
    def get_frame(self) -> ttk.LabelFrame:
        """Get the main frame widget for embedding in parent containers."""
        return self._frame
    
    def set_document(self, document_id: str) -> None:
        """Set the document ID for the session."""
        if not self._active_session:  # Only allow if no active session
            self._document_var.set(document_id)
    
    def refresh_stats(self) -> None:
        """Refresh session statistics display."""
        self._update_session_stats()
    
    def cleanup(self) -> None:
        """Clean up resources when widget is destroyed."""
        if self._timer_job:
            self._frame.after_cancel(self._timer_job)
            self._timer_job = None