"""
Study Buddy GUI - Permission Management System

Provides comprehensive permission and access control for the GUI application:
- Role-based access control (RBAC)
- Resource permission management
- Operation-level authorization
- Permission inheritance and delegation
- Security context enforcement
- Audit trail for permission changes

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Decorator Pattern, Chain of Responsibility
SOLID: SRP (permissions only), OCP (extensible roles), LSP (role substitution), ISP (focused interfaces), DIP (abstraction-based)
"""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Set, Callable

from gui.error_handling import get_debug_logger
from gui.security.secure_storage import get_secure_storage, StorageType
from gui.security.security_audit import get_security_audit, SecurityEventType, SecurityThreatLevel, AuditAction


class Permission(Enum):
    """System permissions for different operations."""
    
    # Document Operations
    DOCUMENT_READ = "document_read"
    DOCUMENT_WRITE = "document_write"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_EXPORT = "document_export"
    
    # Data Operations  
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_IMPORT = "data_import"
    DATA_EXPORT = "data_export"
    
    # System Operations
    SYSTEM_CONFIG = "system_config"
    SYSTEM_LOGS = "system_logs"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    
    # MCP Operations
    MCP_CONNECT = "mcp_connect"
    MCP_TOOL_EXECUTE = "mcp_tool_execute"
    MCP_SERVER_MANAGE = "mcp_server_manage"
    
    # Security Operations
    SECURITY_VIEW = "security_view"
    SECURITY_ADMIN = "security_admin"
    PERMISSION_MANAGE = "permission_manage"
    AUDIT_VIEW = "audit_view"
    
    # User Interface
    UI_CUSTOMIZE = "ui_customize"
    UI_ADVANCED = "ui_advanced"


class Role(Enum):
    """User roles with different permission levels."""
    
    GUEST = "guest"              # Read-only access to documents
    USER = "user"                # Standard user operations  
    POWER_USER = "power_user"    # Advanced features and customization
    ADMIN = "admin"              # Full administrative access


class AccessLevel(Enum):
    """Access levels for fine-grained control."""
    
    NONE = "none"       # No access
    READ = "read"       # Read-only access
    WRITE = "write"     # Read and write access
    ADMIN = "admin"     # Full administrative access


