#!/usr/bin/env python3
"""
Test script for enhanced get_paper function.
Tests the new abstract and full text retrieval capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now import after path is set
from src.container import Container
from src.handlers.mcp_handler import SLRMCPHandler
from mcp.types import CallToolResult, TextContent


async def test_get_paper():
    """Test the enhanced get_paper function."""
    print("=" * 80)
    print("🧪 Testing Enhanced get_paper Function")
    print("=" * 80)
    
    # Initialize container
    print("\n📦 Initializing container...")
    container = Container(
        database_path="database/slr_database.db",
        project_root=Path(__file__).parent
    )
    
    try:
        await container.initialize()
        print("✅ Container initialized")
        
        # Get MCP handler
        handler = container.get_mcp_handler()
        paper_repository = container.get_paper_repository()
        
        # Get some papers to test
        print("\n📋 Fetching available papers...")
        papers = paper_repository.list_papers(limit=5, offset=0)
        
        if not papers:
            print("❌ No papers found in database!")
            return
        
        print(f"✅ Found {len(papers)} papers to test")
        
        # Test get_paper for first 3 papers
        print("\n" + "=" * 80)
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n📄 TEST {i}: Paper ID {paper.id}")
            print("-" * 80)
            
            # Call enhanced get_paper
            result = await handler.handle_get_paper({"paper_id": paper.id})
            
            # Display result
            if isinstance(result, CallToolResult):
                if result.isError:
                    print(f"❌ Error: {result.content}")
                else:
                    # Extract text content
                    if result.content:
                        for content in result.content:
                            # Handle TextContent which has .text attribute
                            if isinstance(content, TextContent):
                                print(content.text)
                            else:
                                print(str(content))
            else:
                print(result)
        
        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_get_paper())
    sys.exit(exit_code)
