#!/usr/bin/env python3
"""
Documentation and Prompts MCP Server
Intelligent documentation indexing, search, and prompt management for agents
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re
import yaml
from dataclasses import dataclass, asdict

from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ReadResourceResult,
    )

try:
    from mcp import types
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions


    HAS_MCP = True
except ImportError:
    HAS_MCP = False


    # Fallback for development without MCP
    class types:
        @staticmethod
        def Tool(**kwargs):
            return kwargs

        @staticmethod
        def TextContent(**kwargs):
            return kwargs


    class Server:
        def __init__(self, name: str, version: str):
            pass

        def list_tools(self):
            return lambda func: func

        def call_tool(self):
            return lambda func: func


    class NotificationOptions:
        pass


    class InitializationOptions:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docs-prompts-mcp-server")
# Configure logging

app = Server("docs-prompts-server")

@dataclass
class DocumentInfo:
    path: str
    title: str
    content: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    last_modified: float
    file_hash: str
    doc_type: str
    links: List[str]
    code_blocks: List[Dict[str, str]]

@dataclass
class PromptInfo:
    id: str
    name: str
    description: str
    category: str
    template: str
    variables: List[str]
    usage_count: int
    created_at: float
    modified_at: float
    tags: List[str]
    version: str



class DocumentationPromptsServer:
    # Class variable to track if GUI has been launched to prevent multiple instances
    _gui_launched = False

    def __init__(self, project_root: str, config_path: Optional[str] = None):
        self.server = Server("docs-prompts-server", "1.0.0")
        self.project_root = Path(project_root)
        # Look for config file relative to the server module location
        if config_path is None:
            # docs-prompts-server/src -> docs-prompts-server
            server_dir = Path(__file__).parent.parent
            config_path = server_dir / "config" / "server_config.yaml"  
        self.config_path = Path(config_path)
        self.db_path = self.project_root / ".docs_prompts_index.db"
        self.prompts_dir = Path(server_dir / "prompts")
        self.config = self._load_config()
        self._init_database()
        self._ensure_prompts_structure()
        # Start GUI in a separate thread after all initialization is complete
        # Only launch GUI once per process to prevent multiple instances
        if not DocumentationPromptsServer._gui_launched:
            gui_thread = threading.Thread(target=self._launch_gui, daemon=True)
            gui_thread.start()
            DocumentationPromptsServer._gui_launched = True

    def _launch_gui(self):
        # Launch GUI in a separate daemon thread to avoid blocking the main server process
        logger.info("Launching GUI...")
        from docs_db_viewer import DocsPromptsViewer, DocsPromptsGUI
        viewer = DocsPromptsViewer(".docs_prompts_index.db")
        gui = DocsPromptsGUI(viewer, server=self)
        gui.run()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            "documentation_paths": [
                "**/*.md",
                "**/*.rst", 
                "**/*.txt",
                "**/*.yaml",
                "**/*.yml",
                "**/*.json",
                "docs/",
                "documentation/",
                ".spec-workflow/",
                "README.md",
                "API.md",
                "ARCHITECTURE.md",
                "CONTRIBUTING.md",
                "CHANGELOG.md"
            ],
            "file_patterns": ["*.md", "*.rst", "*.txt", "*.yaml", "*.yml", "*.json"],
            "exclude_patterns": [
                "node_modules/", ".git/", "__pycache__/", "*.pyc",
                ".env*", "venv/", ".venv/", "dist/", "build/",
                ".pytest_cache/", "coverage/", "**/.*"
            ],
            "max_file_size_mb": 10,
            "architecture_keywords": [
                "architecture", "design", "pattern", "microservice", "api",
                "endpoint", "service", "component", "module", "database",
                "schema", "model", "workflow", "deployment", "infrastructure",
                "system", "integration"
            ],
            "prompt_categories": [
                "code-quality", "architecture", "documentation", "testing",
                "refactoring", "api", "security", "custom"
            ],
            "path_resolution": {
                "enforce_project_root_relative": True,
                "normalize_absolute_paths": True,
                "allow_absolute_paths": False
            }
        }

        if self.config_path.exists():
            logger.info(f"Loading config from {self.config_path}")
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config from {self.config_path}: {e}")

        # Validate and normalize documentation paths to ensure they're project-root relative
        self._validate_and_normalize_paths(default_config)

        return default_config

    def _validate_and_normalize_paths(self, config: Dict[str, Any]):
        """Validate and normalize documentation paths to ensure they're project-root relative"""
        path_resolution_config = config.get("path_resolution", {})
        enforce_relative = path_resolution_config.get("enforce_project_root_relative", True)
        normalize_absolute = path_resolution_config.get("normalize_absolute_paths", True)
        allow_absolute = path_resolution_config.get("allow_absolute_paths", False)

        if not enforce_relative:
            logger.warning("Path resolution enforcement is disabled - paths may not be project-root relative")
            return

        documentation_paths = config.get("documentation_paths", [])
        normalized_paths = []

        for path_str in documentation_paths:
            path_obj = Path(path_str)

            # Check if path is absolute
            if path_obj.is_absolute():
                if not allow_absolute:
                    if normalize_absolute:
                        # Try to make it relative to project root
                        try:
                            relative_path = path_obj.relative_to(self.project_root)
                            logger.info(f"Normalized absolute path '{path_str}' to relative path '{relative_path}'")
                            normalized_paths.append(str(relative_path))
                        except ValueError:
                            # Path is not within project root
                            logger.error(f"Absolute path '{path_str}' is not within project root '{self.project_root}' and absolute paths are not allowed")
                            raise ValueError(f"Documentation path '{path_str}' must be relative to project root or within project root directory")
                    else:
                        logger.error(f"Absolute documentation paths are not allowed: '{path_str}'")
                        raise ValueError(f"Documentation path '{path_str}' must be relative to project root")
                else:
                    # Absolute paths are allowed
                    normalized_paths.append(path_str)
            else:
                # Path is already relative - ensure it's valid
                if ".." in path_str:
                    logger.warning(f"Path '{path_str}' contains '..' which may navigate outside project root")
                normalized_paths.append(path_str)

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in normalized_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        config["documentation_paths"] = unique_paths
        logger.info(f"Validated {len(unique_paths)} documentation paths as project-root relative")

    def _init_database(self):
        logger.info(f"Initializing database at {self.db_path}")
        """Initialize SQLite database for documents and prompts"""
        with sqlite3.connect(self.db_path) as conn:
            # Documents tables
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS documents
                         (
                             path
                             TEXT
                             PRIMARY
                             KEY,
                             title
                             TEXT,
                             content
                             TEXT,
                             sections
                             TEXT,
                             metadata
                             TEXT,
                             last_modified
                             REAL,
                             file_hash
                             TEXT,
                             doc_type
                             TEXT,
                             links
                             TEXT,
                             code_blocks
                             TEXT,
                             indexed_at
                             REAL
                         )
                         """)

            conn.execute("""
                         CREATE TABLE IF NOT EXISTS search_index
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             doc_path
                             TEXT,
                             section_title
                             TEXT,
                             content_chunk
                             TEXT,
                             chunk_type
                             TEXT,
                             FOREIGN
                             KEY
                         (
                             doc_path
                         ) REFERENCES documents
                         (
                             path
                         )
                             )
                         """)

            # Prompts tables
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS prompts
                         (
                             id
                             TEXT
                             PRIMARY
                             KEY,
                             name
                             TEXT,
                             description
                             TEXT,
                             category
                             TEXT,
                             template
                             TEXT,
                             variables
                             TEXT,
                             tags
                             TEXT,
                             created_at
                             REAL,
                             updated_at
                             REAL,
                             usage_count
                             INTEGER
                             DEFAULT
                             0,
                             effectiveness_score
                             REAL
                             DEFAULT
                             0.0
                         )
                         """)

            conn.execute("""
                         CREATE TABLE IF NOT EXISTS prompt_usage
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             prompt_id
                             TEXT,
                             used_at
                             REAL,
                             context
                             TEXT,
                             effectiveness
                             INTEGER,
                             FOREIGN
                             KEY
                         (
                             prompt_id
                         ) REFERENCES prompts
                         (
                             id
                         )
                             )
                         """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_search_content ON search_index(content_chunk)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_path ON search_index(doc_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_category ON prompts(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_tags ON prompts(tags)")

    def _ensure_prompts_structure(self):
        logger.info(f"Ensuring prompts directory structure at {self.prompts_dir}")
        """Create prompts directory structure and default prompts"""
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create category directories
        for category in self.config["prompt_categories"]:
            (self.prompts_dir / category).mkdir(exist_ok=True)

        # Create templates directory
        (self.prompts_dir / "templates").mkdir(exist_ok=True)

        # Create default categories.yaml if it doesn't exist
        categories_file = self.prompts_dir / "categories.yaml"
        if not categories_file.exists():
            default_categories = {
                "categories": {
                    "code-quality": {
                        "name": "Code Quality",
                        "description": "Code review, quality assessment, and best practices",
                        "color": "#2196F3"
                    },
                    "architecture": {
                        "name": "Architecture",
                        "description": "System design validation and architectural analysis",
                        "color": "#4CAF50"
                    },
                    "documentation": {
                        "name": "Documentation",
                        "description": "Documentation generation and maintenance",
                        "color": "#FF9800"
                    },
                    "testing": {
                        "name": "Testing",
                        "description": "Test creation, validation, and strategy",
                        "color": "#9C27B0"
                    },
                    "refactoring": {
                        "name": "Refactoring",
                        "description": "Code improvement and optimization",
                        "color": "#F44336"
                    },
                    "api": {
                        "name": "API Design",
                        "description": "API design, validation, and documentation",
                        "color": "#00BCD4"
                    },
                    "security": {
                        "name": "Security",
                        "description": "Security analysis and vulnerability assessment",
                        "color": "#795548"
                    },
                    "custom": {
                        "name": "Custom",
                        "description": "Project-specific custom prompts",
                        "color": "#607D8B"
                    }
                }
            }

            with open(categories_file, 'w') as f:
                yaml.dump(default_categories, f, indent=2)

        # Load default prompts
        self._create_default_prompts()

    def _create_default_prompts(self):
        """Create default prompts if they don't exist"""
        default_prompts = {
            "code_review": {
                "name": "Comprehensive Code Review",
                "description": "Review code for quality, security, and best practices",
                "category": "code-quality",
                "template": """Review the following code against the project's documented standards:
            
                Architecture Guidelines: {architecture_info}
                Coding Standards: {coding_standards}
                Security Requirements: {security_requirements}
            
                Code to Review:
                {code_content}
            
                Please analyze for:
                1. Adherence to documented architecture patterns
                2. Code quality and maintainability  
                3. Security vulnerabilities
                4. Performance considerations
                5. Documentation completeness
                6. Test coverage adequacy
            
                Provide specific recommendations for improvements.""",
                                "variables": ["architecture_info", "coding_standards", "security_requirements", "code_content"],
                                "tags": ["review", "quality", "security", "best-practices"]
                            },

                            "api_documentation": {
                                "name": "API Documentation Generator",
                                "description": "Generate comprehensive API documentation",
                                "category": "documentation",
                                "template": """Generate API documentation based on the following:
            
                Existing API Patterns: {existing_api_patterns}
                Architecture Style: {architecture_style}
                Authentication Method: {auth_method}
            
                Code/Endpoints to Document:
                {api_code}
            
                Please include:
                - Clear endpoint descriptions
                - Request/response schemas with examples
                - Error handling and status codes
                - Authentication requirements
                - Rate limiting information
                - Usage examples in multiple languages
                - Integration guidelines""",
                                "variables": ["existing_api_patterns", "architecture_style", "auth_method", "api_code"],
                                "tags": ["api", "documentation", "openapi", "endpoints"]
                            },

                            "architecture_review": {
                                "name": "Architecture Compliance Check",
                                "description": "Validate implementation against architecture docs",
                                "category": "architecture",
                                "template": """Validate the following implementation against documented architecture:
            
                Architecture Documentation: {architecture_docs}
                Design Patterns: {design_patterns}
                Integration Guidelines: {integration_guidelines}
                Scalability Requirements: {scalability_requirements}
            
                Implementation to Review:
                {implementation_code}
            
                Please verify:
                1. Compliance with documented patterns
                2. Proper separation of concerns
                3. Integration point correctness
                4. Scalability and performance considerations
                5. Error handling strategy
                6. Monitoring and observability
                7. Security architecture adherence""",
                                "variables": ["architecture_docs", "design_patterns", "integration_guidelines",
                                              "scalability_requirements", "implementation_code"],
                                "tags": ["architecture", "validation", "patterns", "scalability"]
                            },

                            "security_analysis": {
                                "name": "Security Vulnerability Assessment",
                                "description": "Comprehensive security analysis of code",
                                "category": "security",
                                "template": """Perform a security analysis based on documented security requirements:
            
                Security Guidelines: {security_guidelines}
                Threat Model: {threat_model}
                Compliance Requirements: {compliance_requirements}
            
                Code to Analyze:
                {code_content}
            
                Analyze for:
                1. Input validation and sanitization
                2. Authentication and authorization
                3. Data encryption and protection
                4. SQL injection vulnerabilities
                5. XSS and CSRF protection
                6. Secure communication protocols
                7. Logging and monitoring for security events
                8. Compliance with documented security standards
            
                Provide risk assessment and mitigation strategies.""",
                                "variables": ["security_guidelines", "threat_model", "compliance_requirements", "code_content"],
                                "tags": ["security", "vulnerability", "compliance", "risk-assessment"]
                            },

                            "test_generation": {
                                "name": "Test Strategy and Generation",
                                "description": "Generate comprehensive test strategies and test code",
                                "category": "testing",
                                "template": """Generate test strategy and test code based on:
            
                Testing Guidelines: {testing_guidelines}
                Code Coverage Requirements: {coverage_requirements}
                Testing Framework: {testing_framework}
            
                Code to Test:
                {code_content}
            
                Please provide:
                1. Test strategy and approach
                2. Unit test cases with assertions
                3. Integration test scenarios
                4. Edge cases and error conditions
                5. Performance test considerations
                6. Mock and fixture requirements
                7. Test data setup and teardown
                8. Coverage goals and metrics""",
                                "variables": ["testing_guidelines", "coverage_requirements", "testing_framework", "code_content"],
                                "tags": ["testing", "unit-tests", "coverage", "test-strategy"]
                            },

                            "refactoring_analysis": {
                                "name": "Code Refactoring Recommendations",
                                "description": "Analyze code for refactoring opportunities",
                                "category": "refactoring",
                                "template": """Analyze the following code for refactoring opportunities:
            
                Code Quality Guidelines: {quality_guidelines}
                Design Patterns: {design_patterns}
                Performance Requirements: {performance_requirements}
            
                Code to Refactor:
                {code_content}
            
                Please identify:
                1. Code smells and anti-patterns
                2. Duplicate code elimination opportunities
                3. Method and class extraction possibilities
                4. Performance optimization areas
                5. Design pattern application opportunities
                6. Dependency injection improvements
                7. Error handling enhancements
                8. Documentation and naming improvements
            
                Provide specific refactoring steps and expected benefits.""",
                "variables": ["quality_guidelines", "design_patterns", "performance_requirements", "code_content"],
                "tags": ["refactoring", "optimization", "code-quality", "patterns"]
            }
        }

        # Store default prompts in database
        for prompt_id, prompt_data in default_prompts.items():
            self._store_prompt(prompt_id, prompt_data)

    def _store_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]):
        """Store a prompt in the database"""
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prompts 
                (id, name, description, category, template, variables, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt_id,
                prompt_data["name"],
                prompt_data["description"],
                prompt_data["category"],
                prompt_data["template"],
                json.dumps(prompt_data.get("variables", [])),
                json.dumps(prompt_data.get("tags", [])),
                current_time,
                current_time
            ))

    # Documentation methods (similar to previous implementation)
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

    def _should_index_file(self, file_path: Path) -> bool:
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
                logger.debug(f"Skipping {file_path}: too large "
                             f"({size_mb:.1f}MB)")
                return False

            # Secondary check: minimal exclude patterns for edge cases
            # within allowed directories. Since glob patterns already
            # restrict to allowed directories, this is mainly for
            # hidden files, temp files, etc. within those directories
            for pattern in self.config["exclude_patterns"]:
                try:
                    if file_path.match(pattern):
                        logger.debug(f"Excluding {file_path}: "
                                     f"matches '{pattern}'")
                        return False
                except ValueError:
                    # If pattern is invalid, fall back to string check
                    if pattern.replace("*", "") in str(file_path):
                        logger.debug(f"Excluding {file_path}: "
                                     f"contains '{pattern}'")
                        return False

            # Tertiary check: validate file type matches allowed patterns
            # This is validation since directories are pre-filtered
            allowed_extensions = {'.md', '.rst', '.txt',
                                  '.yaml', '.yml', '.json'}
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

    async def index_document(self, file_path: Path) -> Optional[DocumentInfo]:
        """Index a single document"""
        try:
            logger.debug(f"Indexing document: {file_path}")
            logger.debug(f"  type: {type(file_path)}, "
                         f"is_absolute: {file_path.is_absolute()}")
            logger.debug(f"Project root: {self.project_root}")
            logger.debug(f"  type: {type(self.project_root)}, "
                         f"is_absolute: {self.project_root.is_absolute()}")
            if not self._should_index_file(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            file_hash = hashlib.md5(content.encode()).hexdigest()
            last_modified = file_path.stat().st_mtime

            # Check if already indexed and unchanged
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT file_hash FROM documents WHERE path = ?",
                    (str(file_path),)
                )
                result = cursor.fetchone()
                if result and result[0] == file_hash:
                    return None

            # Extract metadata
            title, sections, links, code_blocks = "", [], [], []
            doc_type = file_path.suffix.lower()

            if doc_type in ['.md', '.markdown']:
                title, sections, links, code_blocks = self._extract_markdown_metadata(content)
            elif doc_type in ['.yaml', '.yml']:
                try:
                    yaml_data = yaml.safe_load(content)
                    title = str(yaml_data.get('title', file_path.name))
                    sections = [{"title": "YAML Content", "content": content, "level": 1}]
                except yaml.YAMLError:
                    title = file_path.name
                    sections = [{"title": "Content", "content": content, "level": 1}]
            else:
                title = file_path.name
                sections = [{"title": "Content", "content": content, "level": 1}]

            if not title:
                title = file_path.stem

            metadata = {
                "file_type": doc_type,
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
                doc_type=doc_type,
                links=links,
                code_blocks=code_blocks
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO documents 
                    (path, title, content, sections, metadata, last_modified, file_hash, doc_type, links, code_blocks, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_info.path, doc_info.title, doc_info.content,
                    json.dumps(doc_info.sections), json.dumps(doc_info.metadata),
                    doc_info.last_modified, doc_info.file_hash, doc_info.doc_type,
                    json.dumps(doc_info.links), json.dumps(doc_info.code_blocks),
                    time.time()
                ))

                # Clear old search index entries
                conn.execute("DELETE FROM search_index WHERE doc_path = ?", (doc_info.path,))

                # Add to search index
                for section in sections:
                    conn.execute("""
                                 INSERT INTO search_index (doc_path, section_title, content_chunk, chunk_type)
                                 VALUES (?, ?, ?, ?)
                                 """, (doc_info.path, section["title"], section["content"], "section"))

                for code_block in code_blocks:
                    conn.execute("""
                                 INSERT INTO search_index (doc_path, section_title, content_chunk, chunk_type)
                                 VALUES (?, ?, ?, ?)
                                 """, (doc_info.path, f"Code ({code_block['language']})",
                                       code_block["content"], "code"))

            logger.info(f"Indexed document: {file_path}")
            return doc_info

        except Exception as e:
            logger.error(f"Error indexing document {file_path}: {e}")
            return None

    async def index_all_documents(self) -> Dict[str, Any]:
        """Index all documents using inclusion-only approach.

        Uses directory-specific glob patterns from documentation_paths
        to scan only explicitly allowed directories from project root.
        The _should_index_file method provides final validation for
        file types and edge cases within those directories.
        """
        indexed_count = 0
        error_count = 0

        logger.info(f"Starting inclusion-only indexing of "
                     f"{len(self.config['documentation_paths'])} patterns")

        for doc_path in self.config["documentation_paths"]:
            logger.debug(f"Scanning pattern: {doc_path}")
            # Use glob to find all matching files from project root
            # This already restricts to allowed directories
            try:
                matches = list(self.project_root.glob(doc_path))
                logger.debug(f"Pattern '{doc_path}' matched "
                             f"{len(matches)} files")

                for file_path in matches:
                    if file_path.is_file():
                        result = await self.index_document(file_path)
                        if result:
                            indexed_count += 1
                        elif self._should_index_file(file_path):
                            error_count += 1
            except Exception as e:
                logger.error(f"Error processing pattern '{doc_path}': {e}")
                error_count += 1

        logger.info(f"Inclusion-only indexing complete: "
                    f"{indexed_count} indexed, {error_count} errors")
        return {
            "indexed_count": indexed_count,
            "error_count": error_count,
            "total_documents": self.get_document_count()
        }

    def search_documents(self, query: str, doc_type: Optional[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using text matching"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                  SELECT DISTINCT d.path, \
                                  d.title, \
                                  d.doc_type, \
                                  d.metadata,
                                  s.section_title, \
                                  s.content_chunk, \
                                  s.chunk_type
                  FROM documents d
                           JOIN search_index s ON d.path = s.doc_path
                  WHERE (s.content_chunk LIKE ? OR d.title LIKE ?)
                  """
            params = [f"%{query}%", f"%{query}%"]

            if doc_type:
                sql += " AND d.doc_type = ?"
                params.append(doc_type)

            sql += (" ORDER BY (CASE WHEN d.title LIKE ? THEN 1 ELSE 2 END), "
                     "d.title LIMIT ?")
            params.extend([f"%{query}%", limit])

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                results.append({
                    "path": row[0],
                    "title": row[1],
                    "doc_type": row[2],
                    "metadata": json.loads(row[3]),
                    "section_title": row[4],
                    "content_snippet": (row[5][:200] + "..." if len(row[5]) > 200
                                       else row[5]),
                    "chunk_type": row[6]
                })

            return results

    def get_architecture_info(self) -> Dict[str, Any]:
        """Extract architecture-related information"""
        arch_keywords = self.config["architecture_keywords"]
        results = []

        for keyword in arch_keywords:
            search_results = self.search_documents(keyword, limit=3)
            results.extend(search_results)

        # Remove duplicates
        seen = set()
        unique_results = []
        for result in results:
            if result["path"] not in seen:
                seen.add(result["path"])
                unique_results.append(result)

        return {
            "architecture_documents": unique_results,
            "total_count": len(unique_results)
        }

    def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]

    # Prompt management methods
    def search_prompts(self, query: str, category: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Search prompts by keyword or category"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                  SELECT id, name, description, category, tags, usage_count, effectiveness_score
                  FROM prompts
                  WHERE (name LIKE ? OR description LIKE ? OR tags LIKE ?) \
                  """
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]

            if category:
                sql += " AND category = ?"
                params.append(category)

            sql += " ORDER BY usage_count DESC, effectiveness_score DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            results = []

            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "tags": json.loads(row[4]),
                    "usage_count": row[5],
                    "effectiveness_score": row[6]
                })

            return results

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                                  SELECT id,
                                         name,
                                         description,
                                         category,
                                         template,
                                         variables,
                                         tags,
                                         created_at,
                                         updated_at,
                                         usage_count,
                                         effectiveness_score
                                  FROM prompts
                                  WHERE id = ?
                                  """, (prompt_id,))

            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "description": result[2],
                    "category": result[3],
                    "template": result[4],
                    "variables": json.loads(result[5]),
                    "tags": json.loads(result[6]),
                    "created_at": result[7],
                    "updated_at": result[8],
                    "usage_count": result[9],
                    "effectiveness_score": result[10]
                }
            return None

    def suggest_prompts(self, context: Optional[str] = None
                        ) -> List[Dict[str, Any]]:
        """Suggest prompts based on context"""
        # Simple implementation - can be enhanced with ML
        suggestions = []

        if context:
            # Analyze context for keywords
            context_lower = context.lower()

            # Map keywords to categories
            keyword_categories = {
                "review": ["code-quality"],
                "test": ["testing"],
                "api": ["api", "documentation"],
                "security": ["security"],
                "refactor": ["refactoring"],
                "architecture": ["architecture"],
                "document": ["documentation"]
            }

            relevant_categories = set()
            for keyword, categories in keyword_categories.items():
                if keyword in context_lower:
                    relevant_categories.update(categories)

            if relevant_categories:
                for category in relevant_categories:
                    category_prompts = self.get_prompts_by_category(category, limit=2)
                    suggestions.extend(category_prompts)

        # If no context-specific suggestions, return popular prompts
        if not suggestions:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                                      SELECT id, name, description, category, usage_count, effectiveness_score
                                      FROM prompts
                                      ORDER BY usage_count DESC, effectiveness_score DESC LIMIT 5
                                      """)

                for row in cursor.fetchall():
                    suggestions.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "category": row[3],
                        "usage_count": row[4],
                        "effectiveness_score": row[5]
                    })

        return suggestions

    def get_prompts_by_category(self, category: str,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get prompts by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                                  SELECT id, name, description, tags, usage_count, effectiveness_score
                                  FROM prompts
                                  WHERE category = ?
                                  ORDER BY usage_count DESC, effectiveness_score DESC LIMIT ?
                                  """, (category, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": category,
                    "tags": json.loads(row[3]),
                    "usage_count": row[4],
                    "effectiveness_score": row[5]
                })

            return results

    def create_custom_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Create a new custom prompt"""
        prompt_id = prompt_data.get("id", f"custom_{int(time.time())}")
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO prompts
                (id, name, description, category, template, variables, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt_id,
                prompt_data["name"],
                prompt_data["description"],
                prompt_data.get("category", "custom"),
                prompt_data["template"],
                json.dumps(prompt_data.get("variables", [])),
                json.dumps(prompt_data.get("tags", [])),
                current_time,
                current_time
            ))

        return prompt_id

    def record_prompt_usage(self, prompt_id: str, context: str = "",
                             effectiveness: int = 5):
        """Record prompt usage for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            # Record usage
            conn.execute("""
                         INSERT INTO prompt_usage (prompt_id, used_at, context, effectiveness)
                         VALUES (?, ?, ?, ?)
                         """, (prompt_id, time.time(), context, effectiveness))

            # Update prompt statistics
            conn.execute("""
                         UPDATE prompts
                         SET usage_count         = usage_count + 1,
                             effectiveness_score = (SELECT AVG(effectiveness)
                                                    FROM prompt_usage
                                                    WHERE prompt_id = ?)
                         WHERE id = ?
                         """, (prompt_id, prompt_id))


@app.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available documentation and prompt resources"""
    return [
        # Documentation resources
        Resource(
            uri="docs://index",
            name="Documentation Index",
            description="Complete index of all documented files and metadata",
            mimeType="application/json"
        ),
        Resource(
            uri="docs://architecture",
            name="Architecture Information",
            description="Extracted architecture patterns and design information",
            mimeType="application/json"
        ),
        Resource(
            uri="docs://statistics",
            name="Documentation Statistics",
            description="Statistics about indexed documentation",
            mimeType="application/json"
        ),

        # Prompt resources
        Resource(
            uri="prompts://library",
            name="Prompt Library",
            description="Complete library of available prompts",
            mimeType="application/json"
        ),
        Resource(
            uri="prompts://categories",
            name="Prompt Categories",
            description="Available prompt categories and organization",
            mimeType="application/json"
        ),
        Resource(
            uri="prompts://usage-stats",
            name="Prompt Usage Statistics",
            description="Usage statistics and effectiveness metrics",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """Read resource data"""
    if uri == "docs://index":
        with sqlite3.connect(docs_prompts_server.db_path) as conn:
            cursor = conn.execute("""
                                  SELECT path, title, doc_type, metadata, last_modified
                                  FROM documents
                                  ORDER BY title
                                  """)

            docs = []
            for row in cursor.fetchall():
                docs.append({
                    "path": row[0],
                    "title": row[1],
                    "doc_type": row[2],
                    "metadata": json.loads(row[3]),
                    "last_modified": row[4]
                })

        content = TextContent(
            type="text",
            text=json.dumps({"documents": docs, "total_count": len(docs)}, indent=2)
        )
        return ReadResourceResult(contents=[content])

    elif uri == "docs://architecture":
        arch_info = docs_prompts_server.get_architecture_info()
        content = TextContent(
            type="text",
            text=json.dumps(arch_info, indent=2)
        )
        return ReadResourceResult(contents=[content])

    elif uri == "docs://statistics":
        doc_count = docs_prompts_server.get_document_count()
        stats = {
            "total_documents": doc_count,
            "index_file": str(docs_prompts_server.db_path),
            "config_file": str(docs_prompts_server.config_path),
            "documentation_paths": docs_prompts_server.config["documentation_paths"]
        }
        content = TextContent(
            type="text",
            text=json.dumps(stats, indent=2)
        )
        return ReadResourceResult(contents=[content])

    elif uri == "prompts://library":
        with sqlite3.connect(docs_prompts_server.db_path) as conn:
            cursor = conn.execute("""
                                  SELECT id, name, description, category, tags, usage_count, effectiveness_score
                                  FROM prompts
                                  ORDER BY category, name
                                  """)

            prompts = []
            for row in cursor.fetchall():
                prompts.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "tags": json.loads(row[4]),
                    "usage_count": row[5],
                    "effectiveness_score": row[6]
                })

        content = TextContent(
            type="text",
            text=json.dumps({"prompts": prompts, "total_count": len(prompts)}, indent=2)
        )
        return ReadResourceResult(contents=[content])

    elif uri == "prompts://categories":
        categories_file = docs_prompts_server.prompts_dir / "categories.yaml"
        if categories_file.exists():
            with open(categories_file, 'r') as f:
                categories_data = yaml.safe_load(f)
        else:
            categories_data = {"categories": {}}

        content = TextContent(
            type="text",
            text=json.dumps(categories_data, indent=2)
        )
        return ReadResourceResult(contents=[content])

    elif uri == "prompts://usage-stats":
        with sqlite3.connect(docs_prompts_server.db_path) as conn:
            cursor = conn.execute("""
                                  SELECT p.id,
                                         p.name,
                                         p.category,
                                         p.usage_count,
                                         p.effectiveness_score,
                                         COUNT(pu.id)          as total_uses,
                                         AVG(pu.effectiveness) as avg_effectiveness
                                  FROM prompts p
                                           LEFT JOIN prompt_usage pu ON p.id = pu.prompt_id
                                  GROUP BY p.id
                                  ORDER BY p.usage_count DESC
                                  """)

            stats = []
            for row in cursor.fetchall():
                stats.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "usage_count": row[3],
                    "effectiveness_score": row[4],
                    "total_uses": row[5],
                    "avg_effectiveness": row[6] or 0
                })

        content = TextContent(
            type="text",
            text=json.dumps({"usage_statistics": stats}, indent=2)
        )
        return ReadResourceResult(contents=[content])

    else:
        raise ValueError(f"Unknown resource: {uri}")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available documentation and prompt tools"""
    return [
        # Provide a user-friendly alias that matches the project's guidance "Run docs"
        Tool(
            name="search_docs",
            description="Search documentation using keywords or phrases",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords or phrases)"
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by document type (.md, .rst, .yaml, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_architecture_info",
            description="Extract architecture patterns and design information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="index_documentation",
            description="Re-index all documentation files",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force re-indexing of all files",
                        "default": False
                    }
                }
            }
        ),

        # Prompt management tools
        Tool(
            name="search_prompts",
            description="Search prompts by keyword, category, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for prompt name, description, or tags"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by prompt category"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_prompt",
            description="Retrieve a specific prompt by ID with full details",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_id": {
                        "type": "string",
                        "description": "ID of the prompt to retrieve"
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="suggest_prompts",
            description="Get context-aware prompt suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Context description for prompt suggestions (optional)"
                    }
                }
            }
        ),
        Tool(
            name="create_prompt",
            description="Create a new custom prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the prompt"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the prompt does"
                    },
                    "template": {
                        "type": "string",
                        "description": "The prompt template with variables in {variable} format"
                    },
                    "category": {
                        "type": "string",
                        "description": "Prompt category",
                        "default": "custom"
                    },
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of variable names used in the template"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorizing and searching"
                    }
                },
                "required": ["name", "description", "template"]
            }
        ),

        # Integration tools
        Tool(
            name="generate_contextual_prompt",
            description="Generate a prompt based on current documentation context",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task type (e.g., 'code_review', 'documentation', 'architecture_analysis')"
                    },
                    "docs_query": {
                        "type": "string",
                        "description": "Query to find relevant documentation context"
                    }
                },
                "required": ["task", "docs_query"]
            }
        ),
        Tool(
            name="apply_prompt_with_context",
            description="Apply a prompt with documentation context automatically filled",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_id": {
                        "type": "string",
                        "description": "ID of the prompt to apply"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to analyze (code, documentation, etc.)"
                    },
                    "auto_fill_context": {
                        "type": "boolean",
                        "description": "Automatically fill context variables from documentation",
                        "default": True
                    }
                },
                "required": ["prompt_id", "content"]
            }
        )
    ]


@app.call_tool()
async def call_tool(
        name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for documentation and prompts"""
    try:
        if name == "search_docs":
            query = arguments["query"]
            doc_type = arguments.get("doc_type")
            limit = arguments.get("limit", 10)

            results = docs_prompts_server.search_documents(query, doc_type, limit)

            response_text = f"Documentation Search Results for '{query}':\n\n"

            if results:
                for i, result in enumerate(results, 1):
                    response_text += f"{i}. **{result['title']}** ({result['doc_type']})\n"
                    response_text += f"   Path: {result['path']}\n"
                    response_text += f"   Section: {result['section_title']}\n"
                    response_text += f"   Content: {result['content_snippet']}\n\n"
            else:
                response_text += f"No results found for '{query}'"

            return [TextContent(type="text", text=response_text)]

        elif name == "get_architecture_info":
            arch_info = docs_prompts_server.get_architecture_info()

            response_text = "Architecture Documentation Summary:\n\n"

            if arch_info["architecture_documents"]:
                for doc in arch_info["architecture_documents"]:
                    response_text += f"📋 **{doc['title']}**\n"
                    response_text += f"   Section: {doc['section_title']}\n"
                    response_text += f"   Content: {doc['content_snippet']}\n\n"
            else:
                response_text += "No architecture documentation found."

            return [TextContent(type="text", text=response_text)]

        elif name == "index_documentation":
            force = arguments.get("force", False)

            if force:
                with sqlite3.connect(docs_prompts_server.db_path) as conn:
                    conn.execute("DELETE FROM documents")
                    conn.execute("DELETE FROM search_index")

            result = await docs_prompts_server.index_all_documents()

            response_text = f"Documentation Indexing Results:\n\n"
            response_text += f"✅ Indexed documents: {result['indexed_count']}\n"
            response_text += f"❌ Errors: {result['error_count']}\n"
            response_text += f"📚 Total documents: {result['total_documents']}\n"

            return [TextContent(type="text", text=response_text)]

        elif name == "search_prompts":
            query = arguments["query"]
            category = arguments.get("category")
            limit = arguments.get("limit", 10)

            results = docs_prompts_server.search_prompts(query, category, limit)

            response_text = f"Prompt Search Results for '{query}':\n\n"

            if results:
                for i, result in enumerate(results, 1):
                    response_text += f"{i}. **{result['name']}** ({result['category']})\n"
                    response_text += f"   ID: {result['id']}\n"
                    response_text += f"   Description: {result['description']}\n"
                    response_text += f"   Usage: {result['usage_count']} times\n"
                    response_text += f"   Tags: {', '.join(result['tags'])}\n\n"
            else:
                response_text += f"No prompts found for '{query}'"

            return [TextContent(type="text", text=response_text)]

        elif name == "get_prompt":
            prompt_id = arguments["prompt_id"]
            prompt = docs_prompts_server.get_prompt(prompt_id)

            if prompt:
                # Record usage
                docs_prompts_server.record_prompt_usage(prompt_id)

                response_text = f"Prompt: **{prompt['name']}**\n\n"
                response_text += f"**Description:** {prompt['description']}\n\n"
                response_text += f"**Category:** {prompt['category']}\n\n"
                response_text += f"**Variables:** {', '.join(prompt['variables'])}\n\n"
                response_text += f"**Template:**\n```\n{prompt['template']}\n```\n\n"
                response_text += f"**Usage Count:** {prompt['usage_count']}\n"
                response_text += f"**Effectiveness Score:** {prompt['effectiveness_score']:.1f}/10\n"
            else:
                response_text = f"Prompt not found: {prompt_id}"

            return [TextContent(type="text", text=response_text)]

        elif name == "suggest_prompts":
            context = arguments.get("context", "")
            suggestions = docs_prompts_server.suggest_prompts(context)

            response_text = "Suggested Prompts:\n\n"

            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    response_text += f"{i}. **{suggestion['name']}** ({suggestion['category']})\n"
                    response_text += f"   ID: {suggestion['id']}\n"
                    response_text += f"   Description: {suggestion['description']}\n"
                    response_text += f"   Usage: {suggestion['usage_count']} times\n\n"
            else:
                response_text += "No suggestions available."

            return [TextContent(type="text", text=response_text)]

        elif name == "create_prompt":
            prompt_data = {
                "name": arguments["name"],
                "description": arguments["description"],
                "template": arguments["template"],
                "category": arguments.get("category", "custom"),
                "variables": arguments.get("variables", []),
                "tags": arguments.get("tags", [])
            }

            prompt_id = docs_prompts_server.create_custom_prompt(prompt_data)

            response_text = f"✅ Created new prompt: **{prompt_data['name']}**\n\n"
            response_text += f"**ID:** {prompt_id}\n"
            response_text += f"**Category:** {prompt_data['category']}\n"
            response_text += f"**Variables:** {', '.join(prompt_data['variables'])}\n"
            response_text += f"**Tags:** {', '.join(prompt_data['tags'])}\n"

            return [TextContent(type="text", text=response_text)]

        elif name == "generate_contextual_prompt":
            task = arguments["task"]
            docs_query = arguments["docs_query"]

            # Search for relevant documentation
            doc_results = docs_prompts_server.search_documents(docs_query, limit=3)

            # Extract context from documentation
            context_info = []
            for doc in doc_results:
                context_info.append({
                    "title": doc["title"],
                    "content": doc["content_snippet"]
                })

            # Generate a contextual prompt
            contextual_template = f"""Based on the following project documentation:

    {chr(10).join([f"**{info['title']}**: {info['content']}" for info in context_info])}

    Please {task} the following content:
    {{content}}

    Consider the documented patterns, guidelines, and architecture when providing your analysis."""

            response_text = f"Generated Contextual Prompt for '{task}':\n\n"
            response_text += f"**Documentation Context Found:** {len(doc_results)} documents\n\n"
            response_text += f"**Generated Prompt Template:**\n```\n{contextual_template}\n```\n"

            return [TextContent(type="text", text=response_text)]

        elif name == "apply_prompt_with_context":
            prompt_id = arguments["prompt_id"]
            content = arguments["content"]
            auto_fill = arguments.get("auto_fill_context", True)

            prompt = docs_prompts_server.get_prompt(prompt_id)
            if not prompt:
                return [TextContent(type="text", text=f"Prompt not found: {prompt_id}")]

            template = prompt["template"]

            if auto_fill:
                # Auto-fill context variables from documentation
                context_mappings = {
                    # Original mappings
                    "architecture_info": "architecture patterns",
                    "coding_standards": "coding standards best practices",
                    "security_requirements": "security requirements guidelines",
                    "api_patterns": "api design patterns",
                    "testing_guidelines": "testing strategy guidelines",
                    
                    # Extended mappings for comprehensive prompt support
                    "architecture_docs": "architecture patterns design",
                    "design_patterns": "design patterns microservice architecture",
                    "integration_guidelines": "integration patterns event-driven",
                    "scalability_requirements": "scalability performance requirements",
                    "implementation_code": "implementation patterns",
                    
                    # Event-driven architecture mappings
                    "event_driven_patterns": "event-driven architecture patterns",
                    "service_independence": "microservice independence patterns",
                    "kafka_patterns": "kafka integration patterns",
                    
                    # Security mappings
                    "security_guidelines": "security authentication",
                    "threat_model": "security threat model",
                    "compliance_requirements": "security compliance",
                    
                    # Testing mappings
                    "coverage_requirements": "test coverage requirements",
                    "testing_framework": "testing framework patterns",
                    
                    # Refactoring mappings
                    "quality_guidelines": "code quality guidelines",
                    "performance_requirements": "performance requirements optimization",
                    
                    # API mappings
                    "existing_api_patterns": "api design patterns",
                    "architecture_style": "api architecture style",
                    "auth_method": "authentication authorization patterns"
                }

                filled_template = template
                for var in prompt["variables"]:
                    if var in context_mappings:
                        search_query = context_mappings[var]
                        doc_results = docs_prompts_server.search_documents(search_query, limit=2)

                        if doc_results:
                            context_text = "\n".join([f"- {doc['content_snippet']}" for doc in doc_results])
                            filled_template = filled_template.replace(f"{{{var}}}", context_text)

                # Fill content variable
                filled_template = filled_template.replace("{content}", content)
                filled_template = filled_template.replace("{code_content}", content)
                filled_template = filled_template.replace("{implementation_code}", content)
                filled_template = filled_template.replace("{api_code}", content)
            else:
                filled_template = template.replace("{content}", content)

            # Record usage
            docs_prompts_server.record_prompt_usage(prompt_id, context=f"Applied to content length: {len(content)}")

            response_text = f"Applied Prompt: **{prompt['name']}**\n\n"
            response_text += f"**Filled Prompt:**\n```\n{filled_template}\n```\n"

            return [TextContent(type="text", text=response_text)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}" )]

# Initialize the server
# Use the project root (parent of mcp-servers directory)
server_project_root = Path(__file__).parent.parent.parent.parent
# docs-prompts-server/src -> ... -> workspace_root
docs_prompts_server = DocumentationPromptsServer(str(server_project_root))


async def main():
    """Main entry point for the documentation and prompts MCP server"""
    try:
        from mcp.server.stdio import stdio_server
        """Main entry point"""
        # Auto-index documentation on startup
        try:
            logger.info("Auto-indexing documentation on startup...")
            await docs_prompts_server.index_all_documents()
        except Exception as e:
            logger.error(f"Error during startup indexing: {e}")

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    except Exception as e:
        logger.error("Error during server startup: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(main())