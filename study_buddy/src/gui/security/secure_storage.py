"""
Study Buddy GUI - Secure Storage System

Provides secure storage for sensitive application data including:
- User preferences and settings
- Connection credentials (encrypted)
- Session tokens and temporary data  
- Document metadata and user notes
- Application state and configuration

Architecture: Clean Architecture Layer 4 (Infrastructure)
Patterns: Strategy Pattern, Factory Pattern, Singleton Pattern
SOLID: SRP (storage only), OCP (extensible backends), DIP (storage abstraction)
"""

import json
import sqlite3
import secrets
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from gui.error_handling import get_debug_logger, get_error_tracker, ErrorSeverity, ErrorCategory


class StorageType(Enum):
    """Types of data storage with different security requirements."""
    
    PUBLIC = "public"           # Non-sensitive data (UI preferences, themes)
    PRIVATE = "private"         # User-specific data (notes, bookmarks)  
    SENSITIVE = "sensitive"     # Encrypted data (credentials, tokens)
    TEMPORARY = "temporary"     # Session data (cleared on exit)


class EncryptionLevel(Enum):
    """Levels of encryption for sensitive data."""
    
    NONE = "none"              # No encryption (public data)
    BASIC = "basic"            # Simple encryption (private data)
    STRONG = "strong"          # Strong encryption (sensitive data)
    PARANOID = "paranoid"      # Maximum encryption (critical data)


@dataclass
class StorageEntry:
    """Represents a stored data entry with metadata."""
    
    key: str
    value: Any
    storage_type: StorageType
    encryption_level: EncryptionLevel
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageEntry':
        """Create from dictionary."""
        # Convert ISO strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        return cls(**data)


class IStorageBackend(ABC):
    """Interface for storage backends."""
    
    @abstractmethod
    def store(self, entry: StorageEntry) -> bool:
        """Store an entry."""
        pass
    
    @abstractmethod
    def retrieve(self, key: str, storage_type: StorageType) -> Optional[StorageEntry]:
        """Retrieve an entry by key and type."""
        pass
    
    @abstractmethod
    def delete(self, key: str, storage_type: StorageType) -> bool:
        """Delete an entry."""
        pass
    
    @abstractmethod
    def list_keys(self, storage_type: Optional[StorageType] = None) -> List[str]:
        """List all keys, optionally filtered by storage type."""
        pass
    
    @abstractmethod
    def clear(self, storage_type: Optional[StorageType] = None) -> int:
        """Clear entries, optionally filtered by storage type."""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        pass


class IEncryptionProvider(ABC):
    """Interface for encryption providers."""
    
    @abstractmethod
    def encrypt(self, data: bytes, level: EncryptionLevel) -> bytes:
        """Encrypt data."""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: bytes, level: EncryptionLevel) -> bytes:
        """Decrypt data."""
        pass
    
    @abstractmethod
    def generate_key(self, level: EncryptionLevel) -> bytes:
        """Generate encryption key."""
        pass


class FernetEncryptionProvider(IEncryptionProvider):
    """Encryption provider using Fernet (AES 128/256)."""
    
    def __init__(self, master_password: Optional[str] = None):
        self._keys: Dict[EncryptionLevel, bytes] = {}
        self._master_password = master_password or self._generate_master_password()
        self._lock = threading.RLock()
        
        # Initialize keys for each encryption level
        self._initialize_keys()
    
    def _generate_master_password(self) -> str:
        """Generate secure master password."""
        return secrets.token_urlsafe(32)
    
    def _derive_key(self, password: str, salt: bytes, level: EncryptionLevel) -> bytes:
        """Derive encryption key from password."""
        iterations = {
            EncryptionLevel.NONE: 0,
            EncryptionLevel.BASIC: 100_000,
            EncryptionLevel.STRONG: 200_000,
            EncryptionLevel.PARANOID: 500_000
        }
        
        if level == EncryptionLevel.NONE:
            return b''
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations[level],
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _initialize_keys(self) -> None:
        """Initialize encryption keys for all levels."""
        salt = b'study_buddy_salt_2024'  # In production, use random salt per user
        
        for level in EncryptionLevel:
            if level != EncryptionLevel.NONE:
                key = self._derive_key(self._master_password, salt, level)
                self._keys[level] = key
    
    def encrypt(self, data: bytes, level: EncryptionLevel) -> bytes:
        """Encrypt data using specified level."""
        if level == EncryptionLevel.NONE:
            return data
        
        with self._lock:
            if level not in self._keys:
                raise ValueError(f"No key available for encryption level: {level}")
            
            try:
                fernet = Fernet(self._keys[level])
                return fernet.encrypt(data)
            except Exception as e:
                raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: bytes, level: EncryptionLevel) -> bytes:
        """Decrypt data using specified level."""
        if level == EncryptionLevel.NONE:
            return encrypted_data
        
        with self._lock:
            if level not in self._keys:
                raise ValueError(f"No key available for encryption level: {level}")
            
            try:
                fernet = Fernet(self._keys[level])
                return fernet.decrypt(encrypted_data)
            except Exception as e:
                raise DecryptionError(f"Decryption failed: {e}")
    
    def generate_key(self, level: EncryptionLevel) -> bytes:
        """Generate new encryption key."""
        if level == EncryptionLevel.NONE:
            return b''
        
        # Use Fernet key generation
        return Fernet.generate_key()


