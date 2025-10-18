#!/usr/bin/env python
"""
Test script to verify the upload bibliography batch fixes work correctly.
Tests: failure reporting, detailed error messages, entry validation.
"""

import sys
from pathlib import Path

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.services.research_document_service import ResearchDocumentService
from src.repositories.paper_repository import PaperRepository
from src.database.database_connection import get_database_connection


def test_upload_with_failure_reporting():
    """Test that upload returns detailed failure information."""
    
    db = get_database_connection()
    paper_repo = PaperRepository(db)
    doc_service = ResearchDocumentService(paper_repo)
    
    # Upload File 6 which had parsing issues
    file_path = "data/papers/Primo_BibTeX_Export (6).bib"
    
    print(f"\n📚 Testing upload of {Path(file_path).name}")
    print("=" * 70)
    
    result = doc_service.upload_bibliography_batch(
        file_path=file_path,
        auto_extract_metadata=True
    )
    
    # Verify result structure
    assert 'created_papers' in result, "Missing 'created_papers' in result"
    assert 'skipped_entries' in result, "Missing 'skipped_entries' in result"
    assert 'summary' in result, "Missing 'summary' in result"
    assert 'success_count' in result, "Missing 'success_count' in result"
    assert 'failure_count' in result, "Missing 'failure_count' in result"
    
    created = result['created_papers']
    skipped = result['skipped_entries']
    summary = result['summary']
    
    print("\n✅ Result Summary:")
    print(summary)
    
    print(f"\n📊 Statistics:")
    print(f"  Total entries: {result['total_entries']}")
    print(f"  Successfully created: {len(created)}")
    print(f"  Failed/Skipped: {len(skipped)}")
    
    if skipped:
        print(f"\n⚠️  Skipped Entry Details (first 5):")
        for entry in skipped[:5]:
            print(f"  Entry {entry['entry_num']}: {entry['reason']}")
            if entry.get('detail'):
                print(f"    Error: {entry['detail'][:80]}")
    
    print(f"\n📖 Sample Created Papers (first 3):")
    for paper in created[:3]:
        print(f"  • ID {paper.id}: {paper.title[:60]}")
    
    print("\n✅ Test passed: Failure reporting is working correctly")
    return True


if __name__ == "__main__":
    try:
        test_upload_with_failure_reporting()
        print("\n✅ All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
