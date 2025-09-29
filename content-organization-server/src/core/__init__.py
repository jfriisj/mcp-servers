"""Core functionality for content organization."""

from .common_utils import (
    OrganizationError,
    FileSystemError,
    ValidationError,
    ParseError,
    FileInfo,
    read_file_content,
    write_file_content,
    find_files,
    validate_file_operations
)

from .content_organizer import ContentOrganizer
from .file_reorganizer import FileReorganizer
from .cross_referencer import CrossReferencer, Reference

__all__ = [
    # Errors
    'OrganizationError',
    'FileSystemError',
    'ValidationError',
    'ParseError',
    
    # Data classes
    'FileInfo',
    'Reference',
    
    # Core classes
    'ContentOrganizer',
    'FileReorganizer',
    'CrossReferencer',
    
    # Utilities
    'read_file_content',
    'write_file_content',
    'find_files',
    'validate_file_operations'
]