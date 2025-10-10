"""
Study Buddy GUI - Error Dialog System

Provides user-friendly error dialogs with recovery suggestions,
non-technical error messages, and actionable recovery steps.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Factory Pattern, Template Method Pattern
SOLID: SRP (dialog display only), OCP (extensible dialogs), DIP (abstraction-based)
"""

import threading
import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from tkinter import messagebox, ttk
from typing import Callable, Dict, List, Optional

from gui.error_handling.error_tracker import ErrorCategory, ErrorContext, ErrorSeverity


class ErrorDialogType(Enum):
    """Types of error dialogs available."""

    SIMPLE = "simple"  # Basic error message
    DETAILED = "detailed"  # Error with technical details
    RECOVERY = "recovery"  # Error with recovery options
    PROGRESS = "progress"  # Error during long operation
    CONFIRMATION = "confirmation"  # Confirmation before action


class ErrorRecoveryAction(Enum):
    """Available recovery actions for errors."""

    RETRY = "retry"  # Try the operation again
    CANCEL = "cancel"  # Cancel the operation
    IGNORE = "ignore"  # Continue despite error
    RESTART = "restart"  # Restart the application
    REPORT = "report"  # Report the error
    SETTINGS = "settings"  # Open settings to fix
    OFFLINE = "offline"  # Continue in offline mode


@dataclass
class RecoveryOption:
    """Recovery option for error dialog."""

    action: ErrorRecoveryAction
    label: str
    description: str
    callback: Optional[Callable[[], None]] = None
    is_default: bool = False
    is_destructive: bool = False


@dataclass
class ErrorDialogConfig:
    """Configuration for error dialog display."""

    dialog_type: ErrorDialogType = ErrorDialogType.SIMPLE
    title: str = "Error"
    message: str = ""
    technical_details: str = ""
    recovery_options: List[RecoveryOption] = field(default_factory=list)
    auto_dismiss_seconds: Optional[int] = None
    modal: bool = True
    show_details_button: bool = True
    icon: str = "error"  # error, warning, info, question
    parent: Optional[tk.Widget] = None


class IErrorDialog(ABC):
    """
    Interface for error dialogs.

    Defines contract for different dialog implementations.
    """

    @abstractmethod
    def show(self, config: ErrorDialogConfig) -> Optional[ErrorRecoveryAction]:
        """
        Show error dialog to user.

        Args:
            config: Dialog configuration

        Returns:
            Selected recovery action or None if dismissed
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the dialog."""
        pass


class SimpleErrorDialog(IErrorDialog):
    """
    Simple error dialog with basic message.

    Uses tkinter messagebox for lightweight error display.
    """

    def show(self, config: ErrorDialogConfig) -> Optional[ErrorRecoveryAction]:
        """Show simple message box."""
        try:
            if config.icon == "warning":
                if config.parent is not None:
                    messagebox.showwarning(
                        config.title, config.message, parent=config.parent
                    )
                else:
                    messagebox.showwarning(config.title, config.message)
            elif config.icon == "info":
                if config.parent is not None:
                    messagebox.showinfo(
                        config.title, config.message, parent=config.parent
                    )
                else:
                    messagebox.showinfo(config.title, config.message)
            else:
                if config.parent is not None:
                    messagebox.showerror(
                        config.title, config.message, parent=config.parent
                    )
                else:
                    messagebox.showerror(config.title, config.message)

            return ErrorRecoveryAction.CANCEL
        except Exception:
            # Fallback if GUI not available
            print(f"ERROR: {config.title} - {config.message}")
            return ErrorRecoveryAction.CANCEL

    def close(self) -> None:
        """Simple dialogs auto-close."""
        pass


