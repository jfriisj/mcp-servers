"""
Study Buddy GUI - Data Sanitization System

Provides comprehensive data sanitization and cleaning to prevent security issues,
XSS-like attacks, and ensure data integrity before storage and display.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Chain of Responsibility Pattern  
SOLID: SRP (sanitization only), OCP (extensible rules), DIP (rule abstraction)
"""

import html
import re
import unicodedata
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from gui.error_handling import get_debug_logger, get_error_tracker, ErrorSeverity, ErrorCategory


class SanitizationLevel(Enum):
    """Levels of data sanitization strictness."""
    
    PERMISSIVE = "permissive"       # Light sanitization, preserve formatting
    STANDARD = "standard"           # Balanced sanitization for general use
    STRICT = "strict"               # Heavy sanitization for security-critical data
    PARANOID = "paranoid"           # Maximum sanitization, safety over usability


class DataType(Enum):
    """Types of data being sanitized for context-aware cleaning."""
    
    USER_INPUT = auto()             # Direct user text input
    DOCUMENT_CONTENT = auto()       # Document text content  
    FILE_PATH = auto()              # File paths and names
    SEARCH_QUERY = auto()           # Search query strings
    MARKDOWN_CONTENT = auto()       # Markdown formatted text
    HTML_CONTENT = auto()           # HTML content (if any)
    JSON_DATA = auto()              # JSON structured data
    URL_CONTENT = auto()            # URLs and web content


@dataclass
class SanitizationResult:
    """Result of data sanitization operation."""
    
    original_data: Any
    sanitized_data: Any
    sanitization_level: SanitizationLevel
    data_type: DataType
    changes_made: bool = False
    issues_found: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize lists if not provided."""
        if self.issues_found is None:
            self.issues_found = []
        if self.warnings is None:
            self.warnings = []
        
        # Determine if changes were made
        self.changes_made = self.original_data != self.sanitized_data


class ISanitizationRule(ABC):
    """Interface for data sanitization rules."""
    
    @abstractmethod
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """
        Sanitize data according to rule.
        
        Args:
            data: Data to sanitize
            level: Sanitization strictness level
            data_type: Type of data being sanitized
            context: Optional context information
            
        Returns:
            SanitizationResult with cleaned data and metadata
        """
        pass
    
    @abstractmethod
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to given data type."""
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """Get descriptive name for this rule."""
        pass


