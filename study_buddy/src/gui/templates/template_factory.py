"""
Study Buddy GUI - Prompt Template Factory

Factory class for creating prompt templates following the Factory pattern.
Enables easy extension with new template types while maintaining clean interfaces.

Architecture: Clean Architecture Layer 4 (Infrastructure - Factory)
Pattern: Factory Pattern for template creation
SOLID: Open/Closed (new templates via registration, no modification needed)
"""

from typing import Dict, Type, List
from .base_template import BasePromptTemplate
from .summarization_template import SummarizationTemplate
from .indexing_template import IndexingTemplate
from .search_template import SearchTemplate


class PromptTemplateFactory:
    """
    Factory for creating and managing prompt templates.
    
    Provides a centralized way to access all available prompt templates
    and supports easy extension with new template types through registration.
    
    Follows the Factory pattern to decouple template creation from usage,
    enabling the Open/Closed principle for template extensibility.
    """
    
    def __init__(self):
        """Initialize factory with default templates."""
        self._templates: Dict[str, Type[BasePromptTemplate]] = {}
        self._register_default_templates()
    
    def _register_default_templates(self) -> None:
        """Register all default template types."""
        self.register_template("summarization", SummarizationTemplate)
        self.register_template("indexing", IndexingTemplate)
        self.register_template("search", SearchTemplate)
    
    def register_template(self, template_id: str, template_class: Type[BasePromptTemplate]) -> None:
        """
        Register a new template type with the factory.
        
        Args:
            template_id: Unique identifier for the template
            template_class: Template class that extends BasePromptTemplate
            
        Raises:
            ValueError: If template_id already exists or template_class is invalid
        """
        if template_id in self._templates:
            raise ValueError(f"Template ID '{template_id}' is already registered")
        
        if not issubclass(template_class, BasePromptTemplate):
            raise ValueError(f"Template class must extend BasePromptTemplate")
        
        self._templates[template_id] = template_class
    
    def get_template(self, template_id: str) -> BasePromptTemplate:
        """
        Create and return a template instance by ID.
        
        Args:
            template_id: Identifier for the desired template type
            
        Returns:
            Instance of the requested template
            
        Raises:
            ValueError: If template_id is not registered
        """
        if template_id not in self._templates:
            available = ", ".join(self._templates.keys())
            raise ValueError(f"Unknown template ID '{template_id}'. Available: {available}")
        
        template_class = self._templates[template_id]
        return template_class()
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        Get list of all available templates with metadata.
        
        Returns:
            List of dicts containing template metadata:
            - id: Template identifier
            - name: Human-readable template name  
            - description: Template description
        """
        templates = []
        
        for template_id, template_class in self._templates.items():
            # Create temporary instance to get metadata
            template_instance = template_class()
            
            templates.append({
                "id": template_id,
                "name": template_instance.template_name,
                "description": template_instance.template_description
            })
        
        return templates
    
    def get_template_by_name(self, template_name: str) -> BasePromptTemplate:
        """
        Get template by human-readable name (case-insensitive).
        
        Args:
            template_name: Human-readable template name
            
        Returns:
            Template instance matching the name
            
        Raises:
            ValueError: If no template matches the name
        """
        target_name = template_name.lower().strip()
        
        for template_id, template_class in self._templates.items():
            template_instance = template_class()
            if template_instance.template_name.lower() == target_name:
                return template_instance
        
        available_names = [
            self._templates[tid]().template_name 
            for tid in self._templates
        ]
        raise ValueError(f"No template found with name '{template_name}'. Available: {available_names}")
    
    def has_template(self, template_id: str) -> bool:
        """
        Check if a template ID is registered.
        
        Args:
            template_id: Template identifier to check
            
        Returns:
            True if template exists, False otherwise
        """
        return template_id in self._templates
    
    def unregister_template(self, template_id: str) -> bool:
        """
        Remove a template from the factory.
        
        Args:
            template_id: Template identifier to remove
            
        Returns:
            True if template was removed, False if it didn't exist
        """
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False


# Global factory instance for use throughout the application
template_factory = PromptTemplateFactory()