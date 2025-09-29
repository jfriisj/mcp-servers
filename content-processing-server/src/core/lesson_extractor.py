"""Lesson content extractor module.

This module provides functionality for extracting and analyzing AI algorithm content
from lesson materials."""

import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any, Set

logger = logging.getLogger(__name__)


# Algorithm patterns to identify sections
ALGORITHM_PATTERNS = {
    'a_star': {
        'keywords': ['A*', 'A-star', 'pathfinding', 'best-first search'],
        'section_headers': [r'#\s*A\*', r'#\s*Pathfinding', r'A\*\s*to\s*play'],
        'type': 'pathfinding'
    },
    'fsm': {
        'keywords': ['FSM', 'Finite State Machine', 'state machine', 'finite state'],
        'section_headers': [r'#\s*Finite\s*State\s*Machine', r'FSM\?', r'Hierarchical\s*FSM'],
        'type': 'behavior_control'
    },
    'decision_trees': {
        'keywords': ['Decision Tree', 'decision tree', 'Information Gain', 'entropy'],
        'section_headers': [r'#\s*Decision\s*Tree', r'Introducing\s*Decision\s*Tree'],
        'type': 'decision_making'
    },
    'behavior_trees': {
        'keywords': ['Behavior Tree', 'Behaviour Tree', 'behaviour tree', 'BT'],
        'section_headers': [r'#\s*Behaviour\s*tree', r'Behavior\s*tree', r'What\s*happens.*BT'],
        'type': 'behavior_control'
    }
}


@dataclass
class AlgorithmSection:
    """Represents an extracted AI algorithm section."""
    name: str
    start_line: int
    end_line: int
    content: str
    algorithm_type: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]


