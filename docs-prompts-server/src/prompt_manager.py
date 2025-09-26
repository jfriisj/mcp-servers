"""
Prompt management for the Documentation and Prompts MCP Server
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from database import DatabaseManager

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt operations"""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        self.db_manager = db_manager
        self.config = config
        self._ensure_default_prompts()

    def _ensure_default_prompts(self):
        """Ensure default prompts are loaded"""
        # Check if we have any prompts
        all_prompts = self.db_manager.get_all_prompts()
        if not all_prompts:
            self._create_default_prompts()

    def _load_default_prompts_from_yaml(self) -> Dict[str, Dict[str, Any]]:
        """Load default prompts from YAML file"""
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not available, falling back to empty prompts")
            return {}

        # Find the prompts directory relative to this module
        module_dir = Path(__file__).parent
        prompts_dir = module_dir.parent / "prompts"
        yaml_file = prompts_dir / "default_prompts.yaml"

        if not yaml_file.exists():
            logger.warning(f"Default prompts file not found: {yaml_file}")
            return {}

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.error("Invalid YAML structure in default prompts file")
                    return {}
                return data
        except Exception as e:
            logger.error(f"Error loading default prompts from YAML: {e}")
            return {}

    def _create_default_prompts(self):
        """Create default prompts if they don't exist"""
        default_prompts = self._load_default_prompts_from_yaml()

        # Store default prompts in database
        for prompt_data in default_prompts.values():
            self.db_manager.store_prompt(prompt_data)

    def search_prompts(
        self, query: str, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search prompts by keyword or category"""
        return self.db_manager.search_prompts(query, category, limit)

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID"""
        return self.db_manager.get_prompt(prompt_id)

    def suggest_prompts(self, context: Optional[str] = None) -> List[Dict[str, Any]]:
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
                "document": ["documentation"],
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
            suggestions = self.db_manager.get_popular_prompts(limit=5)

        return suggestions

    def get_prompts_by_category(
        self, category: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get prompts by category"""
        return self.db_manager.get_prompts_by_category(category, limit)

    def create_custom_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Create a new custom prompt"""
        prompt_id = prompt_data.get("id", f"custom_{int(__import__('time').time())}")
        self.db_manager.store_prompt(prompt_data)
        return prompt_id

    def record_prompt_usage(
        self, prompt_id: str, context: str = "", effectiveness: int = 5
    ):
        """Record prompt usage for analytics"""
        self.db_manager.record_prompt_usage(prompt_id, context, effectiveness)

    def get_usage_stats(self) -> List[Dict[str, Any]]:
        """Get usage statistics for all prompts"""
        return self.db_manager.get_usage_stats()
