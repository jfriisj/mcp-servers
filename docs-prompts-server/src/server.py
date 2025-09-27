"""
Main facade for the Documentation and Prompts MCP Server
Follows SOLID principles with dependency injection
"""

import logging
import os
from pathlib import Path
from typing import Optional

from config import ConfigurationManager
from database import DatabaseManager
from document_indexer import DocumentIndexer
from prompt_manager import PromptManager
from gui_manager import GUIManager
from mcp_handler import MCPHandler

logger = logging.getLogger(__name__)


class DocumentationPromptsServer:
    """Main facade coordinating all server components"""

    def __init__(self, project_root: Optional[str] = None):
        # Determine project root
        if project_root is None:
            project_root = os.environ.get("DOCS_PROJECT_ROOT", os.getcwd())

        self.project_root = Path(project_root)
        
        # Auto-detect monorepo root if running from server subdirectory
        self.project_root = self._detect_project_root(self.project_root)

        # Initialize components with dependency injection
        self.config_manager = ConfigurationManager(
            config_path=self._get_config_path(), project_root=self.project_root
        )

        self.db_manager = DatabaseManager(self._get_db_path())
        self.document_indexer = DocumentIndexer(
            self.config_manager.config, self.project_root, self.db_manager
        )
        self.prompt_manager = PromptManager(self.db_manager, self.config_manager.config)
        self.gui_manager = GUIManager(self._get_db_path(), self)
        self.mcp_handler = MCPHandler(
            self.document_indexer,
            self.prompt_manager,
            self.db_manager,
            self.config_manager.config,
            self._get_db_path(),
        )

        # Auto-index documents on startup if configured
        indexing_config = self.config_manager.config.get("indexing", {})
        if indexing_config.get("auto_index_on_startup", False):
            logger.info("Auto-indexing documents on startup...")
            try:
                import asyncio

                # Run indexing in background to not block startup
                import threading

                def auto_index():
                    try:
                        result = asyncio.run(self.index_all_documents())
                        logger.info(f"Auto-indexing complete: {result}")
                    except Exception as e:
                        logger.error(f"Auto-indexing failed: {e}")

                threading.Thread(target=auto_index, daemon=True).start()
            except Exception as e:
                logger.error(f"Failed to start auto-indexing: {e}")

        # Launch GUI
        self.gui_manager.launch_gui()

    def _detect_project_root(self, initial_root: Path) -> Path:
        """Auto-detect the correct project root.
        
        If running from a server subdirectory, check if the parent directory
        appears to be the monorepo root and adjust accordingly.
        """
        # Check if parent directory looks like monorepo root
        parent_dir = initial_root.parent
        
        # Indicators that parent is monorepo root
        monorepo_indicators = [
            parent_dir / "README.md",
            parent_dir / ".git",
        ]
        
        # Check if we're in a server subdirectory
        server_indicators = [
            initial_root / "src",
            initial_root / "config",
            initial_root.name in ["docs-prompts-server", "ruff-server",
                                 "coverage-server"]
        ]
        
        # If parent has monorepo indicators and we're in server directory,
        # use parent as project root
        parent_is_monorepo = all(indicator.exists()
                                for indicator in monorepo_indicators)
        in_server_dir = (any(indicator.exists()
                             for indicator in server_indicators[:-1]) or
                         server_indicators[-1])
        
        if parent_is_monorepo and in_server_dir:
            logger.info(f"Detected monorepo root at: {parent_dir}")
            return parent_dir
        
        # Otherwise use the initial root
        return initial_root

    def _get_config_path(self) -> Optional[Path]:
        """Get the configuration file path"""
        # Look for config file relative to the server module location
        server_dir = Path(__file__).parent.parent
        config_path = server_dir / "config" / "server_config.yaml"
        return config_path if config_path.exists() else None

    def _get_db_path(self) -> Path:
        """Get the database file path"""
        server_dir = Path(__file__).parent.parent
        return server_dir / ".docs_prompts_index.db"

    # Delegate methods to appropriate components
    async def index_all_documents(self):
        """Index all documents"""
        return await self.document_indexer.index_all_documents()

    def index_all_documents_sync(self):
        """Index all documents (synchronous version)"""
        return self.document_indexer.index_all_documents_sync()

    def search_documents(self, query: str, doc_type=None, limit=10):
        """Search documents"""
        return self.document_indexer.search_documents(query, doc_type, limit)

    def get_architecture_info(self):
        """Get architecture information"""
        return self.document_indexer.get_architecture_info()

    def get_document_count(self):
        """Get document count"""
        return self.document_indexer.get_document_count()

    def search_prompts(self, query: str, category=None, limit=10):
        """Search prompts"""
        return self.prompt_manager.search_prompts(query, category, limit)

    def get_prompt(self, prompt_id: str):
        """Get a specific prompt"""
        return self.prompt_manager.get_prompt(prompt_id)

    def suggest_prompts(self, context=None):
        """Suggest prompts based on context"""
        return self.prompt_manager.suggest_prompts(context)

    def create_custom_prompt(self, prompt_data):
        """Create a custom prompt"""
        return self.prompt_manager.create_custom_prompt(prompt_data)

    def record_prompt_usage(self, prompt_id: str, context="", effectiveness=5):
        """Record prompt usage"""
        return self.prompt_manager.record_prompt_usage(
            prompt_id, context, effectiveness
        )

    # MCP protocol methods
    def get_resources(self):
        """Get MCP resources"""
        return self.mcp_handler.get_resources()

    def get_tools(self):
        """Get MCP tools"""
        return self.mcp_handler.get_tools()

    def read_resource(self, uri: str):
        """Read MCP resource"""
        return self.mcp_handler.read_resource(uri)

    def call_tool(self, name: str, arguments):
        """Call MCP tool"""
        return self.mcp_handler.call_tool(name, arguments)

    def clear_index(self):
        """Clear all documents and search index"""
        return self.document_indexer.clear_index()

    def get_all_documents(self):
        """Get all indexed documents"""
        return self.db_manager.get_all_documents()
