"""Educational concept processing module.

This module provides functionality for processing educational concepts into rich
descriptions with structured context."""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Educational knowledge base for Game AI concepts
EDUCATIONAL_KNOWLEDGE = {
    "a_star": {
        "brief_description": "Optimal pathfinding algorithm that uses heuristics to efficiently find shortest paths",
        "detailed_explanation": "A* (A-star) is a graph traversal and path search algorithm that finds the optimal path from a start node to a goal node. It combines the benefits of Dijkstra's algorithm (guaranteed optimality) with the efficiency of greedy best-first search (using heuristics). A* maintains an open list of nodes to explore and a closed list of explored nodes, selecting the node with the lowest f(n) = g(n) + h(n) score, where g(n) is the actual cost from start to node n, and h(n) is the heuristic estimate from node n to goal.",
        "when_to_use": [
            "When you need guaranteed optimal pathfinding",
            "In grid-based or graph-based environments",
            "When computational resources allow for memory usage",
            "For strategic AI that requires perfect navigation",
            "When path quality is more important than speed"
        ],
        "when_not_to_use": [
            "In memory-constrained environments (mobile games)",
            "When approximate paths are sufficient",
            "In highly dynamic environments where paths change frequently",
            "For real-time applications requiring instant responses",
            "When the heuristic function is poor or inadmissible"
        ],
        "real_world_applications": [
            "GPS navigation systems in cars",
            "Robot navigation in warehouses",
            "Network routing protocols",
            "Automated guided vehicles (AGVs) in factories",
            "Drone delivery path planning"
        ],
        "game_specific_uses": [
            "RTS unit movement (StarCraft, Age of Empires)",
            "RPG character navigation (World of Warcraft)",
            "Puzzle games (sliding puzzles, maze solving)",
            "Turn-based strategy games (Civilization)",
            "Platformer enemy AI movement patterns"
        ],
        "comparison_with_alternatives": {
            "dijkstra": "A* is faster due to heuristic guidance, but requires memory for heuristic function",
            "greedy_best_first": "A* guarantees optimality while greedy may find suboptimal paths",
            "breadth_first_search": "A* is more efficient in most cases but requires heuristic design",
            "jump_point_search": "JPS is faster on uniform grids, A* is more general-purpose"
        }
    },
    # Additional concepts can be added here
}


@dataclass
class ConceptDescription:
    """Rich educational description of a concept or algorithm."""
    concept_name: str
    category: str
    brief_description: str
    detailed_explanation: str
    when_to_use: List[str]
    when_not_to_use: List[str]
    real_world_applications: List[str]
    game_specific_uses: List[str]
    comparison_with_alternatives: Dict[str, str]
    learning_progression: Dict[str, str]
    implementation_difficulty: str
    prerequisite_knowledge: List[str]
    common_misconceptions: List[str]
    practical_tips: List[str]
    debugging_guidance: List[str]
    performance_considerations: List[str]
    scalability_notes: List[str]
    industry_usage: List[str]
    academic_context: str
    further_learning: List[str]


