# Test file with various import scenarios for testing
import os  # Standard library
import sys  # Standard library  
from pathlib import Path  # Standard library
from typing import List, Dict  # Standard library

# This would be a third-party import if installed
try:
    import requests  # Third party (may not be installed)
except ImportError:
    requests = None

# Local imports
from domain.models import ImportStatement  # Local import
from infrastructure.import_analyzer import ImportAnalyzer  # Local import

# Unused import for testing
import json  # This will be detected as unused

# Relative import (if this was in a package)
# from .some_module import something  # Would be relative

def test_function():
    """Function that uses some imports but not others"""
    current_path = Path.cwd()  # Uses Path
    files = os.listdir(current_path)  # Uses os
    return len(files)

# Note: sys, requests, ImportStatement, ImportAnalyzer, and json are not used
# This should be detected by the unused import checker