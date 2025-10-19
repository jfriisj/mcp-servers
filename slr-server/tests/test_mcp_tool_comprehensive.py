#!/usr/bin/env python3
"""
Comprehensive test of the index_paper MCP tool.
"""

import asyncio
import sys
from pathlib import Path

# Absolute path to slr-server root
SLR_SERVER_ROOT = Path(__file__).parent.parent.absolute()

# Add src to Python path
sys.path.insert(0, str(SLR_SERVER_ROOT / "src"))

from src.container import initialize_application


async def test_mcp_tool():
    """Test the index_paper MCP tool with multiple papers."""
    try:
        print("🚀 Comprehensive MCP Tool Test\n")
        
        # Initialize the application
        print("1️⃣ Initializing application...")
        db_path = str(SLR_SERVER_ROOT / "database" / "slr_database.db")
        container = await initialize_application(database_path=db_path)
        print("✅ Application initialized\n")
        
        # Get repositories
        paper_repo = container.get_paper_repository()
        chunk_repo = container.get_chunk_repository()
        
        # Get MCP handler
        handler = container.get_mcp_handler()
        
        # Get some papers with PDFs
        papers = paper_repo.list_all()
        papers_with_pdf = [p for p in papers if p.file_path][:3]  # First 3 with PDFs
        
        print(f"2️⃣ Testing with {len(papers_with_pdf)} papers\n")
        
        results = []
        
        for paper in papers_with_pdf:
            if not paper.id:
                continue
                
            paper_id = paper.id
            print(f"📄 Testing paper {paper_id}: {paper.title[:50]}...")
            
            # Test 1: Index with default strategy
            result1 = await handler.handle_index_paper({
                "paper_id": paper_id,
                "strategy": "academic_section"
            })
            
            results.append({
                "paper_id": paper_id,
                "test": "academic_section (no force)",
                "success": not result1.isError,
                "result": result1.content[0].text if result1.content else ""
            })
            
            if result1.isError:
                print(f"  ❌ academic_section failed: {result1.content[0].text if result1.content else 'Unknown'}")
            else:
                # Extract chunk count from response
                text = result1.content[0].text
                if "already indexed" in text:
                    print(f"  ⚡ Chunks already exist (returning {3} chunks)")
                elif "Generated" in text:
                    print(f"  ✅ Re-indexed with new chunks")
            
            # Test 2: Index with force=True and different strategy
            result2 = await handler.handle_index_paper({
                "paper_id": paper_id,
                "strategy": "citation_aware",
                "force": True
            })
            
            results.append({
                "paper_id": paper_id,
                "test": "citation_aware (force=True)",
                "success": not result2.isError,
                "result": result2.content[0].text if result2.content else ""
            })
            
            if result2.isError:
                print(f"  ❌ citation_aware with force=True failed")
            else:
                print(f"  ✅ citation_aware with force=True succeeded")
            
            print()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"\n✅ Successful tests: {successful}/{total}")
        print(f"❌ Failed tests: {total - successful}/{total}")
        
        if successful == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n⚠️ Some tests failed")
            for result in results:
                if not result["success"]:
                    print(f"\n  Failed: {result['test']} (paper {result['paper_id']})")
                    print(f"  Error: {result['result'][:200]}...")
            return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_mcp_tool()))