class LessonContentExtractor:
    """Extract AI algorithm content from lesson materials."""

    def __init__(self, algorithm_patterns: Optional[Dict[str, Dict[str, Any]]] = None):
        """Initialize the content extractor.

        Args:
            algorithm_patterns: Optional custom patterns to identify algorithms
        """
        self.algorithms: List[AlgorithmSection] = []
        self.content_lines: List[str] = []
        self.file_metadata: Dict[str, Any] = {}
        self.algorithm_patterns = algorithm_patterns or ALGORITHM_PATTERNS

    def load_content(self, file_path: str) -> bool:
        """Load lesson content from file.

        Args:
            file_path: Path to the lesson file

        Returns:
            True if loaded successfully
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.content_lines = content.split('\n')
            self.file_metadata = {
                'file_path': str(path),
                'file_name': path.name,
                'total_lines': len(self.content_lines),
                'file_size': path.stat().st_size
            }

            logger.info(f"Loaded {len(self.content_lines)} lines from {path.name}")
            return True

        except Exception as e:
            logger.error(f"Error loading lesson content: {e}")
            return False

    def identify_algorithm_sections(self, algorithms: Optional[List[str]] = None,
                                  extract_types: Optional[List[str]] = None,
                                  section_overlap: int = 20) -> List[AlgorithmSection]:
        """Identify and extract AI algorithm sections from the content.

        Args:
            algorithms: Optional list of specific algorithms to search for
            extract_types: Optional list of section types to extract ("headers", "keywords", "both")
            section_overlap: Maximum lines between sections to consider them part of the same content

        Returns:
            List of extracted algorithm sections
        """
        sections = []
        extract_types = extract_types or ["both"]

        # Filter patterns if specific algorithms requested
        patterns_to_use = {}
        if algorithms:
            for alg in algorithms:
                if alg in self.algorithm_patterns:
                    patterns_to_use[alg] = self.algorithm_patterns[alg]
        else:
            patterns_to_use = self.algorithm_patterns

        for alg_name, patterns in patterns_to_use.items():
            logger.info(f"Searching for {alg_name} sections...")

            matches = []
            if "headers" in extract_types or "both" in extract_types:
                # Find section headers
                header_matches = self._find_section_headers(patterns['section_headers'])
                matches.extend(header_matches)

            if "keywords" in extract_types or "both" in extract_types:
                # Find keyword-based sections
                keyword_matches = self._find_keyword_sections(patterns['keywords'], section_overlap)
                matches.extend(keyword_matches)

            # Combine and process matches
            for start_line, end_line in self._combine_matches(matches):
                content = self._extract_section_content(start_line, end_line)

                section = AlgorithmSection(
                    name=alg_name,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    algorithm_type=patterns['type'],
                    properties=self._extract_algorithm_properties(content, alg_name),
                    metadata=self._extract_section_metadata(content)
                )

                sections.append(section)
                logger.info(f"Extracted {alg_name} section: lines {start_line}-{end_line}")

        self.algorithms = sections
        return sections

    def get_algorithm_summary(self) -> Dict[str, Any]:
        """Get summary of extracted algorithms.

        Returns:
            Dict containing summary information
        """
        if not self.algorithms:
            return {'total_algorithms': 0, 'algorithms': []}

        summary = {
            'total_algorithms': len(self.algorithms),
            'algorithms': [],
            'types': {},
            'total_content_lines': sum(alg.metadata.get('line_count', 0) for alg in self.algorithms),
            'file_metadata': self.file_metadata
        }

        for alg in self.algorithms:
            alg_info = {
                'name': alg.name,
                'type': alg.algorithm_type,
                'lines': f"{alg.start_line}-{alg.end_line}",
                'properties_count': len(alg.properties),
                'content_size': alg.metadata.get('character_count', 0)
            }
            summary['algorithms'].append(alg_info)

            # Count by type
            if alg.algorithm_type not in summary['types']:
                summary['types'][alg.algorithm_type] = 0
            summary['types'][alg.algorithm_type] += 1

        return summary

    def save_extracted_content(self, output_dir: str = "extracted_algorithms") -> bool:
        """Save extracted algorithm content to separate files.

        Args:
            output_dir: Directory to save extracted content

        Returns:
            True if saved successfully
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            for alg in self.algorithms:
                filename = f"{alg.name}_{alg.start_line}-{alg.end_line}.md"
                file_path = output_path / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {alg.name.replace('_', ' ').title()}\n\n")
                    f.write(f"**Type:** {alg.algorithm_type}\n")
                    f.write(f"**Source Lines:** {alg.start_line}-{alg.end_line}\n\n")

                    if alg.properties:
                        f.write("## Properties\n\n")
                        for key, value in alg.properties.items():
                            f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                        f.write("\n")

                    f.write("## Content\n\n")
                    f.write(alg.content)

                logger.info(f"Saved {alg.name} to {file_path}")

            # Save summary
            summary_path = output_path / "extraction_summary.md"
            summary = self.get_algorithm_summary()

            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# Algorithm Extraction Summary\n\n")
                f.write(f"**Total Algorithms Found:** {summary['total_algorithms']}\n")
                f.write(f"**Source File:** {summary['file_metadata']['file_name']}\n")
                f.write(f"**Total Content Lines:** {summary['total_content_lines']}\n\n")

                f.write("## Algorithms by Type\n\n")
                for alg_type, count in summary['types'].items():
                    f.write(f"- **{alg_type.replace('_', ' ').title()}:** {count}\n")

                f.write("\n## Extracted Algorithms\n\n")
                for alg_info in summary['algorithms']:
                    f.write(f"- **{alg_info['name'].replace('_', ' ').title()}** ")
                    f.write(f"({alg_info['type']}) - Lines {alg_info['lines']}\n")

            logger.info(f"Saved extraction summary to {summary_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving extracted content: {e}")
            return False

    def _find_section_headers(self, header_patterns: List[str]) -> List[Tuple[int, int]]:
        """Find sections based on header patterns.

        Args:
            header_patterns: Regex patterns for headers

        Returns:
            List of (start_line, end_line) tuples
        """
        matches = []

        for i, line in enumerate(self.content_lines):
            for pattern in header_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Find the end of this section (next major header or end of file)
                    end_line = self._find_section_end(i)
                    matches.append((i, end_line))
                    break

        return matches

    def _find_keyword_sections(self, keywords: List[str],
                             section_overlap: int = 20) -> List[Tuple[int, int]]:
        """Find sections based on keyword density.

        Args:
            keywords: Keywords to search for
            section_overlap: Maximum lines between sections to consider them part of the same content

        Returns:
            List of (start_line, end_line) tuples
        """
        matches = []
        keyword_lines = []

        # Find lines containing keywords
        for i, line in enumerate(self.content_lines):
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    keyword_lines.append(i)
                    break

        # Group nearby keyword lines into sections
        if keyword_lines:
            current_start = keyword_lines[0]
            current_end = keyword_lines[0]

            for line_num in keyword_lines[1:]:
                if line_num - current_end <= section_overlap:  # Within overlap range
                    current_end = line_num
                else:
                    # Found a gap, finalize current section
                    section_end = self._find_section_end(current_end)
                    matches.append((current_start, section_end))
                    current_start = line_num
                    current_end = line_num

            # Add the final section
            section_end = self._find_section_end(current_end)
            matches.append((current_start, section_end))

        return matches

    def _find_section_end(self, start_line: int) -> int:
        """Find the end of a section starting at start_line.

        Args:
            start_line: Starting line number

        Returns:
            End line number
        """
        # Look for next major header or end of significant content
        for i in range(start_line + 1, len(self.content_lines)):
            line = self.content_lines[i].strip()

            # Major header (single # at start)
            if re.match(r'^#\s+[^#]', line):
                return i - 1

            # Multiple empty lines might indicate section break
            if (i < len(self.content_lines) - 2 and
                not line and
                not self.content_lines[i + 1].strip() and
                not self.content_lines[i + 2].strip()):
                return i - 1

        # Default to reasonable section size or end of file
        return min(start_line + 100, len(self.content_lines) - 1)

    def _combine_matches(self, matches: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Combine and deduplicate section matches.

        Args:
            matches: List of (start_line, end_line) tuples

        Returns:
            List of combined and deduplicated matches
        """
        if not matches:
            return []

        # Sort by start line
        matches.sort(key=lambda x: x[0])

        # Merge overlapping sections
        merged = [matches[0]]

        for start, end in matches[1:]:
            last_start, last_end = merged[-1]

            # If sections overlap or are very close, merge them
            if start <= last_end + 10:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    def _extract_section_content(self, start_line: int, end_line: int) -> str:
        """Extract content from specified line range.

        Args:
            start_line: Start line (inclusive)
            end_line: End line (inclusive)

        Returns:
            Extracted content
        """
        if start_line >= len(self.content_lines):
            return ""

        end_line = min(end_line, len(self.content_lines) - 1)
        return '\n'.join(self.content_lines[start_line:end_line + 1])

    def _extract_algorithm_properties(self, content: str, algorithm_name: str) -> Dict[str, Any]:
        """Extract specific properties for each algorithm type.

        Args:
            content: Section content
            algorithm_name: Name of the algorithm

        Returns:
            Dict of extracted properties
        """
        properties = {}

        if algorithm_name == 'a_star':
            # Extract A* specific properties
            if 'admissible' in content.lower():
                properties['admissible_heuristic'] = True
            if 'shortest path' in content.lower():
                properties['optimal'] = True
            if 'best-first' in content.lower():
                properties['search_type'] = 'best-first'

            # Look for complexity mentions
            complexity_match = re.search(r'O\([^)]+\)', content)
            if complexity_match:
                properties['complexity'] = complexity_match.group(0)

        elif algorithm_name == 'fsm':
            # Extract FSM properties
            if 'hierarchical' in content.lower():
                properties['hierarchical'] = True
            if 'predictable' in content.lower():
                properties['predictable'] = True
            if 'debuggable' in content.lower():
                properties['debuggable'] = True

            # Extract advantages/disadvantages
            advantages = []
            disadvantages = []

            if 'simple' in content.lower():
                advantages.append('simple')
            if 'predictable' in content.lower():
                advantages.append('predictable')
            if 'debuggable' in content.lower():
                advantages.append('debuggable')

            if "doesn't scale" in content.lower():
                disadvantages.append('poor scalability')
            if 'never learns' in content.lower():
                disadvantages.append('no learning')

            if advantages:
                properties['advantages'] = advantages
            if disadvantages:
                properties['disadvantages'] = disadvantages

        elif algorithm_name == 'decision_trees':
            # Extract Decision Tree properties
            if 'information gain' in content.lower():
                properties['splitting_criterion'] = 'information_gain'
            if 'entropy' in content.lower():
                properties['uses_entropy'] = True
            if 'reactive' in content.lower():
                properties['reactive'] = True
            if 'human understandable' in content.lower():
                properties['interpretable'] = True

        elif algorithm_name == 'behavior_trees':
            # Extract Behavior Tree properties
            if 'composites' in content.lower():
                properties['has_composites'] = True
            if 'decorators' in content.lower():
                properties['has_decorators'] = True
            if 'sequence' in content.lower():
                properties['sequence_nodes'] = True
            if 'selector' in content.lower():
                properties['selector_nodes'] = True

        return properties

    def _extract_section_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from section content.

        Args:
            content: Section content

        Returns:
            Dict of extracted metadata
        """
        metadata = {}

        # Count different content types
        metadata['line_count'] = len(content.split('\n'))
        metadata['character_count'] = len(content)
        metadata['word_count'] = len(content.split())

        # Identify content features
        metadata['has_code'] = bool(re.search(r'```|`[^`]+`', content))
        metadata['has_equations'] = bool(re.search(r'\$.*\$|\\[a-zA-Z]+', content))
        metadata['has_bullets'] = bool(re.search(r'^\s*[•●▪▫◦‣⁃-]\s+', content, re.MULTILINE))
        metadata['has_numbers'] = bool(re.search(r'^\s*\d+[.)]\s+', content, re.MULTILINE))

        # Count headers
        headers = re.findall(r'^#+\s+.*$', content, re.MULTILINE)
        metadata['header_count'] = len(headers)

        return metadata