class HTMLSanitizationRule(ISanitizationRule):
    """Sanitizes HTML content and prevents XSS attacks."""
    
    def __init__(self):
        # Dangerous HTML patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',       # Script tags
            r'<iframe[^>]*>.*?</iframe>',       # Iframes
            r'<object[^>]*>.*?</object>',       # Objects
            r'<embed[^>]*>.*?</embed>',         # Embeds
            r'<link[^>]*>',                     # Link tags
            r'<meta[^>]*>',                     # Meta tags
            r'javascript:',                     # JavaScript URLs
            r'on\w+\s*=',                      # Event handlers
            r'data:',                           # Data URLs
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.dangerous_patterns
        ]
        
        # Allowed HTML tags for different strictness levels
        self.allowed_tags = {
            SanitizationLevel.PERMISSIVE: {
                'p', 'br', 'strong', 'em', 'u', 'i', 'b', 
                'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'blockquote', 'code', 'pre', 'a', 'img'
            },
            SanitizationLevel.STANDARD: {
                'p', 'br', 'strong', 'em', 'u', 'i', 'b',
                'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'code', 'pre'
            },
            SanitizationLevel.STRICT: {
                'p', 'br', 'strong', 'em', 'code'
            },
            SanitizationLevel.PARANOID: set()  # No HTML allowed
        }
    
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """Sanitize HTML content."""
        if not isinstance(data, str):
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False
            )
        
        sanitized = data
        issues_found = []
        warnings = []
        
        # Remove dangerous patterns
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(sanitized)
            if matches:
                issues_found.append(f"Removed dangerous HTML pattern: {self.dangerous_patterns[i]}")
                sanitized = pattern.sub('', sanitized)
        
        # Handle allowed tags based on level
        if level == SanitizationLevel.PARANOID:
            # Escape all HTML
            sanitized = html.escape(sanitized)
            if '<' in data or '>' in data:
                warnings.append("All HTML tags escaped due to paranoid sanitization")
        
        else:
            # Remove disallowed tags
            allowed = self.allowed_tags.get(level, set())
            
            # Find all HTML tags
            tag_pattern = re.compile(r'<(/?)(\w+)[^>]*>', re.IGNORECASE)
            
            def replace_tag(match):
                tag_name = match.group(2).lower()
                
                if tag_name in allowed:
                    return match.group(0)  # Keep allowed tags
                else:
                    issues_found.append(f"Removed disallowed HTML tag: <{tag_name}>")
                    return ''  # Remove disallowed tags
            
            sanitized = tag_pattern.sub(replace_tag, sanitized)
        
        # HTML entity decode for safety
        try:
            sanitized = html.unescape(sanitized)
        except Exception:
            warnings.append("Could not decode HTML entities")
        
        return SanitizationResult(
            original_data=data,
            sanitized_data=sanitized,
            sanitization_level=level,
            data_type=data_type,
            changes_made=(data != sanitized),
            issues_found=issues_found,
            warnings=warnings
        )
    
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to data type."""
        return data_type in {
            DataType.USER_INPUT,
            DataType.DOCUMENT_CONTENT,
            DataType.HTML_CONTENT,
            DataType.MARKDOWN_CONTENT
        }
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return "HTMLSanitization"


class UnicodeNormalizationRule(ISanitizationRule):
    """Normalizes Unicode characters to prevent encoding attacks."""
    
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """Normalize Unicode characters."""
        if not isinstance(data, str):
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False
            )
        
        try:
            # Normalize Unicode to NFC (Canonical Decomposition, followed by Canonical Composition)
            sanitized = unicodedata.normalize('NFC', data)
            
            warnings = []
            issues_found = []
            
            # Check for potentially dangerous Unicode characters
            dangerous_chars = []
            for char in sanitized:
                cat = unicodedata.category(char)
                
                # Check for format/control characters
                if cat.startswith('C') and char not in '\n\r\t':
                    dangerous_chars.append((char, cat, hex(ord(char))))
            
            if dangerous_chars:
                if level in {SanitizationLevel.STRICT, SanitizationLevel.PARANOID}:
                    # Remove dangerous characters
                    for char, cat, hex_code in dangerous_chars:
                        sanitized = sanitized.replace(char, '')
                        issues_found.append(f"Removed control character: {hex_code} ({cat})")
                else:
                    # Just warn about them
                    for char, cat, hex_code in dangerous_chars:
                        warnings.append(f"Found control character: {hex_code} ({cat})")
            
            return SanitizationResult(
                original_data=data,
                sanitized_data=sanitized,
                sanitization_level=level,
                data_type=data_type,
                changes_made=(data != sanitized),
                issues_found=issues_found,
                warnings=warnings
            )
        
        except Exception as e:
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False,
                warnings=[f"Unicode normalization failed: {e}"]
            )
    
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to data type."""
        return True  # Unicode normalization applies to all text data
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return "UnicodeNormalization"


