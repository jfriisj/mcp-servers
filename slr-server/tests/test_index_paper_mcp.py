#!/usr/bin/env python3
"""
Test the index_paper MCP tool directly.
"""

import asyncio
import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import initialize_application
from src.handlers.mcp_handler import SLRMCPHandler


async def test_index_paper_mcp():
    """Test indexing a paper using the MCP handler directly."""
    try:
        print("🚀 Testing index_paper MCP tool...")
        
        # Initialize the application
        print("📦 Initializing application...")
        container = await initialize_application()
        
        # Get the MCP handler
        handler = container.get_mcp_handler()
        
        # Test with a paper that has a PDF
        # From the conversation, papers 506-504 and down to 1 have PDFs
        test_paper_id = 506
        
        print(f"\n📄 Testing with paper_id={test_paper_id}")
        
        # Call the handler directly
        result = await handler.handle_index_paper({
            "paper_id": test_paper_id,
            "strategy": "academic_section",
            "force": False
        })
        
        print(f"\n✅ Result type: {type(result)}")
        print(f"📊 Result content count: {len(result.content)}")
        print(f"❌ Is error: {getattr(result, 'isError', False)}")
        
        if result.content:
            text = result.content[0].text
            # Print first 1000 chars
            print(f"\n📋 Response (first 1000 chars):\n{text[:1000]}")
            if len(text) > 1000:
                print(f"...\n[Total length: {len(text)} chars]")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(test_index_paper_mcp()))
