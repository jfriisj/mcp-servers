"""
Study Buddy GUI - Security Audit System

Provides comprehensive security auditing and monitoring for the GUI application:
- Real-time security event monitoring
- User action logging and forensics  
- Permission violation tracking
- Configuration security validation
- Security policy compliance checking
- Threat detection and response

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Observer Pattern, Command Pattern, Chain of Responsibility  
SOLID: SRP (audit only), OCP (extensible policies), ISP (focused interfaces)
"""

import os
import threading
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from gui.error_handling import get_debug_logger, get_error_tracker, ErrorSeverity, ErrorCategory
from gui.security.secure_storage import get_secure_storage, StorageType


class SecurityEventType(Enum):
    """Types of security events to monitor."""
    
    # Authentication & Authorization
    LOGIN_ATTEMPT = auto()
    LOGIN_SUCCESS = auto()
    LOGIN_FAILURE = auto()
    PERMISSION_DENIED = auto()
    PRIVILEGE_ESCALATION = auto()
    
    # Data Access
    DATA_ACCESS = auto()
    DATA_MODIFICATION = auto()
    DATA_DELETION = auto()
    SENSITIVE_DATA_ACCESS = auto()
    
    # Input/Output Security
    INPUT_VALIDATION_FAILURE = auto()
    INJECTION_ATTEMPT = auto()
    XSS_ATTEMPT = auto()
    PATH_TRAVERSAL_ATTEMPT = auto()
    
    # System Security
    FILE_ACCESS_DENIED = auto()
    CONFIGURATION_CHANGE = auto()
    SECURITY_POLICY_VIOLATION = auto()
    SUSPICIOUS_ACTIVITY = auto()
    
    # Network Security
    MCP_CONNECTION_FAILURE = auto()
    MCP_AUTHENTICATION_ERROR = auto()
    NETWORK_TIMEOUT = auto()
    
    # Application Security
    MEMORY_EXHAUSTION = auto()
    RESOURCE_EXHAUSTION = auto()
    PERFORMANCE_ANOMALY = auto()


class SecurityThreatLevel(Enum):
    """Security threat levels for prioritization."""
    
    INFORMATIONAL = "informational"  # Normal security events
    LOW = "low"                     # Minor security concerns
    MEDIUM = "medium"               # Moderate security issues
    HIGH = "high"                   # Serious security threats
    CRITICAL = "critical"           # Critical security breaches


class AuditAction(Enum):
    """User actions to audit."""
    
    # Document Operations
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SEARCH = "document_search"
    
    # Data Operations
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    CONFIGURATION_CHANGE = "configuration_change"
    
    # System Operations
    APPLICATION_START = "application_start"
    APPLICATION_EXIT = "application_exit"
    MCP_CONNECTION = "mcp_connection"
    
    # Security Operations
    PERMISSION_REQUEST = "permission_request"
    SECURITY_SCAN = "security_scan"


@dataclass
class SecurityEvent:
    """Represents a security event for auditing."""
    
    event_id: str
    event_type: SecurityEventType
    threat_level: SecurityThreatLevel
    timestamp: datetime
    user_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    action: Optional[AuditAction]
    resource: Optional[str]
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    remediation_taken: Optional[str] = None
    
    def __post_init__(self):
        """Initialize event details."""
        if not self.details:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.name
        data['threat_level'] = self.threat_level.value
        if self.action:
            data['action'] = self.action.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['event_type'] = SecurityEventType[data['event_type']]
        data['threat_level'] = SecurityThreatLevel(data['threat_level'])
        if data.get('action'):
            data['action'] = AuditAction(data['action'])
        return cls(**data)


class ISecurityPolicy(ABC):
    """Interface for security policies."""
    
    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validate security policy compliance."""
        pass
    
    @abstractmethod
    def get_policy_name(self) -> str:
        """Get policy name."""
        pass
    
    @abstractmethod
    def get_violation_message(self) -> str:
        """Get message for policy violations."""
        pass


class ISecurityEventHandler(ABC):
    """Interface for security event handlers."""
    
    @abstractmethod
    def handle_event(self, event: SecurityEvent) -> None:
        """Handle a security event."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: SecurityEventType) -> bool:
        """Check if handler can process event type."""
        pass