class DetailedErrorDialog(IErrorDialog):
    """
    Detailed error dialog with technical information.

    Custom tkinter dialog with expandable details section.
    """

    def __init__(self):
        self._dialog: Optional[tk.Toplevel] = None
        self._result: Optional[ErrorRecoveryAction] = None

    def show(self, config: ErrorDialogConfig) -> Optional[ErrorRecoveryAction]:
        """Show detailed error dialog."""
        try:
            # Create dialog window
            parent = config.parent
            self._dialog = tk.Toplevel(parent)
            self._dialog.title(config.title)
            self._dialog.grab_set() if config.modal else None
            self._dialog.resizable(False, False)

            # Center on parent
            if parent is not None:
                self._center_dialog(parent)
            else:
                self._center_on_screen()

            # Create UI
            self._create_detailed_ui(config)

            # Wait for result
            self._dialog.wait_window()

            return self._result

        except Exception:
            # Fallback to simple dialog
            return SimpleErrorDialog().show(config)

    def close(self) -> None:
        """Close detailed dialog."""
        if self._dialog:
            self._dialog.destroy()
            self._dialog = None

    def _create_detailed_ui(self, config: ErrorDialogConfig) -> None:
        """Create detailed dialog UI."""
        if not self._dialog:
            return

        # Main frame
        main_frame = ttk.Frame(self._dialog, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Icon and message frame
        msg_frame = ttk.Frame(main_frame)
        msg_frame.pack(fill="x", pady=(0, 20))

        # Icon (using unicode symbols)
        icon_text = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(config.icon, "❌")
        icon_label = ttk.Label(msg_frame, text=icon_text, font=("Arial", 32))
        icon_label.pack(side="left", padx=(0, 20))

        # Message
        message_frame = ttk.Frame(msg_frame)
        message_frame.pack(side="left", fill="both", expand=True)

        title_label = ttk.Label(
            message_frame, text=config.title, font=("Arial", 12, "bold")
        )
        title_label.pack(anchor="w")

        message_label = ttk.Label(
            message_frame,
            text=config.message,
            wraplength=400,
            justify="left",
        )
        message_label.pack(anchor="w", pady=(5, 0))

        # Details section (expandable)
        if config.technical_details and config.show_details_button:
            self._create_details_section(main_frame, config.technical_details)

        # Recovery options
        if config.recovery_options:
            self._create_recovery_buttons(main_frame, config.recovery_options)
        else:
            # Default OK button
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(20, 0))

            ok_button = ttk.Button(
                button_frame,
                text="OK",
                command=lambda: self._set_result(ErrorRecoveryAction.CANCEL),
            )
            ok_button.pack(side="right")

    def _create_details_section(self, parent: ttk.Frame, details: str) -> None:
        """Create expandable details section."""
        details_visible = tk.BooleanVar(value=False)

        def toggle_details():
            if details_visible.get():
                details_frame.pack(fill="both", expand=True, pady=(10, 0))
                details_button.configure(text="Hide Details ▲")
            else:
                details_frame.pack_forget()
                details_button.configure(text="Show Details ▼")

        # Details toggle button
        details_button = ttk.Button(
            parent,
            text="Show Details ▼",
            command=lambda: [
                details_visible.set(not details_visible.get()),
                toggle_details(),
            ],
        )
        details_button.pack(anchor="w", pady=(10, 0))

        # Details frame (initially hidden)
        details_frame = ttk.Frame(parent)

        # Details text with scrollbar
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill="both", expand=True)

        details_text = tk.Text(
            text_frame,
            height=8,
            width=60,
            wrap="word",
            font=("Courier", 9),
            state="normal",
        )
        details_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=details_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        details_text.configure(yscrollcommand=scrollbar.set)

        # Insert details text
        details_text.insert("1.0", details)
        details_text.configure(state="disabled")

    def _create_recovery_buttons(
        self, parent: ttk.Frame, options: List[RecoveryOption]
    ) -> None:
        """Create recovery action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(20, 0))

        # Sort options: default first, destructive last
        sorted_options = sorted(
            options, key=lambda opt: (not opt.is_default, opt.is_destructive)
        )

        for option in sorted_options:
            style = "Accent.TButton" if option.is_default else "TButton"
            if option.is_destructive:
                style = "Destructive.TButton"

            button = ttk.Button(
                button_frame,
                text=option.label,
                command=lambda act=option.action: self._set_result(act),
                style=style,
            )

            # Pack buttons right to left
            side = (
                "right"
                if option.is_default or option.action == ErrorRecoveryAction.CANCEL
                else "left"
            )
            button.pack(side=side, padx=(5, 0) if side == "right" else (0, 5))

        # Add tooltips for recovery options
        for i, option in enumerate(sorted_options):
            if option.description:
                # Simple tooltip simulation (would need proper tooltip widget in production)
                pass

    def _center_dialog(self, parent: tk.Widget) -> None:
        """Center dialog on parent window."""
        if not self._dialog:
            return

        self._dialog.update_idletasks()

        # Get parent geometry
        if parent and hasattr(parent, "winfo_x"):
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
        else:
            # Center on screen
            parent_x = parent_y = 0
            parent_width = self._dialog.winfo_screenwidth()
            parent_height = self._dialog.winfo_screenheight()

        # Get dialog size
        dialog_width = self._dialog.winfo_reqwidth()
        dialog_height = self._dialog.winfo_reqheight()

        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Ensure dialog is on screen
        x = max(0, min(x, self._dialog.winfo_screenwidth() - dialog_width))
        y = max(0, min(y, self._dialog.winfo_screenheight() - dialog_height))

        self._dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _center_on_screen(self) -> None:
        """Center dialog on screen."""
        if not self._dialog:
            return

        self._dialog.update_idletasks()

        # Get screen dimensions
        screen_width = self._dialog.winfo_screenwidth()
        screen_height = self._dialog.winfo_screenheight()

        # Get dialog size
        dialog_width = self._dialog.winfo_reqwidth()
        dialog_height = self._dialog.winfo_reqheight()

        # Calculate center position
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2

        # Ensure dialog is on screen
        x = max(0, x)
        y = max(0, y)

        self._dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _set_result(self, action: ErrorRecoveryAction) -> None:
        """Set dialog result and close."""
        self._result = action
        if self._dialog:
            self._dialog.destroy()


class ProgressErrorDialog(IErrorDialog):
    """
    Error dialog for long-running operations.

    Shows error with progress context and operation cancellation.
    """

    def __init__(self):
        self._dialog: Optional[tk.Toplevel] = None
        self._result: Optional[ErrorRecoveryAction] = None
        self._progress_var: Optional[tk.DoubleVar] = None

    def show(self, config: ErrorDialogConfig) -> Optional[ErrorRecoveryAction]:
        """Show progress error dialog."""
        # Implementation similar to DetailedErrorDialog but with progress bar
        # For brevity, using detailed dialog
        return DetailedErrorDialog().show(config)

    def close(self) -> None:
        """Close progress dialog."""
        if self._dialog:
            self._dialog.destroy()


class ErrorDialogFactory:
    """
    Factory for creating error dialogs.

    Selects appropriate dialog type based on error context and configuration.
    """

    def __init__(self):
        self._dialog_types = {
            ErrorDialogType.SIMPLE: SimpleErrorDialog,
            ErrorDialogType.DETAILED: DetailedErrorDialog,
            ErrorDialogType.RECOVERY: DetailedErrorDialog,  # Same implementation
            ErrorDialogType.PROGRESS: ProgressErrorDialog,
            ErrorDialogType.CONFIRMATION: DetailedErrorDialog,
        }

    def create_dialog(self, dialog_type: ErrorDialogType) -> IErrorDialog:
        """Create dialog of specified type."""
        dialog_class = self._dialog_types.get(dialog_type, SimpleErrorDialog)
        return dialog_class()

    def create_from_error_context(self, context: ErrorContext) -> IErrorDialog:
        """Create appropriate dialog based on error context."""
        # Determine dialog type based on error severity and category
        if context.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            if context.category == ErrorCategory.NETWORK:
                return self.create_dialog(ErrorDialogType.RECOVERY)
            else:
                return self.create_dialog(ErrorDialogType.DETAILED)
        elif context.severity == ErrorSeverity.MEDIUM:
            return self.create_dialog(ErrorDialogType.DETAILED)
        else:
            return self.create_dialog(ErrorDialogType.SIMPLE)


class ErrorMessageFormatter:
    """
    Formats error messages for user-friendly display.

    Converts technical error information into understandable messages.
    """

    def __init__(self):
        # Error message templates
        self._message_templates = {
            # Network errors
            ErrorCategory.NETWORK: {
                "connection_failed": "Could not connect to Study Buddy server. Please check your internet connection.",
                "timeout": "The operation took too long to complete. The server may be busy.",
                "server_error": "The Study Buddy server encountered an error. Please try again later.",
            },
            # File errors
            ErrorCategory.DATA: {
                "file_not_found": "The requested file could not be found. It may have been moved or deleted.",
                "permission_denied": "Permission denied. Please check file permissions or try running as administrator.",
                "corrupt_file": "The file appears to be corrupted or in an unsupported format.",
            },
            # UI errors
            ErrorCategory.UI: {
                "widget_error": "A user interface component encountered an error. Please try refreshing the view.",
                "theme_error": "Theme loading failed. Reverting to default theme.",
                "layout_error": "Window layout error. Please resize the window or restart the application.",
            },
            # Performance errors
            ErrorCategory.PERFORMANCE: {
                "memory_low": "System memory is running low. Consider closing other applications.",
                "slow_operation": "This operation is taking longer than expected. You can continue waiting or cancel.",
            },
            # Generic errors
            "generic": "An unexpected error occurred. Please try again or contact support if the problem persists.",
        }

        # Recovery suggestions
        self._recovery_suggestions = {
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a few moments",
                "Restart the application",
                "Work offline with cached data",
            ],
            ErrorCategory.DATA: [
                "Check file permissions",
                "Verify the file exists",
                "Try a different file",
                "Contact support if problem persists",
            ],
            ErrorCategory.UI: [
                "Refresh the current view",
                "Resize the application window",
                "Restart the application",
                "Reset to default settings",
            ],
            ErrorCategory.PERFORMANCE: [
                "Close other applications",
                "Free up system memory",
                "Restart the application",
                "Check system resources",
            ],
        }

    def format_user_message(self, context: ErrorContext) -> str:
        """
        Format error context into user-friendly message.

        Args:
            context: Error context to format

        Returns:
            User-friendly error message
        """
        category_messages = self._message_templates.get(context.category, {})

        # Try to match specific error patterns
        error_msg_lower = context.error_message.lower()

        # Network error patterns
        if context.category == ErrorCategory.NETWORK:
            if "connection" in error_msg_lower or "refused" in error_msg_lower:
                return category_messages.get(
                    "connection_failed", self._message_templates["generic"]
                )
            elif "timeout" in error_msg_lower:
                return category_messages.get(
                    "timeout", self._message_templates["generic"]
                )
            else:
                return category_messages.get(
                    "server_error", self._message_templates["generic"]
                )

        # File error patterns
        elif context.category == ErrorCategory.DATA:
            if "not found" in error_msg_lower or "no such file" in error_msg_lower:
                return category_messages.get(
                    "file_not_found", self._message_templates["generic"]
                )
            elif "permission" in error_msg_lower or "access" in error_msg_lower:
                return category_messages.get(
                    "permission_denied", self._message_templates["generic"]
                )
            elif "corrupt" in error_msg_lower or "invalid" in error_msg_lower:
                return category_messages.get(
                    "corrupt_file", self._message_templates["generic"]
                )

        # Use generic message for category
        generic_msg = list(category_messages.values())[0] if category_messages else None
        return generic_msg or self._message_templates["generic"]

    def get_recovery_suggestions(self, context: ErrorContext) -> List[str]:
        """Get recovery suggestions for error context."""
        return self._recovery_suggestions.get(
            context.category,
            [
                "Try the operation again",
                "Restart the application",
                "Contact support if problem persists",
            ],
        )

    def create_recovery_options(self, context: ErrorContext) -> List[RecoveryOption]:
        """Create recovery options based on error context."""
        options = []

        # Always include cancel option
        options.append(
            RecoveryOption(
                action=ErrorRecoveryAction.CANCEL,
                label="Cancel",
                description="Close this dialog",
                is_default=False,
            )
        )

        # Add context-specific recovery options
        if context.category == ErrorCategory.NETWORK:
            options.extend(
                [
                    RecoveryOption(
                        action=ErrorRecoveryAction.RETRY,
                        label="Retry",
                        description="Try the operation again",
                        is_default=True,
                    ),
                    RecoveryOption(
                        action=ErrorRecoveryAction.OFFLINE,
                        label="Work Offline",
                        description="Continue with cached data",
                    ),
                ]
            )

        elif context.category == ErrorCategory.DATA:
            options.extend(
                [
                    RecoveryOption(
                        action=ErrorRecoveryAction.RETRY,
                        label="Try Again",
                        description="Retry the file operation",
                        is_default=True,
                    ),
                    RecoveryOption(
                        action=ErrorRecoveryAction.SETTINGS,
                        label="Settings",
                        description="Open settings to configure file locations",
                    ),
                ]
            )

        elif context.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            options.extend(
                [
                    RecoveryOption(
                        action=ErrorRecoveryAction.RESTART,
                        label="Restart App",
                        description="Restart the application",
                    ),
                    RecoveryOption(
                        action=ErrorRecoveryAction.REPORT,
                        label="Report Error",
                        description="Send error report to developers",
                    ),
                ]
            )

        else:
            options.append(
                RecoveryOption(
                    action=ErrorRecoveryAction.RETRY,
                    label="Try Again",
                    description="Retry the operation",
                    is_default=True,
                )
            )

        return options


class ErrorDialogManager:
    """
    Central manager for error dialogs.

    Responsibilities:
    - Show user-friendly error dialogs
    - Format technical errors for users
    - Manage dialog lifecycle and threading
    - Coordinate with error tracker
    - Provide recovery workflows
    """

    def __init__(self):
        self._factory = ErrorDialogFactory()
        self._formatter = ErrorMessageFormatter()
        self._active_dialogs: Dict[str, IErrorDialog] = {}
        self._lock = threading.Lock()

    def show_error_from_context(
        self,
        context: ErrorContext,
        parent: Optional[tk.Widget] = None,
        modal: bool = True,
    ) -> Optional[ErrorRecoveryAction]:
        """
        Show error dialog from error context.

        Args:
            context: Error context to display
            parent: Parent widget for dialog
            modal: Whether dialog should be modal

        Returns:
            Selected recovery action
        """
        with self._lock:
            # Check if already showing dialog for this error
            if context.error_id in self._active_dialogs:
                return None

            # Create dialog
            dialog = self._factory.create_from_error_context(context)

            # Format user-friendly message
            user_message = self._formatter.format_user_message(context)

            # Create recovery options
            recovery_options = self._formatter.create_recovery_options(context)

            # Configure dialog
            config = ErrorDialogConfig(
                title=self._get_error_title(context),
                message=user_message,
                technical_details=self._format_technical_details(context),
                recovery_options=recovery_options,
                modal=modal,
                parent=parent,
                icon=self._get_error_icon(context),
            )

            # Track active dialog
            self._active_dialogs[context.error_id] = dialog

            try:
                # Show dialog
                result = dialog.show(config)
                return result
            finally:
                # Clean up
                if context.error_id in self._active_dialogs:
                    del self._active_dialogs[context.error_id]

    def show_simple_error(
        self,
        message: str,
        title: str = "Error",
        parent: Optional[tk.Widget] = None,
    ) -> None:
        """Show simple error message."""
        dialog = SimpleErrorDialog()
        config = ErrorDialogConfig(
            title=title,
            message=message,
            parent=parent,
        )
        dialog.show(config)

    def show_confirmation_dialog(
        self,
        message: str,
        title: str = "Confirm",
        parent: Optional[tk.Widget] = None,
    ) -> bool:
        """
        Show confirmation dialog.

        Returns:
            True if user confirmed, False otherwise
        """
        try:
            if parent is not None:
                result = messagebox.askyesno(title, message, parent=parent)
            else:
                result = messagebox.askyesno(title, message)
            return result or False
        except Exception:
            return False

    def close_all_dialogs(self) -> None:
        """Close all active error dialogs."""
        with self._lock:
            for dialog in list(self._active_dialogs.values()):
                try:
                    dialog.close()
                except Exception:
                    pass
            self._active_dialogs.clear()

    def _get_error_title(self, context: ErrorContext) -> str:
        """Get appropriate title for error."""
        if context.severity == ErrorSeverity.CRITICAL:
            return "Critical Error"
        elif context.severity == ErrorSeverity.HIGH:
            return "Error"
        elif context.severity == ErrorSeverity.MEDIUM:
            return "Warning"
        else:
            return "Notice"

    def _get_error_icon(self, context: ErrorContext) -> str:
        """Get appropriate icon for error."""
        if context.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.HIGH):
            return "error"
        elif context.severity == ErrorSeverity.MEDIUM:
            return "warning"
        else:
            return "info"

    def _format_technical_details(self, context: ErrorContext) -> str:
        """Format technical details for display."""
        details = []

        details.append(f"Error ID: {context.error_id}")
        details.append(f"Time: {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append(f"Type: {context.error_type}")
        details.append(f"Category: {context.category.value}")
        details.append(f"Severity: {context.severity.value}")

        if context.widget_id:
            details.append(f"Component: {context.widget_id}")

        if context.user_action:
            details.append(f"User Action: {context.user_action}")

        details.append(f"Technical Message: {context.error_message}")

        if context.function_name:
            details.append(f"Function: {context.function_name}")

        if context.stack_trace:
            details.append("\nStack Trace:")
            details.append(context.stack_trace)

        return "\n".join(details)


# Global error dialog manager instance
_error_dialog_manager: Optional[ErrorDialogManager] = None
_dialog_manager_lock = threading.Lock()


def get_error_dialog_manager() -> ErrorDialogManager:
    """
    Get global error dialog manager instance (singleton pattern).

    Returns:
        ErrorDialogManager instance
    """
    global _error_dialog_manager

    if _error_dialog_manager is None:
        with _dialog_manager_lock:
            if _error_dialog_manager is None:
                _error_dialog_manager = ErrorDialogManager()

    return _error_dialog_manager


# Convenience functions for common error dialogs
def show_error(
    message: str,
    title: str = "Error",
    parent: Optional[tk.Widget] = None,
) -> None:
    """Show simple error message."""
    manager = get_error_dialog_manager()
    manager.show_simple_error(message, title, parent)


def show_error_from_context(
    context: ErrorContext,
    parent: Optional[tk.Widget] = None,
) -> Optional[ErrorRecoveryAction]:
    """Show error dialog from error context."""
    manager = get_error_dialog_manager()
    return manager.show_error_from_context(context, parent)


def confirm(
    message: str,
    title: str = "Confirm",
    parent: Optional[tk.Widget] = None,
) -> bool:
    """Show confirmation dialog."""
    manager = get_error_dialog_manager()
    return manager.show_confirmation_dialog(message, title, parent)
