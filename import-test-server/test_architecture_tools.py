#!/usr/bin/env python3
"""
Test the new service dependency and architecture analysis tools
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

async def test_new_architecture_tools():
    """Test the new architecture and service dependency tools"""
    
    print("🏛️  TESTING NEW ARCHITECTURE TOOLS")
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
    
    # Test on the import-test-server itself (clean architecture)
    test_path = "C:/github/mcp-servers/import-test-server/src"
    
    print(f"🎯 Testing on: {test_path}")
    print(f"📊 Available Tools: {len(handler.get_tools())}\n")
    
    # Test 1: Service Dependencies Analysis
    print("1️⃣  SERVICE DEPENDENCIES ANALYSIS")
    print("-" * 60)
    try:
        result = await handler.call_tool("import-test-service-dependencies", {
            "project_path": test_path,
            "format": "text",
            "group_by": "layer",
            "show_details": True
        })
        print("✅ Service dependencies analysis completed")
        print(result[0].text)
        print("\n")
    except Exception as e:
        print(f"❌ Service dependencies analysis failed: {e}\n")
    
    # Test 2: Architecture Analysis
    print("2️⃣  ARCHITECTURE ANALYSIS") 
    print("-" * 60)
    try:
        result = await handler.call_tool("import-test-architecture-analysis", {
            "project_path": test_path,
            "architecture_type": "clean",
            "check_violations": True,
            "format": "text"
        })
        print("✅ Architecture analysis completed")
        print(result[0].text)
        print("\n")
    except Exception as e:
        print(f"❌ Architecture analysis failed: {e}\n")
    
    # Test 3: Service Dependencies Matrix
    print("3️⃣  SERVICE DEPENDENCIES MATRIX")
    print("-" * 60)
    try:
        result = await handler.call_tool("import-test-service-dependencies", {
            "project_path": test_path,
            "format": "matrix",
            "group_by": "layer"
        })
        print("✅ Service dependencies matrix completed")
        print(result[0].text)
        print("\n")
    except Exception as e:
        print(f"❌ Service dependencies matrix failed: {e}\n")
    
    # Test 4: Mermaid Service Dependencies
    print("4️⃣  MERMAID SERVICE DEPENDENCIES")
    print("-" * 60)
    try:
        result = await handler.call_tool("import-test-service-dependencies", {
            "project_path": test_path,
            "format": "mermaid",
            "group_by": "layer"
        })
        print("✅ Mermaid service dependencies completed")
        lines = result[0].text.split('\n')
        for line in lines[:15]:  # Show first 15 lines
            print(line)
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
        print("\n")
    except Exception as e:
        print(f"❌ Mermaid service dependencies failed: {e}\n")
    
    # Test 5: Architecture Analysis on Whisper Server (more complex)
    print("5️⃣  ARCHITECTURE ANALYSIS - WHISPER SERVER")
    print("-" * 60)
    whisper_path = "C:/github/mcp-servers/whisper-server/src"
    try:
        result = await handler.call_tool("import-test-architecture-analysis", {
            "project_path": whisper_path,
            "architecture_type": "auto",
            "check_violations": True,
            "format": "text"
        })
        print("✅ Whisper server architecture analysis completed")
        lines = result[0].text.split('\n')
        for line in lines[:25]:  # Show first 25 lines
            print(line)
        if len(lines) > 25:
            print(f"... ({len(lines) - 25} more lines)")
        print("\n")
    except Exception as e:
        print(f"❌ Whisper architecture analysis failed: {e}\n")
    
    # Test 6: Service Dependencies by Package
    print("6️⃣  SERVICE DEPENDENCIES BY PACKAGE")
    print("-" * 60)
    try:
        result = await handler.call_tool("import-test-service-dependencies", {
            "project_path": whisper_path,
            "format": "text",
            "group_by": "package",
            "show_details": False
        })
        print("✅ Package-level dependencies completed")
        lines = result[0].text.split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print("\n")
    except Exception as e:
        print(f"❌ Package dependencies failed: {e}\n")
    
    print("🎉 ALL ARCHITECTURE TOOLS TESTED!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_new_architecture_tools())