class FileAccessPolicy(ISecurityPolicy):
    """Policy for validating file access patterns."""
    
    def __init__(self):
        # Allowed file extensions
        self.allowed_extensions = {
            '.pdf', '.docx', '.pptx', '.txt', '.md', '.json'
        }
        
        # Restricted directories (relative to app directory)
        self.restricted_dirs = {
            'system32', 'windows', 'program files', 'program files (x86)',
            'users/administrator', 'users/admin'
        }
        
        # Maximum file size (100MB)
        self.max_file_size = 100 * 1024 * 1024
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validate file access request."""
        file_path = context.get('file_path', '')
        if not file_path:
            return False
        
        try:
            path = Path(file_path)
            
            # Check file extension
            if path.suffix.lower() not in self.allowed_extensions:
                return False
            
            # Check for restricted directories
            path_str = str(path).lower().replace('\\', '/')
            for restricted in self.restricted_dirs:
                if restricted in path_str:
                    return False
            
            # Check file size if file exists
            if path.exists() and path.stat().st_size > self.max_file_size:
                return False
            
            # Check for directory traversal
            if '..' in path_str or path_str.startswith('/'):
                return False
            
            return True
        
        except Exception:
            return False
    
    def get_policy_name(self) -> str:
        """Get policy name."""
        return "FileAccessPolicy"
    
    def get_violation_message(self) -> str:
        """Get violation message."""
        return "File access denied: Invalid file type, restricted location, or security violation"


class InputValidationPolicy(ISecurityPolicy):
    """Policy for validating user input security."""
    
    def __init__(self):
        # Dangerous input patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',    # Script injection
            r'javascript:',                   # JavaScript URLs
            r'data:',                        # Data URLs
            r'vbscript:',                    # VBScript URLs
            r'[\'\"](.*?)[\'\"]\s*;',        # SQL injection patterns
            r'(DROP|DELETE|INSERT|UPDATE)\s+', # SQL commands
            r'\.\./\.\./\.\.',               # Directory traversal
            r'\\\\[a-zA-Z0-9]+\\',           # UNC paths
        ]
        
        # Maximum input lengths
        self.max_lengths = {
            'search_query': 1000,
            'document_title': 200,
            'user_input': 5000,
            'file_path': 500,
        }
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validate input security."""
        input_text = context.get('input_text', '')
        input_type = context.get('input_type', 'user_input')
        
        if not isinstance(input_text, str):
            return False
        
        # Check input length
        max_length = self.max_lengths.get(input_type, 1000)
        if len(input_text) > max_length:
            return False
        
        # Check for dangerous patterns
        import re
        for pattern in self.dangerous_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                return False
        
        # Check for control characters
        if any(ord(char) < 32 for char in input_text if char not in '\n\r\t'):
            return False
        
        return True
    
    def get_policy_name(self) -> str:
        """Get policy name."""
        return "InputValidationPolicy"
    
    def get_violation_message(self) -> str:
        """Get violation message."""
        return "Input validation failed: Contains dangerous patterns or exceeds length limits"


