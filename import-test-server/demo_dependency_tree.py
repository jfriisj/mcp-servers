#!/usr/bin/env python3
"""
Simple test to demonstrate the dependency tree tool
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

async def demo_dependency_tree():
    """Demonstrate the dependency tree tool"""
    
    print("🌳 Import Test MCP Server - Dependency Tree Tool Demo")
    print("=" * 70)
    
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
    
    print(f"📊 Total MCP Tools Available: {len(handler.get_tools())}")
    print("\n🎯 Testing new dependency tree tool...\n")
    
    # Test on solid-server
    args = {
        "project_path": "C:/github/mcp-servers/solid-server/src",
        "format": "text",
        "max_depth": 2,
        "include_external": False
    }
    
    try:
        result = await handler.call_tool("import-test-dependency-tree", args)
        
        print("✅ Dependency tree generated successfully!")
        print("\n" + "="*50)
        print("SOLID SERVER DEPENDENCY TREE")
        print("="*50)
        
        output_lines = result[0].text.split('\n')
        # Show first 20 lines
        for line in output_lines[:20]:
            print(line)
        
        if len(output_lines) > 20:
            print("...")
            print(f"(showing first 20 of {len(output_lines)} lines)")
        
        print("\n" + "="*50)
        print("TESTING MERMAID FORMAT")
        print("="*50)
        
        # Test Mermaid format
        args["format"] = "mermaid"
        args["max_depth"] = 2
        result = await handler.call_tool("import-test-dependency-tree", args)
        
        mermaid_lines = result[0].text.split('\n')
        print("✅ Mermaid format generated!")
        print(f"📊 Generated {len(mermaid_lines)} lines of Mermaid code")
        print("\nFirst few lines:")
        for line in mermaid_lines[:10]:
            print(f"  {line}")
        
        print("\n🎉 All dependency tree formats working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_dependency_tree())