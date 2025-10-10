"""
PDF parser implementation for Study Buddy MCP Server.

This module implements PDF document pa            raise ParseError(
                "Failed to parse PDF document",
                file_path=file_path,
                original_error=e
            ) using PyPDF2, following the
Strategy pattern and Clean Architecture Layer 4 principles.
"""

import logging
import os
from typing import Any, Dict

try:
    import PyPDF2
except ImportError:
    raise ImportError(
        "PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2"
    )

from ..models.parse_result import ParseResult

from .base_parser import BaseParser, ParseError


class PDFParser(BaseParser):
    """
    PDF document parser using PyPDF2.

    This class implements the BaseParser interface for PDF documents,
    providing robust content extraction with error handling.

    Features:
    - Text extraction from all pages
    - Metadata extraction (title, author, pages, etc.)
    - Password-protected PDF handling
    - Corrupted file detection and handling
    - Memory-efficient page-by-page processing

    Clean Architecture Layer 4: Infrastructure Implementation
    - Implements parser strategy interface
    - No dependencies on business logic
    - Pure document processing logic
    """

    def __init__(self):
        """Initialize PDF parser with logging."""
        self.logger = logging.getLogger(__name__)

    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if file is a PDF document.

        Args:
            file_path: Path to file to check

        Returns:
            True if file has .pdf extension
        """
        return file_path.lower().endswith(".pdf")

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ["pdf"]

    def parse(self, file_path: str) -> ParseResult:
        """
        Parse PDF document and extract content with metadata.

        Args:
            file_path: Absolute path to PDF file

        Returns:
            ParseResult with extracted content and metadata

        Raises:
            ParseError: If PDF parsing fails
            FileNotFoundError: If file doesn't exist
        """
        # Validate file first
        self.validate_file(file_path)

        try:
            with open(file_path, "rb") as file:
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(file)

                # Check for encryption
                if pdf_reader.is_encrypted:
                    return self._handle_encrypted_pdf(pdf_reader, file_path)

                # Extract content and metadata
                content = self._extract_content(pdf_reader, file_path)
                metadata = self._extract_metadata(pdf_reader, file_path)

                return ParseResult(content=content, metadata=metadata)

        except FileNotFoundError:
            raise
        except ParseError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error parsing PDF {file_path}: {e}")
            raise ParseError(
                "Failed to parse PDF document",
                file_path=file_path,
                original_error=e,
            )

    def _extract_content(
        self, pdf_reader: PyPDF2.PdfReader, file_path: str
    ) -> str:
        """
        Extract text content from all PDF pages.

        Args:
            pdf_reader: PyPDF2 reader instance
            file_path: Path to PDF file (for error reporting)

        Returns:
            Extracted text content

        Raises:
            ParseError: If content extraction fails
        """
        try:
            content_parts = []
            total_pages = len(pdf_reader.pages)

            self.logger.debug(f"Extracting content from {total_pages} pages")

            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    # Extract text from page
                    page_text = page.extract_text()

                    if page_text and page_text.strip():
                        content_parts.append(page_text.strip())
                        self.logger.debug(
                            f"Extracted {len(page_text)} chars from page {page_num}"
                        )
                    else:
                        self.logger.warning(
                            f"No text found on page {page_num}"
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Error extracting page {page_num}: {e}"
                    )
                    # Continue with other pages
                    continue

            if not content_parts:
                raise ParseError(
                    "No text content could be extracted from PDF",
                    file_path=file_path,
                )

            # Join all content with page breaks
            full_content = "\n\n".join(content_parts)

            self.logger.info(
                f"Extracted {len(full_content)} characters from PDF"
            )
            return full_content

        except Exception as e:
            if isinstance(e, ParseError):
                raise
            raise ParseError(
                "Failed to extract content from PDF",
                file_path=file_path,
                original_error=e,
            )

    def _extract_metadata(
        self, pdf_reader: PyPDF2.PdfReader, file_path: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from PDF document.

        Args:
            pdf_reader: PyPDF2 reader instance
            file_path: Path to PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        metadata = {
            "file_type": "pdf",
            "total_pages": len(pdf_reader.pages),
            "file_size": os.path.getsize(file_path),
            "parser": self.get_parser_name(),
        }

        # Extract document info if available
        try:
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata

                # Extract common metadata fields
                if doc_info.title:
                    metadata["title"] = str(doc_info.title).strip()

                if doc_info.author:
                    metadata["author"] = str(doc_info.author).strip()

                if doc_info.subject:
                    metadata["subject"] = str(doc_info.subject).strip()

                if doc_info.creator:
                    metadata["creator"] = str(doc_info.creator).strip()

                if doc_info.producer:
                    metadata["producer"] = str(doc_info.producer).strip()

                # Creation and modification dates
                if (
                    hasattr(doc_info, "creation_date")
                    and doc_info.creation_date
                ):
                    metadata["creation_date"] = str(doc_info.creation_date)

                if (
                    hasattr(doc_info, "modification_date")
                    and doc_info.modification_date
                ):
                    metadata["modification_date"] = str(
                        doc_info.modification_date
                    )

        except Exception as e:
            self.logger.warning(f"Could not extract PDF metadata: {e}")
            # Continue without metadata - not critical

        return metadata

    def _handle_encrypted_pdf(
        self, pdf_reader: PyPDF2.PdfReader, file_path: str
    ) -> ParseResult:
        """
        Handle password-protected PDF documents.

        Args:
            pdf_reader: PyPDF2 reader instance
            file_path: Path to PDF file

        Returns:
            ParseResult with limited content

        Raises:
            ParseError: If PDF cannot be decrypted
        """
        self.logger.warning(f"PDF is password-protected: {file_path}")

        # Try common passwords
        common_passwords = ["", "password", "123456", "admin"]

        for password in common_passwords:
            try:
                if pdf_reader.decrypt(password):
                    self.logger.info(
                        f"Successfully decrypted PDF with password: {password or '(empty)'}"
                    )

                    content = self._extract_content(pdf_reader, file_path)
                    metadata = self._extract_metadata(pdf_reader, file_path)
                    metadata["was_encrypted"] = True
                    metadata["decryption_password"] = password or "(empty)"

                    return ParseResult(content=content, metadata=metadata)

            except Exception as e:
                self.logger.debug(f"Password '{password}' failed: {e}")
                continue

        # Could not decrypt - create minimal result
        metadata = {
            "file_type": "pdf",
            "total_pages": len(pdf_reader.pages)
            if hasattr(pdf_reader, "pages")
            else 0,
            "file_size": os.path.getsize(file_path),
            "parser": self.get_parser_name(),
            "is_encrypted": True,
            "title": "[Password Protected PDF]",
        }

        raise ParseError(
            "PDF is password-protected and could not be decrypted",
            file_path=file_path,
        )