class ResourceUsagePolicy(ISecurityPolicy):
    """Policy for monitoring resource usage patterns."""
    
    def __init__(self):
        # Memory limits (in MB)
        self.max_memory_mb = 500
        
        # CPU usage limits (percentage)
        self.max_cpu_percent = 80.0
        
        # File operation limits
        self.max_files_per_minute = 100
        self.max_file_size_mb = 100
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validate resource usage."""
        try:
            # Check memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                context['violation_reason'] = f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB"
                return False
            
            # Check CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > self.max_cpu_percent:
                context['violation_reason'] = f"CPU usage {cpu_percent:.1f}% exceeds limit {self.max_cpu_percent}%"
                return False
            
            return True
        
        except Exception:
            return True  # Don't block on monitoring errors
    
    def get_policy_name(self) -> str:
        """Get policy name."""
        return "ResourceUsagePolicy"
    
    def get_violation_message(self) -> str:
        """Get violation message."""
        return "Resource usage policy violation: Excessive memory or CPU usage detected"


class SecurityEventLogger(ISecurityEventHandler):
    """Handler for logging security events."""
    
    def __init__(self):
        self._logger = get_debug_logger()
        self._storage = get_secure_storage()
    
    def handle_event(self, event: SecurityEvent) -> None:
        """Log security event."""
        # Log to debug logger
        self._logger.warning(
            f"Security Event: {event.event_type.name}",
            threat_level=event.threat_level.value,
            event_id=event.event_id,
            action=event.action.value if event.action else None,
            resource=event.resource,
            details=event.details
        )
        
        # Store in secure storage for audit trail
        self._storage.store_data(
            key=f"security_event_{event.event_id}",
            value=event.to_dict(),
            storage_type=StorageType.SENSITIVE,
            expires_in_seconds=30 * 24 * 3600  # Keep for 30 days
        )
    
    def can_handle(self, event_type: SecurityEventType) -> bool:
        """Can handle all event types."""
        return True


class ThreatDetectionHandler(ISecurityEventHandler):
    """Handler for detecting security threats."""
    
    def __init__(self):
        self._error_tracker = get_error_tracker()
        self._logger = get_debug_logger()
        
        # Threat detection thresholds
        self.failed_attempts_threshold = 5
        self.suspicious_activity_threshold = 10
        self.time_window_seconds = 300  # 5 minutes
        
        # Track recent events
        self._recent_events: List[SecurityEvent] = []
        self._lock = threading.RLock()
    
    def handle_event(self, event: SecurityEvent) -> None:
        """Analyze event for threats."""
        with self._lock:
            # Add to recent events
            self._recent_events.append(event)
            
            # Clean old events
            cutoff_time = datetime.now(timezone.utc).replace(microsecond=0)
            cutoff_time = cutoff_time.replace(second=cutoff_time.second - self.time_window_seconds)
            
            self._recent_events = [
                e for e in self._recent_events 
                if e.timestamp > cutoff_time
            ]
            
            # Analyze threat patterns
            self._analyze_threat_patterns(event)
    
    def can_handle(self, event_type: SecurityEventType) -> bool:
        """Handle high-risk events."""
        high_risk_events = {
            SecurityEventType.LOGIN_FAILURE,
            SecurityEventType.PERMISSION_DENIED,
            SecurityEventType.INJECTION_ATTEMPT,
            SecurityEventType.XSS_ATTEMPT,
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT,
            SecurityEventType.SECURITY_POLICY_VIOLATION
        }
        return event_type in high_risk_events
    
    def _analyze_threat_patterns(self, current_event: SecurityEvent) -> None:
        """Analyze recent events for threat patterns."""
        # Pattern 1: Multiple failed attempts
        if current_event.event_type == SecurityEventType.LOGIN_FAILURE:
            recent_failures = [
                e for e in self._recent_events
                if e.event_type == SecurityEventType.LOGIN_FAILURE
                and e.user_id == current_event.user_id
            ]
            
            if len(recent_failures) >= self.failed_attempts_threshold:
                self._raise_security_alert(
                    "Multiple failed login attempts detected",
                    SecurityThreatLevel.HIGH,
                    current_event
                )
        
        # Pattern 2: Injection attempt patterns
        injection_events = {
            SecurityEventType.INJECTION_ATTEMPT,
            SecurityEventType.XSS_ATTEMPT,
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT
        }
        
        if current_event.event_type in injection_events:
            recent_injections = [
                e for e in self._recent_events
                if e.event_type in injection_events
            ]
            
            if len(recent_injections) >= 3:
                self._raise_security_alert(
                    "Multiple injection attempts detected",
                    SecurityThreatLevel.CRITICAL,
                    current_event
                )
        
        # Pattern 3: Suspicious activity volume
        high_risk_count = len([
            e for e in self._recent_events
            if e.threat_level in {SecurityThreatLevel.HIGH, SecurityThreatLevel.CRITICAL}
        ])
        
        if high_risk_count >= self.suspicious_activity_threshold:
            self._raise_security_alert(
                "High volume of suspicious security events",
                SecurityThreatLevel.CRITICAL,
                current_event
            )
    
    def _raise_security_alert(
        self, 
        message: str, 
        threat_level: SecurityThreatLevel,
        triggering_event: SecurityEvent
    ) -> None:
        """Raise a security alert."""
        self._logger.critical(
            f"SECURITY ALERT: {message}",
            threat_level=threat_level.value,
            triggering_event_id=triggering_event.event_id,
            recent_events_count=len(self._recent_events)
        )
        
        # Report to error tracker as security incident
        self._error_tracker.capture_error(
            exception=SecurityThreatDetected(message),
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            user_action="Security threat detected",
            operation_context={
                "threat_level": threat_level.value,
                "triggering_event": triggering_event.to_dict(),
                "pattern_analysis": message,
                "recent_events_count": len(self._recent_events)
            }
        )


class SecurityAuditSystem:
    """
    Central security audit system for Study Buddy GUI.
    
    Responsibilities:
    - Monitor security events in real-time
    - Validate security policies
    - Track user actions for forensics
    - Detect and respond to security threats
    - Generate audit reports and compliance data
    """
    
    def __init__(self):
        self._policies: List[ISecurityPolicy] = []
        self._event_handlers: List[ISecurityEventHandler] = []
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()
        self._storage = get_secure_storage()
        self._lock = threading.RLock()
        
        # Audit statistics
        self._stats: Dict[str, Any] = {
            "events_processed": 0,
            "policy_violations": 0,
            "threats_detected": 0,
            "policies_validated": 0,
        }
        
        # Setup default policies and handlers
        self._setup_default_policies()
        self._setup_default_handlers()
    
    def _setup_default_policies(self) -> None:
        """Setup default security policies."""
        self.add_policy(FileAccessPolicy())
        self.add_policy(InputValidationPolicy())
        self.add_policy(ResourceUsagePolicy())
    
    def _setup_default_handlers(self) -> None:
        """Setup default event handlers."""
        self.add_event_handler(SecurityEventLogger())
        self.add_event_handler(ThreatDetectionHandler())
    
    def add_policy(self, policy: ISecurityPolicy) -> None:
        """Add security policy."""
        with self._lock:
            if policy not in self._policies:
                self._policies.append(policy)
                self._logger.debug(f"Added security policy: {policy.get_policy_name()}")
    
    def remove_policy(self, policy: ISecurityPolicy) -> None:
        """Remove security policy."""
        with self._lock:
            if policy in self._policies:
                self._policies.remove(policy)
                self._logger.debug(f"Removed security policy: {policy.get_policy_name()}")
    
    def add_event_handler(self, handler: ISecurityEventHandler) -> None:
        """Add security event handler."""
        with self._lock:
            if handler not in self._event_handlers:
                self._event_handlers.append(handler)
                self._logger.debug(f"Added security event handler: {handler.__class__.__name__}")
    
    def remove_event_handler(self, handler: ISecurityEventHandler) -> None:
        """Remove security event handler."""
        with self._lock:
            if handler in self._event_handlers:
                self._event_handlers.remove(handler)
                self._logger.debug(f"Removed security event handler: {handler.__class__.__name__}")
    
    def validate_security_policies(self, context: Dict[str, Any]) -> bool:
        """
        Validate all security policies against context.
        
        Args:
            context: Security context to validate
            
        Returns:
            True if all policies pass
        """
        with self._lock:
            self._stats["policies_validated"] += 1
            
            for policy in self._policies:
                try:
                    if not policy.validate(context):
                        # Policy violation detected
                        self._stats["policy_violations"] += 1
                        
                        # Create security event
                        event = SecurityEvent(
                            event_id=self._generate_event_id(),
                            event_type=SecurityEventType.SECURITY_POLICY_VIOLATION,
                            threat_level=SecurityThreatLevel.MEDIUM,
                            timestamp=datetime.now(timezone.utc).replace(microsecond=0),
                            user_id=context.get('user_id'),
                            source_ip=context.get('source_ip'),
                            user_agent=context.get('user_agent'),
                            action=context.get('action'),
                            resource=context.get('resource'),
                            details={
                                'policy_name': policy.get_policy_name(),
                                'violation_message': policy.get_violation_message(),
                                'context': context
                            }
                        )
                        
                        self.record_security_event(event)
                        
                        self._logger.warning(
                            f"Security policy violation: {policy.get_policy_name()}",
                            violation_message=policy.get_violation_message(),
                            context=context
                        )
                        
                        return False
                
                except Exception as e:
                    self._logger.error(f"Error validating policy {policy.get_policy_name()}: {e}")
            
            return True
    
    def create_security_event(
        self,
        event_type: SecurityEventType,
        threat_level: SecurityThreatLevel = SecurityThreatLevel.INFORMATIONAL,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> SecurityEvent:
        """
        Create and record a security event.
        
        Args:
            event_type: Type of security event
            threat_level: Security threat level
            user_id: Optional user identifier
            action: Optional user action being audited
            resource: Optional resource being accessed
            details: Optional additional details
            stack_trace: Optional stack trace for errors
            
        Returns:
            Created SecurityEvent
        """
        event = SecurityEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            threat_level=threat_level,
            timestamp=datetime.now(timezone.utc).replace(microsecond=0),
            user_id=user_id,
            source_ip=None,  # Could be enhanced to detect IP
            user_agent=None,  # Could be enhanced for web interface
            action=action,
            resource=resource,
            details=details or {},
            stack_trace=stack_trace
        )
        
        self.record_security_event(event)
        return event
    
    def record_security_event(self, event: SecurityEvent) -> None:
        """Record a security event."""
        with self._lock:
            self._stats["events_processed"] += 1
            
            # Update threat statistics
            if event.threat_level in {SecurityThreatLevel.HIGH, SecurityThreatLevel.CRITICAL}:
                self._stats["threats_detected"] += 1
            
            # Process event with handlers
            for handler in self._event_handlers:
                if handler.can_handle(event.event_type):
                    try:
                        handler.handle_event(event)
                    except Exception as e:
                        self._logger.error(f"Error in security event handler {handler.__class__.__name__}: {e}")
    
    def audit_user_action(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Audit a user action.
        
        Args:
            action: Action being performed
            user_id: Optional user identifier  
            resource: Optional resource being accessed
            success: Whether action was successful
            details: Optional additional details
        """
        event_type = SecurityEventType.DATA_ACCESS
        threat_level = SecurityThreatLevel.INFORMATIONAL
        
        # Determine event type and threat level based on action
        if not success:
            threat_level = SecurityThreatLevel.MEDIUM
            if action in {AuditAction.DOCUMENT_DELETE, AuditAction.DATA_EXPORT}:
                threat_level = SecurityThreatLevel.HIGH
        
        if action == AuditAction.SECURITY_SCAN:
            event_type = SecurityEventType.SUSPICIOUS_ACTIVITY
        elif action in {AuditAction.DATA_EXPORT, AuditAction.DATA_IMPORT}:
            event_type = SecurityEventType.SENSITIVE_DATA_ACCESS
        
        event = SecurityEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            threat_level=threat_level,
            timestamp=datetime.now(timezone.utc).replace(microsecond=0),
            user_id=user_id,
            source_ip=None,
            user_agent=None,
            action=action,
            resource=resource,
            details={
                'success': success,
                'audit_details': details or {}
            }
        )
        
        self.record_security_event(event)
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get security audit statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats['policies_count'] = len(self._policies)
            stats['handlers_count'] = len(self._event_handlers)
            stats['policy_names'] = [p.get_policy_name() for p in self._policies]
            return stats
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = str(int(time.time() * 1000))
        random_data = os.urandom(8)
        hash_data = (timestamp + random_data.hex()).encode()
        return hashlib.sha256(hash_data).hexdigest()[:16]


