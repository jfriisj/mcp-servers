"""
Prompt generation service.

This module provides the business logic for generating AI prompts,
following Clean Architecture principles with proper dependency injection.
"""

from typing import Dict, List, Optional, Any
from prompts.base_strategy import BasePromptStrategy
from prompts.summary_strategy import SummaryPromptStrategy
from models.prompt_result import PromptResult
from study_buddy.server.repositories.document_repository import DocumentRepository
from study_buddy.server.repositories.chunk_repository import ChunkRepository


class PromptService:
    """
    Service for orchestrating AI prompt generation.
    
    Responsibilities:
    - Validate target existence in database
    - Select appropriate prompt strategy
    - Orchestrate prompt generation process
    - Provide business rule enforcement
    
    Does NOT:
    - Know about MCP protocol details
    - Directly access database (uses repositories)
    - Implement prompt generation logic (delegates to strategies)
    """
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository
    ):
        """
        Initialize prompt service with repository dependencies.
        
        Args:
            document_repo: Repository for document data access
            chunk_repo: Repository for chunk data access
        """
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        
        # Initialize available strategies
        self.strategies: Dict[str, BasePromptStrategy] = {
            "summary": SummaryPromptStrategy()
        }
    
    def generate_prompt(
        self,
        prompt_type: str,
        target_ids: List[int],
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        output_format: str = "markdown"
    ) -> PromptResult:
        """
        Generate AI prompt for specified parameters.
        
        Args:
            prompt_type: Type of prompt to generate ("summary", "analysis", etc.)
            target_ids: List of document or chunk IDs to target
            target_type: Type of targets ("document" or "chunk")
            detail_level: Level of detail ("brief", "standard", "detailed")
            focus_areas: Optional list of areas to emphasize
            custom_instructions: Optional user-provided instructions
            output_format: Output format for AI ("markdown", "text", "json")
            
        Returns:
            PromptResult with complete formatted prompt
            
        Raises:
            ValueError: If parameters are invalid or targets don't exist
            NotImplementedError: If prompt type is not supported
        """
        # Validate prompt type
        if prompt_type not in self.strategies:
            available = ", ".join(self.strategies.keys())
            raise ValueError(f"Unsupported prompt type: {prompt_type}. Available: {available}")
        
        # Validate targets exist in database
        self._validate_targets_exist(target_ids, target_type)
        
        # Get appropriate strategy
        strategy = self.strategies[prompt_type]
        
        # Generate prompt using strategy
        return strategy.generate_prompt(
            target_ids=target_ids,
            target_type=target_type,
            detail_level=detail_level,
            focus_areas=focus_areas,
            custom_instructions=custom_instructions,
            output_format=output_format
        )
    
    def get_available_prompt_types(self) -> List[str]:
        """
        Get list of available prompt types.
        
        Returns:
            List of supported prompt types
        """
        return list(self.strategies.keys())
    
    def get_strategy_info(self, prompt_type: str) -> Dict[str, Any]:
        """
        Get information about a specific prompt strategy.
        
        Args:
            prompt_type: Type of prompt strategy
            
        Returns:
            Dictionary with strategy information
            
        Raises:
            ValueError: If prompt type is not supported
        """
        if prompt_type not in self.strategies:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        strategy = self.strategies[prompt_type]
        return {
            "name": strategy.get_strategy_name(),
            "supports_documents": strategy.supports_target_type("document"),
            "supports_chunks": strategy.supports_target_type("chunk"),
            "detail_levels": ["brief", "standard", "detailed"],
            "output_formats": ["markdown", "text", "json"]
        }
    
    def validate_targets_for_prompt(
        self,
        target_ids: List[int],
        target_type: str,
        prompt_type: str
    ) -> Dict[str, Any]:
        """
        Validate targets and return information about them.
        
        Args:
            target_ids: List of target IDs
            target_type: Type of targets
            prompt_type: Type of prompt being generated
            
        Returns:
            Dictionary with validation results and target info
            
        Raises:
            ValueError: If targets are invalid
        """
        # Check if strategy supports target type
        if prompt_type not in self.strategies:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        strategy = self.strategies[prompt_type]
        if not strategy.supports_target_type(target_type):
            raise ValueError(
                f"Prompt type '{prompt_type}' does not support target type '{target_type}'"
            )
        
        # Validate targets exist
        existing_targets = self._validate_targets_exist(target_ids, target_type)
        
        # Return validation results
        return {
            "valid": True,
            "target_count": len(existing_targets),
            "target_type": target_type,
            "prompt_type": prompt_type,
            "targets": existing_targets,
            "strategy_name": strategy.get_strategy_name()
        }
    
    def _validate_targets_exist(
        self,
        target_ids: List[int],
        target_type: str
    ) -> List[Dict[str, Any]]:
        """
        Validate that all specified targets exist in the database.
        
        Args:
            target_ids: List of target IDs to validate
            target_type: Type of targets ("document" or "chunk")
            
        Returns:
            List of existing target information
            
        Raises:
            ValueError: If any targets don't exist
        """
        existing_targets = []
        missing_targets = []
        
        for target_id in target_ids:
            if target_type == "document":
                target = self.document_repo.get_by_id(target_id)
                if target:
                    existing_targets.append({
                        "id": target.id,
                        "title": target.title,
                        "type": "document",
                        "file_type": target.file_type,
                        "indexed": target.indexed,
                        "word_count": target.total_words
                    })
                else:
                    missing_targets.append(f"document:{target_id}")
            
            elif target_type == "chunk":
                chunk = self.chunk_repo.get_by_id(target_id)
                if chunk:
                    existing_targets.append({
                        "id": chunk.id,
                        "title": chunk.title,
                        "type": "chunk",
                        "chunk_type": chunk.chunk_type,
                        "document_id": chunk.document_id,
                        "word_count": chunk.word_count
                    })
                else:
                    missing_targets.append(f"chunk:{target_id}")
        
        # Raise error if any targets are missing
        if missing_targets:
            missing_str = ", ".join(missing_targets)
            raise ValueError(f"The following targets do not exist: {missing_str}")
        
        return existing_targets
    
    def get_prompt_preview(
        self,
        prompt_type: str,
        target_count: int,
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Get a preview description of what the prompt will generate.
        
        Args:
            prompt_type: Type of prompt
            target_count: Number of targets
            target_type: Type of targets
            detail_level: Detail level
            focus_areas: Focus areas
            
        Returns:
            Human-readable description of the prompt
        """
        if prompt_type not in self.strategies:
            return f"Unknown prompt type: {prompt_type}"
        
        strategy = self.strategies[prompt_type]
        word_counts = strategy.get_word_count_target(detail_level)
        focus_text = strategy.format_focus_areas(focus_areas)
        
        if target_count == 1:
            target_desc = f"1 {target_type}"
        else:
            target_desc = f"{target_count} {target_type}s"
        
        return (f"Generate {detail_level} {prompt_type} ({word_counts['min']}-{word_counts['max']} words) "
               f"for {target_desc}, focusing on {focus_text}. "
               f"Uses {strategy.get_strategy_name()} strategy.")