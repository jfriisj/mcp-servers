"""
Study Buddy GUI - Error Handling and Logging System

Provides comprehensive error tracking, user-friendly error dialogs, performance monitoring,
debug logging, and graceful degradation for the GUI application.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Observer Pattern, Strategy Pattern, Factory Pattern
SOLID: SRP (focused responsibilities), OCP (extensible), DIP (abstraction-based)
"""

# Error Tracking System
from gui.error_handling.error_tracker import (
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    ErrorTracker,
    get_error_tracker,
)

# User-Friendly Error Dialogs
from gui.error_handling.error_dialogs import (
    ErrorDialogType,
    ErrorDialogConfig,
    ErrorDialogManager,
    get_error_dialog_manager,
)

# Performance Monitoring
from gui.error_handling.performance_monitor import (
    PerformanceThreshold,
    PerformanceAlert,
    PerformanceMonitor,
    get_performance_monitor,
)

# Debug Logging System
from gui.error_handling.debug_logger import (
    LogLevel,
    LogFormat,
    DebugLogger,
    get_debug_logger,
)

# Graceful Degradation
from gui.error_handling.graceful_degradation import (
    DegradationMode,
    ConnectionState,
    FallbackData,
    IFallbackStrategy,
    CachedDataFallback,
    StaticDataFallback,
    RetryConfig,
    CircuitBreaker,
    GracefulDegradationManager,
    get_degradation_manager,
    get_current_mode,
    is_offline_mode,
    record_mcp_success,
    record_mcp_failure,
    get_fallback_data,
    store_operation_data,
)

# Integration Mixins (for easy widget integration)
# TODO: Create integration mixins for seamless widget integration
# from gui.error_handling.integration import (
#     ErrorHandlingMixin,
#     ErrorAwareWidget,
#     add_error_handling_features,
# )

__all__ = [
    # Error Tracking
    "ErrorContext",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorTracker",
    "get_error_tracker",
    # Error Dialogs
    "ErrorDialogType",
    "ErrorDialogConfig",
    "ErrorDialogManager",
    "get_error_dialog_manager",
    # Performance Monitoring
    "PerformanceThreshold",
    "PerformanceAlert",
    "PerformanceMonitor",
    "get_performance_monitor",
    # Debug Logging
    "LogLevel",
    "LogFormat",
    "DebugLogger",
    "get_debug_logger",
    # Graceful Degradation
    "DegradationMode",
    "ConnectionState",
    "FallbackData",
    "IFallbackStrategy",
    "CachedDataFallback",
    "StaticDataFallback",
    "RetryConfig",
    "CircuitBreaker",
    "GracefulDegradationManager",
    "get_degradation_manager",
    "get_current_mode",
    "is_offline_mode",
    "record_mcp_success",
    "record_mcp_failure",
    "get_fallback_data",
    "store_operation_data",
    # Integration - TODO: Implement integration mixins
    # "ErrorHandlingMixin",
    # "ErrorAwareWidget", 
    # "add_error_handling_features",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "Study Buddy Development Team"
__description__ = "Comprehensive error handling and logging system for Study Buddy GUI"
