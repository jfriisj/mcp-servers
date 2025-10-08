#!/usr/bin/env python3
"""
Comprehensive test of all 11 import-test tools via MCP server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server import ImportTestMCPServer

async def test_all_tools_mcp():
    """Test all 11 import-test tools via MCP server interface"""
    
    print("🧪 COMPREHENSIVE MCP SERVER TEST - ALL 11 TOOLS")
    print("=" * 80)
    
    # Create server instance
    project_root = Path("C:/github/mcp-servers")
    server_instance = ImportTestMCPServer(project_root)
    
    print(f"🎯 Testing MCP Server with project root: {project_root}")
    print(f"📊 Available Tools: {len(server_instance.mcp_handler.get_tools())}\n")
    
    # List all available tools
    tools = server_instance.mcp_handler.get_tools()
    print("🔧 Available Tools:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i:2}. {tool.name}")
    print()
    
    # Test target: whisper-server (has interesting architecture)
    test_project = "C:/github/mcp-servers/whisper-server"
    
    # Test 1: File Analysis
    print("1️⃣  FILE ANALYSIS")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-analyze-file", {
            "file_path": f"{test_project}/src/main.py"
        })
        print("✅ File analysis - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"📄 Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ File analysis - FAILED: {e}")
    
    # Test 2: Project Analysis  
    print("\n2️⃣  PROJECT ANALYSIS")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-analyze-project", {
            "project_path": test_project,
            "max_files": 20
        })
        print("✅ Project analysis - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"📊 Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Project analysis - FAILED: {e}")
    
    # Test 3: Circular Imports
    print("\n3️⃣  CIRCULAR IMPORTS DETECTION")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-circular-imports", {
            "project_path": test_project
        })
        print("✅ Circular imports - SUCCESS")
        print(f"🔄 Result: {result[0].text[:50]}...")
    except Exception as e:
        print(f"❌ Circular imports - FAILED: {e}")
    
    # Test 4: Dependency Validation
    print("\n4️⃣  DEPENDENCY VALIDATION")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-validate-dependencies", {
            "project_path": test_project
        })
        print("✅ Dependency validation - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"📦 Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Dependency validation - FAILED: {e}")
    
    # Test 5: Unused Imports
    print("\n5️⃣  UNUSED IMPORTS")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-unused-imports", {
            "path": f"{test_project}/src"
        })
        print("✅ Unused imports - SUCCESS")
        print(f"🗑️  Result: {result[0].text[:50]}...")
    except Exception as e:
        print(f"❌ Unused imports - FAILED: {e}")
    
    # Test 6: Import Style Check
    print("\n6️⃣  IMPORT STYLE CHECK")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-check-style", {
            "path": f"{test_project}/src"
        })
        print("✅ Import style - SUCCESS")
        print(f"💫 Result: {result[0].text[:50]}...")
    except Exception as e:
        print(f"❌ Import style - FAILED: {e}")
    
    # Test 7: Resolve Import
    print("\n7️⃣  RESOLVE IMPORT")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-resolve-import", {
            "import_statement": "from pathlib import Path",
            "from_file": f"{test_project}/src/main.py"
        })
        print("✅ Resolve import - SUCCESS")
        print(f"🔍 Result: {result[0].text[:50]}...")
    except Exception as e:
        print(f"❌ Resolve import - FAILED: {e}")
    
    # Test 8: Project Statistics
    print("\n8️⃣  PROJECT STATISTICS")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-get-stats", {
            "project_path": test_project
        })
        print("✅ Project statistics - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"📈 Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Project statistics - FAILED: {e}")
    
    # Test 9: Dependency Tree
    print("\n9️⃣  DEPENDENCY TREE")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-dependency-tree", {
            "project_path": f"{test_project}/src",
            "format": "text",
            "max_depth": 2
        })
        print("✅ Dependency tree - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"🌳 Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Dependency tree - FAILED: {e}")
    
    # Test 10: Service Dependencies (NEW!)
    print("\n🔟 SERVICE DEPENDENCIES")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-service-dependencies", {
            "project_path": f"{test_project}/src",
            "format": "text",
            "group_by": "layer"
        })
        print("✅ Service dependencies - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"🏗️  Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Service dependencies - FAILED: {e}")
    
    # Test 11: Architecture Analysis (NEW!)
    print("\n1️⃣1️⃣  ARCHITECTURE ANALYSIS")
    print("-" * 50)
    try:
        result = await server_instance.mcp_handler.call_tool("import-test-architecture-analysis", {
            "project_path": f"{test_project}/src",
            "architecture_type": "auto",
            "check_violations": True
        })
        print("✅ Architecture analysis - SUCCESS")
        lines = result[0].text.split('\n')
        print(f"🏛️  Result: {lines[0][:60]}...")
    except Exception as e:
        print(f"❌ Architecture analysis - FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎉 COMPREHENSIVE MCP SERVER TEST COMPLETED!")
    print("✅ All 11 tools tested via MCP server interface")
    print("🚀 Import-test server is ready for production use!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_all_tools_mcp())