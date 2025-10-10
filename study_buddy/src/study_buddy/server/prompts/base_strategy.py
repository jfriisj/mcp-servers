"""
Abstract base strategy for prompt generation.

This module defines the interface for all prompt generation strategies,
following the Strategy pattern (OCP principle).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from study_buddy.server.models.prompt_result import PromptResult


class BasePromptStrategy(ABC):
    """
    Abstract base class for prompt generation strategies.

    This implements the Strategy pattern, allowing different prompt
    generation approaches to be used interchangeably (OCP principle).

    All concrete strategies MUST:
    - Implement generate_prompt() method
    - Return PromptResult with valid structure
    - Handle error cases gracefully
    - Support all detail levels (brief, standard, detailed)
    """

    @abstractmethod
    def generate_prompt(
        self,
        target_ids: List[int],
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        output_format: str = "markdown",
    ) -> PromptResult:
        """
        Generate AI prompt for specified targets and requirements.

        Args:
            target_ids: List of document or chunk IDs to process
            target_type: Type of targets ("document" or "chunk")
            detail_level: Level of detail ("brief", "standard", "detailed")
            focus_areas: Optional list of topics to emphasize
            custom_instructions: Optional user-provided additional instructions
            output_format: Format for AI output ("markdown", "text", "json")

        Returns:
            PromptResult with complete formatted prompt

        Raises:
            ValueError: If parameters are invalid
            NotImplementedError: If subclass doesn't implement method
        """
        pass

    @abstractmethod
    def supports_target_type(self, target_type: str) -> bool:
        """Check if this strategy supports the specified target type."""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get human-readable name of this strategy."""
        pass

    def validate_parameters(
        self, target_ids: List[int], target_type: str, detail_level: str
    ) -> None:
        """
        Validate common parameters for all strategies.

        Args:
            target_ids: List of IDs to validate
            target_type: Type to validate
            detail_level: Detail level to validate

        Raises:
            ValueError: If any parameter is invalid
        """
        if not target_ids:
            raise ValueError("At least one target ID must be provided")

        if not all(isinstance(tid, int) and tid > 0 for tid in target_ids):
            raise ValueError("All target IDs must be positive integers")

        valid_types = ["document", "chunk"]
        if target_type not in valid_types:
            raise ValueError(
                f"Invalid target type: {target_type}. Must be one of {valid_types}"
            )

        valid_levels = ["brief", "standard", "detailed"]
        if detail_level not in valid_levels:
            raise ValueError(
                f"Invalid detail level: {detail_level}. Must be one of {valid_levels}"
            )

        if not self.supports_target_type(target_type):
            raise ValueError(
                f"Strategy {self.get_strategy_name()} does not support target type: {target_type}"
            )

    def get_word_count_target(self, detail_level: str) -> Dict[str, int]:
        """
        Get target word counts for different detail levels.

        Args:
            detail_level: The detail level

        Returns:
            Dictionary with min/max word counts
        """
        word_counts = {
            "brief": {"min": 100, "max": 150},
            "standard": {"min": 250, "max": 350},
            "detailed": {"min": 500, "max": 750},
        }
        return word_counts.get(detail_level, word_counts["standard"])

    def format_focus_areas(self, focus_areas: Optional[List[str]]) -> str:
        """
        Format focus areas for inclusion in prompt.

        Args:
            focus_areas: List of areas to focus on

        Returns:
            Formatted string for prompt inclusion
        """
        if not focus_areas:
            return "general content and key concepts"

        if len(focus_areas) == 1:
            return focus_areas[0]
        elif len(focus_areas) == 2:
            return f"{focus_areas[0]} and {focus_areas[1]}"
        else:
            return f"{', '.join(focus_areas[:-1])}, and {focus_areas[-1]}"

    def create_prompt_result(
        self,
        prompt_text: str,
        prompt_type: str,
        detail_level: str,
        target_ids: List[int],
        target_type: str,
        focus_areas: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PromptResult:
        """
        Create PromptResult with standardized structure.

        Args:
            prompt_text: The generated prompt text
            prompt_type: Type of prompt
            detail_level: Detail level
            target_ids: List of target IDs
            target_type: Type of targets
            focus_areas: Focus areas
            metadata: Additional metadata

        Returns:
            PromptResult instance
        """
        return PromptResult(
            prompt_text=prompt_text.strip(),
            prompt_type=prompt_type,
            detail_level=detail_level,
            target_info={
                "type": target_type,
                "ids": target_ids,
                "count": len(target_ids),
            },
            focus_areas=focus_areas or [],
            metadata=metadata or {},
            generated_at=datetime.now(),
        )
