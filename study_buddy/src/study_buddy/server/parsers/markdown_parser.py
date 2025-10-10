"""
Markdown parser implementation for Study Buddy MCP Server.

This module implements Markdown document parsing using the markdown library,
following the Strategy pattern and Clean Architecture Layer 4 principles.
"""

import logging
import os
from typing import Any, Dict

try:
    import markdown
except ImportError:
    raise ImportError(
        "markdown is required for Markdown parsing. Install with: pip install markdown"
    )

from ..models.parse_result import ParseResult

from .base_parser import BaseParser, ParseError


class MarkdownParser(BaseParser):
    """
    Markdown document parser using the markdown library.

    This class implements the BaseParser interface for Markdown documents,
    providing content extraction and HTML conversion capabilities.

    Features:
    - Raw markdown text extraction
    - HTML conversion with extensions support
    - Metadata extraction from frontmatter
    - Table of contents generation
    - Code syntax highlighting support

    Clean Architecture Layer 4: Infrastructure Implementation
    - Implements parser strategy interface
    - No dependencies on business logic
    - Pure document processing logic
    """

    def __init__(self):
        """Initialize Markdown parser with logging."""
        self.logger = logging.getLogger(__name__)

        # Configure markdown processor with useful extensions
        self.md_processor = markdown.Markdown(
            extensions=[
                "toc",  # Table of contents
                "tables",  # Table support
                "codehilite",  # Code highlighting
                "fenced_code",  # Fenced code blocks
                "meta",  # Metadata support
                "nl2br",  # Newline to <br>
                "sane_lists",  # Better list handling
            ],
            extension_configs={
                "codehilite": {
                    "use_pygments": False,  # Don't require Pygments
                    "css_class": "highlight",
                },
                "toc": {"anchorlink": True},
            },
        )

    def supports_file_type(self, file_path: str) -> bool:
        """
        Check if file is a Markdown document.

        Args:
            file_path: Path to file to check

        Returns:
            True if file has .md or .markdown extension
        """
        lower_path = file_path.lower()
        return lower_path.endswith(".md") or lower_path.endswith(".markdown")

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions."""
        return ["md", "markdown"]

    def parse(self, file_path: str) -> ParseResult:
        """
        Parse Markdown document and extract content with metadata.

        Args:
            file_path: Absolute path to Markdown file

        Returns:
            ParseResult with extracted content and metadata

        Raises:
            ParseError: If Markdown parsing fails
            FileNotFoundError: If file doesn't exist
        """
        # Validate file first
        self.validate_file(file_path)

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as file:
                raw_content = file.read()

            if not raw_content.strip():
                raise ParseError("Markdown file is empty", file_path=file_path)

            # Process markdown content
            html_content = self.md_processor.convert(raw_content)

            # Extract metadata
            metadata = self._extract_metadata(
                raw_content, html_content, file_path
            )

            # Reset processor for next use
            self.md_processor.reset()

            # Use raw markdown as primary content, HTML as metadata
            metadata["html_content"] = html_content

            return ParseResult(content=raw_content, metadata=metadata)

        except FileNotFoundError:
            raise
        except ParseError:
            raise
        except UnicodeDecodeError as e:
            raise ParseError(
                "Unable to decode Markdown file (encoding issue)",
                file_path=file_path,
                original_error=e,
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error parsing Markdown {file_path}: {e}"
            )
            raise ParseError(
                "Failed to parse Markdown document",
                file_path=file_path,
                original_error=e,
            )

    def _extract_metadata(
        self, raw_content: str, html_content: str, file_path: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from Markdown document.

        Args:
            raw_content: Original markdown text
            html_content: Converted HTML content
            file_path: Path to markdown file

        Returns:
            Dictionary containing markdown metadata
        """
        metadata = {
            "file_type": "md",
            "file_size": os.path.getsize(file_path),
            "parser": self.get_parser_name(),
            "encoding": "utf-8",
        }

        try:
            # Extract frontmatter metadata if available
            if hasattr(self.md_processor, "Meta") and self.md_processor.Meta:
                for key, value in self.md_processor.Meta.items():
                    # Meta values are always lists in python-markdown
                    if isinstance(value, list) and len(value) == 1:
                        metadata[key] = value[0]
                    else:
                        metadata[key] = value

            # Extract title from first heading
            title = self._extract_title(raw_content)
            if title:
                metadata["title"] = title

            # Count various elements
            metadata["line_count"] = len(raw_content.splitlines())
            metadata["character_count"] = len(raw_content)
            metadata["heading_count"] = raw_content.count("#")

            # Count code blocks
            metadata["code_block_count"] = raw_content.count(
                "```"
            ) // 2 + raw_content.count(  # Fenced code blocks
                "    "
            )  # Indented code blocks (approx)

            # Extract table of contents if available
            if hasattr(self.md_processor, "toc") and self.md_processor.toc:
                metadata["table_of_contents"] = self.md_processor.toc

            # HTML content statistics
            metadata["html_length"] = len(html_content)

        except Exception as e:
            self.logger.warning(
                f"Could not extract all Markdown metadata: {e}"
            )
            # Continue without full metadata - not critical

        return metadata

    def _extract_title(self, content: str) -> str | None:
        """
        Extract title from markdown content.

        Looks for the first H1 heading in the document.

        Args:
            content: Markdown content

        Returns:
            Document title or None if not found
        """
        lines = content.splitlines()

        for line in lines:
            line = line.strip()

            # Check for H1 markdown heading
            if line.startswith("# "):
                return line[2:].strip()

            # Check for underlined H1 heading
            if line and not line.startswith("#"):
                # Look for underline in next line
                idx = lines.index(line.strip())
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and all(c == "=" for c in next_line):
                        return line.strip()

        return None
