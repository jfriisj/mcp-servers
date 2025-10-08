#!/usr/bin/env python3
"""
Test script for Import Test MCP Server tools
============================================

This script tests all the tools to ensure they work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_handler import MCPHandler
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase


async def test_all_tools():
    """Test all MCP tools"""
    print("🔧 Testing Import Test MCP Server Tools")
    print("=" * 60)
    
    # Initialize components
    project_root = Path(__file__).parent.parent  # Go up to import-test-server root
    dependency_resolver = DependencyResolver(project_root)
    import_analyzer = ImportAnalyzer(dependency_resolver)
    
    # Initialize use cases
    analyze_imports_uc = AnalyzeImportsUseCase(import_analyzer)
    validate_deps_uc = ValidateDependenciesUseCase(dependency_resolver)
    
    # Initialize MCP handler
    handler = MCPHandler(
        project_root=project_root,
        analyze_imports_uc=analyze_imports_uc,
        validate_deps_uc=validate_deps_uc,
        import_analyzer=import_analyzer,
        dependency_resolver=dependency_resolver
    )
    
    # Test cases
    test_cases = [
        {
            "name": "import-test-analyze-file",
            "args": {"file_path": "src/main.py"},
            "description": "Analyze imports in main.py"
        },
        {
            "name": "import-test-analyze-project", 
            "args": {"project_path": ".", "max_files": 10},
            "description": "Analyze entire project"
        },
        {
            "name": "import-test-circular-imports",
            "args": {"project_path": "."},
            "description": "Check for circular imports"
        },
        {
            "name": "import-test-validate-dependencies",
            "args": {"project_path": "."},
            "description": "Validate dependencies"
        },
        {
            "name": "import-test-unused-imports",
            "args": {"path": "src"},
            "description": "Find unused imports"
        },
        {
            "name": "import-test-get-stats",
            "args": {"project_path": "."},
            "description": "Get import statistics"
        },
        {
            "name": "import-test-check-style",
            "args": {"path": "src"},
            "description": "Check import style (placeholder)"
        },
        {
            "name": "import-test-resolve-import",
            "args": {"import_statement": "import os", "from_file": "src/main.py"},
            "description": "Resolve specific import (placeholder)"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Args: {test_case['args']}")
        
        try:
            result = await handler.call_tool(test_case['name'], test_case['args'])
            
            if result and len(result) > 0:
                # Get the text content and show first few lines
                text = result[0].text if hasattr(result[0], 'text') else str(result[0])
                lines = text.split('\n')
                preview = '\n'.join(lines[:5])
                if len(lines) > 5:
                    preview += f"\n   ... ({len(lines) - 5} more lines)"
                
                print(f"   ✅ SUCCESS")
                print(f"   Preview: {preview[:200]}...")
                results.append({"tool": test_case['name'], "status": "SUCCESS", "preview": preview[:100]})
            else:
                print(f"   ⚠️  WARNING: Empty result")
                results.append({"tool": test_case['name'], "status": "WARNING", "error": "Empty result"})
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({"tool": test_case['name'], "status": "ERROR", "error": str(e)})
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Test Results Summary")
    print(f"{'=' * 60}")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    warning_count = sum(1 for r in results if r['status'] == 'WARNING') 
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"✅ Successful: {success_count}/{len(results)}")
    print(f"⚠️  Warnings: {warning_count}/{len(results)}")
    print(f"❌ Errors: {error_count}/{len(results)}")
    
    if error_count > 0:
        print(f"\n❌ Failed Tools:")
        for result in results:
            if result['status'] == 'ERROR':
                print(f"  - {result['tool']}: {result['error']}")
    
    if warning_count > 0:
        print(f"\n⚠️  Warning Tools:")
        for result in results:
            if result['status'] == 'WARNING':
                print(f"  - {result['tool']}: {result['error']}")
    
    print(f"\n🎯 Overall Status: ", end="")
    if error_count == 0 and warning_count == 0:
        print("🟢 ALL TESTS PASSED")
    elif error_count == 0:
        print("🟡 MOSTLY WORKING (some warnings)")
    else:
        print("🔴 ISSUES FOUND (some errors)")
    
    return success_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)