class SecurityThreatDetected(Exception):
    """Exception raised when security threat is detected."""
    pass


# Global audit system instance
_security_audit: Optional[SecurityAuditSystem] = None
_audit_lock = threading.Lock()


def get_security_audit() -> SecurityAuditSystem:
    """
    Get global security audit system (singleton pattern).
    
    Returns:
        SecurityAuditSystem instance
    """
    global _security_audit
    
    if _security_audit is None:
        with _audit_lock:
            if _security_audit is None:
                _security_audit = SecurityAuditSystem()
    
    return _security_audit


# Convenience functions for common security operations
def validate_file_access(file_path: str, user_id: Optional[str] = None) -> bool:
    """Validate file access against security policies."""
    audit = get_security_audit()
    context = {
        'file_path': file_path,
        'user_id': user_id,
        'action': AuditAction.DOCUMENT_UPLOAD,
    }
    return audit.validate_security_policies(context)


def validate_user_input(input_text: str, input_type: str = 'user_input') -> bool:
    """Validate user input against security policies."""
    audit = get_security_audit()
    context = {
        'input_text': input_text,
        'input_type': input_type,
    }
    return audit.validate_security_policies(context)


def audit_document_action(
    action: AuditAction,
    document_path: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Audit document-related user action."""
    audit = get_security_audit()
    audit.audit_user_action(
        action=action,
        resource=document_path,
        success=success,
        details=details
    )


def record_security_violation(
    violation_type: str,
    details: Dict[str, Any],
    threat_level: SecurityThreatLevel = SecurityThreatLevel.MEDIUM
) -> None:
    """Record a security violation."""
    audit = get_security_audit()
    audit.create_security_event(
        event_type=SecurityEventType.SECURITY_POLICY_VIOLATION,
        threat_level=threat_level,
        details={
            'violation_type': violation_type,
            **details
        }
    )