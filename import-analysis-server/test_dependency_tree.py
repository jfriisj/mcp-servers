#!/usr/bin/env python3
"""
Test script for the new dependency tree tool
"""

import asyncio
import json
from pathlib import Path
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_handler import MCPHandler
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver

async def test_dependency_tree():
    """Test the dependency tree tool"""
    
    # Setup dependencies
    project_root = Path("C:/github/mcp-servers/import-test-server")
    dependency_resolver = DependencyResolver(project_root)
    import_analyzer = ImportAnalyzer(dependency_resolver)
    analyze_imports_uc = AnalyzeImportsUseCase(import_analyzer)
    validate_deps_uc = ValidateDependenciesUseCase(dependency_resolver)
    
    # Create handler
    handler = MCPHandler(
        project_root=project_root,
        analyze_imports_uc=analyze_imports_uc,
        validate_deps_uc=validate_deps_uc,
        import_analyzer=import_analyzer,
        dependency_resolver=dependency_resolver
    )
    
    print("🌳 Testing Dependency Tree Tool")
    print("=" * 50)
    
    # Test 1: Text format
    print("\n1. Text format dependency tree:")
    args = {
        "project_path": "C:/github/mcp-servers/import-test-server/src",
        "format": "text",
        "max_depth": 3,
        "include_external": False
    }
    
    result = await handler._generate_dependency_tree(args)
    print(result[0].text)
    
    # Test 2: ASCII format
    print("\n\n2. ASCII format dependency tree:")
    args["format"] = "ascii"
    result = await handler._generate_dependency_tree(args)
    print(result[0].text)
    
    # Test 3: Mermaid format
    print("\n\n3. Mermaid format dependency tree:")
    args["format"] = "mermaid"
    result = await handler._generate_dependency_tree(args)
    print(result[0].text)
    
    # Test 4: With external dependencies
    print("\n\n4. Including external dependencies:")
    args = {
        "project_path": "C:/github/mcp-servers/import-test-server/src",
        "format": "text",
        "max_depth": 2,
        "include_external": True
    }
    result = await handler._generate_dependency_tree(args)
    print(result[0].text)

if __name__ == "__main__":
    asyncio.run(test_dependency_tree())