class SQLiteStorageBackend(IStorageBackend):
    """SQLite-based storage backend for local data."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._logger = get_debug_logger()
        
        # Create database and tables
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS secure_storage (
                        key TEXT NOT NULL,
                        storage_type TEXT NOT NULL,
                        value_data BLOB NOT NULL,
                        encryption_level TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        expires_at TEXT,
                        metadata TEXT,
                        PRIMARY KEY (key, storage_type)
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_storage_type 
                    ON secure_storage(storage_type)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON secure_storage(expires_at) 
                    WHERE expires_at IS NOT NULL
                """)
                
                conn.commit()
                self._logger.debug(f"Initialized secure storage database: {self.db_path}")
            
            finally:
                conn.close()
    
    def store(self, entry: StorageEntry) -> bool:
        """Store an entry in SQLite database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Serialize value to JSON bytes
                value_json = json.dumps(entry.value, default=str)
                value_data = value_json.encode('utf-8')
                
                # Store entry
                conn.execute("""
                    INSERT OR REPLACE INTO secure_storage 
                    (key, storage_type, value_data, encryption_level, 
                     created_at, updated_at, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    entry.storage_type.value,
                    value_data,
                    entry.encryption_level.value,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    json.dumps(entry.metadata) if entry.metadata else None
                ))
                
                conn.commit()
                return True
            
            except Exception as e:
                self._logger.error(f"Failed to store entry {entry.key}: {e}")
                return False
            
            finally:
                conn.close()
    
    def retrieve(self, key: str, storage_type: StorageType) -> Optional[StorageEntry]:
        """Retrieve an entry from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    SELECT key, storage_type, value_data, encryption_level,
                           created_at, updated_at, expires_at, metadata
                    FROM secure_storage 
                    WHERE key = ? AND storage_type = ?
                """, (key, storage_type.value))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Deserialize data
                value_data = json.loads(row[2].decode('utf-8'))
                created_at = datetime.fromisoformat(row[4])
                updated_at = datetime.fromisoformat(row[5])
                expires_at = datetime.fromisoformat(row[6]) if row[6] else None
                metadata = json.loads(row[7]) if row[7] else None
                
                entry = StorageEntry(
                    key=row[0],
                    value=value_data,
                    storage_type=StorageType(row[1]),
                    encryption_level=EncryptionLevel(row[3]),
                    created_at=created_at,
                    updated_at=updated_at,
                    expires_at=expires_at,
                    metadata=metadata
                )
                
                # Check if expired
                if entry.is_expired():
                    self.delete(key, storage_type)
                    return None
                
                return entry
            
            except Exception as e:
                self._logger.error(f"Failed to retrieve entry {key}: {e}")
                return None
            
            finally:
                conn.close()
    
    def delete(self, key: str, storage_type: StorageType) -> bool:
        """Delete an entry from SQLite database."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute("""
                    DELETE FROM secure_storage 
                    WHERE key = ? AND storage_type = ?
                """, (key, storage_type.value))
                
                conn.commit()
                return cursor.rowcount > 0
            
            except Exception as e:
                self._logger.error(f"Failed to delete entry {key}: {e}")
                return False
            
            finally:
                conn.close()
    
    def list_keys(self, storage_type: Optional[StorageType] = None) -> List[str]:
        """List all keys, optionally filtered by storage type."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                if storage_type:
                    cursor = conn.execute("""
                        SELECT key FROM secure_storage 
                        WHERE storage_type = ?
                        ORDER BY key
                    """, (storage_type.value,))
                else:
                    cursor = conn.execute("""
                        SELECT key FROM secure_storage 
                        ORDER BY key
                    """)
                
                return [row[0] for row in cursor.fetchall()]
            
            except Exception as e:
                self._logger.error(f"Failed to list keys: {e}")
                return []
            
            finally:
                conn.close()
    
    def clear(self, storage_type: Optional[StorageType] = None) -> int:
        """Clear entries, optionally filtered by storage type."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                if storage_type:
                    cursor = conn.execute("""
                        DELETE FROM secure_storage 
                        WHERE storage_type = ?
                    """, (storage_type.value,))
                else:
                    cursor = conn.execute("DELETE FROM secure_storage")
                
                conn.commit()
                return cursor.rowcount
            
            except Exception as e:
                self._logger.error(f"Failed to clear storage: {e}")
                return 0
            
            finally:
                conn.close()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                now = datetime.now(timezone.utc).isoformat()
                cursor = conn.execute("""
                    DELETE FROM secure_storage 
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (now,))
                
                conn.commit()
                return cursor.rowcount
            
            except Exception as e:
                self._logger.error(f"Failed to cleanup expired entries: {e}")
                return 0
            
            finally:
                conn.close()


