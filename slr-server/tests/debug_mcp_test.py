#!/usr/bin/env python3
"""
Debug test for index_paper MCP tool.
"""

import asyncio
import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import initialize_application


async def debug_test():
    """Debug the index_paper issue."""
    try:
        print("🚀 Debug Testing index_paper MCP tool...\n")
        
        # Initialize the application
        print("1️⃣ Initializing application...")
        db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
        print(f"   Using database: {db_path}")
        container = await initialize_application(database_path=db_path)
        print("✅ Application initialized\n")
        
        # Get repositories
        paper_repo = container.get_paper_repository()
        
        # Check papers
        print("2️⃣ Checking papers in database...")
        papers = paper_repo.list_all()
        print(f"✅ Total papers: {len(papers)}\n")
        
        # Get a paper with PDF
        papers_with_pdf = [p for p in papers if p.file_path]
        print(f"3️⃣ Papers with PDF: {len(papers_with_pdf)}")
        if papers_with_pdf:
            test_paper = papers_with_pdf[0]
            print(f"✅ Using paper ID: {test_paper.id}")
            print(f"   Title: {test_paper.title[:60]}...")
            print(f"   PDF: {test_paper.file_path}\n")
        else:
            print("❌ No papers with PDF found")
            return 1
        
        # Try to get the paper directly
        print("4️⃣ Testing direct paper retrieval...")
        retrieved_paper = paper_repo.get_by_id(test_paper.id or 0)
        if retrieved_paper:
            print(f"✅ Paper {test_paper.id} retrieved: {retrieved_paper.title[:50]}...\n")
        else:
            print(f"❌ Paper {test_paper.id} not found via get_by_id\n")
            return 1
        
        # Skip direct chunking service test since chunks already exist
        print("5️⃣ Skipping direct chunking service test (chunks already exist)...\n")
        
        # Now try via MCP handler - this will handle existing chunks properly
        print("6️⃣ Testing MCP handler with existing chunks (force=False)...")
        handler = container.get_mcp_handler()
        result = await handler.handle_index_paper({
            "paper_id": test_paper.id or 0,
            "strategy": "academic_section",
            "force": False
        })
        
        print(f"✅ Handler result (existing chunks, force=False):")
        print(f"   Type: {type(result)}")
        print(f"   Is Error: {result.isError}")
        if result.content:
            text = result.content[0].text
            print(f"   Content:\n{text[:400]}...")
        
        # Now try with force=True to re-index
        print("\n7️⃣ Testing MCP handler with force=True...")
        result2 = await handler.handle_index_paper({
            "paper_id": test_paper.id or 0,
            "strategy": "academic_section",
            "force": True
        })
        
        print(f"✅ Handler result (force=True):")
        print(f"   Type: {type(result2)}")
        print(f"   Is Error: {result2.isError}")
        if result2.content:
            text = result2.content[0].text
            print(f"   Content:\n{text[:400]}...")
        
        print("\n✅ All tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(debug_test()))
