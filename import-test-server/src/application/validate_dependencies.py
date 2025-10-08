"""
Validate Dependencies Use Case
=============================

Use case for validating project dependencies.
"""

from pathlib import Path
from typing import Dict, List, Tuple

from domain.models import DependencyInfo
from infrastructure.dependency_resolver import DependencyResolver


class ValidateDependenciesUseCase:
    """Use case for validating project dependencies"""
    
    def __init__(self, dependency_resolver: DependencyResolver):
        self.dependency_resolver = dependency_resolver
    
    def execute(self, project_root: Path) -> Tuple[Dict[str, DependencyInfo], List[str]]:
        """Execute dependency validation for a project"""
        if not project_root.exists():
            raise FileNotFoundError(f"Project root not found: {project_root}")
        
        # Get installed packages
        installed_packages = self.dependency_resolver.get_installed_packages()
        
        # Check for missing packages (this would require analyzing actual imports)
        missing_packages = []
        
        return installed_packages, missing_packages