class SecureStorage:
    """
    Central secure storage system for Study Buddy GUI.
    
    Responsibilities:
    - Coordinate storage backends and encryption
    - Provide type-safe storage operations
    - Handle data serialization and deserialization
    - Manage encryption levels based on data sensitivity
    - Integrate with error handling and logging
    """
    
    def __init__(
        self, 
        storage_backend: IStorageBackend,
        encryption_provider: IEncryptionProvider
    ):
        self._storage_backend = storage_backend
        self._encryption_provider = encryption_provider
        self._logger = get_debug_logger()
        self._error_tracker = get_error_tracker()
        self._lock = threading.RLock()
        
        # Storage statistics
        self._stats = {
            "operations": 0,
            "encryptions": 0,
            "decryptions": 0,
            "errors": 0,
        }
    
    def store_data(
        self,
        key: str,
        value: Any,
        storage_type: StorageType = StorageType.PRIVATE,
        encryption_level: Optional[EncryptionLevel] = None,
        expires_in_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store data with automatic encryption.
        
        Args:
            key: Unique identifier for the data
            value: Data to store (will be JSON serialized)
            storage_type: Type of storage (public, private, sensitive, temporary)
            encryption_level: Encryption level (auto-determined if None)
            expires_in_seconds: Optional expiration time
            metadata: Optional metadata dictionary
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            self._stats["operations"] += 1
            
            try:
                # Auto-determine encryption level if not specified
                if encryption_level is None:
                    encryption_level = self._get_default_encryption_level(storage_type)
                
                # Calculate expiration time
                expires_at = None
                if expires_in_seconds:
                    expires_at = datetime.now(timezone.utc).replace(microsecond=0)
                    expires_at = expires_at.replace(second=expires_at.second + expires_in_seconds)
                
                # Create storage entry
                now = datetime.now(timezone.utc).replace(microsecond=0)
                entry = StorageEntry(
                    key=key,
                    value=value,
                    storage_type=storage_type,
                    encryption_level=encryption_level,
                    created_at=now,
                    updated_at=now,
                    expires_at=expires_at,
                    metadata=metadata
                )
                
                # Encrypt value if needed
                if encryption_level != EncryptionLevel.NONE:
                    self._encrypt_entry_value(entry)
                    self._stats["encryptions"] += 1
                
                # Store via backend
                success = self._storage_backend.store(entry)
                
                if success:
                    self._logger.debug(
                        f"Stored data: {key}",
                        storage_type=storage_type,
                        encryption_level=encryption_level,
                        has_expiration=expires_at is not None
                    )
                else:
                    self._stats["errors"] += 1
                    self._error_tracker.capture_error(
                        exception=StorageError(f"Failed to store data: {key}"),
                        severity=ErrorSeverity.MEDIUM,
                        category=ErrorCategory.DATA,
                        user_action="Store data",
                        operation_context={
                            "key": key,
                            "storage_type": storage_type,
                            "encryption_level": encryption_level
                        }
                    )
                
                return success
            
            except Exception as e:
                self._stats["errors"] += 1
                self._logger.error(f"Error storing data {key}: {e}")
                self._error_tracker.capture_error(
                    exception=e,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.DATA,
                    user_action="Store data",
                    operation_context={
                        "key": key,
                        "storage_type": storage_type,
                        "error": str(e)
                    }
                )
                return False
    
    def retrieve_data(
        self,
        key: str,
        storage_type: StorageType = StorageType.PRIVATE,
        default: Any = None
    ) -> Any:
        """
        Retrieve data with automatic decryption.
        
        Args:
            key: Unique identifier for the data
            storage_type: Type of storage to search
            default: Default value if not found
            
        Returns:
            Stored data or default value
        """
        with self._lock:
            self._stats["operations"] += 1
            
            try:
                # Retrieve from backend
                entry = self._storage_backend.retrieve(key, storage_type)
                if not entry:
                    return default
                
                # Decrypt value if needed
                if entry.encryption_level != EncryptionLevel.NONE:
                    self._decrypt_entry_value(entry)
                    self._stats["decryptions"] += 1
                
                self._logger.debug(
                    f"Retrieved data: {key}",
                    storage_type=storage_type,
                    encryption_level=entry.encryption_level
                )
                
                return entry.value
            
            except Exception as e:
                self._stats["errors"] += 1
                self._logger.error(f"Error retrieving data {key}: {e}")
                self._error_tracker.capture_error(
                    exception=e,
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.DATA,
                    user_action="Retrieve data",
                    operation_context={
                        "key": key,
                        "storage_type": storage_type,
                        "error": str(e)
                    }
                )
                return default
    
    def delete_data(
        self,
        key: str,
        storage_type: StorageType = StorageType.PRIVATE
    ) -> bool:
        """Delete data entry."""
        with self._lock:
            self._stats["operations"] += 1
            
            try:
                success = self._storage_backend.delete(key, storage_type)
                
                if success:
                    self._logger.debug(f"Deleted data: {key}", storage_type=storage_type)
                else:
                    self._logger.warning(f"Data not found for deletion: {key}")
                
                return success
            
            except Exception as e:
                self._stats["errors"] += 1
                self._logger.error(f"Error deleting data {key}: {e}")
                return False
    
    def list_keys(self, storage_type: Optional[StorageType] = None) -> List[str]:
        """List all stored keys, optionally filtered by storage type."""
        try:
            return self._storage_backend.list_keys(storage_type)
        except Exception as e:
            self._logger.error(f"Error listing keys: {e}")
            return []
    
    def clear_storage(self, storage_type: Optional[StorageType] = None) -> int:
        """Clear stored data, optionally filtered by storage type."""
        with self._lock:
            try:
                count = self._storage_backend.clear(storage_type)
                self._logger.info(f"Cleared {count} storage entries", storage_type=storage_type)
                return count
            except Exception as e:
                self._logger.error(f"Error clearing storage: {e}")
                return 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        try:
            count = self._storage_backend.cleanup_expired()
            if count > 0:
                self._logger.info(f"Cleaned up {count} expired entries")
            return count
        except Exception as e:
            self._logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            return self._stats.copy()
    
    def _get_default_encryption_level(self, storage_type: StorageType) -> EncryptionLevel:
        """Get default encryption level for storage type."""
        mapping = {
            StorageType.PUBLIC: EncryptionLevel.NONE,
            StorageType.PRIVATE: EncryptionLevel.BASIC,
            StorageType.SENSITIVE: EncryptionLevel.STRONG,
            StorageType.TEMPORARY: EncryptionLevel.BASIC,
        }
        return mapping.get(storage_type, EncryptionLevel.BASIC)
    
    def _encrypt_entry_value(self, entry: StorageEntry) -> None:
        """Encrypt entry value in place."""
        if entry.encryption_level == EncryptionLevel.NONE:
            return
        
        # Serialize value to JSON bytes
        value_json = json.dumps(entry.value, default=str)
        value_bytes = value_json.encode('utf-8')
        
        # Encrypt
        encrypted_bytes = self._encryption_provider.encrypt(value_bytes, entry.encryption_level)
        
        # Store as base64 string for JSON compatibility
        entry.value = base64.b64encode(encrypted_bytes).decode('ascii')
    
    def _decrypt_entry_value(self, entry: StorageEntry) -> None:
        """Decrypt entry value in place."""
        if entry.encryption_level == EncryptionLevel.NONE:
            return
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(entry.value.encode('ascii'))
        
        # Decrypt
        decrypted_bytes = self._encryption_provider.decrypt(encrypted_bytes, entry.encryption_level)
        
        # Deserialize from JSON
        value_json = decrypted_bytes.decode('utf-8')
        entry.value = json.loads(value_json)


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


class EncryptionError(Exception):
    """Exception raised for encryption-related errors."""
    pass


class DecryptionError(Exception):
    """Exception raised for decryption-related errors."""
    pass


# Global storage instance
_secure_storage: Optional[SecureStorage] = None
_storage_lock = threading.Lock()


def get_secure_storage() -> SecureStorage:
    """
    Get global secure storage instance (singleton pattern).
    
    Returns:
        SecureStorage instance
    """
    global _secure_storage
    
    if _secure_storage is None:
        with _storage_lock:
            if _secure_storage is None:
                # Initialize with default SQLite backend and Fernet encryption
                storage_dir = Path.home() / '.study_buddy' / 'storage'
                storage_dir.mkdir(parents=True, exist_ok=True)
                
                db_path = storage_dir / 'secure_storage.db'
                
                backend = SQLiteStorageBackend(db_path)
                encryption = FernetEncryptionProvider()
                
                _secure_storage = SecureStorage(backend, encryption)
    
    return _secure_storage


# Convenience functions for common storage operations
def store_user_preference(key: str, value: Any, expires_in_seconds: Optional[int] = None) -> bool:
    """Store user preference data."""
    storage = get_secure_storage()
    return storage.store_data(
        key=f"pref_{key}",
        value=value,
        storage_type=StorageType.PRIVATE,
        encryption_level=EncryptionLevel.BASIC,
        expires_in_seconds=expires_in_seconds
    )


def get_user_preference(key: str, default: Any = None) -> Any:
    """Retrieve user preference data."""
    storage = get_secure_storage()
    return storage.retrieve_data(f"pref_{key}", StorageType.PRIVATE, default)


def store_sensitive_data(key: str, value: Any, expires_in_seconds: Optional[int] = None) -> bool:
    """Store sensitive data with strong encryption."""
    storage = get_secure_storage()
    return storage.store_data(
        key=f"sensitive_{key}",
        value=value,
        storage_type=StorageType.SENSITIVE,
        encryption_level=EncryptionLevel.STRONG,
        expires_in_seconds=expires_in_seconds
    )


def get_sensitive_data(key: str, default: Any = None) -> Any:
    """Retrieve sensitive data."""
    storage = get_secure_storage()
    return storage.retrieve_data(f"sensitive_{key}", StorageType.SENSITIVE, default)


def store_session_data(key: str, value: Any, expires_in_seconds: int = 3600) -> bool:
    """Store temporary session data."""
    storage = get_secure_storage()
    return storage.store_data(
        key=f"session_{key}",
        value=value,
        storage_type=StorageType.TEMPORARY,
        encryption_level=EncryptionLevel.BASIC,
        expires_in_seconds=expires_in_seconds
    )


def get_session_data(key: str, default: Any = None) -> Any:
    """Retrieve session data."""
    storage = get_secure_storage()
    return storage.retrieve_data(f"session_{key}", StorageType.TEMPORARY, default)


def clear_session_data() -> int:
    """Clear all session data."""
    storage = get_secure_storage()
    return storage.clear_storage(StorageType.TEMPORARY)