"""
Factory for prompt generation strategies.

This module implements the Factory pattern to create prompt strategies,
following the Open/Closed Principle (OCP) for extensibility.
"""

from typing import Dict, List, Type
from study_buddy.server.prompts.base_strategy import BasePromptStrategy
from study_buddy.server.prompts.summary_strategy import SummaryPromptStrategy


class PromptStrategyFactory:
    """
    Factory for creating prompt generation strategies.

    Benefits:
    - Centralized strategy creation logic (SRP)
    - Easy to add new strategies without modifying existing code (OCP)
    - Eliminates direct dependencies on concrete strategy classes (DIP)
    - Supports strategy registration and discovery
    """

    def __init__(self):
        """Initialize factory with default strategies."""
        # Register available strategies
        self._strategies: Dict[str, Type[BasePromptStrategy]] = {
            "summary": SummaryPromptStrategy
        }

    def create_strategy(self, strategy_type: str) -> BasePromptStrategy:
        """
        Create prompt strategy instance by type.

        Args:
            strategy_type: Type of strategy to create

        Returns:
            BasePromptStrategy instance

        Raises:
            ValueError: If strategy type is not registered
        """
        if strategy_type not in self._strategies:
            available = ", ".join(self._strategies.keys())
            raise ValueError(
                f"Unknown strategy type '{strategy_type}'. Available: {available}"
            )

        strategy_class = self._strategies[strategy_type]
        return strategy_class()

    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy types.

        Returns:
            List of registered strategy type names
        """
        return list(self._strategies.keys())

    def register_strategy(
        self, strategy_type: str, strategy_class: Type[BasePromptStrategy]
    ) -> None:
        """
        Register new strategy type (for extensibility).

        Args:
            strategy_type: Name of the strategy type
            strategy_class: Strategy class to register

        Raises:
            ValueError: If strategy class doesn't implement BasePromptStrategy
        """
        if not issubclass(strategy_class, BasePromptStrategy):
            raise ValueError(f"Strategy class must inherit from BasePromptStrategy")

        self._strategies[strategy_type] = strategy_class

    def is_strategy_available(self, strategy_type: str) -> bool:
        """
        Check if strategy type is available.

        Args:
            strategy_type: Strategy type to check

        Returns:
            True if strategy is registered
        """
        return strategy_type in self._strategies