@dataclass
class PermissionGrant:
    """Represents a permission grant to a user/role."""
    
    permission: Permission
    access_level: AccessLevel
    granted_at: datetime
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize conditions."""
        if self.conditions is None:
            self.conditions = {}
    
    def is_expired(self) -> bool:
        """Check if grant has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['permission'] = self.permission.value
        data['access_level'] = self.access_level.value
        data['granted_at'] = self.granted_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PermissionGrant':
        """Create from dictionary."""
        data['permission'] = Permission(data['permission'])
        data['access_level'] = AccessLevel(data['access_level'])
        data['granted_at'] = datetime.fromisoformat(data['granted_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


@dataclass
class SecurityContext:
    """Security context for permission checks."""
    
    user_id: str
    session_id: Optional[str] = None
    roles: Optional[Set[Role]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize context."""
        if self.roles is None:
            self.roles = set()
        if self.additional_context is None:
            self.additional_context = {}


class IPermissionProvider(ABC):
    """Interface for permission providers."""
    
    @abstractmethod
    def get_permissions(self, context: SecurityContext) -> Set[PermissionGrant]:
        """Get permissions for security context."""
        pass
    
    @abstractmethod
    def has_permission(
        self, 
        context: SecurityContext, 
        permission: Permission,
        access_level: AccessLevel = AccessLevel.READ
    ) -> bool:
        """Check if context has specific permission."""
        pass


class IAccessController(ABC):
    """Interface for access control strategies."""
    
    @abstractmethod
    def check_access(
        self,
        context: SecurityContext,
        resource: str,
        operation: str,
        permission_required: Permission
    ) -> bool:
        """Check access to resource/operation."""
        pass
    
    @abstractmethod
    def get_allowed_operations(
        self,
        context: SecurityContext,
        resource: str
    ) -> Set[str]:
        """Get allowed operations for resource."""
        pass


class RoleBasedPermissionProvider(IPermissionProvider):
    """Role-based permission provider."""
    
    def __init__(self):
        # Define role-based permissions
        self._role_permissions = {
            Role.GUEST: {
                Permission.DOCUMENT_READ: AccessLevel.READ,
                Permission.DATA_READ: AccessLevel.READ,
                Permission.UI_CUSTOMIZE: AccessLevel.READ,
            },
            Role.USER: {
                Permission.DOCUMENT_READ: AccessLevel.READ,
                Permission.DOCUMENT_WRITE: AccessLevel.WRITE,
                Permission.DOCUMENT_UPLOAD: AccessLevel.WRITE,
                Permission.DATA_READ: AccessLevel.READ,
                Permission.DATA_WRITE: AccessLevel.WRITE,
                Permission.MCP_CONNECT: AccessLevel.WRITE,
                Permission.MCP_TOOL_EXECUTE: AccessLevel.WRITE,
                Permission.UI_CUSTOMIZE: AccessLevel.WRITE,
            },
            Role.POWER_USER: {
                Permission.DOCUMENT_READ: AccessLevel.WRITE,
                Permission.DOCUMENT_WRITE: AccessLevel.WRITE,
                Permission.DOCUMENT_DELETE: AccessLevel.WRITE,
                Permission.DOCUMENT_UPLOAD: AccessLevel.WRITE,
                Permission.DOCUMENT_EXPORT: AccessLevel.WRITE,
                Permission.DATA_READ: AccessLevel.WRITE,
                Permission.DATA_WRITE: AccessLevel.WRITE,
                Permission.DATA_EXPORT: AccessLevel.WRITE,
                Permission.MCP_CONNECT: AccessLevel.WRITE,
                Permission.MCP_TOOL_EXECUTE: AccessLevel.WRITE,
                Permission.SYSTEM_CONFIG: AccessLevel.WRITE,
                Permission.SECURITY_VIEW: AccessLevel.READ,
                Permission.AUDIT_VIEW: AccessLevel.READ,
                Permission.UI_CUSTOMIZE: AccessLevel.WRITE,
                Permission.UI_ADVANCED: AccessLevel.WRITE,
            },
            Role.ADMIN: {
                # Admin has full access to all permissions
                **{perm: AccessLevel.ADMIN for perm in Permission},
            }
        }
    
    def get_permissions(self, context: SecurityContext) -> Set[PermissionGrant]:
        """Get permissions based on user roles."""
        grants = set()
        now = datetime.now(timezone.utc).replace(microsecond=0)
        
        if context.roles:
            for role in context.roles:
                role_perms = self._role_permissions.get(role, {})
                for permission, access_level in role_perms.items():
                    grant = PermissionGrant(
                        permission=permission,
                        access_level=access_level,
                        granted_at=now,
                        granted_by="role_system"
                    )
                    grants.add(grant)
        
        return grants
    
    def has_permission(
        self, 
        context: SecurityContext, 
        permission: Permission,
        access_level: AccessLevel = AccessLevel.READ
    ) -> bool:
        """Check if context has specific permission at required level."""
        if context.roles:
            for role in context.roles:
                role_perms = self._role_permissions.get(role, {})
                granted_level = role_perms.get(permission)
                
                if granted_level and self._access_level_satisfies(granted_level, access_level):
                    return True
        
        return False
    
    def _access_level_satisfies(self, granted: AccessLevel, required: AccessLevel) -> bool:
        """Check if granted access level satisfies required level."""
        level_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1, 
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        
        return level_hierarchy.get(granted, 0) >= level_hierarchy.get(required, 0)


class ResourceAccessController(IAccessController):
    """Access controller for resource-based permissions."""
    
    def __init__(self, permission_provider: IPermissionProvider):
        self._permission_provider = permission_provider
        
        # Define operation to permission mapping
        self._operation_permissions = {
            # Document operations
            "read_document": Permission.DOCUMENT_READ,
            "write_document": Permission.DOCUMENT_WRITE,
            "delete_document": Permission.DOCUMENT_DELETE,
            "upload_document": Permission.DOCUMENT_UPLOAD,
            "export_document": Permission.DOCUMENT_EXPORT,
            
            # Data operations
            "read_data": Permission.DATA_READ,
            "write_data": Permission.DATA_WRITE,
            "delete_data": Permission.DATA_DELETE,
            "export_data": Permission.DATA_EXPORT,
            
            # System operations
            "configure_system": Permission.SYSTEM_CONFIG,
            "view_logs": Permission.SYSTEM_LOGS,
            "backup_system": Permission.SYSTEM_BACKUP,
            
            # MCP operations
            "connect_mcp": Permission.MCP_CONNECT,
            "execute_tool": Permission.MCP_TOOL_EXECUTE,
            "manage_server": Permission.MCP_SERVER_MANAGE,
            
            # Security operations
            "view_security": Permission.SECURITY_VIEW,
            "admin_security": Permission.SECURITY_ADMIN,
            "manage_permissions": Permission.PERMISSION_MANAGE,
            "view_audit": Permission.AUDIT_VIEW,
        }
        
        # Define operation access levels
        self._operation_access_levels = {
            "read_document": AccessLevel.READ,
            "write_document": AccessLevel.WRITE,
            "delete_document": AccessLevel.WRITE,
            "upload_document": AccessLevel.WRITE,
            "export_document": AccessLevel.WRITE,
            "configure_system": AccessLevel.ADMIN,
            "manage_permissions": AccessLevel.ADMIN,
            "admin_security": AccessLevel.ADMIN,
        }
    
    def check_access(
        self,
        context: SecurityContext,
        resource: str,
        operation: str,
        permission_required: Optional[Permission] = None
    ) -> bool:
        """Check access to resource/operation."""
        # Determine required permission
        if permission_required is None:
            permission_required = self._operation_permissions.get(operation)
            if permission_required is None:
                return False  # Unknown operation
        
        # Determine required access level
        required_level = self._operation_access_levels.get(operation, AccessLevel.READ)
        
        # Check permission
        return self._permission_provider.has_permission(
            context, 
            permission_required, 
            required_level
        )
    
    def get_allowed_operations(
        self,
        context: SecurityContext,
        resource: str
    ) -> Set[str]:
        """Get allowed operations for resource."""
        allowed = set()
        
        for operation, permission in self._operation_permissions.items():
            required_level = self._operation_access_levels.get(operation, AccessLevel.READ)
            
            if self._permission_provider.has_permission(context, permission, required_level):
                allowed.add(operation)
        
        return allowed


class PermissionManager:
    """
    Central permission management system.
    
    Responsibilities:
    - Manage user roles and permissions
    - Enforce access control policies
    - Track permission changes and grants
    - Integrate with security audit system
    - Provide authorization decisions
    """
    
    def __init__(self):
        self._permission_provider = RoleBasedPermissionProvider()
        self._access_controller = ResourceAccessController(self._permission_provider)
        self._storage = get_secure_storage()
        self._audit = get_security_audit()
        self._logger = get_debug_logger()
        self._lock = threading.RLock()
        
        # Default user roles
        self._user_roles: Dict[str, Set[Role]] = {}
        
        # Permission statistics
        self._stats: Dict[str, Any] = {
            "permission_checks": 0,
            "access_granted": 0,
            "access_denied": 0,
            "role_assignments": 0,
        }
        
        # Setup default roles
        self._setup_default_roles()
    
    def _setup_default_roles(self) -> None:
        """Setup default user roles."""
        # Default user gets USER role
        self.assign_role("default_user", Role.USER)
    
    def assign_role(self, user_id: str, role: Role) -> bool:
        """
        Assign role to user.
        
        Args:
            user_id: User identifier
            role: Role to assign
            
        Returns:
            True if assigned successfully
        """
        with self._lock:
            try:
                if user_id not in self._user_roles:
                    self._user_roles[user_id] = set()
                
                self._user_roles[user_id].add(role)
                self._stats["role_assignments"] += 1
                
                # Store in secure storage
                roles_data = [r.value for r in self._user_roles[user_id]]
                self._storage.store_data(
                    key=f"user_roles_{user_id}",
                    value=roles_data,
                    storage_type=StorageType.SENSITIVE
                )
                
                # Audit role assignment
                self._audit.audit_user_action(
                    action=AuditAction.PERMISSION_REQUEST,
                    user_id=user_id,
                    success=True,
                    details={
                        "operation": "assign_role",
                        "role": role.value,
                        "assigned_roles": roles_data
                    }
                )
                
                self._logger.info(
                    f"Assigned role {role.value} to user {user_id}",
                    user_id=user_id,
                    role=role.value,
                    total_roles=len(self._user_roles[user_id])
                )
                
                return True
            
            except Exception as e:
                self._logger.error(f"Failed to assign role {role.value} to user {user_id}: {e}")
                return False
    
    def revoke_role(self, user_id: str, role: Role) -> bool:
        """
        Revoke role from user.
        
        Args:
            user_id: User identifier  
            role: Role to revoke
            
        Returns:
            True if revoked successfully
        """
        with self._lock:
            try:
                if user_id in self._user_roles and role in self._user_roles[user_id]:
                    self._user_roles[user_id].remove(role)
                    
                    # Update storage
                    if self._user_roles[user_id]:
                        roles_data = [r.value for r in self._user_roles[user_id]]
                        self._storage.store_data(
                            key=f"user_roles_{user_id}",
                            value=roles_data,
                            storage_type=StorageType.SENSITIVE
                        )
                    else:
                        # Remove user if no roles left
                        self._storage.delete_data(f"user_roles_{user_id}", StorageType.SENSITIVE)
                        del self._user_roles[user_id]
                    
                    # Audit role revocation
                    self._audit.audit_user_action(
                        action=AuditAction.PERMISSION_REQUEST,
                        user_id=user_id,
                        success=True,
                        details={
                            "operation": "revoke_role", 
                            "role": role.value,
                            "remaining_roles": [r.value for r in self._user_roles.get(user_id, set())]
                        }
                    )
                    
                    self._logger.info(f"Revoked role {role.value} from user {user_id}")
                    return True
                
                return False
            
            except Exception as e:
                self._logger.error(f"Failed to revoke role {role.value} from user {user_id}: {e}")
                return False
    
    def get_user_roles(self, user_id: str) -> Set[Role]:
        """Get roles assigned to user."""
        with self._lock:
            # Try memory first
            if user_id in self._user_roles:
                return self._user_roles[user_id].copy()
            
            # Try storage
            try:
                roles_data = self._storage.retrieve_data(
                    f"user_roles_{user_id}", 
                    StorageType.SENSITIVE,
                    default=[]
                )
                
                if roles_data:
                    roles = {Role(r) for r in roles_data}
                    self._user_roles[user_id] = roles
                    return roles.copy()
            
            except Exception as e:
                self._logger.error(f"Failed to load roles for user {user_id}: {e}")
            
            # Default to guest role
            return {Role.GUEST}
    
    def has_permission(
        self,
        user_id: str,
        permission: Permission,
        access_level: AccessLevel = AccessLevel.READ,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id: User identifier
            permission: Permission to check
            access_level: Required access level
            context: Optional additional context
            
        Returns:
            True if user has permission
        """
        with self._lock:
            self._stats["permission_checks"] += 1
            
            try:
                # Create security context
                roles = self.get_user_roles(user_id)
                security_context = SecurityContext(
                    user_id=user_id,
                    roles=roles,
                    additional_context=context
                )
                
                # Check permission
                has_perm = self._permission_provider.has_permission(
                    security_context, 
                    permission, 
                    access_level
                )
                
                if has_perm:
                    self._stats["access_granted"] += 1
                else:
                    self._stats["access_denied"] += 1
                    
                    # Audit denied permission
                    self._audit.create_security_event(
                        event_type=SecurityEventType.PERMISSION_DENIED,
                        threat_level=SecurityThreatLevel.LOW,
                        user_id=user_id,
                        action=AuditAction.PERMISSION_REQUEST,
                        details={
                            "permission": permission.value,
                            "access_level": access_level.value,
                            "user_roles": [r.value for r in roles],
                            "context": context
                        }
                    )
                
                self._logger.debug(
                    f"Permission check: {permission.value} -> {'GRANTED' if has_perm else 'DENIED'}",
                    user_id=user_id,
                    permission=permission.value,
                    access_level=access_level.value,
                    result=has_perm,
                    roles=[r.value for r in roles]
                )
                
                return has_perm
            
            except Exception as e:
                self._stats["access_denied"] += 1
                self._logger.error(f"Error checking permission {permission.value} for user {user_id}: {e}")
                return False
    
    def check_resource_access(
        self,
        user_id: str,
        resource: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user can perform operation on resource.
        
        Args:
            user_id: User identifier
            resource: Resource being accessed
            operation: Operation being performed
            context: Optional additional context
            
        Returns:
            True if access allowed
        """
        with self._lock:
            self._stats["permission_checks"] += 1
            
            try:
                # Create security context
                roles = self.get_user_roles(user_id)
                security_context = SecurityContext(
                    user_id=user_id,
                    roles=roles,
                    additional_context=context
                )
                
                # Check access
                has_access = self._access_controller.check_access(
                    security_context,
                    resource, 
                    operation
                )
                
                if has_access:
                    self._stats["access_granted"] += 1
                else:
                    self._stats["access_denied"] += 1
                    
                    # Audit denied access
                    self._audit.create_security_event(
                        event_type=SecurityEventType.PERMISSION_DENIED,
                        threat_level=SecurityThreatLevel.MEDIUM,
                        user_id=user_id,
                        resource=resource,
                        details={
                            "operation": operation,
                            "user_roles": [r.value for r in roles],
                            "context": context
                        }
                    )
                
                self._logger.debug(
                    f"Resource access check: {operation} on {resource} -> {'ALLOWED' if has_access else 'DENIED'}",
                    user_id=user_id,
                    resource=resource,
                    operation=operation,
                    result=has_access,
                    roles=[r.value for r in roles]
                )
                
                return has_access
            
            except Exception as e:
                self._stats["access_denied"] += 1
                self._logger.error(f"Error checking resource access for user {user_id}: {e}")
                return False
    
    def get_allowed_operations(
        self,
        user_id: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """Get operations user is allowed to perform on resource."""
        try:
            # Create security context
            roles = self.get_user_roles(user_id)
            security_context = SecurityContext(
                user_id=user_id,
                roles=roles,
                additional_context=context
            )
            
            return self._access_controller.get_allowed_operations(security_context, resource)
        
        except Exception as e:
            self._logger.error(f"Error getting allowed operations for user {user_id}: {e}")
            return set()
    
    def get_permission_statistics(self) -> Dict[str, Any]:
        """Get permission management statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats["total_users"] = len(self._user_roles)
            stats["total_roles"] = len(Role)
            stats["total_permissions"] = len(Permission)
            
            # Role distribution
            role_counts = {}
            for roles in self._user_roles.values():
                for role in roles:
                    role_counts[role.value] = role_counts.get(role.value, 0) + 1
            
            stats["role_distribution"] = role_counts
            return stats


# Authorization decorator
def requires_permission(permission: Permission, access_level: AccessLevel = AccessLevel.READ):
    """
    Decorator to enforce permission requirements on functions.
    
    Args:
        permission: Required permission
        access_level: Required access level
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Try to extract user_id from various sources
            user_id = None
            
            # Check kwargs
            if 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            # Check if first arg is self with user context
            elif args and hasattr(args[0], 'current_user_id'):
                user_id = args[0].current_user_id
            
            # Default user if none found
            if not user_id:
                user_id = "default_user"
            
            # Check permission
            perm_manager = get_permission_manager()
            if not perm_manager.has_permission(user_id, permission, access_level):
                raise PermissionError(
                    f"User {user_id} does not have permission {permission.value} "
                    f"at level {access_level.value}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global permission manager instance
_permission_manager: Optional[PermissionManager] = None
_permission_lock = threading.Lock()


def get_permission_manager() -> PermissionManager:
    """
    Get global permission manager (singleton pattern).
    
    Returns:
        PermissionManager instance
    """
    global _permission_manager
    
    if _permission_manager is None:
        with _permission_lock:
            if _permission_manager is None:
                _permission_manager = PermissionManager()
    
    return _permission_manager


# Convenience functions for common permission operations
def check_document_permission(
    user_id: str, 
    operation: str,
    document_path: Optional[str] = None
) -> bool:
    """Check if user has permission for document operation."""
    manager = get_permission_manager()
    resource = document_path or "documents"
    return manager.check_resource_access(user_id, resource, operation)


def check_system_permission(user_id: str, operation: str) -> bool:
    """Check if user has permission for system operation.""" 
    manager = get_permission_manager()
    return manager.check_resource_access(user_id, "system", operation)


def assign_user_role(user_id: str, role: Role) -> bool:
    """Assign role to user."""
    manager = get_permission_manager()
    return manager.assign_role(user_id, role)


def get_user_permissions(user_id: str) -> Dict[str, Any]:
    """Get comprehensive permission information for user."""
    manager = get_permission_manager()
    
    return {
        "user_id": user_id,
        "roles": [r.value for r in manager.get_user_roles(user_id)],
        "document_operations": list(manager.get_allowed_operations(user_id, "documents")),
        "system_operations": list(manager.get_allowed_operations(user_id, "system")),
        "mcp_operations": list(manager.get_allowed_operations(user_id, "mcp")),
    }