class PathSanitizationRule(ISanitizationRule):
    """Sanitizes file paths to prevent directory traversal attacks."""
    
    def __init__(self):
        # Dangerous path patterns
        self.dangerous_patterns = [
            r'\.\.',                    # Directory traversal
            r'[<>:\"|?*]',             # Windows invalid chars
            r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
            r'^\.+$',                   # Only dots
            r'^\s+|\s+$',              # Leading/trailing whitespace
            r'/\.+/',                   # Hidden directory patterns
            r'\\\.+\\',                 # Windows hidden directory patterns
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.dangerous_patterns
        ]
    
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """Sanitize file path."""
        if not isinstance(data, str):
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False
            )
        
        sanitized = data
        issues_found = []
        warnings = []
        
        # Check for dangerous patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(sanitized):
                issues_found.append(f"Dangerous path pattern found: {self.dangerous_patterns[i]}")
                
                if level in {SanitizationLevel.STRICT, SanitizationLevel.PARANOID}:
                    # Remove or replace dangerous patterns
                    if i == 0:  # Directory traversal
                        sanitized = pattern.sub('', sanitized)
                    elif i == 1:  # Invalid Windows chars
                        sanitized = pattern.sub('_', sanitized)
                    elif i == 2:  # Reserved names
                        sanitized = '_' + sanitized
                    else:
                        sanitized = pattern.sub('', sanitized)
        
        # Normalize path separators
        sanitized = sanitized.replace('\\', '/')
        
        # Remove multiple consecutive slashes
        sanitized = re.sub(r'/+', '/', sanitized)
        
        # Ensure path doesn't start with /
        if sanitized.startswith('/'):
            sanitized = sanitized[1:]
            warnings.append("Removed leading slash from path")
        
        # Check path length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
            warnings.append("Path truncated to 255 characters")
        
        return SanitizationResult(
            original_data=data,
            sanitized_data=sanitized,
            sanitization_level=level,
            data_type=data_type,
            changes_made=(data != sanitized),
            issues_found=issues_found,
            warnings=warnings
        )
    
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to data type."""
        return data_type == DataType.FILE_PATH
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return "PathSanitization"


class SQLInjectionPreventionRule(ISanitizationRule):
    """Prevents SQL injection attempts in search queries and user input."""
    
    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b',
            r'[;\'\"\\]',                # SQL metacharacters
            r'--|\*/',                    # SQL comments
            r'\b(OR|AND)\s+\d+\s*=\s*\d+',  # Boolean injection
            r'\bUNION\s+SELECT\b',        # Union-based injection
            r'[\'\"]\s*OR\s+[\'\"]\d+[\'\"]\s*=\s*[\'\"]\d+[\'\"]\s*--',
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.sql_patterns
        ]
    
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """Prevent SQL injection attacks."""
        if not isinstance(data, str):
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False
            )
        
        sanitized = data
        issues_found = []
        warnings = []
        
        # Check for SQL injection patterns
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(sanitized)
            if matches:
                issues_found.append(f"Potential SQL injection pattern: {self.sql_patterns[i]}")
                
                if level in {SanitizationLevel.STRICT, SanitizationLevel.PARANOID}:
                    # Remove SQL keywords and dangerous characters
                    sanitized = pattern.sub(' ', sanitized)
                else:
                    # Just escape dangerous characters
                    if i == 1:  # SQL metacharacters
                        sanitized = sanitized.replace("'", "\\'").replace('"', '\\"').replace(';', '\\;')
        
        # Additional escaping for search queries
        if data_type == DataType.SEARCH_QUERY:
            # Escape special search characters but preserve basic search functionality
            special_chars = ['%', '_', '[', ']', '^', '-']
            for char in special_chars:
                if char in sanitized:
                    sanitized = sanitized.replace(char, f'\\{char}')
                    warnings.append(f"Escaped search special character: {char}")
        
        return SanitizationResult(
            original_data=data,
            sanitized_data=sanitized,
            sanitization_level=level,
            data_type=data_type,
            changes_made=(data != sanitized),
            issues_found=issues_found,
            warnings=warnings
        )
    
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to data type."""
        return data_type in {
            DataType.USER_INPUT,
            DataType.SEARCH_QUERY,
            DataType.DOCUMENT_CONTENT
        }
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return "SQLInjectionPrevention"


