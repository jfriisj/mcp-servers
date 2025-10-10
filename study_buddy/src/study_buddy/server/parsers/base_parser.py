"""
Base parser interface for Study Buddy MCP Server.

This module defines the abstract BaseParser interface following the Strategy
pattern, enabling extensible document parsing with consistent contracts.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.parse_result import ParseResult


class ParseError(Exception):
    """
    Exception raised when document parsing fails.

    This exception provides detailed error information for debugging
    and user feedback when document parsing operations fail.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize ParseError with context information.

        Args:
            message: Human-readable error description
            file_path: Path to file that failed to parse
            original_error: Original exception that caused the failure
        """
        self.file_path = file_path
        self.original_error = original_error

        error_msg = message
        if file_path:
            error_msg = f"{message} (file: {file_path})"
        if original_error:
            error_msg = f"{error_msg} - {str(original_error)}"

        super().__init__(error_msg)


class BaseParser(ABC):
    """
    Abstract base parser interface following Strategy pattern.

    This class defines the contract that all document parsers must implement,
    enabling extensible parsing capabilities without modifying existing code.

    Following SOLID principles:
    - SRP: Single responsibility for defining parser contract
    - OCP: Open for extension (new parsers), closed for modification
    - LSP: All subclasses must honor this contract
    - ISP: Focused interface with only essential methods
    - DIP: High-level modules depend on this abstraction

    Clean Architecture Layer 4: Infrastructure Interface
    - Defines contract for document parsing
    - No dependencies on business logic or external frameworks
    - Pure abstraction enabling testability and extensibility
    """

    @abstractmethod
    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file type.

        Args:
            file_path: Path to the file to check

        Returns:
            True if parser supports this file type, False otherwise
        """
        pass

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """
        Parse document file and extract content with metadata.

        This method must:
        1. Read and parse the document file
        2. Extract text content from all relevant sections
        3. Extract metadata (title, author, pages, etc.)
        4. Handle errors gracefully with informative messages
        5. Return a valid ParseResult with content and metadata

        Args:
            file_path: Absolute path to document file

        Returns:
            ParseResult containing extracted content and metadata

        Raises:
            ParseError: If parsing fails for any reason
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
        """
        pass

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of file extensions supported by this parser.

        Returns:
            List of supported file extensions (without dots)
        """
        return []

    def get_parser_name(self) -> str:
        """
        Get human-readable name of this parser.

        Returns:
            Parser name for logging and error messages
        """
        return self.__class__.__name__

    def validate_file(self, file_path: str) -> None:
        """
        Validate file before parsing.

        Args:
            file_path: Path to file to validate

        Raises:
            ParseError: If file validation fails
            FileNotFoundError: If file doesn't exist
        """
        import os

        if not file_path:
            raise ParseError("File path cannot be empty")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ParseError(f"Path is not a file: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise ParseError(f"File is empty: {file_path}")

        if not self.supports_file_type(file_path):
            raise ParseError(
                f"File type not supported by {self.get_parser_name()}: {file_path}"
            )
