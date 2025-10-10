"""
Study Buddy GUI - Base Prompt Template

Abstract base class for all prompt templates following the Strategy pattern.
Enables extensible prompt generation for different AI workflows.

Architecture: Clean Architecture Layer 4 (Infrastructure - Strategy Interface)
Pattern: Strategy Pattern for template extensibility
SOLID: Single Responsibility (template generation), Open/Closed (extensible via new templates)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class PromptStyle(Enum):
    """Available prompt styles for AI summaries."""
    BRIEF = "brief"
    STANDARD = "standard" 
    DETAILED = "detailed"


class FocusArea(Enum):
    """Available focus areas for AI analysis."""
    KEY_CONCEPTS = "key_concepts"
    CODE_EXAMPLES = "code_examples"
    DEFINITIONS = "definitions"
    METHODOLOGY = "methodology"
    CONCLUSIONS = "conclusions"
    EXAMPLES = "examples"
    TECHNICAL_DETAILS = "technical_details"
    BEST_PRACTICES = "best_practices"


@dataclass
class TemplateContext:
    """
    Context information for prompt template generation.
    
    Contains all the information needed to generate a complete AI prompt
    from user selections and document metadata.
    """
    # Document information
    document_title: str
    document_id: int
    document_type: str  # "pdf", "docx", "md", etc.
    
    # Chunk information (optional for document-level operations)
    chunk_title: Optional[str] = None
    chunk_id: Optional[int] = None
    chunk_type: Optional[str] = None  # "chapter", "section", etc.
    
    # Style and focus preferences
    style: PromptStyle = PromptStyle.STANDARD
    focus_areas: Optional[List[FocusArea]] = None
    
    # Additional context
    user_instructions: Optional[str] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.focus_areas is None:
            self.focus_areas = [FocusArea.KEY_CONCEPTS]
    
    @property
    def target_description(self) -> str:
        """Get human-readable description of the target (document or chunk)."""
        if self.chunk_title:
            return f'"{self.chunk_title}" from "{self.document_title}"'
        return f'"{self.document_title}"'
    
    @property
    def focus_areas_text(self) -> str:
        """Get comma-separated list of focus areas for template insertion."""
        if not self.focus_areas:
            return "Key Concepts"
        return ", ".join([area.value.replace("_", " ").title() for area in self.focus_areas])


class BasePromptTemplate(ABC):
    """
    Abstract base class for all AI prompt templates.
    
    Implements the Strategy pattern to allow different prompt generation
    strategies for various AI workflows (summarization, indexing, search, etc.).
    
    Responsibilities:
    - Define template interface contract
    - Provide common template utilities
    - Ensure consistent prompt structure
    
    Does NOT:
    - Contain specific template content (delegated to concrete classes)
    - Handle UI interactions (handled by PromptBuilderWidget)
    - Execute AI operations (handled by AI agents via MCP tools)
    """
    
    @property
    @abstractmethod
    def template_name(self) -> str:
        """Human-readable name for this template type."""
        pass
    
    @property
    @abstractmethod
    def template_description(self) -> str:
        """Description of what this template generates."""
        pass
    
    @property
    @abstractmethod
    def required_context(self) -> List[str]:
        """List of required TemplateContext fields for this template."""
        pass
    
    @abstractmethod
    def generate_prompt(self, context: TemplateContext) -> str:
        """
        Generate the complete AI prompt from the provided context.
        
        Args:
            context: TemplateContext with all necessary information
            
        Returns:
            Complete prompt string ready for AI agent execution
            
        Raises:
            ValueError: If required context fields are missing
            TemplateError: If template generation fails
        """
        pass
    
    def validate_context(self, context: TemplateContext) -> None:
        """
        Validate that the context contains all required fields.
        
        Args:
            context: TemplateContext to validate
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check required fields
        for field in self.required_context:
            if not hasattr(context, field):
                raise ValueError(f"Template {self.template_name} requires field: {field}")
            
            value = getattr(context, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Template {self.template_name} requires non-empty field: {field}")
    
    def _format_style_instructions(self, style: PromptStyle) -> str:
        """
        Convert PromptStyle enum to human-readable instructions.
        
        Args:
            style: PromptStyle enum value
            
        Returns:
            Formatted style instructions for AI
        """
        style_instructions = {
            PromptStyle.BRIEF: "Create a brief summary (100-150 words) focusing on the most essential points.",
            PromptStyle.STANDARD: "Create a standard summary (250-350 words) with good coverage of key topics.",
            PromptStyle.DETAILED: "Create a detailed summary (500-750 words) with comprehensive coverage and examples."
        }
        return style_instructions.get(style, style_instructions[PromptStyle.STANDARD])
    
    def _format_focus_instructions(self, focus_areas: List[FocusArea]) -> str:
        """
        Convert focus areas to formatted instructions.
        
        Args:
            focus_areas: List of FocusArea enum values
            
        Returns:
            Formatted focus area instructions for AI
        """
        if not focus_areas:
            return "Focus on the most important aspects of the content."
        
        focus_descriptions = {
            FocusArea.KEY_CONCEPTS: "key concepts and main ideas",
            FocusArea.CODE_EXAMPLES: "code examples and implementation details",
            FocusArea.DEFINITIONS: "important definitions and terminology",
            FocusArea.METHODOLOGY: "methodologies and approaches used",
            FocusArea.CONCLUSIONS: "conclusions and results",
            FocusArea.EXAMPLES: "practical examples and use cases",
            FocusArea.TECHNICAL_DETAILS: "technical details and specifications",
            FocusArea.BEST_PRACTICES: "best practices and recommendations"
        }
        
        focus_list = [focus_descriptions.get(area, area.value) for area in focus_areas]
        
        if len(focus_list) == 1:
            return f"Focus particularly on {focus_list[0]}."
        elif len(focus_list) == 2:
            return f"Focus particularly on {focus_list[0]} and {focus_list[1]}."
        else:
            return f"Focus particularly on {', '.join(focus_list[:-1])}, and {focus_list[-1]}."


class TemplateError(Exception):
    """Exception raised when template generation fails."""
    
    def __init__(self, template_name: str, message: str, context: Optional[TemplateContext] = None):
        self.template_name = template_name
        self.context = context
        super().__init__(f"Template '{template_name}' error: {message}")