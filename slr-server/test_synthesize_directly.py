"""Direct test of synthesize_evidence to get full traceback."""

import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.container import Container


async def test_synthesize():
    """Test synthesize evidence directly."""
    # Initialize container
    container = Container()
    await container.initialize()
    
    # Get evidence service
    evidence_service = container.get_evidence_service()
    
    # Test with papers that have NO publication years
    paper_ids = [253, 252, 251]
    
    print(f"Testing synthesize_evidence with papers {paper_ids}")
    print("=" * 60)
    
    try:
        result = await evidence_service.synthesize_evidence(
            paper_ids=paper_ids,
            synthesis_method="narrative",
            outcome_measures=[]
        )
        print("✅ SUCCESS!")
        if result.narrative_summary:
            print(f"Result: {result.narrative_summary[:200]}...")
        else:
            print("Result: No narrative summary generated")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Close container
    container.close()


if __name__ == "__main__":
    asyncio.run(test_synthesize())
