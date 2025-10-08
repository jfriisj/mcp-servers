#!/usr/bin/env python3
"""
Comprehensive test of all import-test tools on whisper-server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_handler import MCPHandler
from application.analyze_imports import AnalyzeImportsUseCase
from application.validate_dependencies import ValidateDependenciesUseCase
from infrastructure.import_analyzer import ImportAnalyzer
from infrastructure.dependency_resolver import DependencyResolver

async def test_all_tools_on_whisper():
    """Test all import-test tools on whisper-server"""
    
    print("🎙️  COMPREHENSIVE IMPORT ANALYSIS - WHISPER SERVER")
    print("=" * 80)
    
    # Setup
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
    
    whisper_path = "C:/github/mcp-servers/whisper-server"
    
    print(f"📊 Available Tools: {len(handler.get_tools())}")
    print(f"🎯 Target: {whisper_path}\n")
    
    # Test 1: Project Analysis
    print("1️⃣  PROJECT-WIDE ANALYSIS")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-analyze-project", {
            "project_path": whisper_path,
            "max_files": 50
        })
        print("✅ Project analysis completed")
        lines = result[0].text.split('\n')
        for line in lines[:15]:  # Show first 15 lines
            print(line)
        print("...\n")
    except Exception as e:
        print(f"❌ Project analysis failed: {e}\n")
    
    # Test 2: Circular Imports
    print("2️⃣  CIRCULAR IMPORT DETECTION")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-circular-imports", {
            "project_path": whisper_path
        })
        print("✅ Circular import check completed")
        print(result[0].text)
        print()
    except Exception as e:
        print(f"❌ Circular import check failed: {e}\n")
    
    # Test 3: Dependency Validation
    print("3️⃣  DEPENDENCY VALIDATION")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-validate-dependencies", {
            "project_path": whisper_path
        })
        print("✅ Dependency validation completed")
        lines = result[0].text.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            print(line)
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print()
    except Exception as e:
        print(f"❌ Dependency validation failed: {e}\n")
    
    # Test 4: Unused Imports
    print("4️⃣  UNUSED IMPORTS DETECTION")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-unused-imports", {
            "path": whisper_path + "/src"
        })
        print("✅ Unused imports check completed")
        lines = result[0].text.split('\n')
        for line in lines[:15]:
            print(line)
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
        print()
    except Exception as e:
        print(f"❌ Unused imports check failed: {e}\n")
    
    # Test 5: Statistics
    print("5️⃣  PROJECT STATISTICS")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-get-stats", {
            "project_path": whisper_path
        })
        print("✅ Statistics generated")
        print(result[0].text)
        print()
    except Exception as e:
        print(f"❌ Statistics generation failed: {e}\n")
    
    # Test 6: Dependency Tree
    print("6️⃣  DEPENDENCY TREE VISUALIZATION")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-dependency-tree", {
            "project_path": whisper_path + "/src",
            "format": "text",
            "max_depth": 3,
            "include_external": False
        })
        print("✅ Dependency tree generated")
        lines = result[0].text.split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print()
    except Exception as e:
        print(f"❌ Dependency tree generation failed: {e}\n")
    
    # Test 7: Specific File Analysis
    print("7️⃣  SPECIFIC FILE ANALYSIS")
    print("-" * 50)
    main_file = whisper_path + "/src/main.py"
    try:
        result = await handler.call_tool("import-test-analyze-file", {
            "file_path": main_file
        })
        print(f"✅ File analysis completed for main.py")
        lines = result[0].text.split('\n')
        for line in lines[:15]:
            print(line)
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
        print()
    except Exception as e:
        print(f"❌ File analysis failed: {e}\n")
    
    # Test 8: Dependency Tree with External Dependencies
    print("8️⃣  DEPENDENCY TREE WITH EXTERNALS")
    print("-" * 50)
    try:
        result = await handler.call_tool("import-test-dependency-tree", {
            "project_path": whisper_path + "/src",
            "format": "text",
            "max_depth": 2,
            "include_external": True
        })
        print("✅ Dependency tree with externals generated")
        lines = result[0].text.split('\n')
        for line in lines[:15]:
            print(line)
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
        print()
    except Exception as e:
        print(f"❌ External dependency tree failed: {e}\n")
    
    print("🎉 COMPREHENSIVE ANALYSIS COMPLETED!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_all_tools_on_whisper())