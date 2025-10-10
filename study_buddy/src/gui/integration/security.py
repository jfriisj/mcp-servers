"""
Security Validation Components for Study Buddy GUI Integration Layer.

This module provides comprehensive security validation and sanitization for all
MCP tool interactions, including input validation, file path security, search
query sanitization, and secure error handling.

Architecture: Clean Architecture Layer 4 (Infrastructure)
SOLID Compliance: Full compliance with all SOLID principles
Purpose: Ensure secure and validated MCP communication with comprehensive protection
"""

import re
import os
import hashlib
import hmac
import logging
import secrets
import threading
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Set, Union, Pattern, Callable
from datetime import datetime, timedelta
import html


# ============================================================================
# SECURITY ENUMS AND CONSTANTS
# ============================================================================

class SecurityLevel(Enum):
    """Security validation levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """Validation result types."""
    VALID = "valid"
    INVALID = "invalid"
    SANITIZED = "sanitized"
    BLOCKED = "blocked"


class ThreatType(Enum):
    """Security threat categories."""
    DIRECTORY_TRAVERSAL = "directory_traversal"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    FILE_INCLUSION = "file_inclusion"
    BUFFER_OVERFLOW = "buffer_overflow"
    MALFORMED_INPUT = "malformed_input"
    INFORMATION_DISCLOSURE = "information_disclosure"


# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

@dataclass
class SecurityConfig:
    """Configuration for security validation components."""
    
    # General settings
    enable_validation: bool = True
    security_level: SecurityLevel = SecurityLevel.HIGH
    log_security_events: bool = True
    
    # File path validation
    allow_absolute_paths: bool = False
    max_path_length: int = 260  # Windows MAX_PATH
    allowed_path_chars: Optional[Set[str]] = None
    blocked_path_patterns: Optional[List[str]] = None
    
    # Input validation
    max_string_length: int = 10000
    max_array_length: int = 1000
    allow_unicode: bool = True
    
    # Search query validation
    max_search_length: int = 500
    allow_regex_search: bool = False
    blocked_search_patterns: Optional[List[str]] = None
    
    # Error handling
    expose_stack_traces: bool = False
    log_all_errors: bool = True
    sanitize_error_messages: bool = True
    
    def __post_init__(self):
        """Initialize default values for complex types."""
        if self.allowed_path_chars is None:
            # Safe characters for file paths
            self.allowed_path_chars = set(
                "abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789"
                "-_.()/\\ "
            )
        
        if self.blocked_path_patterns is None:
            self.blocked_path_patterns = [
                r"\.\.[\\/]",  # Directory traversal
                r"^[\\/]",     # Absolute paths (if not allowed)
                r"[<>:|*?]",   # Invalid Windows characters
                r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$",  # Windows reserved names
            ]
        
        if self.blocked_search_patterns is None:
            self.blocked_search_patterns = [
                r"<script[^>]*>",     # XSS attempt
                r"javascript:",       # XSS attempt
                r"data:text/html",    # XSS attempt
                r"['\";]",            # SQL injection attempts
                r"\\x[0-9a-fA-F]{2}", # Hex encoding attempts
                r"%[0-9a-fA-F]{2}",   # URL encoding attempts
            ]


# ============================================================================
# VALIDATION RESULT CLASSES
# ============================================================================

@dataclass
class ValidationError:
    """Represents a security validation error."""
    
    threat_type: ThreatType
    message: str
    original_value: str
    sanitized_value: Optional[str] = None
    severity: SecurityLevel = SecurityLevel.MEDIUM
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    
    is_valid: bool
    result_type: ValidationResult
    original_value: Any
    sanitized_value: Any = None
    errors: Optional[List[ValidationError]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


# ============================================================================
# ABSTRACT SECURITY INTERFACES
# ============================================================================

class SecurityValidator(ABC):
    """Abstract base class for security validators."""
    
    @abstractmethod
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate input and return security report."""
        pass
    
    @abstractmethod
    def sanitize(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Sanitize input to make it safe."""
        pass
    
    @abstractmethod
    def get_threat_types(self) -> List[ThreatType]:
        """Get list of threat types this validator protects against."""
        pass


class SecurityAuditor(ABC):
    """Abstract interface for security audit logging."""
    
    @abstractmethod
    def log_security_event(
        self, 
        event_type: str, 
        details: Dict[str, Any], 
        severity: SecurityLevel = SecurityLevel.MEDIUM
    ) -> None:
        """Log security event."""
        pass
    
    @abstractmethod
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics."""
        pass


# ============================================================================
# FILE PATH SECURITY VALIDATOR
# ============================================================================

class FilePathValidator(SecurityValidator):
    """
    Validator for file paths to prevent directory traversal and other file-based attacks.
    
    Protects against:
    - Directory traversal attacks (../, ..\\)
    - Absolute path injection
    - Invalid characters in file names
    - Reserved system file names
    - Excessively long paths
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize file path validator."""
        self.config = config
        self.logger = logging.getLogger(__name__ + ".FilePathValidator")
        
        # Compile regex patterns for better performance
        self._blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in (config.blocked_path_patterns or [])
        ]
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate file path for security issues."""
        if not isinstance(value, (str, Path, PurePath)):
            return ValidationReport(
                is_valid=False,
                result_type=ValidationResult.INVALID,
                original_value=value,
                errors=[ValidationError(
                    threat_type=ThreatType.MALFORMED_INPUT,
                    message="File path must be a string or Path object",
                    original_value=str(value)
                )]
            )
        
        path_str = str(value)
        errors = []
        warnings = []
        
        # Check path length
        if len(path_str) > self.config.max_path_length:
            errors.append(ValidationError(
                threat_type=ThreatType.BUFFER_OVERFLOW,
                message=f"Path length {len(path_str)} exceeds maximum {self.config.max_path_length}",
                original_value=path_str,
                severity=SecurityLevel.HIGH
            ))
        
        # Check for directory traversal
        if self._contains_directory_traversal(path_str):
            errors.append(ValidationError(
                threat_type=ThreatType.DIRECTORY_TRAVERSAL,
                message="Path contains directory traversal sequences",
                original_value=path_str,
                severity=SecurityLevel.CRITICAL
            ))
        
        # Check for absolute paths (if not allowed)
        if not self.config.allow_absolute_paths and os.path.isabs(path_str):
            errors.append(ValidationError(
                threat_type=ThreatType.DIRECTORY_TRAVERSAL,
                message="Absolute paths are not allowed",
                original_value=path_str,
                severity=SecurityLevel.HIGH
            ))
        
        # Check for invalid characters
        invalid_chars = self._find_invalid_characters(path_str)
        if invalid_chars:
            errors.append(ValidationError(
                threat_type=ThreatType.MALFORMED_INPUT,
                message=f"Path contains invalid characters: {invalid_chars}",
                original_value=path_str,
                severity=SecurityLevel.MEDIUM
            ))
        
        # Check against blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.search(path_str):
                errors.append(ValidationError(
                    threat_type=ThreatType.MALFORMED_INPUT,
                    message=f"Path matches blocked pattern: {pattern.pattern}",
                    original_value=path_str,
                    severity=SecurityLevel.HIGH
                ))
        
        # Check for reserved names (Windows)
        if self._is_reserved_name(path_str):
            warnings.append("Path uses a reserved system name")
        
        # Determine validation result
        if errors:
            return ValidationReport(
                is_valid=False,
                result_type=ValidationResult.INVALID,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        else:
            sanitized = self.sanitize(path_str)
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.SANITIZED if sanitized != path_str else ValidationResult.VALID,
                original_value=value,
                sanitized_value=sanitized,
                warnings=warnings
            )
    
    def sanitize(self, value: Any, context: Optional[Dict[str, Any]] = None) -> str:
        """Sanitize file path to make it safe."""
        path_str = str(value)
        
        # Normalize path separators
        path_str = path_str.replace('\\', os.sep).replace('/', os.sep)
        
        # Remove dangerous sequences
        path_str = re.sub(r'\.\.[\\/]+', '', path_str)
        
        # Remove invalid characters
        allowed_chars = self.config.allowed_path_chars or set()
        sanitized_chars = []
        for char in path_str:
            if char in allowed_chars:
                sanitized_chars.append(char)
            else:
                sanitized_chars.append('_')  # Replace with safe character
        
        sanitized = ''.join(sanitized_chars)
        
        # Ensure path doesn't exceed length limit
        if len(sanitized) > self.config.max_path_length:
            sanitized = sanitized[:self.config.max_path_length]
        
        # Normalize and resolve path
        try:
            normalized = os.path.normpath(sanitized)
            return normalized
        except Exception:
            return sanitized
    
    def get_threat_types(self) -> List[ThreatType]:
        """Get threat types this validator protects against."""
        return [
            ThreatType.DIRECTORY_TRAVERSAL,
            ThreatType.FILE_INCLUSION,
            ThreatType.MALFORMED_INPUT,
            ThreatType.BUFFER_OVERFLOW
        ]
    
    def _contains_directory_traversal(self, path: str) -> bool:
        """Check if path contains directory traversal sequences."""
        traversal_patterns = [
            '../', '..\\',
            '..%2f', '..%5c',  # URL encoded
            '..%252f', '..%255c',  # Double URL encoded
            '%2e%2e%2f', '%2e%2e%5c',  # Fully encoded
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in traversal_patterns)
    
    def _find_invalid_characters(self, path: str) -> Set[str]:
        """Find characters that are not in the allowed set."""
        allowed_chars = self.config.allowed_path_chars or set()
        return set(path) - allowed_chars
    
    def _is_reserved_name(self, path: str) -> bool:
        """Check if path uses Windows reserved names."""
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5',
            'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        # Extract filename without extension
        filename = os.path.basename(path)
        name_without_ext = os.path.splitext(filename)[0].upper()
        
        return name_without_ext in reserved_names


# ============================================================================
# INPUT SANITIZATION VALIDATOR
# ============================================================================

class InputSanitizer(SecurityValidator):
    """
    General input sanitization for MCP tool parameters.
    
    Protects against:
    - XSS attacks
    - SQL injection attempts
    - Command injection
    - Malformed Unicode
    - Excessively long inputs
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize input sanitizer."""
        self.config = config
        self.logger = logging.getLogger(__name__ + ".InputSanitizer")
        
        # XSS prevention patterns
        self._xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'<object[^>]*>', re.IGNORECASE),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
        ]
        
        # SQL injection patterns
        self._sql_patterns = [
            re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)', re.IGNORECASE),
            re.compile(r'(\b(UNION|OR|AND)\b.*\b(SELECT)\b)', re.IGNORECASE),
            re.compile(r'[\'";].*(-{2}|/\*)', re.IGNORECASE),  # Comment injection
        ]
        
        # Command injection patterns
        self._command_patterns = [
            re.compile(r'[;&|`$(){}[\]\\]'),  # Shell metacharacters
            re.compile(r'\b(bash|sh|cmd|powershell|python|perl|ruby)\b', re.IGNORECASE),
        ]
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate input for security issues."""
        if value is None:
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.VALID,
                original_value=value
            )
        
        # Convert to string for validation
        if isinstance(value, (list, tuple)):
            # Validate array length
            if len(value) > self.config.max_array_length:
                return ValidationReport(
                    is_valid=False,
                    result_type=ValidationResult.INVALID,
                    original_value=value,
                    errors=[ValidationError(
                        threat_type=ThreatType.BUFFER_OVERFLOW,
                        message=f"Array length {len(value)} exceeds maximum {self.config.max_array_length}",
                        original_value=str(value)
                    )]
                )
            
            # Validate each element
            errors = []
            for i, item in enumerate(value):
                item_report = self.validate(item, context)
                if not item_report.is_valid:
                    for error in (item_report.errors or []):
                        error.message = f"Array element [{i}]: {error.message}"
                        errors.append(error)
            
            if errors:
                return ValidationReport(
                    is_valid=False,
                    result_type=ValidationResult.INVALID,
                    original_value=value,
                    errors=errors
                )
        
        value_str = str(value)
        errors = []
        warnings = []
        
        # Check string length
        if len(value_str) > self.config.max_string_length:
            errors.append(ValidationError(
                threat_type=ThreatType.BUFFER_OVERFLOW,
                message=f"Input length {len(value_str)} exceeds maximum {self.config.max_string_length}",
                original_value=value_str,
                severity=SecurityLevel.MEDIUM
            ))
        
        # Check for XSS attempts
        for pattern in self._xss_patterns:
            if pattern.search(value_str):
                errors.append(ValidationError(
                    threat_type=ThreatType.XSS,
                    message=f"Input contains potential XSS: {pattern.pattern}",
                    original_value=value_str,
                    severity=SecurityLevel.HIGH
                ))
        
        # Check for SQL injection attempts
        for pattern in self._sql_patterns:
            if pattern.search(value_str):
                errors.append(ValidationError(
                    threat_type=ThreatType.SQL_INJECTION,
                    message=f"Input contains potential SQL injection: {pattern.pattern}",
                    original_value=value_str,
                    severity=SecurityLevel.HIGH
                ))
        
        # Check for command injection attempts
        for pattern in self._command_patterns:
            if pattern.search(value_str):
                errors.append(ValidationError(
                    threat_type=ThreatType.COMMAND_INJECTION,
                    message=f"Input contains potential command injection: {pattern.pattern}",
                    original_value=value_str,
                    severity=SecurityLevel.CRITICAL
                ))
        
        # Unicode validation
        if not self.config.allow_unicode:
            try:
                value_str.encode('ascii')
            except UnicodeEncodeError:
                warnings.append("Input contains non-ASCII characters")
        
        # Determine result
        if errors:
            return ValidationReport(
                is_valid=False,
                result_type=ValidationResult.INVALID,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        else:
            sanitized = self.sanitize(value, context)
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.SANITIZED if sanitized != value else ValidationResult.VALID,
                original_value=value,
                sanitized_value=sanitized,
                warnings=warnings
            )
    
    def sanitize(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Sanitize input to remove dangerous content."""
        if value is None:
            return value
        
        if isinstance(value, (list, tuple)):
            return [self.sanitize(item, context) for item in value]
        
        if isinstance(value, dict):
            return {key: self.sanitize(val, context) for key, val in value.items()}
        
        value_str = str(value)
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value_str, quote=True)
        
        # Remove or escape dangerous patterns
        for pattern in self._xss_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Limit length
        if len(sanitized) > self.config.max_string_length:
            sanitized = sanitized[:self.config.max_string_length]
        
        # Normalize Unicode if needed
        if not self.config.allow_unicode:
            sanitized = sanitized.encode('ascii', errors='ignore').decode('ascii')
        
        return sanitized
    
    def get_threat_types(self) -> List[ThreatType]:
        """Get threat types this validator protects against."""
        return [
            ThreatType.XSS,
            ThreatType.SQL_INJECTION,
            ThreatType.COMMAND_INJECTION,
            ThreatType.BUFFER_OVERFLOW,
            ThreatType.MALFORMED_INPUT
        ]


# ============================================================================
# SEARCH QUERY VALIDATOR
# ============================================================================

class SearchQueryValidator(SecurityValidator):
    """
    Specialized validator for search queries.
    
    Protects against:
    - Regex injection attacks
    - Search query manipulation
    - Information disclosure through search patterns
    - Excessive search complexity
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize search query validator."""
        self.config = config
        self.logger = logging.getLogger(__name__ + ".SearchQueryValidator")
        
        # Compile blocked patterns
        self._blocked_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in (config.blocked_search_patterns or [])
        ]
        
        # Dangerous regex patterns that could cause ReDoS
        self._redos_patterns = [
            re.compile(r'\(\?\=.*\)\*'),  # Lookahead with quantifier
            re.compile(r'\(\?\!.*\)\+'),  # Negative lookahead with quantifier
            re.compile(r'\w\*\+'),        # Nested quantifiers
            re.compile(r'\.\*\.\*'),      # Multiple wildcards
        ]
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate search query for security issues."""
        if not isinstance(value, str):
            return ValidationReport(
                is_valid=False,
                result_type=ValidationResult.INVALID,
                original_value=value,
                errors=[ValidationError(
                    threat_type=ThreatType.MALFORMED_INPUT,
                    message="Search query must be a string",
                    original_value=str(value)
                )]
            )
        
        errors = []
        warnings = []
        
        # Check length
        if len(value) > self.config.max_search_length:
            errors.append(ValidationError(
                threat_type=ThreatType.BUFFER_OVERFLOW,
                message=f"Search query length {len(value)} exceeds maximum {self.config.max_search_length}",
                original_value=value,
                severity=SecurityLevel.MEDIUM
            ))
        
        # Check for blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.search(value):
                errors.append(ValidationError(
                    threat_type=ThreatType.XSS,
                    message=f"Search query contains blocked pattern: {pattern.pattern}",
                    original_value=value,
                    severity=SecurityLevel.HIGH
                ))
        
        # Check for ReDoS patterns if regex is allowed
        if self.config.allow_regex_search:
            for pattern in self._redos_patterns:
                if pattern.search(value):
                    errors.append(ValidationError(
                        threat_type=ThreatType.BUFFER_OVERFLOW,
                        message=f"Search query contains dangerous regex pattern: {pattern.pattern}",
                        original_value=value,
                        severity=SecurityLevel.CRITICAL
                    ))
        else:
            # Check for regex metacharacters when regex is not allowed
            regex_chars = set('.*+?[]{}()^$|\\')
            if any(char in value for char in regex_chars):
                warnings.append("Search query contains regex metacharacters but regex search is disabled")
        
        # Check for potential information disclosure patterns
        if self._contains_disclosure_patterns(value):
            errors.append(ValidationError(
                threat_type=ThreatType.INFORMATION_DISCLOSURE,
                message="Search query may lead to information disclosure",
                original_value=value,
                severity=SecurityLevel.MEDIUM
            ))
        
        # Determine result
        if errors:
            return ValidationReport(
                is_valid=False,
                result_type=ValidationResult.INVALID,
                original_value=value,
                errors=errors,
                warnings=warnings
            )
        else:
            sanitized = self.sanitize(value, context)
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.SANITIZED if sanitized != value else ValidationResult.VALID,
                original_value=value,
                sanitized_value=sanitized,
                warnings=warnings
            )
    
    def sanitize(self, value: Any, context: Optional[Dict[str, Any]] = None) -> str:
        """Sanitize search query to make it safe."""
        query = str(value)
        
        # Escape HTML to prevent XSS
        sanitized = html.escape(query, quote=True)
        
        # Remove blocked patterns
        for pattern in self._blocked_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Escape regex metacharacters if regex is not allowed
        if not self.config.allow_regex_search:
            regex_chars = '.*+?[]{}()^$|\\'
            for char in regex_chars:
                sanitized = sanitized.replace(char, f'\\{char}')
        
        # Limit length
        if len(sanitized) > self.config.max_search_length:
            sanitized = sanitized[:self.config.max_search_length]
        
        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def get_threat_types(self) -> List[ThreatType]:
        """Get threat types this validator protects against."""
        return [
            ThreatType.XSS,
            ThreatType.BUFFER_OVERFLOW,
            ThreatType.INFORMATION_DISCLOSURE,
            ThreatType.MALFORMED_INPUT
        ]
    
    def _contains_disclosure_patterns(self, query: str) -> bool:
        """Check for patterns that might lead to information disclosure."""
        disclosure_patterns = [
            r'password\s*[:=]',
            r'token\s*[:=]',
            r'key\s*[:=]',
            r'secret\s*[:=]',
            r'credit.*card',
            r'ssn\s*[:=]',
            r'social.*security',
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in disclosure_patterns)


