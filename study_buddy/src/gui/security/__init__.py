"""
Study Buddy GUI - Security Features Package

Comprehensive security infrastructure for the Study Buddy application.
Provides input validation, data sanitization, secure storage, security auditing,
and permission management with seamless integration.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Design Patterns: Strategy Pattern, Observer Pattern, Factory Pattern
SOLID Principles: All components follow SRP, OCP, LSP, ISP, DIP

Components Overview:
- InputValidator: Sanitize and validate user inputs to prevent injection attacks
- DataSanitizer: Clean data before storage/display to prevent security issues
- SecureStorage: Encrypt sensitive data and manage secure configuration
- SecurityAudit: Track and monitor security events with comprehensive logging
- PermissionManager: File access controls and operation authorization
"""

from .input_validator import (
    ValidationSeverity,
    ValidationType,
    ValidationResult,
    IValidationRule,
    LengthValidationRule,
    FormatValidationRule,
    PathValidationRule,
    InjectionValidationRule,
    EncodingValidationRule,
    InputValidator,
    get_input_validator,
)

from .data_sanitizer import (
    DataSanitizer,
    SanitizationLevel,
    DataType,
    SanitizationResult,
    get_data_sanitizer,
    
    # Convenience functions
    sanitize_user_input,
    sanitize_file_path,
    sanitize_search_query,
    sanitize_document_content,
)

from .secure_storage import (
    SecureStorage,
    StorageType,
    EncryptionLevel,
    StorageEntry,
    get_secure_storage,
    
    # Convenience functions
    store_user_preference,
    get_user_preference,
    store_sensitive_data,
    get_sensitive_data,
    store_session_data,
    get_session_data,
    clear_session_data,
)

from .security_audit import (
    SecurityAuditSystem,
    SecurityEvent,
    SecurityEventType,
    SecurityThreatLevel,
    AuditAction,
    get_security_audit,
    
    # Convenience functions
    validate_file_access,
    validate_user_input,
    audit_document_action,
    record_security_violation,
)

from .permission_manager import (
    PermissionManager,
    Permission,
    Role,
    AccessLevel,
    SecurityContext,
    PermissionGrant,
    get_permission_manager,
    requires_permission,
    
    # Convenience functions
    check_document_permission,
    check_system_permission,
    assign_user_role,
    get_user_permissions,
)


# Version information
__version__ = "1.0.0"
__author__ = "Study Buddy Development Team"

# Package metadata
__all__ = [
    # Input Validation
    "ValidationSeverity",
    "ValidationType", 
    "ValidationResult",
    "IValidationRule",
    "LengthValidationRule",
    "FormatValidationRule",
    "PathValidationRule",
    "InjectionValidationRule",
    "EncodingValidationRule",
    "InputValidator",
    "get_input_validator",
    
    # Data Sanitization
    "DataSanitizer",
    "SanitizationLevel",
    "DataType",
    "SanitizationResult",
    "get_data_sanitizer",
    "sanitize_user_input",
    "sanitize_file_path",
    "sanitize_search_query",
    "sanitize_document_content",
    
    # Secure Storage
    "SecureStorage",
    "StorageType",
    "EncryptionLevel",
    "StorageEntry",
    "get_secure_storage",
    "store_user_preference",
    "get_user_preference",
    "store_sensitive_data",
    "get_sensitive_data",
    "store_session_data",
    "get_session_data",
    "clear_session_data",
    
    # Security Audit
    "SecurityAuditSystem",
    "SecurityEvent",
    "SecurityEventType",
    "SecurityThreatLevel",
    "AuditAction",
    "get_security_audit",
    "validate_file_access",
    "validate_user_input",
    "audit_document_action",
    "record_security_violation",
    
    # Permission Management
    "PermissionManager",
    "Permission",
    "Role",
    "AccessLevel",
    "SecurityContext",
    "PermissionGrant",
    "get_permission_manager",
    "requires_permission",
    "check_document_permission",
    "check_system_permission",
    "assign_user_role",
    "get_user_permissions",
]