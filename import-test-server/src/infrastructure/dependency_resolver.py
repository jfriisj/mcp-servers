"""
Dependency Resolver Implementation
=================================

Concrete implementation of dependency resolution and validation.
"""

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Optional, Set, List
import pkgutil
import subprocess

from domain.interfaces import DependencyResolverInterface
from domain.models import ImportStatement, DependencyInfo


class DependencyResolver(DependencyResolverInterface):
    """Concrete implementation of dependency resolution"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._stdlib_modules = self._get_stdlib_modules()
        self._installed_packages = None  # Lazy loading
    
    def resolve_import(self, import_stmt: ImportStatement, from_file: Path) -> bool:
        """Check if an import can be resolved"""
        try:
            # Handle relative imports
            if import_stmt.is_relative:
                return self._resolve_relative_import(import_stmt, from_file)
            
            # Try to resolve absolute import
            module_name = import_stmt.module
            
            # Check standard library
            if self.is_standard_library(module_name):
                return True
            
            # Check installed packages
            if self.is_third_party(module_name):
                return True
            
            # Check local modules
            module_path = self.get_module_path(module_name, from_file)
            if module_path and module_path.exists():
                # If importing specific names, check they exist
                if import_stmt.names and not import_stmt.is_wildcard:
                    return self._check_names_in_module(module_path, import_stmt.names)
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_module_path(self, module_name: str, from_file: Path) -> Optional[Path]:
        """Get the file path for a module"""
        # Split module name into parts
        parts = module_name.split('.')
        
        # Start from project root or current file's directory
        search_paths = [
            self.project_root,
            from_file.parent
        ]
        
        for search_path in search_paths:
            current_path = search_path
            
            # Navigate through module parts
            for part in parts:
                # Check for package directory
                package_dir = current_path / part
                if package_dir.is_dir() and (package_dir / "__init__.py").exists():
                    current_path = package_dir
                    continue
                
                # Check for module file
                module_file = current_path / f"{part}.py"
                if module_file.exists():
                    return module_file
                
                # If this part doesn't exist, try next search path
                break
            else:
                # All parts found, check for __init__.py
                init_file = current_path / "__init__.py"
                if init_file.exists():
                    return init_file
        
        return None
    
    def is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of Python standard library"""
        # Get top-level module name
        top_module = module_name.split('.')[0]
        return top_module in self._stdlib_modules
    
    def is_third_party(self, module_name: str) -> bool:
        """Check if module is a third-party package"""
        try:
            # Check if module can be imported
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False
            
            # If it's not stdlib and can be imported, it's likely third-party
            return not self.is_standard_library(module_name)
            
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    
    def get_installed_packages(self) -> Dict[str, DependencyInfo]:
        """Get information about installed packages with caching"""
        if self._installed_packages is None:
            # Only discover when actually needed
            self._installed_packages = self._discover_installed_packages()
        return self._installed_packages
    
    def _resolve_relative_import(self, import_stmt: ImportStatement, from_file: Path) -> bool:
        """Resolve relative import"""
        try:
            # Calculate the target module path based on relative level
            current_dir = from_file.parent
            
            # Go up 'level' directories
            for _ in range(import_stmt.level):
                current_dir = current_dir.parent
                if current_dir == self.project_root.parent:
                    # Gone too far up
                    return False
            
            # If there's a module name, navigate to it
            if import_stmt.module:
                target_path = current_dir
                for part in import_stmt.module.split('.'):
                    target_path = target_path / part
                
                # Check if it's a module file or package
                if (target_path.with_suffix('.py')).exists():
                    return True
                elif target_path.is_dir() and (target_path / "__init__.py").exists():
                    return True
            else:
                # Just relative to current level
                return (current_dir / "__init__.py").exists()
            
            return False
            
        except Exception:
            return False
    
    def _check_names_in_module(self, module_path: Path, names: List[str]) -> bool:
        """Check if specific names exist in a module"""
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple check - see if names are defined in the module
            # This is not perfect but works for most cases
            for name in names:
                if name == '*':  # Wildcard import
                    continue
                
                # Look for function/class definitions, assignments, etc.
                patterns = [
                    f"def {name}(",
                    f"class {name}(",  
                    f"class {name}:",
                    f"{name} =",
                    f"'{name}'",
                    f'"{name}"'
                ]
                
                if any(pattern in content for pattern in patterns):
                    continue
                else:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Get set of standard library module names"""
        # This is a simplified list of common stdlib modules
        # In a real implementation, you might want to use a more comprehensive approach
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'json', 're', 'datetime', 'collections',
            'itertools', 'functools', 'typing', 'dataclasses', 'enum',
            'abc', 'asyncio', 'concurrent', 'threading', 'multiprocessing',
            'subprocess', 'shutil', 'tempfile', 'glob', 'fnmatch',
            'argparse', 'configparser', 'logging', 'unittest', 'doctest',
            'http', 'urllib', 'email', 'html', 'xml', 'csv', 'sqlite3',
            'pickle', 'gzip', 'zipfile', 'tarfile', 'base64', 'hashlib',
            'hmac', 'secrets', 'uuid', 'random', 'math', 'statistics',
            'decimal', 'fractions', 'time', 'calendar', 'locale',
            'gettext', 'socket', 'ssl', 'select', 'selectors', 'signal',
            'mmap', 'ctypes', 'struct', 'codecs', 'unicodedata',
            'stringprep', 'readline', 'rlcompleter', 'pdb', 'profile',
            'pstats', 'timeit', 'trace', 'traceback', 'faulthandler',
            'pydoc', 'doctest', 'unittest', 'test', 'bdb', 'faulthandler'
        }
        
        # Try to get more comprehensive list from sys.stdlib_module_names (Python 3.10+)
        if hasattr(sys, 'stdlib_module_names'):
            stdlib_modules.update(sys.stdlib_module_names)
        
        return stdlib_modules
    
    def _discover_installed_packages(self) -> Dict[str, DependencyInfo]:
        """Discover installed packages using pip list with timeout"""
        packages = {}
        
        try:
            # Run pip list with timeout to avoid hanging
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10  # 10 second timeout
            )
            
            import json
            pip_packages = json.loads(result.stdout)
            
            for pkg in pip_packages:
                packages[pkg['name']] = DependencyInfo(
                    name=pkg['name'],
                    version=pkg['version'],
                    is_installed=True,
                    source='pip'
                )
                
        except (subprocess.TimeoutExpired, Exception):
            # Fallback to faster importlib approach
            try:
                for importer, modname, ispkg in pkgutil.iter_modules():
                    if not self.is_standard_library(modname):
                        packages[modname] = DependencyInfo(
                            name=modname,
                            is_installed=True,
                            source='importlib'
                        )
            except Exception:
                # Last resort - return empty dict
                pass
        
        return packages