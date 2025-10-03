"""
Domain Models
=============
Core business entities and value objects.
These are independent of any framework or implementation details.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class SolidPrinciple(Enum):
    """SOLID principles enumeration"""
    SINGLE_RESPONSIBILITY = "SRP"
    OPEN_CLOSED = "OCP"
    LISKOV_SUBSTITUTION = "LSP"
    INTERFACE_SEGREGATION = "ISP"
    DEPENDENCY_INVERSION = "DIP"


@dataclass
class SolidViolation:
    """
    Represents a violation of a SOLID principle.
    This is a value object - immutable and contains no business logic.
    """
    principle: SolidPrinciple
    severity: str  # "high", "medium", "low"
    line_number: int
    message: str
    suggestion: str
    code_snippet: str


@dataclass
class SolidReport:
    """
    Complete SOLID analysis report for a file.
    This is a value object that aggregates violations.
    """
    file_path: str
    violations: List[SolidViolation]
    score: float  # 0-100, higher is better
    summary: Dict[SolidPrinciple, int]  # violation count per principle