class ConceptProcessor:
    """Process educational concepts into rich descriptions."""

    def __init__(self):
        """Initialize the concept processor."""
        self.educational_knowledge = EDUCATIONAL_KNOWLEDGE

    def get_supported_concepts(self) -> List[str]:
        """Get list of supported concepts.

        Returns:
            List of concept names that can be processed.
        """
        return list(self.educational_knowledge.keys())

    def process_concept(self, concept_name: str, category: str = "algorithm",
                       algorithm_data: Optional[Dict[str, Any]] = None) -> ConceptDescription:
        """Process a concept into a rich educational description.

        Args:
            concept_name: Name of the concept to process
            category: Category of the concept
            algorithm_data: Additional data about the algorithm

        Returns:
            Rich concept description

        Raises:
            ValueError: If concept_name is not recognized
        """
        # Normalize concept name
        normalized_name = concept_name.lower().replace(" ", "_").replace("-", "_")

        # Get base knowledge or create default
        base_knowledge = self.educational_knowledge.get(normalized_name, {})
        if not base_knowledge and not algorithm_data:
            raise ValueError(f"Unknown concept: {concept_name}")

        # Extract information from algorithm data
        if algorithm_data is None:
            algorithm_data = {}

        complexity = algorithm_data.get('complexity', {})
        advantages = algorithm_data.get('advantages', [])
        disadvantages = algorithm_data.get('disadvantages', [])
        use_cases = algorithm_data.get('use_cases', [])
        related_algorithms = algorithm_data.get('related_algorithms', [])

        # Build educational description
        return ConceptDescription(
            concept_name=concept_name,
            category=category,
            brief_description=base_knowledge.get('brief_description',
                f"{concept_name} - {algorithm_data.get('description', 'Advanced algorithm for game AI')}"),
            detailed_explanation=base_knowledge.get('detailed_explanation',
                f"This algorithm is used in {category} applications and provides {', '.join(advantages[:2]) if advantages else 'advanced functionality'}."),
            when_to_use=base_knowledge.get('when_to_use', [
                f"When you need {category} functionality",
                "For applications requiring " + (advantages[0] if advantages else "advanced features"),
                "In scenarios where " + (use_cases[0] if use_cases else "this algorithm excels")
            ]),
            when_not_to_use=base_knowledge.get('when_not_to_use', [
                f"When {disadvantage.lower()}" for disadvantage in disadvantages[:3]
            ] + ["When simpler alternatives are sufficient"]),
            real_world_applications=base_knowledge.get('real_world_applications', [
                f"{category.title()} systems in various industries",
                "Commercial software applications",
                "Research and development projects"
            ]),
            game_specific_uses=base_knowledge.get('game_specific_uses', [
                f"{category.title()} implementation in game AI",
                "Character behavior systems",
                "Game mechanics optimization"
            ]),
            comparison_with_alternatives=base_knowledge.get('comparison_with_alternatives', {
                rel_algo.lower(): f"{concept_name} differs from {rel_algo} in implementation and use cases"
                for rel_algo in related_algorithms[:3]
            }),
            learning_progression=base_knowledge.get('learning_progression', {
                "beginner": f"Understand basic {category} concepts first",
                "intermediate": f"Learn {concept_name} implementation details",
                "advanced": f"Explore optimizations and variations of {concept_name}"
            }),
            implementation_difficulty=self._assess_difficulty(complexity, advantages, disadvantages),
            prerequisite_knowledge=base_knowledge.get('prerequisite_knowledge', [
                "Basic programming concepts",
                f"Understanding of {category} principles",
                "Data structures and algorithms fundamentals"
            ]),
            common_misconceptions=base_knowledge.get('common_misconceptions', [
                f"{concept_name} is not a magic solution for all {category} problems",
                "Implementation complexity varies based on requirements",
                "Performance depends on proper configuration and usage"
            ]),
            practical_tips=base_knowledge.get('practical_tips', [
                f"Start with simple {concept_name} implementations",
                "Test thoroughly before deploying to production",
                "Consider performance implications for your use case",
                "Document your implementation decisions"
            ]),
            debugging_guidance=base_knowledge.get('debugging_guidance', [
                f"Use logging to trace {concept_name} execution",
                "Visualize algorithm behavior when possible",
                "Test with known inputs to verify correctness",
                "Profile performance on target hardware"
            ]),
            performance_considerations=base_knowledge.get('performance_considerations', [
                f"Time complexity: {complexity.get('time', 'Varies based on implementation')}",
                f"Space complexity: {complexity.get('space', 'Varies based on implementation')}",
                "Consider caching for repeated operations",
                "Profile actual performance in your application"
            ]),
            scalability_notes=[
                f"Scales according to {complexity.get('time', 'implementation requirements')}",
                "Consider distributed implementations for large-scale applications",
                "Monitor performance as problem size increases"
            ],
            industry_usage=base_knowledge.get('industry_usage', [
                f"Widely used in {category} applications",
                "Standard in academic research",
                "Common in commercial software development"
            ]),
            academic_context=f"Studied extensively in {category} courses and research. "
                       f"Fundamental algorithm for understanding {category} principles.",
            further_learning=[
                f"Advanced {concept_name} implementations and optimizations",
                f"Related algorithms: {', '.join(related_algorithms[:3])}",
                f"Recent research developments in {category}",
                "Practical applications and case studies"
            ]
        )

    def to_json(self, description: ConceptDescription) -> str:
        """Convert concept description to JSON string.

        Args:
            description: Concept description to convert

        Returns:
            JSON string representation
        """
        return json.dumps(asdict(description), indent=2)

    def _assess_difficulty(self, complexity: Dict[str, str],
                         advantages: List[str],
                         disadvantages: List[str]) -> str:
        """Assess implementation difficulty based on algorithm characteristics.

        Args:
            complexity: Time and space complexity information
            advantages: List of advantages
            disadvantages: List of disadvantages

        Returns:
            Difficulty level ("beginner", "intermediate", or "advanced")
        """
        # Factors that increase difficulty
        difficulty_score = 0

        # Complexity analysis
        time_complexity = complexity.get('time', 'O(n)')
        if 'log' in time_complexity:
            difficulty_score += 1
        if 'n^2' in time_complexity or 'exponential' in time_complexity:
            difficulty_score += 2

        # Disadvantages analysis
        complex_disadvantages = ['memory intensive', 'complex', 'hard to maintain', 'sensitive']
        for disadvantage in disadvantages:
            if any(term in disadvantage.lower() for term in complex_disadvantages):
                difficulty_score += 1

        # Simple advantages reduce difficulty
        simple_advantages = ['simple', 'easy', 'straightforward', 'predictable']
        for advantage in advantages:
            if any(term in advantage.lower() for term in simple_advantages):
                difficulty_score -= 1

        # Determine difficulty level
        if difficulty_score <= 0:
            return "beginner"
        elif difficulty_score <= 2:
            return "intermediate"
        else:
            return "advanced"