"""
Prompt generation result model.

This module defines the data structure for AI prompt generation results.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class PromptResult:
    """
    Result of AI prompt generation.
    
    Attributes:
        prompt_text: Complete formatted prompt ready for AI agent
        prompt_type: Type of prompt (summary, analysis, comparison)
        detail_level: Level of detail (brief, standard, detailed)
        target_info: Information about target documents/chunks
        focus_areas: Areas to emphasize in the prompt
        metadata: Additional prompt metadata
        generated_at: Timestamp of generation
    """
    prompt_text: str
    prompt_type: str
    detail_level: str
    target_info: Dict[str, Any]
    focus_areas: List[str]
    metadata: Dict[str, Any]
    generated_at: datetime
    
    def __post_init__(self):
        """Validate prompt result data after initialization."""
        if not self.prompt_text or not self.prompt_text.strip():
            raise ValueError("Prompt text cannot be empty")
        
        valid_types = ["summary", "analysis", "comparison", "extraction"]
        if self.prompt_type not in valid_types:
            raise ValueError(f"Invalid prompt type: {self.prompt_type}. Must be one of {valid_types}")
        
        valid_levels = ["brief", "standard", "detailed"]
        if self.detail_level not in valid_levels:
            raise ValueError(f"Invalid detail level: {self.detail_level}. Must be one of {valid_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt result to dictionary for MCP response."""
        return {
            "prompt_text": self.prompt_text,
            "prompt_type": self.prompt_type,
            "detail_level": self.detail_level,
            "target_info": self.target_info,
            "focus_areas": self.focus_areas,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
            "word_count": len(self.prompt_text.split()),
            "line_count": len(self.prompt_text.split('\n'))
        }
    
    def get_summary_info(self) -> str:
        """Get human-readable summary of what this prompt will do."""
        target_type = self.target_info.get("type", "unknown")
        target_count = len(self.target_info.get("ids", []))
        
        if target_type == "chunk":
            target_desc = f"{target_count} chunk(s)"
        elif target_type == "document":
            target_desc = f"{target_count} document(s)"
        else:
            target_desc = f"{target_count} target(s)"
        
        focus_desc = ", ".join(self.focus_areas) if self.focus_areas else "general content"
        
        return (f"{self.prompt_type.title()} prompt for {target_desc} "
               f"with {self.detail_level} detail level, focusing on: {focus_desc}")