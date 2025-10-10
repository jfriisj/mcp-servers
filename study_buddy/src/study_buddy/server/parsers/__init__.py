"""
Document parsers package for Study Buddy MCP Server.

This package provides document parsing capabilities following the Strategy
pattern and Clean Architecture Layer 4 principles.
"""

from .base_parser import BaseParser, ParseError
from .docx_parser import DOCXParser
from .markdown_parser import MarkdownParser
from .parser_factory import ParserFactory, parse_document, supports_file_type
from .pdf_parser import PDFParser

__all__ = [
    "BaseParser",
    "ParseError",
    "PDFParser",
    "MarkdownParser",
    "DOCXParser",
    "ParserFactory",
    "parse_document",
    "supports_file_type",
]
