#!/usr/bin/env python3
"""
Test the screen_paper MCP tool to verify it records screening decisions correctly.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.container import Container
from src.handlers.mcp_handler import SLRMCPHandler
from mcp.types import TextContent


async def test_screen_paper_tool():
    """Test the enhanced screen_paper MCP tool."""
    print("=" * 100)
    print("🧪 Testing screen_paper MCP Tool for Recording Screening Decisions")
    print("=" * 100)
    
    # Initialize container
    print("\n📦 Initializing system...")
    container = Container(
        database_path="database/slr_database.db",
        project_root=Path(__file__).parent
    )
    
    try:
        await container.initialize()
        print("✅ System initialized")
        
        # Get MCP handler
        handler = container.get_mcp_handler()
        paper_repository = container.get_paper_repository()
        
        # Get some papers to test with
        print("\n📋 Fetching papers for screening test...")
        papers = paper_repository.list_papers(limit=5, offset=0)
        
        if not papers:
            print("❌ No papers found in database!")
            return 1
        
        print(f"✅ Found {len(papers)} papers to test")
        
        # Test cases: INCLUDE, EXCLUDE, UNCERTAIN with different confidence levels
        test_cases = [
            {
                "paper_id": papers[0].id if papers[0].id else 1,
                "decision": "include",
                "reviewer_id": "reviewer_1",
                "confidence_level": 0.95,
                "reason": "Directly addresses real-time speech translation platform with neural approaches",
                "description": "TEST 1: INCLUDE decision (high confidence)"
            },
            {
                "paper_id": papers[1].id if papers[1].id else 2,
                "decision": "exclude",
                "reviewer_id": "reviewer_2",
                "confidence_level": 0.90,
                "reason": "Text-only translation without speech component",
                "exclusion_criteria": ["EC2_TEXTONLY"],
                "description": "TEST 2: EXCLUDE decision with criteria"
            },
            {
                "paper_id": papers[2].id if papers[2].id else 4,
                "decision": "uncertain",
                "reviewer_id": "reviewer_1",
                "confidence_level": 0.55,
                "reason": "Limited information in abstract, needs full-text review for clarity",
                "description": "TEST 3: UNCERTAIN decision (needs discussion)"
            },
            {
                "paper_id": papers[3].id if papers[3].id else 5,
                "decision": "include",
                "reviewer_id": "reviewer_2",
                "confidence_level": 0.85,
                "reason": "Platform architecture design with multilingual support and evaluation",
                "description": "TEST 4: INCLUDE from different reviewer"
            },
            {
                "paper_id": papers[4].id if papers[4].id else 7,
                "decision": "exclude",
                "reviewer_id": "reviewer_1",
                "confidence_level": 0.92,
                "reason": "Conference proceedings with insufficient detail",
                "exclusion_criteria": ["EC3_INSUFFICIENT", "EC4_QUALITY"],
                "description": "TEST 5: EXCLUDE with multiple criteria"
            }
        ]
        
        print("\n" + "=" * 100)
        print("🔍 TESTING screen_paper TOOL")
        print("=" * 100)
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{test_case['description']}")
            print("-" * 100)
            
            # Prepare arguments for screen_paper tool
            arguments = {
                "project_id": 1,
                "paper_id": test_case["paper_id"],
                "decision": test_case["decision"],
                "stage": "title_abstract",
                "reviewer_id": test_case["reviewer_id"],
                "reason": test_case["reason"],
                "confidence_level": test_case["confidence_level"]
            }
            
            # Add exclusion criteria if provided
            if "exclusion_criteria" in test_case:
                arguments["exclusion_criteria"] = test_case["exclusion_criteria"]
            
            print(f"📝 Parameters:")
            print(f"   Paper ID: {test_case['paper_id']}")
            print(f"   Decision: {test_case['decision'].upper()}")
            print(f"   Reviewer: {test_case['reviewer_id']}")
            print(f"   Confidence: {test_case['confidence_level']}")
            print(f"   Reason: {test_case['reason']}")
            if "exclusion_criteria" in test_case:
                print(f"   Criteria: {', '.join(test_case['exclusion_criteria'])}")
            
            # Call screen_paper tool
            try:
                result = await handler.screen_paper(arguments)
                
                if result.isError:
                    print(f"\n❌ Error: {result.content}")
                    results.append({
                        "test": i,
                        "status": "FAILED",
                        "reason": "Tool returned error"
                    })
                else:
                    # Extract response
                    if result.content and isinstance(result.content[0], TextContent):
                        response_text = result.content[0].text
                        print(f"\n✅ SUCCESS!")
                        print(f"\nResponse:\n{response_text}")
                        
                        results.append({
                            "test": i,
                            "status": "PASSED",
                            "decision": test_case["decision"],
                            "paper_id": test_case["paper_id"]
                        })
                    else:
                        print(f"\n⚠️ Invalid response format")
                        results.append({
                            "test": i,
                            "status": "FAILED",
                            "reason": "Invalid response format"
                        })
            
            except Exception as e:
                print(f"\n❌ Exception: {str(e)}")
                results.append({
                    "test": i,
                    "status": "FAILED",
                    "reason": str(e)
                })
        
        # Summary
        print("\n" + "=" * 100)
        print("📊 TEST SUMMARY")
        print("=" * 100)
        
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        total = len(results)
        
        print(f"\n✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"Success Rate: {100*passed/total:.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 100)
        for r in results:
            status_emoji = "✅" if r["status"] == "PASSED" else "❌"
            print(f"  Test {r['test']}: {status_emoji} {r['status']}")
            if "decision" in r:
                print(f"             Decision: {r['decision'].upper()}, Paper: {r['paper_id']}")
            if "reason" in r:
                print(f"             Reason: {r['reason']}")
        
        print("\n" + "=" * 100)
        if failed == 0:
            print("✅ ALL TESTS PASSED - screen_paper MCP tool is working correctly!")
            print("=" * 100)
            return 0
        else:
            print(f"⚠️ {failed} test(s) failed - please review the output above")
            print("=" * 100)
            return 1
    
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_screen_paper_tool())
    sys.exit(exit_code)