# ============================================================================
# SECURE ERROR HANDLER
# ============================================================================

class SecureErrorHandler:
    """
    Handles errors securely to prevent information leakage.
    
    Provides sanitized error messages that don't expose sensitive information
    while maintaining sufficient detail for debugging in safe environments.
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize secure error handler."""
        self.config = config
        self.logger = logging.getLogger(__name__ + ".SecureErrorHandler")
    
    def sanitize_error_message(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """Sanitize error message to prevent information leakage."""
        if not self.config.sanitize_error_messages:
            return str(error)
        
        error_str = str(error).lower()
        
        # Generic message for potentially sensitive errors
        if any(keyword in error_str for keyword in [
            'password', 'token', 'key', 'secret', 'credential',
            'path', 'file', 'directory', 'connection',
            'database', 'sql', 'query'
        ]):
            return "An error occurred while processing your request"
        
        # Remove file paths from error messages
        sanitized = re.sub(r'[/\\][^/\\]*[/\\][^/\\]*', '/***/', str(error))
        
        # Remove IP addresses
        sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '***', sanitized)
        
        # Remove potential sensitive data patterns
        sanitized = re.sub(r'[a-zA-Z0-9+/]{20,}={0,2}', '***', sanitized)  # Base64
        sanitized = re.sub(r'[0-9a-fA-F]{8,}', '***', sanitized)  # Hex strings
        
        return sanitized
    
    def create_safe_error_response(
        self, 
        error: Exception, 
        operation: str = "operation",
        include_type: bool = False
    ) -> Dict[str, Any]:
        """Create a safe error response dictionary."""
        sanitized_message = self.sanitize_error_message(error)
        
        response = {
            "success": False,
            "error": sanitized_message,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        
        if include_type and not self.config.sanitize_error_messages:
            response["error_type"] = type(error).__name__
        
        # Log full error details securely
        if self.config.log_all_errors:
            self.logger.error(
                f"Operation '{operation}' failed: {type(error).__name__}: {str(error)}",
                exc_info=True
            )
        
        return response
    
    def should_expose_stack_trace(self, error: Exception) -> bool:
        """Determine if stack trace should be exposed."""
        return (
            self.config.expose_stack_traces and
            not self.config.sanitize_error_messages and
            self.config.security_level in [SecurityLevel.LOW, SecurityLevel.MEDIUM]
        )


# ============================================================================
# COMPREHENSIVE SECURITY MANAGER
# ============================================================================

class SecurityManager:
    """
    Comprehensive security validation manager that coordinates all validators.
    
    Provides a unified interface for all security validation needs in the
    integration layer, with centralized configuration and audit logging.
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize security manager."""
        self.config = config or SecurityConfig()
        self.logger = logging.getLogger(__name__ + ".SecurityManager")
        
        # Initialize validators
        self.file_path_validator = FilePathValidator(self.config)
        self.input_sanitizer = InputSanitizer(self.config)
        self.search_validator = SearchQueryValidator(self.config)
        self.error_handler = SecureErrorHandler(self.config)
        
        # Security metrics
        self._validation_count = 0
        self._blocked_attempts = 0
        self._threat_counts = {threat: 0 for threat in ThreatType}
        
        self.logger.info(f"Security manager initialized with level: {self.config.security_level.value}")
    
    def validate_file_path(self, path: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate file path for security issues."""
        self._validation_count += 1
        
        if not self.config.enable_validation:
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.VALID,
                original_value=path
            )
        
        report = self.file_path_validator.validate(path, context)
        self._update_metrics(report)
        return report
    
    def validate_input(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate general input for security issues."""
        self._validation_count += 1
        
        if not self.config.enable_validation:
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.VALID,
                original_value=value
            )
        
        report = self.input_sanitizer.validate(value, context)
        self._update_metrics(report)
        return report
    
    def validate_search_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate search query for security issues."""
        self._validation_count += 1
        
        if not self.config.enable_validation:
            return ValidationReport(
                is_valid=True,
                result_type=ValidationResult.VALID,
                original_value=query
            )
        
        report = self.search_validator.validate(query, context)
        self._update_metrics(report)
        return report
    
    def sanitize_mcp_parameters(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all parameters for an MCP tool call."""
        sanitized_params = {}
        
        for key, value in params.items():
            # Special handling for file paths
            if key in ['file_path', 'path', 'document_path']:
                report = self.validate_file_path(value)
                if report.is_valid:
                    sanitized_params[key] = report.sanitized_value or report.original_value
                else:
                    self.logger.warning(f"Invalid file path in {tool_name}.{key}: {report.errors}")
                    # Use sanitized version even if invalid for safer operation
                    sanitized_params[key] = self.file_path_validator.sanitize(value)
            
            # Special handling for search queries
            elif key in ['query', 'search', 'search_query']:
                report = self.validate_search_query(value)
                if report.is_valid:
                    sanitized_params[key] = report.sanitized_value or report.original_value
                else:
                    self.logger.warning(f"Invalid search query in {tool_name}.{key}: {report.errors}")
                    sanitized_params[key] = self.search_validator.sanitize(value)
            
            # General input validation
            else:
                report = self.validate_input(value)
                if report.is_valid:
                    sanitized_params[key] = report.sanitized_value or report.original_value
                else:
                    self.logger.warning(f"Invalid input in {tool_name}.{key}: {report.errors}")
                    sanitized_params[key] = self.input_sanitizer.sanitize(value)
        
        return sanitized_params
    
    def create_secure_error_response(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Create secure error response that doesn't leak sensitive information."""
        return self.error_handler.create_safe_error_response(error, operation)
    
    def _update_metrics(self, report: ValidationReport):
        """Update security metrics based on validation report."""
        if not report.is_valid:
            self._blocked_attempts += 1
        
        for error in (report.errors or []):
            self._threat_counts[error.threat_type] += 1
            
            # Log security events
            if self.config.log_security_events:
                self.logger.warning(
                    f"Security threat detected - {error.threat_type.value}: {error.message}"
                )
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics."""
        return {
            "total_validations": self._validation_count,
            "blocked_attempts": self._blocked_attempts,
            "threat_counts": {threat.value: count for threat, count in self._threat_counts.items()},
            "block_rate_percent": (self._blocked_attempts / max(self._validation_count, 1)) * 100,
            "security_level": self.config.security_level.value,
            "validation_enabled": self.config.enable_validation
        }
    
    def reset_metrics(self):
        """Reset security metrics (for testing)."""
        self._validation_count = 0
        self._blocked_attempts = 0
        self._threat_counts = {threat: 0 for threat in ThreatType}


# ============================================================================
# GLOBAL SECURITY INSTANCE
# ============================================================================

# Global security manager instance (initialized lazily)
_global_security_manager: Optional[SecurityManager] = None
_security_lock = threading.Lock()


def get_global_security_manager(config: Optional[SecurityConfig] = None) -> SecurityManager:
    """Get or create global security manager instance."""
    global _global_security_manager
    
    with _security_lock:
        if _global_security_manager is None:
            if config is None:
                config = SecurityConfig()
            _global_security_manager = SecurityManager(config)
        
        return _global_security_manager


def reset_global_security_manager() -> None:
    """Reset global security manager (for testing)."""
    global _global_security_manager
    
    with _security_lock:
        _global_security_manager = None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def validate_file_path(path: str) -> ValidationReport:
    """Convenience function to validate file path."""
    return get_global_security_manager().validate_file_path(path)


def validate_input(value: Any) -> ValidationReport:
    """Convenience function to validate general input."""
    return get_global_security_manager().validate_input(value)


def validate_search_query(query: str) -> ValidationReport:
    """Convenience function to validate search query."""
    return get_global_security_manager().validate_search_query(query)


def sanitize_mcp_parameters(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to sanitize MCP tool parameters."""
    return get_global_security_manager().sanitize_mcp_parameters(tool_name, params)


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def _test_security_components():
    """Test security validation components."""
    print("🔒 Testing Security Validation Components...")
    
    # Test configuration
    config = SecurityConfig(
        security_level=SecurityLevel.HIGH,
        enable_validation=True
    )
    
    # Test security manager
    security_mgr = SecurityManager(config)
    
    # Test file path validation
    print("\n📁 Testing file path validation:")
    
    # Safe path
    safe_path = "documents/test.pdf"
    report = security_mgr.validate_file_path(safe_path)
    print(f"Safe path '{safe_path}': {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    
    # Dangerous path (directory traversal)
    dangerous_path = "../../../etc/passwd"
    report = security_mgr.validate_file_path(dangerous_path)
    print(f"Dangerous path '{dangerous_path}': {'❌ BLOCKED' if not report.is_valid else '⚠️  ALLOWED'}")
    
    # Test input sanitization
    print("\n🧹 Testing input sanitization:")
    
    # Safe input
    safe_input = "Hello World"
    report = security_mgr.validate_input(safe_input)
    print(f"Safe input '{safe_input}': {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    
    # XSS attempt
    xss_input = "<script>alert('xss')</script>"
    report = security_mgr.validate_input(xss_input)
    print(f"XSS input '{xss_input}': {'❌ BLOCKED' if not report.is_valid else '⚠️  ALLOWED'}")
    
    # Test search query validation
    print("\n🔍 Testing search query validation:")
    
    # Safe search
    safe_search = "python programming"
    report = security_mgr.validate_search_query(safe_search)
    print(f"Safe search '{safe_search}': {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    
    # Dangerous search
    dangerous_search = "<script>alert('xss')</script> OR 1=1"
    report = security_mgr.validate_search_query(dangerous_search)
    print(f"Dangerous search: {'❌ BLOCKED' if not report.is_valid else '⚠️  ALLOWED'}")
    
    # Test MCP parameter sanitization
    print("\n🛡️  Testing MCP parameter sanitization:")
    
    unsafe_params = {
        "file_path": "../../../secret.txt",
        "query": "<script>alert('hack')</script>",
        "title": "Safe Title",
        "tags": ["<script>", "safe_tag"]
    }
    
    safe_params = security_mgr.sanitize_mcp_parameters("upload_document", unsafe_params)
    print(f"Original params: {unsafe_params}")
    print(f"Sanitized params: {safe_params}")
    
    # Test security metrics
    print("\n📊 Security Metrics:")
    metrics = security_mgr.get_security_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n🎉 Security validation components tested successfully!")


if __name__ == "__main__":
    _test_security_components()