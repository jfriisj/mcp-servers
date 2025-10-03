"""
Domain Layer - Core Business Logic
==================================
This layer contains interfaces, models, and domain services.
It has no dependencies on other layers.
"""

from .interfaces import IAnalyzer, IPrincipleChecker, IFormatter
from .models import SolidPrinciple, SolidViolation, SolidReport

__all__ = [
    'IAnalyzer',
    'IPrincipleChecker',
    'IFormatter',
    'SolidPrinciple',
    'SolidViolation',
    'SolidReport',
]
