"""Incremental lesson processor module.

This module provides functionality for processing lesson content in incremental
steps, allowing for step-by-step analysis and enhancement."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .lesson_extractor import LessonContentExtractor
from .concept_processor import ConceptProcessor

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStep:
    """Represents a processing step with its output."""
    step_number: int
    step_type: str
    input_content: str
    output_content: str
    metadata: Dict[str, Any]
    resources_used: List[str]
    success: bool
    error: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of incremental processing."""
    total_steps: int
    completed_steps: int
    steps: List[ProcessingStep]
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class IncrementalProcessor:
    """Process lesson content in incremental steps."""

    def __init__(self):
        """Initialize the incremental processor."""
        self.lesson_extractor = LessonContentExtractor()
        self.concept_processor = ConceptProcessor()
        self.current_step = 0
        self.total_steps = 0
        self.current_content = ""
        self.steps: List[ProcessingStep] = []
        self.metadata: Dict[str, Any] = {}

    def process_lesson(self, lesson_file: str, start_step: int = 1,
                      end_step: int = 0, include_exercises: bool = True) -> ProcessingResult:
        """Process a lesson file in incremental steps.

        Args:
            lesson_file: Path to the lesson file
            start_step: Starting step number (1-based)
            end_step: Ending step number (0 for all steps)
            include_exercises: Whether to include exercise sections

        Returns:
            ProcessingResult containing all processing steps and metadata

        Raises:
            ValueError: If lesson_file doesn't exist or steps are invalid
            RuntimeError: If processing fails
        """
        try:
            # Load and validate lesson file
            if not self.lesson_extractor.load_content(lesson_file):
                raise ValueError(f"Failed to load lesson file: {lesson_file}")

            self.current_content = "\n".join(self.lesson_extractor.content_lines)
            self._init_processing()

            # Validate step range
            if start_step < 1:
                raise ValueError("start_step must be >= 1")
            if end_step > self.total_steps and end_step != 0:
                raise ValueError(f"end_step ({end_step}) exceeds total steps ({self.total_steps})")
            if end_step == 0:
                end_step = self.total_steps

            # Process each step
            for step in range(start_step, end_step + 1):
                self.current_step = step
                try:
                    step_result = self._process_step(step, include_exercises)
                    self.steps.append(step_result)
                    if not step_result.success:
                        logger.warning(f"Step {step} failed: {step_result.error}")
                        break
                except Exception as e:
                    logger.error(f"Error in step {step}: {e}")
                    self.steps.append(ProcessingStep(
                        step_number=step,
                        step_type="unknown",
                        input_content=self.current_content,
                        output_content="",
                        metadata={},
                        resources_used=[],
                        success=False,
                        error=str(e)
                    ))
                    break

            # Prepare final result
            completed = len([s for s in self.steps if s.success])
            success = completed == (end_step - start_step + 1)

            return ProcessingResult(
                total_steps=self.total_steps,
                completed_steps=completed,
                steps=self.steps,
                metadata=self.metadata,
                success=success,
                error=None if success else "Processing incomplete"
            )

        except Exception as e:
            logger.error(f"Failed to process lesson: {e}")
            return ProcessingResult(
                total_steps=self.total_steps,
                completed_steps=0,
                steps=[],
                metadata={},
                success=False,
                error=str(e)
            )

    def save_processing_result(self, result: ProcessingResult,
                             output_file: str) -> bool:
        """Save processing result to a file.

        Args:
            result: Processing result to save
            output_file: Path to save the result

        Returns:
            True if saved successfully
        """
        try:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            data = {
                "total_steps": result.total_steps,
                "completed_steps": result.completed_steps,
                "success": result.success,
                "error": result.error,
                "metadata": result.metadata,
                "steps": [
                    {
                        "step_number": step.step_number,
                        "step_type": step.step_type,
                        "input_content": step.input_content,
                        "output_content": step.output_content,
                        "metadata": step.metadata,
                        "resources_used": step.resources_used,
                        "success": step.success,
                        "error": step.error
                    }
                    for step in result.steps
                ]
            }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved processing result to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save processing result: {e}")
            return False

    def _init_processing(self) -> None:
        """Initialize processing metadata and steps."""
        self.steps = []
        self.current_step = 0
        self.metadata = {
            'content_size': len(self.current_content),
            'line_count': len(self.current_content.split('\n')),
            'processing_stages': [
                "content_extraction",
                "algorithm_identification",
                "property_extraction",
                "metadata_collection",
                "cross_referencing"
            ]
        }
        self.total_steps = len(self.metadata['processing_stages'])

    def _process_step(self, step: int, include_exercises: bool) -> ProcessingStep:
        """Process a single step.

        Args:
            step: Step number to process
            include_exercises: Whether to include exercise sections

        Returns:
            ProcessingStep with results

        Raises:
            ValueError: If step number is invalid
        """
        if step < 1 or step > self.total_steps:
            raise ValueError(f"Invalid step number: {step}")

        step_type = self.metadata['processing_stages'][step - 1]
        resources_used = []
        input_content = self.current_content

        try:
            # Execute step-specific processing
            if step_type == "content_extraction":
                output_content, metadata = self._extract_content(include_exercises)
                resources_used = ["lesson_extractor"]

            elif step_type == "algorithm_identification":
                output_content, metadata = self._identify_algorithms()
                resources_used = ["lesson_extractor", "algorithm_patterns"]

            elif step_type == "property_extraction":
                output_content, metadata = self._extract_properties()
                resources_used = ["concept_processor"]

            elif step_type == "metadata_collection":
                output_content, metadata = self._collect_metadata()
                resources_used = ["lesson_extractor", "metadata_analyzer"]

            elif step_type == "cross_referencing":
                output_content, metadata = self._cross_reference()
                resources_used = ["concept_processor", "knowledge_base"]

            else:
                raise ValueError(f"Unknown step type: {step_type}")

            # Update current content for next step
            self.current_content = output_content

            return ProcessingStep(
                step_number=step,
                step_type=step_type,
                input_content=input_content,
                output_content=output_content,
                metadata=metadata,
                resources_used=resources_used,
                success=True
            )

        except Exception as e:
            logger.error(f"Error in step {step} ({step_type}): {e}")
            return ProcessingStep(
                step_number=step,
                step_type=step_type,
                input_content=input_content,
                output_content="",
                metadata={},
                resources_used=resources_used,
                success=False,
                error=str(e)
            )

    def _extract_content(self, include_exercises: bool) -> tuple[str, Dict[str, Any]]:
        """Extract content from lesson material.

        Args:
            include_exercises: Whether to include exercise sections

        Returns:
            Tuple of (processed content, metadata)
        """
        sections = self.lesson_extractor.identify_algorithm_sections()
        metadata = {
            'total_sections': len(sections),
            'section_types': {},
            'exercise_sections': 0
        }

        processed_content = []
        for section in sections:
            # Skip exercise sections if not included
            if not include_exercises and 'exercise' in section.content.lower():
                metadata['exercise_sections'] += 1
                continue

            # Track section types
            if section.algorithm_type not in metadata['section_types']:
                metadata['section_types'][section.algorithm_type] = 0
            metadata['section_types'][section.algorithm_type] += 1

            # Add processed section
            processed_content.append(section.content)

        return "\n\n".join(processed_content), metadata

    def _identify_algorithms(self) -> tuple[str, Dict[str, Any]]:
        """Identify algorithms in the content.

        Returns:
            Tuple of (processed content, metadata)
        """
        sections = self.lesson_extractor.identify_algorithm_sections()
        metadata = self.lesson_extractor.get_algorithm_summary()

        # Enhance content with algorithm identification
        processed_content = []
        for section in sections:
            header = f"# {section.name.replace('_', ' ').title()}\n"
            header += f"Type: {section.algorithm_type}\n"
            header += f"Lines: {section.start_line}-{section.end_line}\n\n"
            processed_content.append(header + section.content)

        return "\n\n".join(processed_content), metadata

    def _extract_properties(self) -> tuple[str, Dict[str, Any]]:
        """Extract algorithm properties.

        Returns:
            Tuple of (processed content, metadata)
        """
        sections = self.lesson_extractor.identify_algorithm_sections()
        metadata = {
            'processed_algorithms': [],
            'property_counts': {}
        }

        processed_content = []
        for section in sections:
            # Extract properties
            properties = self.lesson_extractor._extract_algorithm_properties(
                section.content,
                section.name
            )

            # Process the concept
            concept = self.concept_processor.process_concept(
                section.name,
                category=section.algorithm_type,
                algorithm_data={'description': section.content[:100] + "..."}
            )

            # Build enhanced content
            content = f"# {section.name.replace('_', ' ').title()}\n\n"
            content += f"## Overview\n{concept.brief_description}\n\n"
            content += f"## Detailed Explanation\n{concept.detailed_explanation}\n\n"
            content += f"## Properties\n"
            for key, value in properties.items():
                content += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            content += f"\n## Original Content\n{section.content}\n"

            processed_content.append(content)

            # Update metadata
            metadata['processed_algorithms'].append({
                'name': section.name,
                'type': section.algorithm_type,
                'property_count': len(properties)
            })
            metadata['property_counts'][section.name] = len(properties)

        return "\n\n".join(processed_content), metadata

    def _collect_metadata(self) -> tuple[str, Dict[str, Any]]:
        """Collect metadata about the content.

        Returns:
            Tuple of (processed content, metadata)
        """
        sections = self.lesson_extractor.identify_algorithm_sections()
        metadata = {}

        for section in sections:
            section_metadata = self.lesson_extractor._extract_section_metadata(section.content)
            metadata[section.name] = section_metadata

        # Add metadata headers to content
        processed_content = []
        for section in sections:
            meta = metadata[section.name]
            header = f"# {section.name.replace('_', ' ').title()}\n"
            header += "## Metadata\n"
            for key, value in meta.items():
                header += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            header += f"\n## Content\n{section.content}"
            processed_content.append(header)

        return "\n\n".join(processed_content), metadata

    def _cross_reference(self) -> tuple[str, Dict[str, Any]]:
        """Create cross-references between algorithms.

        Returns:
            Tuple of (processed content, metadata)
        """
        sections = self.lesson_extractor.identify_algorithm_sections()
        metadata = {
            'cross_references': {},
            'related_concepts': {}
        }

        # Build cross-references
        for section in sections:
            concept = self.concept_processor.process_concept(section.name)
            metadata['related_concepts'][section.name] = list(
                concept.comparison_with_alternatives.keys())

        # Add cross-references to content
        processed_content = []
        for section in sections:
            content = f"# {section.name.replace('_', ' ').title()}\n\n"
            
            # Add related concepts
            if section.name in metadata['related_concepts']:
                content += "## Related Concepts\n"
                for related in metadata['related_concepts'][section.name]:
                    content += f"- {related.replace('_', ' ').title()}\n"
                content += "\n"

            content += f"## Content\n{section.content}"
            processed_content.append(content)

        return "\n\n".join(processed_content), metadata