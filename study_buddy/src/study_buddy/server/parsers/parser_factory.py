"""
Parser factory for Study Buddy MCP Server.

This module implements the Factory pattern for automatic parser selection
and registration, enabling extensible document parsing without modifying
existing code.
"""

import logging
import os
from typing import Dict, List, Optional, Type

from .base_parser import BaseParser, ParseError
from .pdf_parser import PDFParser


class ParserFactory:
    """
    Factory for creating appropriate document parsers.

    This class implements the Factory pattern to automatically select
    the appropriate parser based on file type, enabling extensible
    document processing without modifying existing code.

    Following SOLID principles:
    - SRP: Single responsibility for parser creation and management
    - OCP: Open for extension (new parsers), closed for modification
    - LSP: All parsers must honor BaseParser contract
    - ISP: Focused interface for parser creation
    - DIP: Depends on BaseParser abstraction, not concrete implementations

    Clean Architecture Layer 4: Infrastructure Factory
    - Manages parser instantiation and selection
    - No dependencies on business logic
    - Pure infrastructure concern for parser management
    """

    def __init__(self):
        """Initialize parser factory with default parsers."""
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._extension_map: Dict[str, Type[BaseParser]] = {}
        self.logger = logging.getLogger(__name__)

        # Register default parsers
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """Register built-in parsers."""
        # Import parsers here to avoid circular imports
        try:
            self.register_parser(PDFParser)

            # Import additional parsers if available
            try:
                from .markdown_parser import MarkdownParser

                self.register_parser(MarkdownParser)
            except ImportError:
                self.logger.debug("MarkdownParser not available")

            try:
                from .docx_parser import DOCXParser

                self.register_parser(DOCXParser)
            except ImportError:
                self.logger.debug("DOCXParser not available")

        except Exception as e:
            self.logger.error(f"Error registering default parsers: {e}")

    def register_parser(self, parser_class: Type[BaseParser]) -> None:
        """
        Register a parser class with the factory.

        Args:
            parser_class: Parser class that implements BaseParser

        Raises:
            ValueError: If parser_class is invalid
        """
        if not issubclass(parser_class, BaseParser):
            raise ValueError(
                f"Parser class must inherit from BaseParser: {parser_class}"
            )

        # Create instance to get supported extensions
        try:
            parser_instance = parser_class()
            parser_name = parser_instance.get_parser_name()
            extensions = parser_instance.get_supported_extensions()

            # Register parser
            self._parsers[parser_name] = parser_class

            # Register extensions mapping
            for ext in extensions:
                self._extension_map[ext.lower()] = parser_class

            self.logger.info(
                f"Registered parser {parser_name} for extensions: {extensions}"
            )

        except Exception as e:
            self.logger.error(f"Failed to register parser {parser_class}: {e}")
            raise ValueError(f"Invalid parser class: {e}")

    def get_parser(self, file_path: str) -> BaseParser:
        """
        Get appropriate parser for the given file.

        Args:
            file_path: Path to file that needs parsing

        Returns:
            Parser instance capable of handling the file

        Raises:
            ParseError: If no suitable parser is found
            ValueError: If file_path is invalid
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        # Extract file extension
        _, ext = os.path.splitext(file_path.lower())
        ext = ext.lstrip(".")  # Remove leading dot

        if not ext:
            raise ParseError(
                f"Cannot determine file type (no extension): {file_path}"
            )

        # Find parser for extension
        parser_class = self._extension_map.get(ext)
        if not parser_class:
            raise ParseError(
                f"No parser available for file type '.{ext}': {file_path}"
            )

        try:
            parser = parser_class()

            # Double-check parser supports the file
            if not parser.supports_file_type(file_path):
                raise ParseError(
                    f"Parser {parser.get_parser_name()} does not support file: {file_path}"
                )

            self.logger.debug(
                f"Selected {parser.get_parser_name()} for {file_path}"
            )
            return parser

        except Exception as e:
            if isinstance(e, ParseError):
                raise
            raise ParseError(
                f"Failed to create parser for {file_path}",
                file_path=file_path,
                original_error=e,
            )

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.

        Returns:
            List of supported file extensions (without dots)
        """
        return list(self._extension_map.keys())

    def get_registered_parsers(self) -> List[str]:
        """
        Get list of registered parser names.

        Returns:
            List of registered parser names
        """
        return list(self._parsers.keys())

    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if factory can handle the given file type.

        Args:
            file_path: Path to file to check

        Returns:
            True if a parser is available for this file type
        """
        try:
            self.get_parser(file_path)
            return True
        except (ParseError, ValueError):
            return False

    def parse_document(self, file_path: str):
        """
        Parse document using appropriate parser.

        This is a convenience method that combines parser selection
        and document parsing in one call.

        Args:
            file_path: Path to document to parse

        Returns:
            ParseResult with extracted content and metadata

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        parser = self.get_parser(file_path)
        return parser.parse(file_path)


# Global factory instance for convenience
_default_factory: Optional[ParserFactory] = None


def get_default_factory() -> ParserFactory:
    """
    Get the default parser factory instance.

    Returns:
        Singleton ParserFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = ParserFactory()
    return _default_factory


def parse_document(file_path: str):
    """
    Convenience function to parse document with default factory.

    Args:
        file_path: Path to document to parse

    Returns:
        ParseResult with extracted content and metadata
    """
    return get_default_factory().parse_document(file_path)


def supports_file_type(file_path: str) -> bool:
    """
    Convenience function to check file type support.

    Args:
        file_path: Path to file to check

    Returns:
        True if file type is supported
    """
    return get_default_factory().supports_file_type(file_path)