class URLSanitizationRule(ISanitizationRule):
    """Sanitizes URLs to prevent malicious redirects and XSS."""
    
    def __init__(self):
        # Allowed URL schemes
        self.allowed_schemes = {
            SanitizationLevel.PERMISSIVE: {'http', 'https', 'ftp', 'mailto', 'file'},
            SanitizationLevel.STANDARD: {'http', 'https', 'mailto'},
            SanitizationLevel.STRICT: {'https'},
            SanitizationLevel.PARANOID: set()  # No URLs allowed
        }
        
        # Dangerous URL patterns
        self.dangerous_patterns = [
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'about:',
            r'file:///[a-zA-Z]:', # Local file access
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.dangerous_patterns
        ]
    
    def sanitize(
        self, 
        data: Any, 
        level: SanitizationLevel,
        data_type: DataType,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """Sanitize URLs."""
        if not isinstance(data, str):
            return SanitizationResult(
                original_data=data,
                sanitized_data=data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=False
            )
        
        sanitized = data
        issues_found = []
        warnings = []
        
        # Check for dangerous URL schemes
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(sanitized):
                issues_found.append(f"Dangerous URL scheme: {self.dangerous_patterns[i]}")
                sanitized = pattern.sub('', sanitized)
        
        # Validate URL scheme
        if '://' in sanitized:
            scheme = sanitized.split('://')[0].lower()
            allowed = self.allowed_schemes.get(level, set())
            
            if scheme not in allowed:
                issues_found.append(f"Disallowed URL scheme: {scheme}")
                if level == SanitizationLevel.PARANOID:
                    sanitized = ''
                else:
                    sanitized = sanitized.replace(f'{scheme}://', 'https://', 1)
                    warnings.append(f"Replaced {scheme}:// with https://")
        
        # URL encode dangerous characters
        if level in {SanitizationLevel.STRICT, SanitizationLevel.PARANOID}:
            # Encode potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
            for char in dangerous_chars:
                if char in sanitized:
                    sanitized = sanitized.replace(char, quote(char))
                    warnings.append(f"URL encoded character: {char}")
        
        return SanitizationResult(
            original_data=data,
            sanitized_data=sanitized,
            sanitization_level=level,
            data_type=data_type,
            changes_made=(data != sanitized),
            issues_found=issues_found,
            warnings=warnings
        )
    
    def applies_to_type(self, data_type: DataType) -> bool:
        """Check if rule applies to data type."""
        return data_type in {
            DataType.USER_INPUT,
            DataType.URL_CONTENT,
            DataType.HTML_CONTENT,
            DataType.MARKDOWN_CONTENT
        }
    
    def get_rule_name(self) -> str:
        """Get rule name."""
        return "URLSanitization"


class DataSanitizer:
    """
    Central data sanitization system.
    
    Responsibilities:
    - Coordinate multiple sanitization rules
    - Provide context-aware sanitization
    - Track sanitization statistics and security events
    - Integrate with error handling and logging systems
    """
    
    def __init__(self):
        self._rules: List[ISanitizationRule] = []
        self._sanitization_stats: Dict[str, Any] = {
            "total_sanitizations": 0,
            "issues_found": 0,
            "warnings_generated": 0,
            "security_events": 0,
        }
        
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()
        self._lock = threading.RLock()
        
        # Setup default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default sanitization rules."""
        self.add_rule(HTMLSanitizationRule())
        self.add_rule(UnicodeNormalizationRule())
        self.add_rule(PathSanitizationRule())
        self.add_rule(SQLInjectionPreventionRule())
        self.add_rule(URLSanitizationRule())
    
    def add_rule(self, rule: ISanitizationRule) -> None:
        """Add sanitization rule."""
        with self._lock:
            if rule not in self._rules:
                self._rules.append(rule)
                self._logger.debug(f"Added sanitization rule: {rule.get_rule_name()}")
    
    def remove_rule(self, rule: ISanitizationRule) -> None:
        """Remove sanitization rule."""
        with self._lock:
            if rule in self._rules:
                self._rules.remove(rule)
                self._logger.debug(f"Removed sanitization rule: {rule.get_rule_name()}")
    
    def sanitize_data(
        self,
        data: Any,
        data_type: DataType,
        level: SanitizationLevel = SanitizationLevel.STANDARD,
        context: Optional[Dict[str, Any]] = None
    ) -> SanitizationResult:
        """
        Sanitize data using applicable rules.
        
        Args:
            data: Data to sanitize
            data_type: Type of data being sanitized
            level: Sanitization strictness level
            context: Optional context information
            
        Returns:
            Combined SanitizationResult
        """
        with self._lock:
            self._sanitization_stats["total_sanitizations"] += 1
            
            current_data = data
            all_issues = []
            all_warnings = []
            overall_changes = False
            
            # Apply all applicable rules in sequence
            for rule in self._rules:
                if rule.applies_to_type(data_type):
                    try:
                        result = rule.sanitize(current_data, level, data_type, context)
                        
                        # Update current data with sanitized version
                        current_data = result.sanitized_data
                        
                        # Accumulate results
                        if result.changes_made:
                            overall_changes = True
                        
                        if result.issues_found:
                            all_issues.extend(result.issues_found)
                        if result.warnings:
                            all_warnings.extend(result.warnings)
                        
                        # Track security events
                        if result.issues_found:
                            self._sanitization_stats["security_events"] += len(result.issues_found)
                            
                            # Report high-severity security issues
                            for issue in result.issues_found:
                                if any(keyword in issue.lower() for keyword in ['injection', 'xss', 'dangerous', 'attack']):
                                    self._error_tracker.capture_error(
                                        exception=SecurityError(f"Security issue detected: {issue}"),
                                        severity=ErrorSeverity.HIGH,
                                        category=ErrorCategory.SECURITY,
                                        user_action="Data sanitization",
                                        operation_context={
                                            "rule_name": rule.get_rule_name(),
                                            "data_type": data_type.name,
                                            "sanitization_level": level.value,
                                            "issue": issue,
                                            "data_preview": str(data)[:100]
                                        }
                                    )
                    
                    except Exception as e:
                        error_message = f"Sanitization rule failed: {rule.get_rule_name()} - {e}"
                        all_warnings.append(error_message)
                        self._logger.error(error_message)
            
            # Update statistics
            if all_issues:
                self._sanitization_stats["issues_found"] += len(all_issues)
            if all_warnings:
                self._sanitization_stats["warnings_generated"] += len(all_warnings)
            
            # Create combined result
            final_result = SanitizationResult(
                original_data=data,
                sanitized_data=current_data,
                sanitization_level=level,
                data_type=data_type,
                changes_made=overall_changes,
                issues_found=all_issues,
                warnings=all_warnings
            )
            
            # Log significant sanitization events
            if all_issues:
                self._logger.warning(
                    f"Data sanitization found {len(all_issues)} security issues",
                    data_type=data_type.name,
                    sanitization_level=level.value,
                    issues_count=len(all_issues),
                    changes_made=overall_changes
                )
            
            return final_result
    
    def sanitize_user_input(self, text: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
        """Quick sanitization of user input text."""
        result = self.sanitize_data(text, DataType.USER_INPUT, level)
        return result.sanitized_data
    
    def sanitize_file_path(self, path: str, level: SanitizationLevel = SanitizationLevel.STRICT) -> str:
        """Quick sanitization of file path."""
        result = self.sanitize_data(path, DataType.FILE_PATH, level)
        return result.sanitized_data
    
    def sanitize_search_query(self, query: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
        """Quick sanitization of search query."""
        result = self.sanitize_data(query, DataType.SEARCH_QUERY, level)
        return result.sanitized_data
    
    def sanitize_document_content(self, content: str, level: SanitizationLevel = SanitizationLevel.PERMISSIVE) -> str:
        """Quick sanitization of document content."""
        result = self.sanitize_data(content, DataType.DOCUMENT_CONTENT, level)
        return result.sanitized_data
    
    def get_sanitization_statistics(self) -> Dict[str, Any]:
        """Get sanitization statistics."""
        with self._lock:
            stats = self._sanitization_stats.copy()
            stats["rules_count"] = len(self._rules)
            stats["rule_names"] = [rule.get_rule_name() for rule in self._rules]
            return stats
    
    def reset_statistics(self) -> None:
        """Reset sanitization statistics."""
        with self._lock:
            self._sanitization_stats = {
                "total_sanitizations": 0,
                "issues_found": 0,
                "warnings_generated": 0,
                "security_events": 0,
            }
            self._logger.info("Sanitization statistics reset")


class SecurityError(Exception):
    """Exception raised for security-related sanitization issues."""
    pass


# Global sanitizer instance
_data_sanitizer: Optional[DataSanitizer] = None
_data_sanitizer_lock = threading.Lock()


def get_data_sanitizer() -> DataSanitizer:
    """
    Get global data sanitizer instance (singleton pattern).
    
    Returns:
        DataSanitizer instance
    """
    global _data_sanitizer
    
    if _data_sanitizer is None:
        with _data_sanitizer_lock:
            if _data_sanitizer is None:
                _data_sanitizer = DataSanitizer()
    
    return _data_sanitizer


# Convenience functions
def sanitize_user_input(text: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
    """Sanitize user input text."""
    sanitizer = get_data_sanitizer()
    return sanitizer.sanitize_user_input(text, level)


def sanitize_file_path(path: str, level: SanitizationLevel = SanitizationLevel.STRICT) -> str:
    """Sanitize file path."""
    sanitizer = get_data_sanitizer()
    return sanitizer.sanitize_file_path(path, level)


def sanitize_search_query(query: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
    """Sanitize search query."""
    sanitizer = get_data_sanitizer()
    return sanitizer.sanitize_search_query(query, level)


def sanitize_document_content(content: str, level: SanitizationLevel = SanitizationLevel.PERMISSIVE) -> str:
    """Sanitize document content."""
    sanitizer = get_data_sanitizer()
    return sanitizer.sanitize_document_content(content, level)