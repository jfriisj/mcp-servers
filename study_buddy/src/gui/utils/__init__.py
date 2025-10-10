"""
Study Buddy GUI - Utilities Package

Common utilities for GUI operations including clipboard management,
formatting helpers, and other cross-cutting concerns.

Architecture: Clean Architecture Layer 4 (Infrastructure - Utilities)
"""

from .clipboard_manager import ClipboardManager

__all__ = [
    'ClipboardManager'
]