"""
Document processing for the Documentation and Prompts MCP Server
"""
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import hashlib
import yaml

from models import DocumentInfo

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document parsing and validation"""

    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root

    def should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed using inclusion-only approach.

        With inclusion-only configuration, glob patterns in
        documentation_paths already restrict files to allowed
        directories. This method provides final validation for
        file type and edge cases within allowed directories.
        """
        try:
            # Primary check: file size limits
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config["max_file_size_mb"]:
                logger.debug(f"Skipping {file_path}: too large ({size_mb:.1f}MB)")
                return False

            # Secondary check: minimal exclude patterns for edge cases
            # within allowed directories. Since glob patterns already
            # restrict to allowed directories, this is mainly for
            # hidden files, temp files, etc. within those directories
            for pattern in self.config["exclude_patterns"]:
                try:
                    if file_path.match(pattern):
                        logger.debug(f"Excluding {file_path}: matches '{pattern}'")
                        return False
                except ValueError:
                    # If pattern is invalid, fall back to string check
                    if pattern.replace("*", "") in str(file_path):
                        logger.debug(f"Excluding {file_path}: contains '{pattern}'")
                        return False

            # Tertiary check: validate file type matches allowed patterns
            allowed_extensions = {'.md', '.rst', '.txt', '.yaml', '.yml', '.json'}
            if file_path.suffix.lower() in allowed_extensions:
                file_allowed = True
            else:
                file_allowed = False

            if not file_allowed:
                logger.debug(f"Skipping {file_path}: type not allowed")
                return False

            # File passed all inclusion-only validation checks
            logger.debug(f"Including {file_path}: validation passed")
            return True

        except OSError as e:
            logger.debug(f"Skipping {file_path}: access error - {e}")
            return False

    def process_document(self, file_path: Path) -> Optional[DocumentInfo]:
        """Process a single document and extract metadata"""
        try:
            logger.debug(f"Processing document: {file_path}")

            if not self.should_index_file(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            file_hash = hashlib.md5(content.encode()).hexdigest()
            last_modified = file_path.stat().st_mtime

            # Extract metadata based on file type
            title, sections, links, code_blocks = self._extract_metadata(content, file_path)

            if not title:
                title = file_path.stem

            metadata = {
                "file_type": file_path.suffix.lower(),
                "size_bytes": len(content),
                "line_count": len(content.split('\n')),
                "relative_path": str(file_path.relative_to(self.project_root))
            }

            doc_info = DocumentInfo(
                path=str(file_path),
                title=title,
                content=content,
                sections=sections,
                metadata=metadata,
                last_modified=last_modified,
                file_hash=file_hash,
                doc_type=file_path.suffix.lower(),
                links=links,
                code_blocks=code_blocks
            )

            logger.debug(f"Processed document: {file_path}")
            return doc_info

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return None

    def _extract_metadata(self, content: str, file_path: Path) -> Tuple[str, List[Dict], List[str], List[Dict]]:
        """Extract metadata from document content"""
        doc_type = file_path.suffix.lower()

        if doc_type in ['.md', '.markdown']:
            return self._extract_markdown_metadata(content)
        elif doc_type in ['.yaml', '.yml']:
            return self._extract_yaml_metadata(content, file_path)
        else:
            # Plain text or other formats
            return self._extract_plain_metadata(content, file_path)

    def _extract_markdown_metadata(self, content: str) -> Tuple[str, List[Dict], List[str], List[Dict]]:
        """Extract metadata from markdown content"""
        lines = content.split('\n')
        title = ""
        sections = []
        links = []
        code_blocks = []
        current_section = None
        current_content = []

        # Extract title (first H1)
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Extract sections, links, and code blocks
        in_code_block = False
        current_code_lang = ""
        current_code_content = []

        for i, line in enumerate(lines):
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    code_blocks.append({
                        "language": current_code_lang,
                        "content": '\n'.join(current_code_content)
                    })
                    current_code_content = []
                    in_code_block = False
                else:
                    current_code_lang = line[3:].strip()
                    in_code_block = True
            elif in_code_block:
                current_code_content.append(line)

            # Headers (sections)
            elif line.startswith('#'):
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip(),
                        "level": len([c for c in current_section if c == '#'])
                    })

                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)

                # Links
                link_matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
                for match in link_matches:
                    links.append(match[1])

        # Add final section
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip(),
                "level": len([c for c in current_section if c == '#'])
            })

        return title, sections, links, code_blocks

    def _extract_yaml_metadata(self, content: str, file_path: Path) -> Tuple[str, List[Dict], List[str], List[Dict]]:
        """Extract metadata from YAML content"""
        try:
            yaml_data = yaml.safe_load(content)
            title = str(yaml_data.get('title', file_path.name))
            sections = [{"title": "YAML Content", "content": content, "level": 1}]
            return title, sections, [], []
        except yaml.YAMLError:
            title = file_path.name
            sections = [{"title": "Content", "content": content, "level": 1}]
            return title, sections, [], []

    def _extract_plain_metadata(self, content: str, file_path: Path) -> Tuple[str, List[Dict], List[str], List[Dict]]:
        """Extract metadata from plain text content"""
        title = file_path.stem
        sections = [{"title": "Content", "content": content, "level": 1}]
        return title, sections, [], []