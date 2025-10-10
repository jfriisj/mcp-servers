"""
Study Buddy GUI - Prompt Template System

This package provides the template system for generating AI prompts following
the Strategy pattern for extensibility and maintainability.

Architecture: Clean Architecture Layer 4 (Infrastructure)
Components:
- BasePromptTemplate: Abstract template interface
- Concrete templates: SummarizationTemplate, IndexingTemplate, etc.
- PromptTemplateFactory: Factory for template selection
"""

from .base_template import BasePromptTemplate, TemplateContext
from .summarization_template import SummarizationTemplate
from .indexing_template import IndexingTemplate
from .search_template import SearchTemplate
from .template_factory import PromptTemplateFactory

__all__ = [
    'BasePromptTemplate',
    'TemplateContext', 
    'SummarizationTemplate',
    'IndexingTemplate',
    'SearchTemplate',
    'PromptTemplateFactory'
]