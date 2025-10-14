#!/usr/bin/env python3
"""
Test script to verify SLR workflow guidance tools are properly integrated.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import SLRMCPServer

async def test_workflow_tools():
    """Test that workflow tools are properly integrated."""
    try:
        # Initialize server
        print("🚀 Initializing SLR MCP Server...")
        server = SLRMCPServer()
        
        # Initialize dependencies
        print("⚙️ Initializing dependencies...")
        await server._initialize_dependencies()
        
        print("✅ Server initialization successful")
        
        # Check workflow tools availability
        print("\n📋 Available workflow tools:")
        handler = server.mcp_handler
        
        workflow_tools = [
            "create_slr_project",
            "get_slr_progress", 
            "get_next_steps",
            "create_screening_workflow",
            "screen_paper",
            "get_slr_guide"
        ]
        
        for tool in workflow_tools:
            has_tool = hasattr(handler, tool)
            status = "✅" if has_tool else "❌"
            print(f"{status} {tool}: {has_tool}")
        
        print("\n🎉 Workflow tools verification complete!")
        
        # Test will be done separately to avoid event loop conflicts
        print("📝 Note: Tool testing should be done in a separate process to avoid event loop conflicts.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_tools())